from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping

import httpx

from pyznuny.ticket.models import TicketCreatePayload

if TYPE_CHECKING:
    from pyznuny.ticket.client import TicketClient


class SessionRoutes:
    def __init__(self, client: "TicketClient") -> None:
        self._client = client

    def create(self, username: str, password: str) -> httpx.Response:
        """
        Creates a new session with the given username and password.
        
        :param username: username for authentication
        :type username: str
        :param password: password for authentication
        :type password: str
        :return: Response object containing session details
        :rtype: Response
        """
        return self._client.request(
            "session_create",
            json={"UserLogin": username, "Password": password},
        )


class TicketRoutes:
    def __init__(self, client: "TicketClient") -> None:
        self._client = client

    def create(
        self,
        payload: TicketCreatePayload | Mapping[str, Any] | None = None,
        **payload_kwargs: Any,
    ) -> httpx.Response:
        
        if payload is None:
            payload_dict = dict(payload_kwargs)
            
        elif isinstance(payload, TicketCreatePayload):
            payload_dict = payload.to_dict()
            payload_dict.update(payload_kwargs)
        else:
            payload_dict = dict(payload)
            payload_dict.update(payload_kwargs)

        payload_dict.update({"SessionID": self._client.session_id})
        return self._client.request("ticket_create", json=payload_dict)
    

    def update(self, ticket_id: str | int , **payload: dict) -> httpx.Response:
        identifier = self._client.endpoint_identifier("ticket_update")
        
        payload.update({"SessionID": self._client.session_id})
        return self._client.request(
            "ticket_update",
            path_params={identifier: ticket_id},
            json=payload,
        )
        
    def get(self, ticket_id: str | int, 
            dynamic_fields:int=0,
            all_articles:int=0) -> httpx.Response:
        identifier = self._client.endpoint_identifier("ticket_get")
        return self._client.request(
            "ticket_get",
            path_params={identifier: ticket_id},
            params={"SessionID": self._client.session_id,
                    "DynamicFields": dynamic_fields,
                    "AllArticles": all_articles},
        )
