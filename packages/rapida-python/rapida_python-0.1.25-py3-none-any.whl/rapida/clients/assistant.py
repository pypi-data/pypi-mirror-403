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
#
#  Author: Prashant <prashant@rapida.ai>
from typing import Union
from rapida.clients.protos.assistant_knowledge_pb2 import (
    GetAllAssistantKnowledgeRequest,
    GetAllAssistantKnowledgeResponse,
    GetAssistantKnowledgeRequest,
    GetAssistantKnowledgeResponse,
)

from rapida.clients.protos.common_pb2 import (
    GetAllAssistantConversationRequest,
    GetAllAssistantConversationResponse,
)
from rapida.clients.protos.assistant_webhook_pb2 import (
    GetAllAssistantWebhookLogRequest,
    GetAllAssistantWebhookLogResponse,
    GetAllAssistantWebhookRequest,
    GetAllAssistantWebhookResponse,
    GetAssistantWebhookLogRequest,
    GetAssistantWebhookLogResponse,
    GetAssistantWebhookRequest,
    GetAssistantWebhookResponse,
)

from rapida.clients.protos.assistant_analysis_pb2 import (
    GetAllAssistantAnalysisRequest,
    GetAssistantAnalysisRequest,
    GetAssistantAnalysisResponse,
    GetAllAssistantAnalysisResponse
)
from rapida.clients.protos.assistant_tool_pb2 import (
    GetAllAssistantToolRequest,
    GetAllAssistantToolResponse,
    GetAssistantToolRequest,
    GetAssistantToolResponse,
)
from rapida.clients.protos.assistant_api_pb2 import (
    GetAllAssistantRequest,
    GetAllAssistantResponse,
    GetAssistantConversationRequest,
    GetAssistantConversationResponse,
    GetAssistantRequest,
    GetAssistantResponse,
)
from rapida.connections import ConnectionConfig, UserAuthInfo, ClientAuthInfo


def get_assistant(
    client_cfg: ConnectionConfig,
    request: GetAssistantRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAssistantResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAssistant(
        request,
        metadata=auth,
    )


def get_all_assistant(
    client_cfg: ConnectionConfig,
    request: GetAllAssistantRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAllAssistantResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAllAssistant(
        request,
        metadata=auth,
    )


def get_assistant_conversation(
    client_cfg: ConnectionConfig,
    request: GetAssistantConversationRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAssistantConversationResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAssistantConversation(
        request,
        metadata=auth,
    )


def get_all_assistant_conversation(
    client_cfg: ConnectionConfig,
    request: GetAllAssistantConversationRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAllAssistantConversationResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAllAssistantConversation(
        request,
        metadata=auth,
    )


def get_assistant_webhook(
    client_cfg: ConnectionConfig,
    request: GetAssistantWebhookRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAssistantWebhookResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAssistantWebhook(
        request,
        metadata=auth,
    )


def get_all_assistant_webhook(
    client_cfg: ConnectionConfig,
    request: GetAllAssistantWebhookRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAllAssistantWebhookResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAllAssistantWebhook(
        request,
        metadata=auth,
    )


def get_assistant_knowledge(
    client_cfg: ConnectionConfig,
    request: GetAssistantKnowledgeRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAssistantKnowledgeResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAssistantKnowledge(
        request,
        metadata=auth,
    )


def get_all_assistant_knowledge(
    client_cfg: ConnectionConfig,
    request: GetAllAssistantKnowledgeRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAllAssistantKnowledgeResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAllAssistantKnowledge(
        request,
        metadata=auth,
    )


def get_assistant_tool(
    client_cfg: ConnectionConfig,
    request: GetAssistantToolRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAssistantToolResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAssistantTool(
        request,
        metadata=auth,
    )


def get_all_assistant_tool(
    client_cfg: ConnectionConfig,
    request: GetAllAssistantToolRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAllAssistantToolResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAllAssistantTool(
        request,
        metadata=auth,
    )


def get_assistant_analysis(
    client_cfg: ConnectionConfig,
    request: GetAssistantAnalysisRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAssistantAnalysisResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAssistantAnalysis(
        request,
        metadata=auth,
    )


def get_all_assistant_analysis(
    client_cfg: ConnectionConfig,
    request: GetAllAssistantAnalysisRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAllAssistantAnalysisResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAllAssistantAnalysis(
        request,
        metadata=auth,
    )


def get_assistant_webhook_log(
    client_cfg: ConnectionConfig,
    request: GetAssistantWebhookLogRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAssistantWebhookLogResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAssistantTool(
        request,
        metadata=auth,
    )


def get_all_assistant_webhook_log(
    client_cfg: ConnectionConfig,
    request: GetAllAssistantWebhookLogRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAllAssistantWebhookLogResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.assistant_client.GetAllAssistantTool(
        request,
        metadata=auth,
    )
