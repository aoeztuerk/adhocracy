from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey, or_
from sqlalchemy import DateTime, Integer, Unicode

import meta

log = logging.getLogger(__name__)


useremail_table = Table(
    'useremail', meta.data,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('email', Unicode(255), unique=True),
    Column('activation_code', Unicode(255), nullable=True, unique=False),
    Column('delete_time', DateTime, nullable=True)
)


class UserEmail(object):

    def __init__(self, user, email):
        self.user = user
        self.email = email

    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        if self.delete_time is None:
            self.delete_time = delete_time

    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
            self.delete_time <= at_time

    def _get_email(self):
        return self._email

    def _set_email(self, email):
        import adhocracy.lib.util as util
        if not self._email == email:
            self.activation_code = util.random_token()
        self._email = email

    email = property(_get_email, _set_email)

    def is_email_activated(self):
        return self.email is not None and self.activation_code is None

    def __repr__(self):
        return u"<UserEmail(%d,%d,%s)>" % (self.id,
                                            self.user.user_id,
                                            self.email)

