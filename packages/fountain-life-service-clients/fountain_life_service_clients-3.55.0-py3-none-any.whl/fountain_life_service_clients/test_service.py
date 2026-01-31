# This file was generated automatically. Do not edit it directly.
from typing import List, NotRequired, TypedDict, Unpack, cast
from urllib.parse import quote

from fountain_life_service_clients._base_client import (
    AlphaConfig,
    AlphaResponse,
    BaseClient,
)


class GenerateV2TestUserRequest(TypedDict):
    groupId: NotRequired[str]
    allowMultiAccount: NotRequired[bool]
    clientId: NotRequired[str]
    lifePlus: NotRequired[bool]
    email: NotRequired[str]
    phoneNumber: NotRequired[str]
    deleteAt: NotRequired[str]


class Credentials(TypedDict):
    """
    The user's API credentials.
    """

    id: str
    name: str
    key: str
    dateCreated: str
    dateExpires: str


class GenerateV2TestUserResponse(TypedDict):
    username: str
    credentials: Credentials


class ReauthenticateV2TestUserRequest(TypedDict):
    allowMultiAccount: NotRequired[bool]


class ReauthenticateV2TestUserResponse(TypedDict):
    username: str
    credentials: Credentials


class CreateAccountRequest(TypedDict):
    deletionDate: NotRequired[str]
    accountSuffix: NotRequired[str]
    products: List[str]


class CreateAccountResponse(TypedDict):
    account: str
    administratorsGroupId: str
    usersGroupId: str
    subjectsGroupId: str


class DeleteAccountParams(TypedDict):
    immediate: NotRequired[bool]


class GetAccountInfoResponse(TypedDict):
    account: str
    administratorsGroupId: str
    usersGroupId: str
    subjectsGroupId: str


class TestServiceClient(BaseClient):
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        kwargs = {"target": "lambda://test-service:deployed", **(cfg or {})}
        super().__init__(**kwargs)

    async def generate_v2_test_user(self, body: GenerateV2TestUserRequest):
        """Creates a V2 test user with enhanced options."""
        res = await self.client.request(
            path="/v1/test/usersV2", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[GenerateV2TestUserResponse], res)

    async def reauthenticate_v2_test_user(
        self, username: str, body: ReauthenticateV2TestUserRequest
    ):
        """Reauthenticates a V2 test user (creates a new API key)."""
        res = await self.client.request(
            path=f"/v1/test/usersV2/{quote(username)}",
            method="PUT",
            body=cast(dict, body),
        )
        return cast(AlphaResponse[ReauthenticateV2TestUserResponse], res)

    async def destroy_v2_test_user(self, username: str):
        """Deletes the V2 test user specified with the username."""
        await self.client.request(
            path=f"/v1/test/usersV2/{quote(username)}", method="DELETE"
        )

    async def create_account(self, body: CreateAccountRequest):
        """Creates a test account with the specified configuration."""
        res = await self.client.request(
            path="/v1/test/accounts", method="POST", body=cast(dict, body)
        )
        return cast(AlphaResponse[CreateAccountResponse], res)

    async def delete_account(self, id: str, params: DeleteAccountParams):
        """Deletes the test account specified with the account id."""
        await self.client.request(
            path=f"/v1/test/accounts/{quote(id)}",
            method="DELETE",
            params=cast(dict, params),
        )

    async def get_account_info(self, id: str):
        """Gets information about the specified test account."""
        res = await self.client.request(
            path=f"/v1/test/accounts/{quote(id)}", method="GET"
        )
        return cast(AlphaResponse[GetAccountInfoResponse], res)
