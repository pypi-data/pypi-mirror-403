# coding=utf8
"""Sopel Pets Plugin

A plugin for Sopel that posts pets in the channel
"""
from __future__ import annotations

from random import seed

from sopel import plugin
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine, event, exc
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import Pool
from sqlalchemy.sql.functions import random


__author__ = 'Rusty Bower'
__email__ = 'rusty@rustybower.com'
__version__ = '1.0.0'


Base = declarative_base()


@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except Exception:
        raise exc.DisconnectionError()
    cursor.close()


class PetsDB(Base):
    __tablename__ = 'pets'
    id = Column(Integer, primary_key=True)
    url = Column(String(255))
    type = Column(String(4))


class Pets:
    @staticmethod
    def add(bot, url, pettype):
        session = bot.db.session()
        if Pets.search(bot, url):
            return False
        new_pet = PetsDB(url=url, type=pettype)
        session.add(new_pet)
        session.commit()
        session.close()
        return True

    @staticmethod
    def delete(bot, url):
        session = bot.db.session()
        if not Pets.search(bot, url):
            return False
        session.query(PetsDB).filter(PetsDB.url == url).delete()
        session.commit()
        session.close()
        return True

    @staticmethod
    def search(bot, url):
        session = bot.db.session()
        res = session.query(PetsDB).filter(PetsDB.url == url).one_or_none()
        session.close()
        return res

    @staticmethod
    def random(bot, pettype):
        session = bot.db.session()
        res = session.query(PetsDB).filter(PetsDB.type == pettype).order_by(random()).first()
        session.close()
        return res


def setup(bot):
    engine = create_engine(bot.db.url)
    Base.metadata.create_all(engine)
    seed()


def pets(bot, trigger, pettype):
    if not trigger.group(2):
        m = Pets.random(bot, pettype)
        if not m:
            return bot.say(f'ERROR: Unable to get random {pettype}')
        return bot.say(m.url)

    args = trigger.group(2).split()

    if len(args) < 2:
        return bot.say('Error: Invalid Arguments')

    if len(args[1]) > 255:
        return bot.say('ERROR: URL Too Long (>255 characters)')

    if args[0].casefold() == 'add':
        if not Pets.add(bot, args[1], pettype):
            return bot.say(f'ERROR: {pettype} already exists')
        return bot.say(f'{pettype} added')

    elif args[0].casefold() == 'delete':
        if not Pets.delete(bot, args[1]):
            return bot.say('ERROR: URL Does Not Exist')
        return bot.say(f'{pettype} deleted')

    else:
        return bot.say('Error: Invalid Arguments')


@plugin.command('meow')
@plugin.priority('high')
@plugin.example('.meow')
@plugin.example('.meow add URL')
@plugin.example('.meow delete URL')
def meow(bot, trigger):
    """Post random cat to the channel, or add/delete cats."""
    pets(bot, trigger, 'meow')


@plugin.command('woof')
@plugin.priority('high')
@plugin.example('.woof')
@plugin.example('.woof add URL')
@plugin.example('.woof delete URL')
def woof(bot, trigger):
    """Post random dog to the channel, or add/delete dogs."""
    pets(bot, trigger, 'woof')
