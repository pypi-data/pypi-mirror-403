#  Copyright (c) 2024. Rapida
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import pytest
import sys
import os
import importlib.util

# Import directly from the version.py file to bypass rapida/__init__.py
version_path = os.path.join(os.path.dirname(__file__), '..', 'rapida', 'version.py')
spec = importlib.util.spec_from_file_location('version', version_path)
version_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version_module)

VERSION = version_module.VERSION
VERSION_SHORT = version_module.VERSION_SHORT
_MAJOR = version_module._MAJOR
_MINOR = version_module._MINOR
_REVISION = version_module._REVISION


class TestVersion:
    """Test cases for version module."""

    def test_version_format(self):
        """Test that VERSION follows semantic versioning format."""
        assert VERSION == f"{_MAJOR}.{_MINOR}.{_REVISION}"

    def test_version_short_format(self):
        """Test that VERSION_SHORT contains major and minor versions."""
        assert VERSION_SHORT == f"{_MAJOR}.{_MINOR}"

    def test_version_components_are_strings(self):
        """Test that version components are strings."""
        assert isinstance(_MAJOR, str)
        assert isinstance(_MINOR, str)
        assert isinstance(_REVISION, str)

    def test_version_components_are_numeric(self):
        """Test that version components can be converted to integers."""
        assert int(_MAJOR) >= 0
        assert int(_MINOR) >= 0
        assert int(_REVISION) >= 0

    def test_version_is_not_empty(self):
        """Test that VERSION is not an empty string."""
        assert len(VERSION) > 0
        assert len(VERSION_SHORT) > 0

    def test_version_contains_dots(self):
        """Test VERSION contains proper separators."""
        assert VERSION.count('.') == 2
        assert VERSION_SHORT.count('.') == 1
