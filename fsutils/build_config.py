#!/usr/bin/env python3
# $LicenseInfo:firstyear=2026&license=viewerlgpl$
# Second Life Viewer Source Code
# Copyright (C) 2026, Linden Research, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation;
# version 2.1 of the License only.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Linden Research, Inc., 945 Battery Street, San Francisco, CA  94111  USA
# $/LicenseInfo$

"""
build_config.py

BuildConfig helper class to load build configuration settings.
"""

import json
import os

class BuildConfig:
    def __init__(self, config_file=None):
        if config_file is None:
            if os.path.exists('./fsutils/build_config.json'):
                config_file = './fsutils/build_config.json'
            else:
                config_file = os.path.join(os.path.dirname(__file__), 'build_config.json')
        with open(config_file, 'r') as f:
            config_data = json.load(f)

        self.supported_os_dirs = config_data.get('os_download_dirs', [])
        # channel_to_build_type is a map from Beta, Release and Nightly to folder names preview release and nightly
        self.build_type_hosted_folder = config_data.get('build_type_hosted_folder', {})
        self.fs_version_mgr_platform = config_data.get('fs_version_mgr_platform', {})
        self.os_hosted_folder = config_data.get('os_hosted_folder', {})
        self.platforms_printable = config_data.get('platforms_printable', {})
        self.grids_printable = config_data.get('grids_printable', {})
        self.download_root = config_data.get('download_root', '')
        self.viewer_channel_mapping = config_data.get('viewer_channel_mapping', {})
        self.variant_printable = config_data.get('variant_printable', {})
