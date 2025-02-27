# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------

from copy import deepcopy
from typing import TYPE_CHECKING

from azure.core import PipelineClient
from azure.purview.scanning.core.rest import HttpResponse, _StreamContextManager
from msrest import Deserializer, Serializer

if TYPE_CHECKING:
    # pylint: disable=unused-import,ungrouped-imports
    from typing import Any, Dict

    from azure.core.credentials import TokenCredential
    from azure.purview.scanning.core.rest import HttpRequest

from ._configuration import PurviewScanningClientConfiguration


class PurviewScanningClient(object):
    """Creates a Microsoft.Scanning management client.

    :param credential: Credential needed for the client to connect to Azure.
    :type credential: ~azure.core.credentials.TokenCredential
    :param endpoint: The scanning endpoint of your purview account. Example: https://{accountName}.scan.purview.azure.com.
    :type endpoint: str
    """

    def __init__(
        self,
        credential,  # type: "TokenCredential"
        endpoint,  # type: str
        **kwargs  # type: Any
    ):
        # type: (...) -> None
        base_url = '{Endpoint}'
        self._config = PurviewScanningClientConfiguration(credential, endpoint, **kwargs)
        self._client = PipelineClient(base_url=base_url, config=self._config, **kwargs)

        self._serialize = Serializer()
        self._deserialize = Deserializer()
        self._serialize.client_side_validation = False

    def send_request(self, http_request, **kwargs):
        # type: (HttpRequest, Any) -> HttpResponse
        """Runs the network request through the client's chained policies.

        We have helper methods to create requests specific to this service in `azure.purview.scanning.rest`.
        Use these helper methods to create the request you pass to this method. See our example below:

        >>> from azure.purview.scanning.rest import build_get_request
        >>> request = build_get_request(key_vault_name)
        <HttpRequest [GET], url: '/azureKeyVaults/{keyVaultName}'>
        >>> response = client.send_request(request)
        <HttpResponse: 200 OK>

        For more information on this code flow, see https://aka.ms/azsdk/python/protocol/quickstart

        For advanced cases, you can also create your own :class:`~azure.purview.scanning.core.rest.HttpRequest`
        and pass it in.

        :param http_request: The network request you want to make. Required.
        :type http_request: ~azure.purview.scanning.core.rest.HttpRequest
        :keyword bool stream_response: Whether the response payload will be streamed. Defaults to False.
        :return: The response of your network call. Does not do error handling on your response.
        :rtype: ~azure.purview.scanning.core.rest.HttpResponse
        """
        request_copy = deepcopy(http_request)
        path_format_arguments = {
            'Endpoint': self._serialize.url("self._config.endpoint", self._config.endpoint, 'str', skip_quote=True),
        }
        request_copy.url = self._client.format_url(request_copy.url, **path_format_arguments)
        if kwargs.pop("stream_response", False):
            return _StreamContextManager(
                client=self._client._pipeline,
                request=request_copy,
            )
        pipeline_response = self._client._pipeline.run(request_copy._internal_request, **kwargs)
        response = HttpResponse(
            status_code=pipeline_response.http_response.status_code,
            request=request_copy,
            _internal_response=pipeline_response.http_response
        )
        response.read()
        return response

    def close(self):
        # type: () -> None
        self._client.close()

    def __enter__(self):
        # type: () -> PurviewScanningClient
        self._client.__enter__()
        return self

    def __exit__(self, *exc_details):
        # type: (Any) -> None
        self._client.__exit__(*exc_details)
