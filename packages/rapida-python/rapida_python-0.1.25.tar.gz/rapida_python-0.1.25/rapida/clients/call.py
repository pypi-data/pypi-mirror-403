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
from rapida.clients.protos.talk_api_pb2 import (
    CreateBulkPhoneCallRequest,
    CreateBulkPhoneCallResponse,
    CreatePhoneCallRequest,
    CreatePhoneCallResponse,
)
from rapida.connections import ConnectionConfig, UserAuthInfo, ClientAuthInfo


def create_phone_call(
    client_cfg: ConnectionConfig,
    request: CreatePhoneCallRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> CreatePhoneCallResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.conversation_client.CreatePhoneCall(
        request,
        metadata=auth,
    )


def create_bulk_phone_call(
    client_cfg: ConnectionConfig,
    request: CreateBulkPhoneCallRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> CreateBulkPhoneCallResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.conversation_client.CreateBulkPhoneCall(
        request,
        metadata=auth,
    )
