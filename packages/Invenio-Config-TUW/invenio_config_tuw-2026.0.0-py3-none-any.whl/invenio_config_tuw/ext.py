# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2026 TU Wien.
#
# Invenio-Config-TUW is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module containing some customizations and configuration for TU Wien."""

from datetime import UTC, datetime
from traceback import format_exc
from typing import List

from celery.signals import task_failure
from flask import got_request_exception, request
from flask_minify import Minify
from flask_principal import identity_loaded
from flask_security import current_user
from flask_security.signals import user_registered
from invenio_base.utils import obj_or_import_string
from invenio_files_rest.models import Location
from redis import StrictRedis
from werkzeug.utils import cached_property

from . import config
from .auth.utils import auto_trust_user
from .permissions.generators import tiss_user_need
from .startup.config import (
    assemble_and_populate_config,
    override_flask_config,
    override_prefixed_config,
)


def load_tiss_user_need_on_identity_loaded(sender, identity):
    """Mark users with a TISS ID in their profile with a special ``SystemRoleNeed``."""
    if bool(current_user) and current_user.is_authenticated:
        if current_user.user_profile.get("tiss_id"):
            identity.provides.add(tiss_user_need)


@user_registered.connect
def auto_trust_new_user(sender, user, **kwargs):
    """Execute `auto_trust_user()` on newly created users.

    NOTE: this function won't be called when a user is created via the CLI
          ('invenio users create'), because it doesn't send the 'user_registered' signal
    """
    # NOTE: 'sender' and 'kwargs' are ignored, but they're required to match the
    #       expected function signature
    auto_trust_user(user)


