from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
ping = Table('ping', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('message', String(length=150)),
    Column('timestamp', DateTime),
    Column('startTime', DateTime),
    Column('endTime', DateTime),
    Column('impressions', Integer),
    Column('engagements', Integer),
    Column('company_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['ping'].columns['engagements'].create()
    post_meta.tables['ping'].columns['impressions'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['ping'].columns['engagements'].drop()
    post_meta.tables['ping'].columns['impressions'].drop()
