# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2025 Northwestern University.
#
# invenio-administration is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio administration views module."""

from .blueprint import get_administration_panel_bp

__all__ = ("get_administration_panel_bp",)