class InvenioConfigTUW(object):
    """Invenio-Config-TUW extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.app = app
        self.init_config(app)
        self.init_minify(app)
        self.handle_server_name(app)
        self.register_celery_task_failure_handler()
        self.register_request_exception_logger()
        self.register_noindex_header()
        identity_loaded.connect_via(app)(load_tiss_user_need_on_identity_loaded)
        app.extensions["invenio-config-tuw"] = self

    def register_noindex_header(self):
        """Set the "X-Robots-Tag: noindex" header on every response if configured."""
        if self.app.config.get("CONFIG_TUW_ROBOTS_NOINDEX", False):

            @self.app.after_request
            def _set_noindex_header(response):
                response.headers["X-Robots-Tag"] = "noindex"
                return response

    def handle_server_name(self, app):
        """Pop the `SERVER_NAME` configuration item between requests.

        This can be useful in multi-domain setups where for some reason, absolute
        URLs with the currently requested hostname need to be generated inside an
        active request context (e.g. OIDC redirect URIs).
        It seems like if `SERVER_NAME` is set, it will take precedence over
        HTTP `Host` when calling `url_for()`.
        """
        self.server_name = app.config.get("SERVER_NAME", None)

        # since allowing the client to set arbitrary vlaues of the HTTP Host header
        # field can lead to arbitrary redirects, it's important to keep track of
        # allowed values
        trusted_hosts = app.config.get("TRUSTED_HOSTS") or []
        if self.server_name and self.server_name not in trusted_hosts:
            trusted_hosts.append(self.server_name)

        app.config["TRUSTED_HOSTS"] = trusted_hosts

        @app.before_request
        def pop_server_name():
            """Unset `SERVER_NAME` to prefer the HOST HTTP header value."""
            self.server_name = app.config.get("SERVER_NAME", None)
            app.config["SERVER_NAME"] = None

        @app.after_request
        def restore_server_name(response):
            """Restore `SERVER_NAME` enable creating URLs outside of requests."""
            app.config.setdefault("SERVER_NAME", self.server_name)
            return response

    def init_config(self, app):
        """Initialize configuration.

        We use our comfortable position between the finalized initial loading of
        configuration and the start of extension loading to perform a little bit
        of magic on the configuration items, like building connection URIs from
        their various pieces.
        """
        override_flask_config(app)
        override_prefixed_config(app)
        assemble_and_populate_config(app)

        for key in dir(config):
            self.app.config.setdefault(key, getattr(config, key))

        # the datacenter symbol seems to be the username for DataCite Fabrica
        if app.config.get("DATACITE_ENABLED", False):
            key = "DATACITE_DATACENTER_SYMBOL"
            if not app.config.get(key, None):
                app.config[key] = app.config["DATACITE_USERNAME"]

    def init_minify(self, app):
        """Initialize the Flask-Minify extension.

        It seems like this extension may cause issues with certain user-related
        operations in the system and has thus been disabled by default.
        """
        minify_enabled = app.config.get("CONFIG_TUW_MINIFY_ENABLED", False)
        if minify_enabled and "flask-minify" not in app.extensions:
            minify = Minify(app, static=False, go=False)
            app.extensions["flask-minify"] = minify

    def auto_accept_record_curation_request(self, request) -> bool:
        """Check if the request should be auto-accepted according to the config."""
        auto_accept = self.app.config.get(
            "CONFIG_TUW_AUTO_ACCEPT_CURATION_REQUESTS", False
        )
        if isinstance(auto_accept, bool):
            return auto_accept

        return obj_or_import_string(auto_accept)(request)

    def _validate_kv_category(self, category):
        """Validate the category being either 'fail' or 'error'.

        The 'fail' category is for (Celery) background task failures,
        'error' is for unhandled request exceptions.
        """
        if category not in ["fail", "error"]:
            raise ValueError(
                f"unknown category '{category}', needs to be either 'fail' or 'error'"
            )

    def _store_kv_set(self, category, entry_id, data, ttl=None):
        """Store the given set entry in the KV store."""
        ttl = ttl if ttl is not None else self.app.config["CONFIG_TUW_KV_LOG_TTL"]
        self._validate_kv_category(category)
        key = f"tuw:{category}:{entry_id}"
        self.kv_store.hset(key, mapping={k: str(v) for k, v in data.items()})

        if ttl := abs(ttl or 0):
            self.kv_store.expire(key, ttl)

        return key

    def _get_stored_kv_sets(self, category):
        """Get all stored set entries for the given category from the KV store."""
        self._validate_kv_category(category)
        keys = self.kv_store.keys(f"tuw:{category}:*")
        entries = [
            {k.decode(): v.decode() for k, v in self.kv_store.hgetall(key).items()}
            for key in keys
        ]
        for entry in entries:
            if timestamp := entry.get("timestamp"):
                entry["timestamp"] = datetime.fromtimestamp(float(timestamp), tz=UTC)

        return entries

    def register_celery_task_failure_handler(self):
        """Register a handler for celery task failures."""
        if not self.app.config["CONFIG_TUW_LOG_TASK_FAILURES"]:
            return

        @task_failure.connect(weak=False)
        def store_failure(task_id, exception, einfo, sender, *args, **kwargs):
            """Collect info about the task failure and store it."""
            info = {
                "task_id": task_id,
                "task_name": sender.name,
                "task_args": kwargs["args"],
                "task_kwargs": kwargs["kwargs"],
                "exception": exception,
                "exception_info": einfo,
                "timestamp": datetime.now(tz=UTC).timestamp(),
            }
            self.store_task_failure(info)

    def store_task_failure(self, task_failure_data, ttl=None):
        """Store information about a background task's failure."""
        return self._store_kv_set(
            "fail", task_failure_data["task_id"], task_failure_data, ttl=ttl
        )

    def get_stored_task_failures(self):
        """Retrieve the stored information about recent task failures."""
        return self._get_stored_kv_sets("fail")

    def register_request_exception_logger(self):
        """Register a handler for unhandled request exceptions."""
        if not self.app.config["CONFIG_TUW_LOG_UNHANDLED_REQUEST_EXCEPTIONS"]:
            return

        def store_request_exception_details(sender, exception, **extra):
            """Collect info about the exception and store it."""
            current_timestamp = datetime.now(tz=UTC).timestamp()
            data = {
                "id": f"{int(current_timestamp)}-{id(exception)}",
                "exception": exception,
                "exception_type": type(exception).__name__,
                "traceback": format_exc(),
                "user_id": None,
                "user": "anonymous",
                "request_url": request.url,
                "request_remote_addr": request.remote_addr,
                "request_body": "<no body>",
                "request_body_length": request.content_length or 0,
                "timestamp": current_timestamp,
            }

            if request.content_length and request.content_length < (1024 * 512):
                data["body"] = request.get_data(as_text=True)

            if bool(current_user) and not current_user.is_anonymous:
                data["user_id"] = current_user.id
                data["user"] = current_user.email

            self.store_request_exception(data)

        got_request_exception.connect_via(self.app)(store_request_exception_details)

    def store_request_exception(self, exception_data, ttl=None):
        """Store information about an unhandled request exception."""
        return self._store_kv_set(
            "error", exception_data["id"], exception_data, ttl=ttl
        )

    def get_stored_request_exceptions(self):
        """Retrieve the stored information about recent unhandled request exceptions."""
        return self._get_stored_kv_sets("error")

    def generate_record_curation_request_remarks(self, request) -> List[str]:
        """Generate remarks to automatically add as comment to the curation request."""
        generate_remarks = self.app.config.get(
            "CONFIG_TUW_AUTO_COMMENT_CURATION_REQUESTS", None
        )
        if generate_remarks is None:
            return []

        return obj_or_import_string(generate_remarks)(request)

    def default_location_for_ip(self, ip_addr):
        """Return the default storage location per IP address."""
        lookup = self.app.config.get("CONFIG_TUW_STORAGE_LOCATION_FOR_IP", {})
        if ip_addr not in lookup:
            return None

        location = lookup[ip_addr]
        if isinstance(location, Location):
            return location
        elif isinstance(location, str):
            return Location.get_by_name(location)
        else:
            self.app.logger.warning(
                f"invalid location set for address {ip_addr}: {location}"
            )
            return None

    @property
    def curations_enabled(self):
        """Shorthand for ``self.app.config.get["CONFIG_TUW_CURATIONS_ENABLED"]``."""
        return self.app.config["CONFIG_TUW_CURATIONS_ENABLED"]

    @property
    def email_xsender_value(self):
        """Return the value for the X-Sender email header field."""
        value = self.app.config.get("CONFIG_TUW_MAIL_XSENDER", None)
        identifier = self.app.config.get("CONFIG_TUW_SITE_IDENTIFIER", None)
        hostname = self.app.config.get("SERVER_NAME", None)

        # get the first "allowed host" entry
        trusted_hosts = [*self.app.config.get("TRUSTED_HOSTS", []), None]
        trusted_host = trusted_hosts[0]

        # return the first value that isn't None
        return value or identifier or hostname or trusted_host

    @cached_property
    def kv_store(self):
        """Get the key/value store, typically Redis/Valkey."""
        redis_url = self.app.config.get("CACHE_REDIS_URL", None)
        if redis_url:
            return StrictRedis.from_url(redis_url)
