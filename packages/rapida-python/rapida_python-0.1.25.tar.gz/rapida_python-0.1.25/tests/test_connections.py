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

"""
Tests for ConnectionConfig and related types.
These tests use mocking to verify the function behavior without
requiring actual gRPC connections or protobuf dependencies.
"""

import pytest
import sys
import os
import importlib.util
from unittest.mock import Mock, MagicMock

# Mock all the protobuf modules and gRPC before importing connections
sys.modules['rapida.clients.protos.talk_api_pb2_grpc'] = MagicMock()
sys.modules['rapida.clients.protos.assistant_api_pb2_grpc'] = MagicMock()
sys.modules['rapida.clients.protos.invoker_api_pb2_grpc'] = MagicMock()
sys.modules['rapida.clients.protos.web_api_pb2_grpc'] = MagicMock()
sys.modules['rapida.clients.protos.knowledge_api_pb2_grpc'] = MagicMock()
sys.modules['rapida.clients.protos.document_api_pb2_grpc'] = MagicMock()
sys.modules['rapida.clients.protos.vault_api_pb2_grpc'] = MagicMock()
sys.modules['rapida.clients.protos.endpoint_api_pb2_grpc'] = MagicMock()
sys.modules['rapida.clients.protos.audit_logging_api_pb2_grpc'] = MagicMock()
sys.modules['rapida.clients.protos.marketplace_api_pb2_grpc'] = MagicMock()
sys.modules['rapida.clients.protos.assistant_deployment_pb2_grpc'] = MagicMock()
sys.modules['rapida.clients.protos.connect_api_pb2_grpc'] = MagicMock()
sys.modules['rapida.clients.protos.provider_api_pb2_grpc'] = MagicMock()
sys.modules['grpc'] = MagicMock()

# Import header and source utils directly
module_path = os.path.join(os.path.dirname(__file__), '..', 'rapida', 'utils', 'rapida_header.py')
spec = importlib.util.spec_from_file_location('rapida_header', module_path)
header_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(header_module)

HEADER_API_KEY = header_module.HEADER_API_KEY
HEADER_AUTH_ID = header_module.HEADER_AUTH_ID
HEADER_PROJECT_ID = header_module.HEADER_PROJECT_ID
HEADER_SOURCE_KEY = header_module.HEADER_SOURCE_KEY

# Import configs directly
configs_path = os.path.join(os.path.dirname(__file__), '..', 'rapida', 'configs', '__init__.py')
spec = importlib.util.spec_from_file_location('configs', configs_path)
configs_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configs_module)

ASSISTANT_API = configs_module.ASSISTANT_API
WEB_API = configs_module.WEB_API
ENDPOINT_API = configs_module.ENDPOINT_API
LOCAL_ASSISTANT_API = configs_module.LOCAL_ASSISTANT_API
LOCAL_WEB_API = configs_module.LOCAL_WEB_API
LOCAL_ENDPOINT_API = configs_module.LOCAL_ENDPOINT_API

# Now we need to mock the rapida.utils.rapida_source module for connections import
# Create a mock RapidaSource class
class MockRapidaSource:
    DEBUGGER = MagicMock()
    DEBUGGER.get.return_value = "debugger"
    SDK = MagicMock()
    SDK.get.return_value = "sdk"
    WEB_PLUGIN = MagicMock()
    WEB_PLUGIN.get.return_value = "web-plugin"

sys.modules['rapida.utils.rapida_source'] = MagicMock()
sys.modules['rapida.utils.rapida_source'].RapidaSource = MockRapidaSource

# Mock rapida.utils.rapida_header
sys.modules['rapida.utils.rapida_header'] = header_module

# Mock rapida.configs
sys.modules['rapida.configs'] = configs_module

# Load the connections module directly
connections_path = os.path.join(os.path.dirname(__file__), '..', 'rapida', 'connections', '__init__.py')
spec = importlib.util.spec_from_file_location('connections', connections_path)
connections_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(connections_module)

ConnectionConfig = connections_module.ConnectionConfig


