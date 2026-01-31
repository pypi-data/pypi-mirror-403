from typing import TYPE_CHECKING

from ..response import Response

if TYPE_CHECKING:
    from ..API import GreenApi


class Queues:
    def __init__(self, api: "GreenApi"):
        self.api = api

    def showMessagesQueue(self) -> Response:
        """
        The method is aimed for getting a list of messages in the queue
        to be sent.

        https://green-api.com/telegram/docs/api/queues/ShowMessagesQueue/
        """

        return self.api.request(
            "GET", (
                "{{host}}/waInstance{{idInstance}}/"
                "showMessagesQueue/{{apiTokenInstance}}"
            )
        )

    async def showMessagesQueueAsync(self) -> Response:
        return await self.api.requestAsync(
            "GET", "{{host}}/waInstance{{idInstance}}/showMessagesQueue/{{apiTokenInstance}}"
        )
    
    def getMessagesCount(self) -> Response:
        """
        The method is aimed for getting a list of messages in the queue
        to be sent.

        https://green-api.com/telegram/docs/api/queues/GetMessagesCount/
        """

        return self.api.request(
            "GET", (
                "{{host}}/waInstance{{idInstance}}/"
                "getMessagesCount/{{apiTokenInstance}}"
            )
        )

    async def getMessagesCountAsync(self) -> Response:
        return await self.api.requestAsync(
            "GET", "{{host}}/waInstance{{idInstance}}/getMessagesCountAsync/{{apiTokenInstance}}"
        )

    def clearMessagesQueue(self) -> Response:
        """
        The method is aimed for clearing the queue of messages to be
        sent.

        https://green-api.com/telegram/docs/api/queues/ClearMessagesQueue/
        """

        return self.api.request(
            "GET", (
                "{{host}}/waInstance{{idInstance}}/"
                "clearMessagesQueue/{{apiTokenInstance}}"
            )
        )

    async def clearMessagesQueueAsync(self) -> Response:
        return await self.api.requestAsync(
            "GET", "{{host}}/waInstance{{idInstance}}/clearMessagesQueue/{{apiTokenInstance}}"
        )
    
    def getWebhooksCount(self) -> Response:
        """
        The method is aimed for getting a list of messages in the queue
        to be sent.

        https://green-api.com/telegram/docs/api/queues/GetWebhooksCount/
        """

        return self.api.request(
            "GET", (
                "{{host}}/waInstance{{idInstance}}/"
                "getWebhooksCount/{{apiTokenInstance}}"
            )
        )

    async def getWebhooksCountAsync(self) -> Response:
        return await self.api.requestAsync(
            "GET", "{{host}}/waInstance{{idInstance}}/getWebhooksCountAsync/{{apiTokenInstance}}"
        )

    def clearWebhooksQueue(self) -> Response:
        """
        The method is aimed for clearing the queue of messages to be
        sent.

        https://green-api.com/telegram/docs/api/queues/clearWebhooksQueue/
        """

        return self.api.request(
            "GET", (
                "{{host}}/waInstance{{idInstance}}/"
                "clearWebhooksQueue/{{apiTokenInstance}}"
            )
        )

    async def clearWebhooksQueueAsync(self) -> Response:
        return await self.api.requestAsync(
            "GET", "{{host}}/waInstance{{idInstance}}/clearWebhooksQueue/{{apiTokenInstance}}"
        )