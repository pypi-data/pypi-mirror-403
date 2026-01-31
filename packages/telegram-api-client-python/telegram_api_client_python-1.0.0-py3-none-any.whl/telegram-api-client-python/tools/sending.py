import mimetypes
import pathlib
from typing import Dict, List, Optional, TYPE_CHECKING, Union

import aiofiles

from ..response import Response

if TYPE_CHECKING:
    from ..API import GreenApi


class Sending:
    def __init__(self, api: "GreenApi"):
        self.api = api

    def sendMessage(
            self,
            chatId: str,
            message: str,
    ) -> Response:
        """
        The method is aimed for sending a text message to a personal or
        a group chat.

        https://green-api.com/telegram/docs/api/sending/SendMessage/
        """

        request_body = self.__handle_parameters(locals())

        return self.api.request(
            "POST", (
                "{{host}}/waInstance{{idInstance}}/"
                "sendMessage/{{apiTokenInstance}}"
            ), request_body
        )

    async def sendMessageAsync(
            self,
            chatId: str,
            message: str,
    ) -> Response:
        request_body = self.__handle_parameters(locals())

        return await self.api.requestAsync(
            "POST",
            "{{host}}/waInstance{{idInstance}}/sendMessage/{{apiTokenInstance}}",
            request_body
        )

    def sendFileByUpload(
            self,
            chatId: str,
            path: str,
            fileName: Optional[str] = None,
            caption: Optional[str] = None,
    ) -> Response:
        """
        The method is aimed for sending a file uploaded by form
        (form-data).

        https://green-api.com/telegram/docs/api/sending/SendFileByUpload/
        """

        request_body = self.__handle_parameters(locals())

        file_name = pathlib.Path(path).name
        content_type = mimetypes.guess_type(file_name)[0]

        files = {"file": (file_name, open(path, "rb"), content_type)}

        request_body.pop("path")

        return self.api.request(
            "POST", (
                "{{media}}/waInstance{{idInstance}}/"
                "sendFileByUpload/{{apiTokenInstance}}"
            ), request_body, files
        )

    async def sendFileByUploadAsync(
            self,
            chatId: str,
            path: str,
            fileName: Optional[str] = None,
            caption: Optional[str] = None,
    ) -> Response:
        request_body = self.__handle_parameters(locals())

        file_name = pathlib.Path(path).name
        content_type = mimetypes.guess_type(file_name)[0]

        async with aiofiles.open(path, "rb") as file:
            file_data = await file.read()
            files = {"file": (file_name, file_data, content_type)}

        request_body.pop("path")

        return await self.api.requestAsync(
            "POST", 
            "{{media}}/waInstance{{idInstance}}/sendFileByUpload/{{apiTokenInstance}}",
            request_body, 
            files=files
        )

    def sendFileByUrl(
            self,
            chatId: str,
            urlFile: str,
            fileName: str,
            caption: Optional[str] = None,
    ) -> Response:
        """
        The method is aimed for sending a file uploaded by URL.

        https://green-api.com/telegram/docs/api/sending/SendFileByUrl/
        """

        request_body = self.__handle_parameters(locals())

        return self.api.request(
            "POST", (
                "{{host}}/waInstance{{idInstance}}/"
                "sendFileByUrl/{{apiTokenInstance}}"
            ), request_body
        )

    async def sendFileByUrlAsync(
            self,
            chatId: str,
            urlFile: str,
            fileName: str,
            caption: Optional[str] = None,
    ) -> Response:
        request_body = self.__handle_parameters(locals())

        return await self.api.requestAsync(
            "POST",
            "{{host}}/waInstance{{idInstance}}/sendFileByUrl/{{apiTokenInstance}}",
            request_body
        )

    def uploadFile(self, path: str) -> Response:
        """
        The method is designed to upload a file to the cloud storage,
        which can be sent using the sendFileByUrl method.

        https://green-api.com/telegram/docs/api/sending/UploadFile/
        """

        file_name = pathlib.Path(path).name
        content_type = mimetypes.guess_type(file_name)[0]

        with open(path, "rb") as file:
            return self.api.raw_request(
                method="POST",
                url=(
                    f"{self.api.media}/waInstance{self.api.idInstance}/"
                    f"uploadFile/{self.api.apiTokenInstance}"
                ),
                data=file.read(),
                headers={"Content-Type": content_type,
                         "GA-Filename": file_name}
            )

    async def uploadFileAsync(self, path: str) -> Response:
        file_name = pathlib.Path(path).name
        content_type = mimetypes.guess_type(file_name)[0]

        async with aiofiles.open(path, "rb") as file:
            return await self.api.raw_request_async(
                method="POST",
                url=(
                    f"{self.api.media}/waInstance{self.api.idInstance}/"
                    f"uploadFile/{self.api.apiTokenInstance}"
                ),
                data=file.read(),
                headers={"Content-Type": content_type,
                         "GA-Filename": file_name}
            )

    def sendLocation(
            self,
            chatId: str,
            latitude: float,
            longitude: float,
    ) -> Response:
        """
        The method is aimed for sending location message.

        https://green-api.com/telegram/docs/api/sending/SendLocation/
        """

        request_body = self.__handle_parameters(locals())

        return self.api.request(
            "POST", (
                "{{host}}/waInstance{{idInstance}}/"
                "sendLocation/{{apiTokenInstance}}"
            ), request_body
        )

    async def sendLocationAsync(
            self,
            chatId: str,
            latitude: float,
            longitude: float,
    ) -> Response:
        request_body = self.__handle_parameters(locals())

        return await self.api.requestAsync(
            "POST",
            "{{host}}/waInstance{{idInstance}}/sendLocation/{{apiTokenInstance}}",
            request_body
        )

    def sendContact(
            self,
            chatId: str,
            contact: Dict[str, Union[int, str]],
    ) -> Response:
        """
        The method is aimed for sending a contact message.

        https://green-api.com/telegram/docs/api/sending/SendContact/
        """

        request_body = self.__handle_parameters(locals())

        return self.api.request(
            "POST", (
                "{{host}}/waInstance{{idInstance}}/"
                "sendContact/{{apiTokenInstance}}"
            ), request_body
        )

    async def sendContactAsync(
            self,
            chatId: str,
            contact: Dict[str, Union[int, str]],
    ) -> Response:
        request_body = self.__handle_parameters(locals())

        return await self.api.requestAsync(
            "POST",
            "{{host}}/waInstance{{idInstance}}/sendContact/{{apiTokenInstance}}",
            request_body
        )


    def sendPoll(
            self,
            chatId: str,
            message: str,
            options: List[Dict[str, str]],
            multipleAnswers: Optional[bool] = None,
            isAnonymous: Optional[bool] = None
    ) -> Response:
        """
        This method is intended for sending messages with a poll to a
        private or group chat.

        https://green-api.com/telegram/docs/api/sending/SendPoll/
        """

        request_body = self.__handle_parameters(locals())

        return self.api.request(
            "POST", (
                "{{host}}/waInstance{{idInstance}}/"
                "sendPoll/{{apiTokenInstance}}"
            ), request_body
        )

    async def sendPollAsync(
            self,
            chatId: str,
            message: str,
            options: List[Dict[str, str]],
            multipleAnswers: Optional[bool] = None,
            isAnonymous: Optional[bool] = None
    ) -> Response:
        request_body = self.__handle_parameters(locals())

        return await self.api.requestAsync(
            "POST",
            "{{host}}/waInstance{{idInstance}}/sendPoll/{{apiTokenInstance}}",
            request_body
        )


    @classmethod
    def __handle_parameters(cls, parameters: dict) -> dict:
        handled_parameters = parameters.copy()
        handled_parameters.pop("self")

        for key, value in parameters.items():
            if value is None:
                handled_parameters.pop(key)

        return handled_parameters