import logging
import typing
from contextlib import contextmanager

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from ...db.models import Base, Contact, Participant, Room

if typing.TYPE_CHECKING:
    from slidge import BaseGateway


class DBMixin:
    stored: Base
    xmpp: "BaseGateway"
    log: logging.Logger

    def merge(self) -> None:
        with self.xmpp.store.session() as orm:
            self.stored = orm.merge(self.stored)

    def commit(self, merge: bool = False) -> None:
        with self.xmpp.store.session(expire_on_commit=False) as orm:
            if merge:
                self.log.debug("Merging %s", self.stored)
                self.stored = orm.merge(self.stored)
                self.log.debug("Merged %s", self.stored)
            orm.add(self.stored)
            self.log.debug("Committing to DB")
            orm.commit()


class UpdateInfoMixin(DBMixin):
    """
    This mixin just adds a context manager that prevents commiting to the DB
    on every attribute change.
    """

    stored: Contact | Room
    xmpp: "BaseGateway"
    log: logging.Logger

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._updating_info = False
        self.__deserialize()

    def __deserialize(self):
        if self.stored.extra_attributes is not None:
            self.deserialize_extra_attributes(self.stored.extra_attributes)

    def refresh(self) -> None:
        with self.xmpp.store.session(expire_on_commit=False) as orm:
            orm.add(self.stored)
            orm.refresh(self.stored)
            self.__deserialize()

    def serialize_extra_attributes(self) -> dict | None:
        """
        If you want custom attributes of your instance to be stored persistently
        to the DB, here is where you have to return them as a dict to be used in
        `deserialize_extra_attributes()`.

        """
        return None

    def deserialize_extra_attributes(self, data: dict) -> None:
        """
        This is where you get the dict that you passed in
        `serialize_extra_attributes()`.

        ⚠ Since it is serialized as json, dictionary keys are converted to strings!
        Be sure to convert to other types if necessary.
        """
        pass

    @contextmanager
    def updating_info(self, merge=True):
        self._updating_info = True
        yield
        self._updating_info = False
        self.stored.updated = True
        try:
            self.commit(merge=merge)
        except IntegrityError as e:
            from slidge.group import LegacyMUC

            if not isinstance(self, LegacyMUC):
                raise e
            if not self._ALL_INFO_FILLED_ON_STARTUP:
                raise e
            with self.xmpp.store.session(expire_on_commit=False) as orm:
                if self.stored.id is None:
                    self.stored.id = self.xmpp.store.rooms.get(
                        orm, self.user_pk, legacy_id=str(self.legacy_id)
                    ).id
                merged = orm.merge(self.stored)
                resources = set()
                participants: list[Participant] = []
                for participant in merged.participants:
                    if participant.resource in resources:
                        self.session.log.warning("ditching: %s", participant)
                        continue
                    resources.add(participant.resource)
                merged.participants = participants
                self.stored = merged
                orm.add(self.stored)
                orm.commit()

    def commit(self, merge: bool = False) -> None:
        if self._updating_info:
            self.log.debug("Not updating %s right now", self.stored)
        else:
            self.stored.extra_attributes = self.serialize_extra_attributes()
            super().commit(merge=merge)

    def update_stored_attribute(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self.stored, key, value)
        if self._updating_info:
            return
        with self.xmpp.store.session() as orm:
            orm.execute(
                sa.update(self.stored.__class__)
                .where(self.stored.__class__.id == self.stored.id)
                .values(**kwargs)
            )
            orm.commit()
