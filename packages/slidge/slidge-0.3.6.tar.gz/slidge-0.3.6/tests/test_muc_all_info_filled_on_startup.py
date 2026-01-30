import pytest
from slixmpp.exceptions import XMPPError

from conftest import AvatarFixtureMixin, UUIDFixtureMixin
from slixmpp import JID, Iq

from slidge import BaseGateway, BaseSession, GatewayUser
from slidge.contact import LegacyContact
from slidge.group import LegacyBookmarks, LegacyMUC
from slidge.util.test import SlidgeTest


class Gateway(BaseGateway):
    COMPONENT_NAME = "A test"
    GROUPS = True


class Session(BaseSession):
    async def login(self):
        return "YUP"


class Contact(LegacyContact):
    async def update_info(self):
        if self.legacy_id.startswith("room"):
            raise XMPPError
        if self.legacy_id == "no-nick":
            self.online()
            return
        self.name = "duplicate"


class MUC(LegacyMUC):
    _ALL_INFO_FILLED_ON_STARTUP = True

    async def update_participants(self):
        if self.legacy_id == "room-occupant-id":
            await self.get_participant("nick", occupant_id="unique-id-1")
            await self.get_participant("nick", occupant_id="unique-id-2")
        elif self.legacy_id == "room-user-nick-taken":
            await self.get_participant("user", occupant_id="unique-id-1")
            await self.get_user_participant(occupant_id="user-id")
        else:
            await self.get_participant_by_legacy_id("dup1")
            dup = await self.get_participant(occupant_id="unique-id")
            dup.nickname = "duplicate"


class Bookmarks(LegacyBookmarks):
    ROOMS = ["room", "room-occupant-id", "room-user-nick-taken"]

    async def fill(self):
        for legacy_id in Bookmarks.ROOMS:
            muc = await self.by_legacy_id(legacy_id)
            await muc.update_participants()


