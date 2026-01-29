# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 TU Wien.
#
# Invenio-Config-TUW is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tests for services and service components."""

import pytest
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service


@pytest.fixture()
def curations_disabled(app):
    curations_enabled = app.config["CONFIG_TUW_CURATIONS_ENABLED"]
    app.config["CONFIG_TUW_CURATIONS_ENABLED"] = False
    yield

    app.config["CONFIG_TUW_CURATIONS_ENABLED"] = curations_enabled


def test_internal_image_url_rewrite(app, example_draft, curations_disabled):
    """Test the URL rewrite for internally hosted images in the description."""
    draft_id = example_draft.pid.pid_value
    draft_description = (
        "Top text<br>"
        f'<img width="800" height="800" src="https://localhost:5000/api/iiif/draft:{draft_id}:image_name.png/full/!800,800/0/default.png"></img>'
        f'<img width="800" src="https://localhost:5000/api/records/{draft_id}/draft/files/image_name.png/content" height="800" />'
        f'<img src="https://localhost:5000/api/records/{draft_id}/draft/files/another_image_name.png/content" height="800" />'
        f'<img src="https://localhost:5000/records/{draft_id}/files/image_name.png?download=1">'  # this link should not be affected
        "Bottom text<br>"
    )
    record_description = (
        "Top text<br>"
        f'<img width="800" height="800" src="https://localhost/api/iiif/record:{draft_id}:image_name.png/full/!800,800/0/default.png"></img>'
        f'<img width="800" src="https://localhost/api/records/{draft_id}/files/image_name.png/content" height="800" />'
        f'<img src="https://localhost/api/records/{draft_id}/files/another_image_name.png/content" height="800" />'
        f'<img src="https://localhost:5000/records/{draft_id}/files/image_name.png?download=1">'  # this link should not be affected
        "Bottom text<br>"
    )

    example_draft.metadata["description"] = draft_description
    example_draft.commit()
    record = records_service.publish(system_identity, draft_id)._obj

    # check if the description has been updated as expected
    assert record.metadata["description"] == record_description