class TestConnectionConfigStaticMethods:
    """Test cases for ConnectionConfig static methods."""

    def test_with_debugger(self):
        """Test with_debugger creates correct UserAuthInfo."""
        result = ConnectionConfig.with_debugger(
            authorization="token123",
            user_id="user456",
            project_id="project789"
        )
        assert result["authorization"] == "token123"
        assert result[HEADER_AUTH_ID] == "user456"
        assert result[HEADER_PROJECT_ID] == "project789"
        assert result[HEADER_SOURCE_KEY] == "debugger"

    def test_with_personal_token(self):
        """Test with_personal_token creates correct UserAuthInfo."""
        result = ConnectionConfig.with_personal_token(
            authorization="token123",
            auth_id="auth456",
            project_id="project789"
        )
        assert result["authorization"] == "token123"
        assert result[HEADER_AUTH_ID] == "auth456"
        assert result[HEADER_PROJECT_ID] == "project789"
        assert result[HEADER_SOURCE_KEY] == "sdk"

    def test_with_webplugin_client(self):
        """Test with_webplugin_client creates correct ClientAuthInfo."""
        result = ConnectionConfig.with_webplugin_client(
            api_key="apikey123",
            user_id="user456"
        )
        assert result[HEADER_API_KEY] == "apikey123"
        assert result[HEADER_AUTH_ID] == "user456"
        assert result[HEADER_SOURCE_KEY] == "web-plugin"

    def test_with_webplugin_client_no_user(self):
        """Test with_webplugin_client without user_id."""
        result = ConnectionConfig.with_webplugin_client(api_key="apikey123")
        assert result[HEADER_API_KEY] == "apikey123"
        assert result[HEADER_AUTH_ID] is None
        assert result[HEADER_SOURCE_KEY] == "web-plugin"

    def test_with_sdk(self):
        """Test with_sdk creates correct ClientAuthInfo."""
        result = ConnectionConfig.with_sdk(
            api_key="apikey123",
            user_id="user456"
        )
        assert result[HEADER_API_KEY] == "apikey123"
        assert result[HEADER_AUTH_ID] == "user456"
        assert result[HEADER_SOURCE_KEY] == "sdk"

    def test_with_sdk_no_user(self):
        """Test with_sdk without user_id."""
        result = ConnectionConfig.with_sdk(api_key="apikey123")
        assert result[HEADER_API_KEY] == "apikey123"
        assert result[HEADER_AUTH_ID] is None


class TestConnectionConfigInit:
    """Test cases for ConnectionConfig initialization."""

    def test_default_init(self):
        """Test default initialization."""
        config = ConnectionConfig()
        assert config._debug is False
        assert config._auth is None
        assert config._endpoint["assistant"] == ASSISTANT_API
        assert config._endpoint["web"] == WEB_API
        assert config._endpoint["endpoint"] == ENDPOINT_API

    def test_init_with_custom_endpoint(self):
        """Test initialization with custom endpoint."""
        custom_endpoint = {
            "assistant": "custom.assistant.api",
            "web": "custom.web.api",
            "endpoint": "custom.endpoint.api",
        }
        config = ConnectionConfig(endpoint=custom_endpoint)
        assert config._endpoint == custom_endpoint

    def test_init_with_debug(self):
        """Test initialization with debug mode."""
        config = ConnectionConfig(debug=True)
        assert config._debug is True


class TestConnectionConfigMethods:
    """Test cases for ConnectionConfig instance methods."""

    def test_get_client_options(self):
        """Test get_client_options returns correct options."""
        config = ConnectionConfig(debug=True)
        options = config.get_client_options()
        assert options == {"debug": True}

    def test_get_client_options_no_debug(self):
        """Test get_client_options with debug=False."""
        config = ConnectionConfig()
        options = config.get_client_options()
        assert options == {"debug": False}

    def test_with_custom_endpoint(self):
        """Test with_custom_endpoint updates endpoint and returns self."""
        config = ConnectionConfig()
        custom_endpoint = {
            "assistant": "new.assistant.api",
            "web": "new.web.api",
            "endpoint": "new.endpoint.api",
        }
        result = config.with_custom_endpoint(custom_endpoint, True)
        assert result is config
        assert config._endpoint == custom_endpoint
        assert config._debug is True

    def test_with_custom_endpoint_defaults(self):
        """Test with_custom_endpoint with None values uses defaults."""
        config = ConnectionConfig()
        config._debug = True
        result = config.with_custom_endpoint(None, None)
        assert result is config
        assert config._endpoint["assistant"] == ASSISTANT_API
        assert config._debug is True

    def test_with_auth(self):
        """Test with_auth sets auth and returns self."""
        config = ConnectionConfig()
        auth = {"key": "value"}
        result = config.with_auth(auth)
        assert result is config
        assert config._auth == auth

    def test_auth_property_none(self):
        """Test auth property when _auth is None."""
        config = ConnectionConfig()
        assert config.auth == []

    def test_auth_property_dict(self):
        """Test auth property when _auth is a dict."""
        config = ConnectionConfig()
        config._auth = {"key1": "value1", "key2": "value2"}
        result = config.auth
        assert ("key1", "value1") in result
        assert ("key2", "value2") in result

    def test_auth_property_list(self):
        """Test auth property when _auth is already a list."""
        config = ConnectionConfig()
        auth_list = [("key1", "value1"), ("key2", "value2")]
        config._auth = auth_list
        assert config.auth == auth_list

    def test_with_local(self):
        """Test with_local sets local endpoints."""
        config = ConnectionConfig()
        result = config.with_local()
        assert result is config
        assert config._endpoint["assistant"] == LOCAL_ASSISTANT_API
        assert config._endpoint["web"] == LOCAL_WEB_API
        assert config._endpoint["endpoint"] == LOCAL_ENDPOINT_API
        assert config._debug is True

    def test_default_connection_config(self):
        """Test default_connection_config creates config with auth."""
        auth = {"key": "value"}
        config = ConnectionConfig.default_connection_config(auth)
        assert isinstance(config, ConnectionConfig)
        assert config._auth == auth
