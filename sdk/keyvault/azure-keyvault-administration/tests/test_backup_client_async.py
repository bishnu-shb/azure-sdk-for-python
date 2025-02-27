# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
import time
from unittest import mock
from urllib.parse import urlparse

from azure.core.credentials import AccessToken
from azure.core.exceptions import ResourceExistsError
from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.keys.aio import KeyClient
from azure.keyvault.administration._internal import HttpChallengeCache
from azure.keyvault.administration.aio import KeyVaultBackupClient
from devtools_testutils import ResourceGroupPreparer, StorageAccountPreparer
import pytest

from _shared.helpers_async import get_completed_future
from _shared.test_case_async import KeyVaultTestCase
from blob_container_preparer import BlobContainerPreparer


@pytest.mark.usefixtures("managed_hsm")
class BackupClientTests(KeyVaultTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, match_body=False, **kwargs)

    def setUp(self, *args, **kwargs):
        if self.is_live:
            real = urlparse(self.managed_hsm["url"])
            playback = urlparse(self.managed_hsm["playback_url"])
            self.scrubber.register_name_pair(real.netloc, playback.netloc)
        super().setUp(*args, **kwargs)

    def tearDown(self):
        HttpChallengeCache.clear()
        assert len(HttpChallengeCache._cache) == 0
        super(KeyVaultTestCase, self).tearDown()

    @property
    def credential(self):
        if self.is_live:
            return DefaultAzureCredential()

        async def get_token(*_, **__):
            return AccessToken("secret", time.time() + 3600)

        return mock.Mock(get_token=get_token)

    @ResourceGroupPreparer(random_name_enabled=True, use_cache=True)
    @StorageAccountPreparer(random_name_enabled=True)
    @BlobContainerPreparer()
    async def test_full_backup_and_restore(self, container_uri, sas_token):
        # backup the vault
        backup_client = KeyVaultBackupClient(self.managed_hsm["url"], self.credential)
        backup_poller = await backup_client.begin_backup(container_uri, sas_token)
        backup_operation = await backup_poller.result()

        # restore the backup
        restore_poller = await backup_client.begin_restore(backup_operation.folder_url, sas_token)
        await restore_poller.wait()

    @ResourceGroupPreparer(random_name_enabled=True, use_cache=True)
    @StorageAccountPreparer(random_name_enabled=True)
    @BlobContainerPreparer()
    async def test_selective_key_restore(self, container_uri, sas_token):
        # create a key to selectively restore
        key_client = KeyClient(self.managed_hsm["url"], self.credential)
        key_name = self.get_resource_name("selective-restore-test-key")
        await key_client.create_rsa_key(key_name)

        # backup the vault
        backup_client = KeyVaultBackupClient(self.managed_hsm["url"], self.credential)
        backup_poller = await backup_client.begin_backup(container_uri, sas_token)
        backup_operation = await backup_poller.result()

        # restore the key
        restore_poller = await backup_client.begin_restore(backup_operation.folder_url, sas_token, key_name=key_name)
        await restore_poller.wait()

        # delete the key
        await self._poll_until_no_exception(key_client.delete_key, key_name, expected_exception=ResourceExistsError)
        await key_client.purge_deleted_key(key_name)


@pytest.mark.asyncio
async def test_continuation_token():
    """Methods returning pollers should accept continuation tokens"""

    expected_token = "token"

    mock_generated_client = mock.Mock()
    mock_methods = [
        getattr(mock_generated_client, method_name)
        for method_name in (
            "begin_full_backup",
            "begin_full_restore_operation",
            "begin_selective_key_restore_operation",
        )
    ]
    for method in mock_methods:
        # the mock client's methods must return awaitables, and we don't have AsyncMock before 3.8
        method.return_value = get_completed_future()

    backup_client = KeyVaultBackupClient("vault-url", object())
    backup_client._client = mock_generated_client
    await backup_client.begin_restore("storage uri", "sas", continuation_token=expected_token)
    await backup_client.begin_backup("storage uri", "sas", continuation_token=expected_token)
    await backup_client.begin_restore("storage uri", "sas", key_name="key", continuation_token=expected_token)

    for method in mock_methods:
        assert method.call_count == 1
        _, kwargs = method.call_args
        assert kwargs["continuation_token"] == expected_token
