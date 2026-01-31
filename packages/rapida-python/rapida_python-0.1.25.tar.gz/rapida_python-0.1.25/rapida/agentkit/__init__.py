# Copyright (c) 2024. Rapida
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Author: Prashant <prashant@rapida.ai>

"""
Rapida Agent Kit

Infrastructure layer for building voice AI agents with Rapida.

- AgentKitServer: gRPC server handling SSL, auth, and lifecycle
- AgentKitAgent: Base class with response builders for sending data to Rapida

Developer is responsible for:
- LLM integration
- Tool execution
- Conversation logic

Usage:
    from rapida import AgentKitServer, AgentKitAgent
    
    class MyAgent(AgentKitAgent):
        def Talk(self, request_iterator, context):
            for request in request_iterator:
                if request.HasField("configuration"):
                    yield self.configuration_response(request.configuration)
                elif request.HasField("message"):
                    msg = request.message
                    # Your LLM logic here
                    yield self.assistant_response(msg.id, "Hello!", completed=False)
                    yield self.assistant_response(msg.id, "Hello!", completed=True)
    
    server = AgentKitServer(
        agent=MyAgent(),
        port=50051,
        ssl_config={"cert_path": "server.crt", "key_path": "server.key"},
        auth_config={"enabled": True, "token": "secret"},
    )
    server.start()
    server.wait_for_termination()
"""

import logging
import os
from concurrent import futures
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterator, Optional

import grpc
from grpc import ServerInterceptor

from rapida.clients.protos.talk_api_pb2 import (
    ConversationConfiguration,
    ConversationAssistantMessage,
    ConversationDirective,
    ConversationToolCall,
    ConversationToolResult,
)
from rapida.clients.protos.talk_api_pb2 import (
    TalkInput,
    TalkOutput,
)
from rapida.clients.protos.common_pb2 import (
    Error,
)
from rapida.clients.protos.talk_api_pb2_grpc import (
    AgentKitServicer,
    add_AgentKitServicer_to_server,
)
from rapida.utils.rapida_value import string_to_any

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class SSLConfig:
    """SSL/TLS configuration for secure connections."""

    cert_path: str
    key_path: str
    ca_cert_path: Optional[str] = None  # For mutual TLS

    def load_credentials(self) -> grpc.ServerCredentials:
        """Load SSL credentials from files."""
        with open(self.key_path, "rb") as f:
            private_key = f.read()
        with open(self.cert_path, "rb") as f:
            certificate_chain = f.read()

        root_certificates = None
        if self.ca_cert_path and os.path.exists(self.ca_cert_path):
            with open(self.ca_cert_path, "rb") as f:
                root_certificates = f.read()

        return grpc.ssl_server_credentials(
            [(private_key, certificate_chain)],
            root_certificates=root_certificates,
            require_client_auth=root_certificates is not None,
        )


@dataclass
class AuthConfig:
    """Authentication configuration."""

    enabled: bool = False
    token: Optional[str] = None
    header_key: str = "authorization"
    validator: Optional[Callable[[str, Dict[str, str]], bool]] = None


# ============================================================================
# AUTHORIZATION INTERCEPTOR
# ============================================================================


class AuthorizationInterceptor(ServerInterceptor):
    """gRPC interceptor for token-based authentication."""

    def __init__(self, auth_config: AuthConfig):
        self.auth_config = auth_config

    def intercept_service(self, continuation, handler_call_details):
        if not self.auth_config.enabled:
            return continuation(handler_call_details)

        metadata = dict(handler_call_details.invocation_metadata)
        token = metadata.get(self.auth_config.header_key)

        # Custom validator takes precedence
        if self.auth_config.validator:
            if not self.auth_config.validator(token, metadata):
                return self._abort_handler()
        # Default token comparison
        elif token != self.auth_config.token:
            return self._abort_handler()

        return continuation(handler_call_details)

    def _abort_handler(self):
        def abort(ignored_request, context):
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED, "Invalid authorization token"
            )
        return grpc.unary_unary_rpc_method_handler(abort)