@pytest.mark.usefixtures("avatar")
class TestMUCAllInfoOnStartup(UUIDFixtureMixin, AvatarFixtureMixin, SlidgeTest):
    plugin = globals()
    xmpp: Gateway

    def setUp(self):
        super().setUp()
        with self.xmpp.store.session() as orm:
            user = GatewayUser(
                jid=JID("user@test").bare,
                legacy_module_data={"username": "myname", "city": ""},
                preferences={"sync_avatar": False, "sync_presence": True},
            )
            orm.add(user)
            orm.commit()
        self.run_coro(
            self.xmpp._BaseGateway__dispatcher._on_user_register(
                Iq(sfrom="user@test")
            )
        )
        welcome = self.next_sent()
        assert welcome["body"]
        stanza = self.next_sent()
        assert "logging in" in stanza["status"].lower(), stanza
        stanza = self.next_sent()
        assert "syncing contacts" in stanza["status"].lower(), stanza
        stanza = self.next_sent()
        assert "syncing groups" in stanza["status"].lower(), stanza
        probe = self.next_sent()
        assert probe.get_type() == "probe"
        stanza = self.next_sent()
        assert "yup" in stanza["status"].lower(), stanza


    @property
    def user_session(self) -> Session:
        return BaseSession.get_self_or_unique_subclass().from_jid(
            JID("user@test")
        )

    def test_join(self):
        self.recv(  # language=XML
            f"""
            <presence from="{self.user_session.user_jid}/client"
                      to="room@aim.shakespeare.lit/mynick">
              <x xmlns='http://jabber.org/protocol/muc' />
            </presence>
            """
        )
        self.send(  # language=XML
            """
            <presence from="room@aim.shakespeare.lit/duplicate"
                      to="user@test/client">
              <x xmlns="http://jabber.org/protocol/muc#user">
                <item affiliation="member"
                      role="participant" />
              </x>
              <occupant-id xmlns="urn:xmpp:occupant-id:0"
                           id="dup1@aim.shakespeare.lit/slidge" />
            </presence>
            """
        )
        self.send(  # language=XML
            """
            <presence from="room@aim.shakespeare.lit/duplicate (unique-id)"
                      to="user@test/client">
              <x xmlns="http://jabber.org/protocol/muc#user">
                <item affiliation="member"
                      role="participant" />
              </x>
              <occupant-id xmlns="urn:xmpp:occupant-id:0"
                           id="unique-id" />
            </presence>
            """
        )
        self.send(  # language=XML
            f"""
            <presence from="room@aim.shakespeare.lit/user"
                      to="user@test/client">
              <x xmlns="http://jabber.org/protocol/muc#user">
                <item affiliation="member"
                      role="participant" />
                <status code="210" />
                <status code="110" />
              </x>
              <occupant-id xmlns="urn:xmpp:occupant-id:0"
                           id="slidge-user" />
            </presence>
            """
        )
        self.send(  # language=XML
            """
            <message type="groupchat"
                     from="room@aim.shakespeare.lit"
                     to="user@test/client">
              <stanza-id xmlns="urn:xmpp:sid:0"
                         id="5"
                         by="room@aim.shakespeare.lit" />
              <subject />
              <occupant-id xmlns="urn:xmpp:occupant-id:0"
                           id="room" />
            </message>
            """,
            use_values=False,
        )
        self.send("""
            <presence xmlns="jabber:component:accept"
                      to="user@test/client"
                      from="room@aim.shakespeare.lit">
              <x xmlns="vcard-temp:x:update">
                <photo />
              </x>
            </presence>
            """, use_values=False)
        self.recv(  # language=XML
            """
            <iq type="get"
                from="user@test/client"
                to="room@aim.shakespeare.lit"
                id="123">
              <query xmlns='http://jabber.org/protocol/disco#info' />
            </iq>
            """
        )
        self.send(  # language=XML
            """
            <iq xmlns="jabber:component:accept"
                type="result"
                from="room@aim.shakespeare.lit"
                to="user@test/client"
                id="123">
              <query xmlns="http://jabber.org/protocol/disco#info">
                <identity category="conference"
                          type="text" />
                <feature var="http://jabber.org/protocol/muc" />
                <feature var="http://jabber.org/protocol/muc#stable_id" />
                <feature var="http://jabber.org/protocol/muc#self-ping-optimization" />
                <feature var="urn:xmpp:mam:2" />
                <feature var="urn:xmpp:mam:2#extended" />
                <feature var="urn:xmpp:sid:0" />
                <feature var="muc_persistent" />
                <feature var="vcard-temp" />
                <feature var="urn:xmpp:ping" />
                <feature var="urn:xmpp:occupant-id:0" />
                <feature var="jabber:iq:register" />
                <feature var="urn:xmpp:message-moderate:1" />
                <feature var="muc_open" />
                <feature var="muc_semianonymous" />
                <feature var="muc_public" />
                <x xmlns="jabber:x:data"
                   type="result">
                  <field var="FORM_TYPE"
                         type="hidden">
                    <value>http://jabber.org/protocol/muc#roominfo</value>
                  </field>
                  <field var="muc#roomconfig_persistentroom"
                         type="boolean">
                    <value>1</value>
                  </field>
                  <field var="muc#roomconfig_changesubject"
                         type="boolean">
                    <value>0</value>
                  </field>
                  <field var="muc#maxhistoryfetch">
                    <value>100</value>
                  </field>
                  <field var="muc#roominfo_subjectmod"
                         type="boolean">
                    <value>0</value>
                  </field>
                  <field var="muc#roominfo_occupants">
                    <value>3</value>
                  </field>
                  <field var="muc#roomconfig_membersonly"
                         type="boolean">
                    <value>0</value>
                  </field>
                  <field var="muc#roomconfig_whois"
                         type="list-single">
                    <value>moderators</value>
                  </field>
                  <field var="muc#roomconfig_publicroom"
                         type="boolean">
                    <value>1</value>
                  </field>
                  <field var="muc#roomconfig_allowpm"
                         type="boolean">
                    <value>0</value>
                  </field>
                </x>
              </query>
            </iq>
            """
        )

    def test_join_occupant_id(self):
        self.recv(  # language=XML
            f"""
            <presence from="{self.user_session.user_jid}/client"
                      to="room-occupant-id@aim.shakespeare.lit/mynick">
              <x xmlns='http://jabber.org/protocol/muc' />
            </presence>
            """
        )
        self.send(  # language=XML
            """
            <presence from="room-occupant-id@aim.shakespeare.lit/nick"
                      to="user@test/client">
              <x xmlns="http://jabber.org/protocol/muc#user">
                <item affiliation="member"
                      role="participant" />
              </x>
              <occupant-id xmlns="urn:xmpp:occupant-id:0"
                           id="unique-id-1" />
            </presence>
            """
        )
        self.send(  # language=XML
            """
            <presence from="room-occupant-id@aim.shakespeare.lit/nick (unique-id-2)"
                      to="user@test/client">
              <x xmlns="http://jabber.org/protocol/muc#user">
                <item affiliation="member"
                      role="participant" />
              </x>
              <occupant-id xmlns="urn:xmpp:occupant-id:0"
                           id="unique-id-2" />
            </presence>
            """
        )
        self.send(  # language=XML
            f"""
            <presence from="room-occupant-id@aim.shakespeare.lit/user"
                      to="user@test/client">
              <x xmlns="http://jabber.org/protocol/muc#user">
                <item affiliation="member"
                      role="participant" />
                <status code="210" />
                <status code="110" />
              </x>
              <occupant-id xmlns="urn:xmpp:occupant-id:0"
                           id="slidge-user" />
            </presence>
            """
        )
        self.send(  # language=XML
            """
            <message type="groupchat"
                     from="room-occupant-id@aim.shakespeare.lit"
                     to="user@test/client">
              <stanza-id xmlns="urn:xmpp:sid:0"
                         id="5"
                         by="room-occupant-id@aim.shakespeare.lit" />
              <subject />
              <occupant-id xmlns="urn:xmpp:occupant-id:0"
                           id="room" />
            </message>
            """,
            use_values=False,
        )

    def test_updating_info(self):
        contact = self.run_coro(self.user_session.contacts.by_legacy_id("no-nick"))
        with contact.updating_info():
            contact.name = "prout"
        assert contact.name == "prout"
        contact = self.run_coro(self.user_session.contacts.by_legacy_id("no-nick"))
        assert contact.name == "prout"


