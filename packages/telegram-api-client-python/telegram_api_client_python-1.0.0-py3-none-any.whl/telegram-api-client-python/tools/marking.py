from typing import TYPE_CHECKING

from ..response import Response

if TYPE_CHECKING:
    from ..API import GreenApi


class Marking:
    def __init__(self, api: "GreenApi"):
        self.api = api

    def readChat(self, chatId: str) -> Response:
        """
        The method is aimed for marking messages in a chat as read.

        https://green-api.com/telegram/docs/api/marks/ReadChat/
        """

        request_body = locals()
        request_body.pop("self")

        return self.api.request(
            "POST", (
                "{{host}}/waInstance{{idInstance}}/"
                "readChat/{{apiTokenInstance}}"
            ), request_body
        )

    async def readChatAsync(self, chatId: str) -> Response:
        request_body = locals()
        request_body.pop("self")

        return await self.api.requestAsync(
            "POST",
            "{{host}}/waInstance{{idInstance}}/readChat/{{apiTokenInstance}}",
            request_body
        )