# ============================================================================
# AGENT KIT AGENT - Base class with response builders
# ============================================================================


class AgentKitAgent(AgentKitServicer):
    """
    Base class for building Rapida voice AI agents.

    Extends AgentKitServicer with helper methods for:
    - Sending responses back to Rapida
    - Building assistant messages
    - Building tool call actions
    - Building error responses

    Subclass this and implement Talk() with your LLM logic.

    Example:
        class MyAgent(AgentKitAgent):
            def Talk(self, request_iterator, context):
                for request in request_iterator:
                    if request.HasField("configuration"):
                        yield self.configuration_response(request.configuration)
                    elif request.HasField("message"):
                        msg = request.message
                        # Stream text back to Rapida
                        yield self.assistant_response(msg.id, "Hello ", completed=False)
                        yield self.assistant_response(msg.id, "world!", completed=False)
                        yield self.assistant_response(msg.id, "Hello world!", completed=True)
    """

    # ========================================================================
    # RESPONSE BUILDERS - Send data back to Rapida
    # ========================================================================

    def response(
        self, code: int = 200, success: bool = True, **kwargs
    ) -> TalkOutput:
        """
        Build a generic response to send back to Rapida.

        Args:
            code: HTTP-style status code (default: 200)
            success: Whether the request was successful
            **kwargs: Additional response fields (configuration, assistant, action, error)

        Returns:
            TalkOutput to yield back to Rapida
        """
        return TalkOutput(code=code, success=success, **kwargs)

    def configuration_response(
        self, configuration: ConversationConfiguration
    ) -> TalkOutput:
        """
        Acknowledge a configuration request from Rapida.

        Args:
            configuration: The configuration received from the request

        Returns:
            TalkOutput acknowledging the configuration
        """
        return self.response(configuration=configuration)

    def assistant_response(
        self, msg_id: str, content: str, completed: bool = False
    ) -> TalkOutput:
        """
        Send assistant text response back to Rapida.

        Use completed=False for streaming chunks, completed=True for final message.

        Args:
            msg_id: Message ID from the request
            content: Text content to send
            completed: True if this is the final message in the response

        Returns:
            TalkOutput with assistant text
        """
        return self.response(
            assistant=ConversationAssistantMessage(
                id=msg_id,
                completed=completed,
                text=content,
            )
        )

    def error_response(self, code: int, message: str) -> TalkOutput:
        """
        Send an error response back to Rapida.

        Args:
            code: Error code
            message: Error message

        Returns:
            TalkOutput with error
        """
        return self.response(
            code=code,
            success=False,
            error=Error(errorCode=code, errorMessage=message),
        )

    def tool_call(
        self, msg_id: str, tool_id: str, name: str, args: Dict[str, Any]
    ) -> TalkOutput:
        """
        Send an intermediate tool call action back to Rapida.

        Use this when the agent calls a tool but the conversation continues.

        Args:
            msg_id: Message ID from the request
            tool_id: Tool ID
            name: Tool name
            args: Tool arguments as a dictionary

        Returns:
            TalkOutput with tool action
        """
        _args = {}
        # Set map fields with Any values after construction
        for k, v in (args or {}).items():
            _args[str(k)] = string_to_any(str(v))

        return self.response(tool=ConversationToolCall(
            id=str(msg_id),
            toolId=str(tool_id),
            name=str(name),
            args=_args
        ))
    
    def tool_call_result(
        self, msg_id: str, tool_id: str, name: str, result: Any, success: bool = True
    ) -> TalkOutput:
        """
        Send a tool call result back to Rapida.

        Use this when the agent has executed a tool and has results.

        Args:
            msg_id: Message ID from the request
            tool_id: Tool ID
            name: Tool name
            result: Tool result (can be dict, string, or any serializable type)
            success: Whether the tool call was successful

        Returns:
            TalkOutput with tool result
        """
        _args = {}
        # Set map fields with Any values after construction
        if result is not None:
            if isinstance(result, dict):
                for k, v in result.items():
                    _args[str(k)] = string_to_any(str(v))
            else:
                # For non-dict results, store under "result" key
                _args["result"] = string_to_any(str(result))

        return self.response(toolResult=ConversationToolResult(
            id=str(msg_id),
            toolId=str(tool_id),
            name=str(name),
            success=bool(success),
            args=_args
        ))

    def transfer_call(
        self, msg_id: str, args: Dict[str, Any]
    ) -> TalkOutput:
        """
        Send a transfer call directive back to Rapida.

        Args:
            msg_id: Message ID from the request
            args: Transfer arguments as a dictionary

        Returns:
            TalkOutput with TRANSFER_CALL action
        """
        _args = {}
        # Set map fields with Any values after construction
        for k, v in (args or {}).items():
            _args[str(k)] = string_to_any(str(v))

        return self.response(directive=ConversationDirective(
            id=str(msg_id),
            type=ConversationDirective.TRANSFER_CONVERSATION,
            args=_args
        ))

    def terminate_call(
        self, msg_id: str, args: Dict[str, Any]
    ) -> TalkOutput:
        """
        Send a tool call that ends the conversation back to Rapida.

        Use this for tools like "terminate_call" that should end the session.

        Args:
            msg_id: Message ID from the request
            args: Tool arguments as a dictionary

        Returns:
            TalkOutput with END_CONVERSATION action
        """
        _arg = {}
        # Set map fields with Any values after construction
        for k, v in (args or {}).items():
            _arg[str(k)] = string_to_any(str(v))
        
        return self.response(directive=ConversationDirective(
            id=str(msg_id),
            type=ConversationDirective.END_CONVERSATION,
            args=_arg))

    # ========================================================================
    # REQUEST HELPERS - Receive data from Rapida
    # ========================================================================

    def get_user_text(self, request: TalkInput) -> Optional[str]:
        """
        Extract user text content from a request.

        Args:
            request: The incoming request from Rapida

        Returns:
            User's text content, or None if not a text message
        """
        if request.HasField("message") and request.message.HasField("text"):
            return request.message.text
        return None

    def get_message_id(self, request: TalkInput) -> Optional[str]:
        """
        Extract message ID from a request.

        Args:
            request: The incoming request from Rapida

        Returns:
            Message ID, or None if not a message request
        """
        if request.HasField("message"):
            return request.message.id
        return None

    def is_configuration_request(self, request: TalkInput) -> bool:
        """Check if request is a configuration request."""
        return request.HasField("configuration")

    def is_message_request(self, request: TalkInput) -> bool:
        """Check if request is a message request."""
        return request.HasField("message")

    def is_text_message(self, request: TalkInput) -> bool:
        """Check if request is a text message."""
        return (
            request.HasField("message")
            and request.message.HasField("text")
        )

    def is_audio_message(self, request: TalkInput) -> bool:
        """Check if request is an audio message."""
        return (
            request.HasField("message")
            and request.message.HasField("audio")
        )