class TestMUCUserNickIsTaken(UUIDFixtureMixin, AvatarFixtureMixin, SlidgeTest):
    plugin = globals()
    xmpp: Gateway

    def setUp(self):
        super().setUp()
        with self.xmpp.store.session() as orm:
            user = GatewayUser(
                jid=JID("user@test").bare,
                legacy_module_data={"username": "myname", "city": ""},
                preferences={"sync_avatar": False, "sync_presence": True},
            )
            orm.add(user)
            orm.commit()
        self.run_coro(
            self.xmpp._BaseGateway__dispatcher._on_user_register(
                Iq(sfrom="user@test")
            )
        )
        welcome = self.next_sent()
        assert welcome["body"]
        stanza = self.next_sent()
        assert "logging in" in stanza["status"].lower(), stanza
        stanza = self.next_sent()
        assert "syncing contacts" in stanza["status"].lower(), stanza
        stanza = self.next_sent()
        assert "syncing groups" in stanza["status"].lower(), stanza
        probe = self.next_sent()
        assert probe.get_type() == "probe"
        stanza = self.next_sent()
        assert "yup" in stanza["status"].lower(), stanza

    def test_user_nick_is_taken(self):
        self.recv(  # language=XML
            f"""
            <presence from="user@test/client"
                      to="room-user-nick-taken@aim.shakespeare.lit/user">
              <x xmlns='http://jabber.org/protocol/muc' />
            </presence>
            """
        )
        self.send(  # language=XML
            """
            <presence from="room-user-nick-taken@aim.shakespeare.lit/user"
                      to="user@test/client">
              <x xmlns="http://jabber.org/protocol/muc#user">
                <item affiliation="member"
                      role="participant" />
              </x>
              <occupant-id xmlns="urn:xmpp:occupant-id:0"
                           id="unique-id-1" />
            </presence>
            """
        )
        self.send(  # language=XML
            """
            <presence from="room-user-nick-taken@aim.shakespeare.lit/user (user-id)"
                      to="user@test/client">
              <x xmlns="http://jabber.org/protocol/muc#user">
                <item affiliation="member"
                      role="participant" />
                <status code="110" />
                <status code="210" />
              </x>
              <occupant-id xmlns="urn:xmpp:occupant-id:0"
                           id="user-id" />
            </presence>
            """,
            use_values=False,
        )
        assert self.next_sent() is not None # subject
        assert self.next_sent() is not None # room avatar
