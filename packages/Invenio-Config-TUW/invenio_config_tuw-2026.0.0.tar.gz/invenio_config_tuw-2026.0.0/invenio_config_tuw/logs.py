# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2026 TU Wien.
#
# Invenio-Config-TUW is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom logging formatters."""

from logging import Formatter

from flask import has_request_context, request
from flask_security import current_user

custom_format = """\
Time:               %(asctime)s
Level:              %(levelname)s
Location:           %(pathname)s:%(lineno)d
Function:           %(funcName)s
Request URL:        %(request_url)s
From:               %(remote_addr)s
User ID:            %(user_id)s
Error:              %(exc_type_name)s


Message:

%(message)s
"""


class DetailedFormatter(Formatter):
    """Custom logging formatter providing more information about the request context.

    Note that by default, Flask only logs unhandled exceptions in production mode;
    with a development setup, exceptions are instead bubbled up to be handled
    by the debugger.
    However, the `got_request_exception` signal always gets sent in any setup.
    See: https://flask.palletsprojects.com/en/stable/api/#flask.Flask.handle_exception
    """

    def __init__(self, fmt=custom_format, **kwargs):
        """Constructor."""
        super().__init__(fmt=fmt, **kwargs)

    def format(self, record):
        """Format the specified log record as text."""
        record.user_id = None
        record.request_url = None
        record.remote_addr = None
        record.exc_type_name = None

        if has_request_context():
            user_id = "Anonymous"
            if current_user and current_user.is_authenticated:
                user_id = current_user.id

            record.user_id = user_id
            record.request_url = request.url
            record.remote_addr = request.remote_addr

        if record.exc_info:
            record.exc_type_name = record.exc_info[0].__name__

        return super().format(record)
