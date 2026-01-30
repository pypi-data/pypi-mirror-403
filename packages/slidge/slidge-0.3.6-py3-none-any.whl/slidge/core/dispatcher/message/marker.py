from typing import Any

from slixmpp import JID, Message
from slixmpp.xmlstream import StanzaBase

from ....contact import LegacyContact
from ....group.room import LegacyMUC
from ....util.types import Recipient
from ..util import DispatcherMixin, exceptions_to_xmpp_errors, get_recipient


class MarkerMixin(DispatcherMixin):
    __slots__: list[str] = []

    def __init__(self, xmpp) -> None:
        super().__init__(xmpp)
        xmpp.add_event_handler("marker_displayed", self.on_marker_displayed)
        xmpp.add_event_handler(
            "message_displayed_synchronization_publish",
            self.on_message_displayed_synchronization_publish,
        )

    @exceptions_to_xmpp_errors
    async def on_marker_displayed(self, msg: StanzaBase) -> None:
        assert isinstance(msg, Message)
        session = await self._get_session(msg)

        e: Recipient = await get_recipient(session, msg)
        legacy_thread = await self._xmpp_to_legacy_thread(session, msg, e)
        to_mark = self.__to_mark(e, msg["displayed"]["id"])
        for xmpp_id in to_mark:
            await session.on_displayed(
                e, self._xmpp_msg_id_to_legacy(session, xmpp_id, e), legacy_thread
            )
        if isinstance(e, LegacyMUC):
            await e.echo(msg, None)

    def __to_mark(
        self, chat: LegacyContact[Any] | LegacyMUC[Any, Any, Any, Any], msg_id: str
    ) -> list[str]:
        if self.xmpp.MARK_ALL_MESSAGES:
            return chat.pop_unread_xmpp_ids_up_to(msg_id)
        else:
            return [msg_id]

    @exceptions_to_xmpp_errors
    async def on_message_displayed_synchronization_publish(
        self, msg: StanzaBase
    ) -> None:
        assert isinstance(msg, Message)
        chat_jid = JID(msg["pubsub_event"]["items"]["item"]["id"])
        if chat_jid.server != self.xmpp.boundjid.bare:
            return

        session = await self._get_session(msg, timeout=None)

        if chat_jid == self.xmpp.boundjid.bare:
            return

        chat = await session.get_contact_or_group_or_participant(chat_jid)
        if not isinstance(chat, LegacyMUC):
            session.log.debug("Ignoring non-groupchat MDS event")
            return

        stanza_id = msg["pubsub_event"]["items"]["item"]["displayed"]["stanza_id"]["id"]
        to_mark = self.__to_mark(chat, stanza_id)
        for xmpp_id in to_mark:
            await session.on_displayed(
                chat, self._xmpp_msg_id_to_legacy(session, xmpp_id, chat)
            )
