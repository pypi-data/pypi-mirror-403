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
from rapida.clients.protos.endpoint_api_pb2 import (
    GetAllEndpointLogRequest,
    GetAllEndpointLogResponse,
    GetAllEndpointRequest,
    GetAllEndpointResponse,
    GetEndpointLogRequest,
    GetEndpointLogResponse,
    GetEndpointRequest,
    GetEndpointResponse,
)
from rapida.connections import ConnectionConfig, UserAuthInfo, ClientAuthInfo


def get_endpoint(
    client_cfg: ConnectionConfig,
    request: GetEndpointRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetEndpointResponse:
    if auth is None:
        auth = client_cfg.auth

    return client_cfg.endpoint_client.GetEndpoint(
        request,
        metadata=auth,
    )


def get_all_endpoint(
    client_cfg: ConnectionConfig,
    request: GetAllEndpointRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAllEndpointResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.endpoint_client.GetAllEndpoint(
        request,
        metadata=auth,
    )


def get_endpoint_log(
    client_cfg: ConnectionConfig,
    request: GetEndpointLogRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetEndpointLogResponse:
    if auth is None:
        auth = client_cfg.auth

    return client_cfg.endpoint_client.GetEndpointLog(
        request,
        metadata=auth,
    )


def get_all_endpoint_log(
    client_cfg: ConnectionConfig,
    request: GetAllEndpointLogRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAllEndpointLogResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.endpoint_client.GetAllEndpointLog(
        request,
        metadata=auth,
    )
