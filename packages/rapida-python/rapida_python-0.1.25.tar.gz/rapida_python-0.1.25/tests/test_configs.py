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

# Import directly from the file to bypass rapida/__init__.py
module_path = os.path.join(os.path.dirname(__file__), '..', 'rapida', 'configs', '__init__.py')
spec = importlib.util.spec_from_file_location('configs', module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Extract the constants we need
ASSISTANT_API = module.ASSISTANT_API
WEB_API = module.WEB_API
ENDPOINT_API = module.ENDPOINT_API
LOCAL_ASSISTANT_API = module.LOCAL_ASSISTANT_API
LOCAL_WEB_API = module.LOCAL_WEB_API
LOCAL_ENDPOINT_API = module.LOCAL_ENDPOINT_API
GRPC_ENDPOINT_URL = module.GRPC_ENDPOINT_URL
GRPC_ASSISTANT_URL = module.GRPC_ASSISTANT_URL
GRPC_GATEWAY_URL = module.GRPC_GATEWAY_URL

# Old import kept for reference:
# from rapida.configs import (
#     ASSISTANT_API, WEB_API, ENDPOINT_API,
#     LOCAL_ASSISTANT_API, LOCAL_WEB_API, LOCAL_ENDPOINT_API,
#     GRPC_ENDPOINT_URL, GRPC_ASSISTANT_URL, GRPC_GATEWAY_URL,
# )


class TestConfigs:
    """Test cases for configs module."""

    def test_assistant_api_is_set(self):
        """Test ASSISTANT_API has a value."""
        assert ASSISTANT_API is not None
        assert len(ASSISTANT_API) > 0

    def test_web_api_is_set(self):
        """Test WEB_API has a value."""
        assert WEB_API is not None
        assert len(WEB_API) > 0

    def test_endpoint_api_is_set(self):
        """Test ENDPOINT_API has a value."""
        assert ENDPOINT_API is not None
        assert len(ENDPOINT_API) > 0

    def test_local_assistant_api_is_localhost(self):
        """Test LOCAL_ASSISTANT_API points to localhost."""
        assert "localhost" in LOCAL_ASSISTANT_API

    def test_local_web_api_is_localhost(self):
        """Test LOCAL_WEB_API points to localhost."""
        assert "localhost" in LOCAL_WEB_API

    def test_local_endpoint_api_is_localhost(self):
        """Test LOCAL_ENDPOINT_API points to localhost."""
        assert "localhost" in LOCAL_ENDPOINT_API

    def test_grpc_endpoint_url_is_set(self):
        """Test GRPC_ENDPOINT_URL has a value."""
        assert GRPC_ENDPOINT_URL is not None
        assert len(GRPC_ENDPOINT_URL) > 0

    def test_grpc_assistant_url_is_set(self):
        """Test GRPC_ASSISTANT_URL has a value."""
        assert GRPC_ASSISTANT_URL is not None
        assert len(GRPC_ASSISTANT_URL) > 0

    def test_grpc_gateway_url_is_set(self):
        """Test GRPC_GATEWAY_URL has a value."""
        assert GRPC_GATEWAY_URL is not None
        assert len(GRPC_GATEWAY_URL) > 0

    def test_production_apis_are_rapida_domain(self):
        """Test production APIs use rapida.ai domain."""
        assert "rapida.ai" in ASSISTANT_API
        assert "rapida.ai" in WEB_API
        assert "rapida.ai" in ENDPOINT_API

    def test_local_apis_have_port_numbers(self):
        """Test local APIs have port numbers."""
        assert ":" in LOCAL_ASSISTANT_API
        assert ":" in LOCAL_WEB_API
        assert ":" in LOCAL_ENDPOINT_API