# ============================================================================
# AGENT KIT SERVER - gRPC infrastructure
# ============================================================================


class AgentKitServer:
    """
    gRPC server for Rapida Agent Kit.

    Handles infrastructure only:
    - gRPC server setup and lifecycle
    - SSL/TLS configuration
    - Token-based authentication

    Developer provides their own AgentKitAgent implementation.

    Example:
        from rapida import AgentKitServer, AgentKitAgent

        class MyAgent(AgentKitAgent):
            def Talk(self, request_iterator, context):
                for request in request_iterator:
                    if self.is_configuration_request(request):
                        yield self.configuration_response(request.configuration)
                    elif self.is_text_message(request):
                        msg_id = self.get_message_id(request)
                        text = self.get_user_text(request)
                        # Your LLM logic here
                        yield self.assistant_response(msg_id, "Hello!", completed=True)
        
        server = AgentKitServer(agent=MyAgent(), port=50051)
        server.start()
        server.wait_for_termination()

    With SSL and Auth:
        server = AgentKitServer(
            agent=MyAgent(),
            port=50051,
            ssl_config={"cert_path": "server.crt", "key_path": "server.key"},
            auth_config={"enabled": True, "token": "mysecrettoken"},
        )
    """

    def __init__(
        self,
        agent: AgentKitServicer,
        host: str = "0.0.0.0",
        port: int = 50051,
        max_workers: int = 10,
        ssl_config: Optional[Dict[str, str]] = None,
        auth_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the Agent Kit Server.

        Args:
            agent: Your AgentKitAgent (or AgentKitServicer) implementation.
            host: Host address to bind (default: "0.0.0.0").
            port: Port to listen on (default: 50051).
            max_workers: Maximum thread pool workers (default: 10).
            ssl_config: Optional SSL configuration dict:
                - cert_path: Path to SSL certificate file
                - key_path: Path to SSL private key file
                - ca_cert_path: Optional CA certificate for mutual TLS
            auth_config: Optional authentication configuration dict:
                - enabled: Whether auth is enabled (default: False)
                - token: Expected token value
                - header_key: Metadata header key (default: "authorization")
                - validator: Custom validator function(token, metadata) -> bool
        """
        self.agent = agent
        self.host = host
        self.port = port
        self.max_workers = max_workers

        # Parse SSL config
        self._ssl_config: Optional[SSLConfig] = None
        if ssl_config:
            self._ssl_config = SSLConfig(
                cert_path=ssl_config["cert_path"],
                key_path=ssl_config["key_path"],
                ca_cert_path=ssl_config.get("ca_cert_path"),
            )

        # Parse auth config
        self._auth_config: Optional[AuthConfig] = None
        if auth_config:
            self._auth_config = AuthConfig(
                enabled=auth_config.get("enabled", False),
                token=auth_config.get("token"),
                header_key=auth_config.get("header_key", "authorization"),
                validator=auth_config.get("validator"),
            )

        self._server: Optional[grpc.Server] = None

    def start(self) -> None:
        """Start the gRPC server."""
        # Build interceptors
        interceptors = []
        if self._auth_config and self._auth_config.enabled:
            interceptors.append(AuthorizationInterceptor(self._auth_config))
            logger.info("Authorization interceptor enabled")

        # Create server
        self._server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=self.max_workers),
            interceptors=interceptors,
        )

        # Register agent
        add_AgentKitServicer_to_server(self.agent, self._server)

        # Configure address and credentials
        address = f"{self.host}:{self.port}"

        if self._ssl_config:
            if not os.path.exists(self._ssl_config.cert_path):
                raise FileNotFoundError(
                    f"SSL certificate not found: {self._ssl_config.cert_path}"
                )
            if not os.path.exists(self._ssl_config.key_path):
                raise FileNotFoundError(
                    f"SSL key not found: {self._ssl_config.key_path}"
                )

            credentials = self._ssl_config.load_credentials()
            self._server.add_secure_port(address, credentials)
            logger.info(f"Starting secure server on {address}")
        else:
            self._server.add_insecure_port(address)
            logger.warning(f"Starting INSECURE server on {address}")

        self._server.start()
        logger.info(f"Server started on {address}")

    def stop(self, grace: Optional[int] = 5) -> None:
        """
        Stop the gRPC server.

        Args:
            grace: Grace period in seconds for ongoing RPCs to complete.
        """
        if self._server:
            logger.info(f"Stopping server (grace={grace}s)...")
            self._server.stop(grace)
            logger.info("Server stopped")

    def wait_for_termination(self, timeout: Optional[float] = None) -> bool:
        """
        Block until the server terminates.

        Args:
            timeout: Optional timeout in seconds.

        Returns:
            True if server terminated, False if timeout occurred.
        """
        if self._server:
            return self._server.wait_for_termination(timeout)
        return True

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._server is not None

    @property
    def address(self) -> str:
        """Get server address."""
        return f"{self.host}:{self.port}"


__all__ = [
    "AgentKitAgent",
    "AgentKitServer",
    "SSLConfig",
    "AuthConfig",
    "AuthorizationInterceptor",
]
