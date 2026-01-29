# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 TU Wien.
#
# Invenio-Config-TUW is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.


"""Overrides for core services."""

import re
from collections import namedtuple
from datetime import datetime
from typing import Iterable, Optional
from urllib.parse import urlparse

import dictdiffer
from flask import Flask, current_app, request
from invenio_base import invenio_url_for
from invenio_curations.services.components import (
    CurationComponent as BaseCurationComponent,
)
from invenio_drafts_resources.services.records.components import ServiceComponent
from invenio_pidstore.models import PIDStatus
from invenio_rdm_records.records.api import get_files_quota
from invenio_rdm_records.services.components import DefaultRecordsComponents
from invenio_records_resources.services.uow import TaskOp
from invenio_requests.resolvers.registry import ResolverRegistry
from werkzeug.exceptions import HTTPException

from .proxies import current_config_tuw
from .tasks import send_metadata_edit_notification, send_publication_notification

_img_tag_pattern = re.compile(r"<img(.*?)/?>")
"""Pattern for finding <img> tag content in texts (with whitespace stripped)."""

_img_src_attribute_pattern = re.compile(r'src="([^"]+)"')
"""Pattern for finding the src attribute in <img> tags (with whitespace stripped)."""


def _get_img_src_attributes(text: str) -> Iterable[re.Match]:
    """Generator for finding all <img> src attributes in the text."""
    text = re.sub(r"\s", "", text.replace("'", '"'))

    for match in _img_tag_pattern.finditer(text):
        img_tag_content = match.group(1)
        if (src_attrib := _img_src_attribute_pattern.search(img_tag_content)) is None:
            continue

        yield src_attrib


def _get_app_for_endpoint(endpoint) -> Optional[Flask]:
    """Try to get the running Flask application that knows given endpoint."""
    app = current_app
    try:
        if endpoint not in app.view_functions:
            app = app.wsgi_app.app.mounts["/api"]

    except (KeyError, AttributeError):
        return None

    return app


class ParentAccessSettingsComponent(ServiceComponent):
    """Service component that allows access requests per default."""

    def create(self, identity, record, **kwargs):
        """Set the parent access settings to allow access requests."""
        settings = record.parent.access.settings
        settings.allow_guest_requests = True
        settings.allow_user_requests = True
        settings.secret_link_expiration = 30


class PublicationNotificationComponent(ServiceComponent):
    """Component for notifying users about the publication of their record."""

    def publish(self, identity, draft=None, record=None, **kwargs):
        """Register a task to send off the notification email."""
        # the first time the record gets published, the PID's status
        # gets set to "R" but that won't have been transferred to the
        # record's data until the `record.commit()` from the unit of work
        has_been_published = (
            draft.pid.status == draft["pid"]["status"] == PIDStatus.REGISTERED
        )

        if not has_been_published:
            self.uow.register(
                TaskOp(send_publication_notification, record.pid.pid_value)
            )


class CurationComponent(BaseCurationComponent):
    """Curation component that only activates if curations are enabled."""

    def publish(self, identity, draft=None, record=None, **kwargs):
        """Check if record curation request has been accepted."""
        if current_config_tuw.curations_enabled:
            return super().publish(identity, draft=draft, record=record, **kwargs)

    def delete_draft(self, identity, draft=None, record=None, force=False):
        """Delete a draft."""
        if current_config_tuw.curations_enabled:
            return super().delete_draft(
                identity, draft=draft, record=record, force=force
            )

    def update_draft(self, identity, data=None, record=None, errors=None):
        """Update draft handler."""
        if current_config_tuw.curations_enabled:
            value = super().update_draft(
                identity, data=data, record=record, errors=errors
            )

            # suppress the "missing field: rdm-curation" error as that is more
            # confusing than helpful
            errors = errors or []
            curation_field_errors = [
                e for e in errors if e.get("field") == "custom_fields.rdm-curation"
            ]
            for e in curation_field_errors:
                errors.remove(e)

            return value


class PublicationDateComponent(ServiceComponent):
    """Component for populating the "publication_date" metadata field."""

    def new_version(self, identity, draft=None, record=None):
        """Set "publication_date" for new record versions."""
        draft.metadata.setdefault(
            "publication_date", datetime.now().strftime("%Y-%m-%d")
        )


class MetadataEditNotificationComponent(ServiceComponent):
    """Component for notifying the record owner about metadata edits."""

    def publish(self, identity, draft=None, record=None):
        """Send a notification to the record owner about edits they haven't made."""
        if not record or not (owner := record.parent.access.owned_by):
            return

        owner_id = str(owner.owner_id)
        has_revisions = record and list(record.revisions)
        is_system_or_owner = identity and str(identity.id) in ["system", owner_id]
        if not has_revisions or is_system_or_owner:
            # skip if there are no revisions, or if the owner published the edit, or
            # if the system is the publisher (mostly happens in scripts)
            return

        # compare the latest revision with the `draft` - this seems to list more
        # details (e.g. access settings) than comparisons with the `record`
        *_, latest_rev = record.revisions
        diffs = list(
            dictdiffer.diff(latest_rev, draft, dot_notation=False, expand=True)
        )
        if not latest_rev or not diffs:
            return

        Diff = namedtuple("Diff", ["field", "change"])
        additions, changes, removals = [], [], []
        for diff in diffs:
            type_, field_path, change = diff
            field_path = field_path.copy()

            # if certain fields didn't have values in the draft, their fields may not
            # have been present at all in its dict form - in this case, the change will
            # include the field's name (similar for removals, but other way):
            #
            # ('add', ['metadata'], [('version', '1')])
            # ('add', ['metadata'], [('languages', [{'id': 'eng'}])])
            # ('remove', ['metadata'], [('dates', [{'date': '2025', 'type': {'id': 'accepted'}}])])
            if type_ in ["add", "remove"] and len(change) == 1:
                field_name, change_ = change[0]
                if isinstance(field_name, str):
                    field_path.append(field_name)
                    change = change_

            difference = Diff(field_path, change)
            if type_ == "add":
                additions.append(difference)
            elif type_ == "remove":
                removals.append(difference)
            elif type_ == "change":
                changes.append(difference)
            else:
                current_app.logger.warning(
                    f"(calculating record diff) unknown diff type: {diff}"
                )

        # note: we use the "resolver registry" from Invenio-Requests here because it
        # operates on "raw" objects rather than service result items (which we don't
        # have available here) like the one from Invenio-Notifications does
        self.uow.register(
            TaskOp(
                send_metadata_edit_notification,
                record.pid.pid_value,
                ResolverRegistry.reference_identity(identity),
                additions,
                removals,
                changes,
            )
        )


