# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 TU Wien.
#
# Invenio-Config-TUW is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tests the rdm-curation utilities."""

from flask import current_app
from invenio_access.permissions import system_identity
from invenio_curations.proxies import current_curations_service as curations_service
from invenio_requests.proxies import current_requests_service as requests_service

from invenio_config_tuw.curations.tasks import (
    auto_generate_curation_request_remarks,
    auto_review_curation_request,
    remind_reviewers_about_open_reviews,
    remind_uploaders_about_accepted_reviews,
)


def test_curation_auto_remarks(example_record, roles):
    """Test the automatic generation of remarks on rdm-curation requests."""
    request = curations_service.create(
        system_identity, {"topic": {"record": example_record.pid.pid_value}}
    )
    remarks = auto_generate_curation_request_remarks(request._obj)
    assert len(remarks) == 2
    assert len([r for r in remarks if "description" in r]) == 1
    assert len([r for r in remarks if "license" in r]) == 1

    # clean the rdm-curation request for other tests
    requests_service.delete(system_identity, request.id)


def test_curation_image_link_auto_remarks(db, example_record, roles, licenses):
    """Test rdm-curation request remarks on external images being referenced."""
    example_record.metadata["description"] = (
        'Top text<br><img width="800" src="https://media1.tenor.com/m/E-HF7gHr3mQAAAAd/delet-this-delete-this.gif" height="480"><br>Bottom text'
    )
    example_record.metadata["rights"] = [{"id": "cc-by-4.0"}]
    example_record.commit()
    db.session.commit()

    request = curations_service.create(
        system_identity, {"topic": {"record": example_record.pid.pid_value}}
    )

    # setting a license would require another vocabulary fixture
    remarks = auto_generate_curation_request_remarks(request._obj)
    assert len(remarks) == 1
    assert len([r for r in remarks if "externally hosted images" in r]) == 1

    # clean the rdm-curation request for other tests
    requests_service.delete(system_identity, request.id)


def test_auto_accept_curation_requests(example_record, roles):
    """Test the automatic acceptance of rdm-curation requests."""
    request = curations_service.create(
        system_identity, {"topic": {"record": example_record.pid.pid_value}}
    )

    # if not enabled, don't auto-accept requests
    current_app.config["CONFIG_TUW_AUTO_ACCEPT_CURATION_REQUESTS"] = False
    auto_review_curation_request(request.id)
    request = requests_service.read(system_identity, request.id)._obj
    assert request.status == "submitted"

    # if enabled, don auto-accept requests
    current_app.config["CONFIG_TUW_AUTO_ACCEPT_CURATION_REQUESTS"] = True
    auto_review_curation_request(request.id)
    request = requests_service.read(system_identity, request.id)._obj
    assert request.status == "accepted"

    # clean the rdm-curation request for other tests
    requests_service.delete(system_identity, request.id)
    current_app.config["CONFIG_TUW_AUTO_ACCEPT_CURATION_REQUESTS"] = False


def test_remind_reviewers_about_open_requests(example_record, example_draft, roles):
    """Test the automatic reminder emails to reviewers about open curation requests."""
    # create request & force-sync search index
    request = curations_service.create(
        system_identity, {"topic": {"record": example_record.pid.pid_value}}
    )
    requests_service.indexer.index(request._obj, arguments={"refresh": "wait_for"})

    # we're dealing with published records here, so we don't expect any notifications
    assert request._obj.status == "submitted"
    assert len(remind_reviewers_about_open_reviews()) == 0
    assert len(remind_reviewers_about_open_reviews([1])) == 0
    assert len(remind_reviewers_about_open_reviews([0])) == 0

    # clean the rdm-curation request for other tests
    requests_service.delete(system_identity, request.id)

    # -------------------------------------
    # now we do the same thing with a draft
    # -------------------------------------

    request = curations_service.create(
        system_identity, {"topic": {"record": example_draft.pid.pid_value}}
    )
    requests_service.indexer.index(request._obj, arguments={"refresh": "wait_for"})

    assert request._obj.status == "submitted"
    assert len(remind_reviewers_about_open_reviews()) == 0
    assert len(remind_reviewers_about_open_reviews([1])) == 0
    assert len(remind_reviewers_about_open_reviews([0])) == 1

    # clean the rdm-curation request for other tests
    requests_service.delete(system_identity, request.id)


def test_remind_uploaders_about_accepted_requests(example_record, example_draft, roles):
    """Test the automatic reminder emails to users about accepted curation requests."""
    # create request & force-sync search index
    request = curations_service.create(
        system_identity, {"topic": {"record": example_record.pid.pid_value}}
    )
    if request._obj.status != "accepted":
        request = requests_service.execute_action(system_identity, request.id, "review")
        request = requests_service.execute_action(system_identity, request.id, "accept")
    requests_service.indexer.index(request._obj, arguments={"refresh": "wait_for"})

    # we're dealing with published records here, so we don't expect any notifications
    assert request._obj.status == "accepted"
    assert len(remind_uploaders_about_accepted_reviews()) == 0
    assert len(remind_uploaders_about_accepted_reviews([1])) == 0
    assert len(remind_uploaders_about_accepted_reviews([0])) == 0

    # clean the rdm-curation request for other tests
    requests_service.delete(system_identity, request.id)

    # -------------------------------------
    # now we do the same thing with a draft
    # -------------------------------------

    request = curations_service.create(
        system_identity, {"topic": {"record": example_draft.pid.pid_value}}
    )
    if request._obj.status != "accepted":
        request = requests_service.execute_action(system_identity, request.id, "review")
        request = requests_service.execute_action(system_identity, request.id, "accept")
    requests_service.indexer.index(request._obj, arguments={"refresh": "wait_for"})

    assert request._obj.status == "accepted"
    assert len(remind_uploaders_about_accepted_reviews()) == 0
    assert len(remind_uploaders_about_accepted_reviews([1])) == 0
    assert len(remind_uploaders_about_accepted_reviews([0])) == 1

    # clean the rdm-curation request for other tests
    requests_service.delete(system_identity, request.id)
