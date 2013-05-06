from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey, or_
from sqlalchemy import DateTime, Integer, Unicode

import meta

log = logging.getLogger(__name__)


multiple_email_table = Table(
    'multiple_email', meta.data,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('email', Unicode(255), nullable=True, unique=True),
    Column('activation_code', Unicode(255), nullable=True, unique=False),
    Column('verified', Boolean, default=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True)
)


class Multiple_email(object):

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

    def __repr__(self):
        return u"<Multiple_email(%d,%s)>" % (self.id,
                                            self.user.user_id,
                                            self.email)

