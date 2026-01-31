# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 Northwestern University.
#
# invenio-administration is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Administration blueprint."""


def get_administration_panel_bp(app):
    """Get administration panel blueprint.

    For historical reasons the blueprint was created in `InvenioAdministration`
    and this just fetches it to be registered.
    """
    ext = app.extensions["invenio-administration"]
    return ext.administration.blueprint
