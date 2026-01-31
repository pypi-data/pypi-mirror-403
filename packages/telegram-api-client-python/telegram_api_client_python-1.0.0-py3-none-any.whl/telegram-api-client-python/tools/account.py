from pathlib import Path
from typing import Dict, TYPE_CHECKING, Optional, Union

import aiofiles

from ..response import Response

if TYPE_CHECKING:
    from ..API import GreenApi


class Account:
    def __init__(self, api: "GreenApi"):
        self.api = api

    def getSettings(self) -> Response:
        """
        The method is aimed for getting the current account settings.

        https://green-api.com/telegram/docs/api/account/GetSettings/
        """

        return self.api.request(
            "GET", (
                "{{host}}/waInstance{{idInstance}}/"
                "getSettings/{{apiTokenInstance}}"
            )
        )

    async def getSettingsAsync(self) -> Response:
        return await self.api.requestAsync(
            "GET", "{{host}}/waInstance{{idInstance}}/getSettings/{{apiTokenInstance}}"
        )

    def getAccountSettings(self) -> Response:
        """
        The method is aimed to get information about the Account
        account.

        https://green-api.com/telegram/docs/api/account/getAccountSettings/
        """

        return self.api.request(
            "GET", (
                "{{host}}/waInstance{{idInstance}}/"
                "getAccountSettings/{{apiTokenInstance}}"
            )
        )

    async def getAccountSettingsAsync(self) -> Response:
        return await self.api.requestAsync(
            "GET", "{{host}}/waInstance{{idInstance}}/getAccountSettings/{{apiTokenInstance}}"
        )

    def setSettings(self, requestBody: Dict[str, Union[int, str]]) -> Response:
        """
        The method is aimed for setting account settings.

        https://green-api.com/telegram/docs/api/account/SetSettings/
        """

        return self.api.request(
            "POST", (
                "{{host}}/waInstance{{idInstance}}/"
                "setSettings/{{apiTokenInstance}}"
            ), requestBody
        )

    async def setSettingsAsync(self, requestBody: Dict[str, Union[int, str]]) -> Response:
        return await self.api.requestAsync(
            "POST",
            "{{host}}/waInstance{{idInstance}}/setSettings/{{apiTokenInstance}}",
            requestBody
        )


    def getStateInstance(self) -> Response:
        """
        The method is aimed for getting the account state.

        https://green-api.com/telegram/docs/api/account/GetStateInstance/
        """

        return self.api.request(
            "GET", (
                "{{host}}/waInstance{{idInstance}}/"
                "getStateInstance/{{apiTokenInstance}}"
            )
        )

    async def getStateInstanceAsync(self) -> Response:
        return await self.api.requestAsync(
            "GET", "{{host}}/waInstance{{idInstance}}/getStateInstance/{{apiTokenInstance}}"
        )
    
    def reboot(self) -> Response:
        """
        The method is aimed for rebooting an account.

        https://green-api.com/telegram/docs/api/account/Reboot/
        """

        return self.api.request(
            "GET", (
                "{{host}}/waInstance{{idInstance}}/reboot/{{apiTokenInstance}}"
            )
        )

    async def rebootAsync(self) -> Response:
        return await self.api.requestAsync(
            "GET", "{{host}}/waInstance{{idInstance}}/reboot/{{apiTokenInstance}}"
        )

    def logout(self) -> Response:
        """
        The method is aimed for logging out an account.

        https://green-api.com/telegram/docs/api/account/Logout/
        """

        return self.api.request(
            "GET", (
                "{{host}}/waInstance{{idInstance}}/logout/{{apiTokenInstance}}"
            )
        )

    async def logoutAsync(self) -> Response:
        return await self.api.requestAsync(
            "GET", "{{host}}/waInstance{{idInstance}}/logout/{{apiTokenInstance}}"
        )

    def qr(self) -> Response:
        """
        The method is aimed for getting QR code.

        https://green-api.com/telegram/docs/api/account/QR/
        """

        return self.api.request(
            "GET", "{{host}}/waInstance{{idInstance}}/qr/{{apiTokenInstance}}"
        )

    async def qrAsync(self) -> Response:
        return await self.api.requestAsync(
            "GET", "{{host}}/waInstance{{idInstance}}/qr/{{apiTokenInstance}}"
        )

    def setProfilePicture(self, path: str) -> Response:
        """
        The method is aimed for setting an account picture.

        https://green-api.com/telegram/docs/api/account/SetProfilePicture/
        """

        file_name = Path(path).name
        files = {"file": (file_name, open(path, "rb"), "image/jpeg")}

        return self.api.request(
            "POST", (
                "{{host}}/waInstance{{idInstance}}/"
                "setProfilePicture/{{apiTokenInstance}}"
            ), files=files
        )

    async def setProfilePictureAsync(self, path: str) -> Response:
        file_name = Path(path).name
        async with aiofiles.open(path, "rb") as file:
            file_data = await file.read()
            files = {"file": (file_name, file_data, "image/jpeg")}

        return await self.api.requestAsync(
            "POST", 
            "{{host}}/waInstance{{idInstance}}/setProfilePicture/{{apiTokenInstance}}",
            files=files
        )


    def startAuthorization(self, phoneNumber: int) -> Response:
        """
        The method is designed to receive code for instance authorization.

        https://green-api.com/telegram/docs/api/account/StartAuthorization/
        """

        request_body = locals()
        request_body.pop("self")

        return self.api.request(
            "POST", (
                "{{host}}/waInstance{{idInstance}}/"
                "startAuthorization/{{apiTokenInstance}}"
            ), request_body
        )
    
    async def startAuthorizationAsync(self, phoneNumber: int) -> Response:
        request_body = locals()
        request_body.pop("self")

        return await self.api.requestAsync(
            "POST", 
            "{{host}}/waInstance{{idInstance}}/startAuthorization/{{apiTokenInstance}}",
            request_body
        )
    
    def sendAuthorizationCode(self, code: str,  password: Optional[str] = None) -> Response:
        """
        The method is designed to receive code for instance authorization.

        https://green-api.com/telegram/docs/api/account/SendAuthorizationCode/
        """

        request_body = locals()
        if password is None:
            request_body.pop("password")
        request_body.pop("self")

        return self.api.request(
            "POST", (
                "{{host}}/waInstance{{idInstance}}/"
                "sendAuthorizationCode/{{apiTokenInstance}}"
            ), request_body
        )
    
    async def sendAuthorizationCodeAsync(self, code: str,  password: Optional[str] = None) -> Response:
        request_body = locals()
        if password is None:
            request_body.pop("password")
        request_body.pop("self")

        return await self.api.requestAsync(
            "POST", 
            "{{host}}/waInstance{{idInstance}}/sendAuthorizationCode/{{apiTokenInstance}}",
            request_body
        )
    
    def sendAuthorizationPassword(self, password: str) -> Response:
        """
        The method is designed to receive code for instance authorization.

        https://green-api.com/telegram/docs/api/account/SendAuthorizationPassword/
        """

        request_body = locals()
        request_body.pop("self")

        return self.api.request(
            "POST", (
                "{{host}}/waInstance{{idInstance}}/"
                "sendAuthorizationPassword/{{apiTokenInstance}}"
            ), request_body
        )
    
    async def sendAuthorizationPasswordAsync(self, password: str) -> Response:
        request_body = locals()
        request_body.pop("self")

        return await self.api.requestAsync(
            "POST", 
            "{{host}}/waInstance{{idInstance}}/sendAuthorizationPassword/{{apiTokenInstance}}",
            request_body
        )