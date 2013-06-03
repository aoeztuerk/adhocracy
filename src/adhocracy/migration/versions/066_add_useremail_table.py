from datetime import datetime
from sqlalchemy import *

meta = MetaData()

user_table = Table('user', meta,
    Column('id', Integer, primary_key=True),
    Column('user_name', Unicode(255), nullable=False, unique=True, index=True),
    Column('display_name', Unicode(255), nullable=True, index=True),
    Column('bio', UnicodeText(), nullable=True),
    Column('email', Unicode(255), nullable=True, unique=False),
    Column('email_priority', Integer, default=3),
    Column('activation_code', Unicode(255), nullable=True, unique=False),
    Column('reset_code', Unicode(255), nullable=True, unique=False),
    Column('password', Unicode(80), nullable=False),
    Column('locale', Unicode(7), nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('delete_time', DateTime)
    )

useremail_table = Table(
    'useremail', meta,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('email', Unicode(255), unique=True),
    Column('activation_code', Unicode(255), nullable=True, unique=False),
    Column('delete_time', DateTime, nullable=True)
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    useremail_table.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
