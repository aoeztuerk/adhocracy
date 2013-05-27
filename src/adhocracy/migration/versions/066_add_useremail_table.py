from sqlalchemy import MetaData, Column, Table
from sqlalchemy import Unicode, UnicodeText

metadata = MetaData()

useremail_table = Table(
    'useremail', meta.data,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('email', Unicode(255), unique=True),
    Column('activation_code', Unicode(255), nullable=True, unique=False),
    Column('delete_time', DateTime, nullable=True)
)


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    useremail_table.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