class RecordQuotaServiceComponent(ServiceComponent):
    """Service component to set the record's bucket quota.

    This is effectively the same as the following PR:
    https://github.com/inveniosoftware/invenio-rdm-records/pull/2037

    It can be removed once that PR is merged.
    """

    def create(self, identity, data=None, record=None, errors=None):
        """Assigns files.enabled and sets the bucket's quota size & max file size."""
        quota = get_files_quota(record)
        if quota_size := quota.get("quota_size"):
            record.files.bucket.quota_size = quota_size

        if max_file_size := quota.get("max_file_size"):
            record.files.bucket.max_file_size = max_file_size


class ImageSourceRewriteComponent(ServiceComponent):
    """Service component for rewriting internal image source URLs on publish.

    This component is relevant for when users embed images in the record's description,
    because the file URLs change depending on the state (draft vs. published record).
    If the URLs didn't get rewritten automatically, the user would have to either use
    the "correct" URLs from the start (which requires manual tweaks), or update the
    description (respectively the embedded images) after publication with the URLs
    that are now easy to obtain.

    Note: This may replace the hostname used in the image URLs with another one
    that can be used for the system.
    """

    def publish(self, identity, draft=None, record=None):
        """Rewrite URLs from draft to record for embedded images in the description."""
        trusted_hostnames = current_app.config["TRUSTED_HOSTS"]
        description = record.metadata.get("description", "")
        draft_uuid_pattern = re.compile(r"^draft:")
        iiif_img_endpoint = "iiif.image_api"
        draft_file_endpoint = "draft_files.read_content"
        record_file_endpoint = "record_files.read_content"

        # try to find the app instance that has API endpoints
        if (app := _get_app_for_endpoint(iiif_img_endpoint)) is None:
            current_app.logger.warn(
                "Skipping source URL rewrite for images in the record description "
                "because the relevant API endpoints cannot be found on the app in use"
            )
            return

        api_url_adapter = app.create_url_adapter(request)

        for img_src_attrib in _get_img_src_attributes(description):
            src_value, new_src_value = img_src_attrib.group(1), None
            parsed_url = urlparse(src_value)
            hostname = parsed_url.netloc

            # we only care about internal links, i.e. either relative URLs, or ones
            # for our hostnames
            if hostname and hostname not in trusted_hostnames:
                continue

            # relevant endpoints (in InvenioRDM v13):
            #
            # API     "{draft,record}_files.read_content" (.read only gives JSON info)
            #         "iiif.image_api"
            #
            #           > the <uuid> part in the IIIF endpoints is expected to follow
            #             the shape "<type>:<recid>[:<key>]", where <type> can be
            #             "draft" or "record", which needs to be replaced
            #
            #
            # UI      "invenio_app_rdm_records.record_file_download" (_preview is a UI)
            #         "invenio_app_rdm_records.record_media_file_download"
            #
            #           > the "?download=1" flag makes browsers download the file
            #             instead of rendering it; it should already be set correctly
            #           > the "?preview=1" flag tries the draft service first, before
            #             trying the record service
            #
            #           -> thus, leaving both flags as is should be fine
            #           -> which means the URLs can stay as they are
            try:
                url_path = parsed_url.path
                try:
                    endpoint, params = api_url_adapter.match(url_path, "GET")
                except HTTPException:
                    # the API endpoint URLs typically don't match with the /api prefix
                    stripped_url = url_path.removeprefix("/api")
                    endpoint, params = api_url_adapter.match(stripped_url, "GET")

                # perform the necessary operation, depending on the endpoint
                if endpoint == iiif_img_endpoint:
                    params["uuid"] = draft_uuid_pattern.sub("record:", params["uuid"])
                    new_src_value = invenio_url_for(iiif_img_endpoint, **params)

                elif endpoint == draft_file_endpoint:
                    new_src_value = invenio_url_for(record_file_endpoint, **params)

            except HTTPException:
                pass

            if new_src_value:
                # note: this could theoretically replace URLs other than just the
                #       identified image source attribute, but since the URL
                #       replacements are very specific, this shouldn't do any real harm
                description = description.replace(src_value, new_src_value)

        record.metadata["description"] = description


TUWRecordsComponents = [
    *DefaultRecordsComponents,
    ImageSourceRewriteComponent,
    ParentAccessSettingsComponent,
    RecordQuotaServiceComponent,
    PublicationDateComponent,
    PublicationNotificationComponent,
    MetadataEditNotificationComponent,
    CurationComponent,
]
