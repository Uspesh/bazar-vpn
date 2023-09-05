from .database import Base
from sqlalchemy import Integer, String, Date, Column, ForeignKey, Boolean

'''
Dates:
c_date - дата создания
e_date - дата окончания, экспирации
'''


class VPNConfig(Base):
    __tablename__ = 'vpn_configs'

    id = Column(Integer, primary_key=True)
    peer_id = Column(Integer)
    country = Column(String)
    address = Column(String)
    private_key = Column(String)
    listen_port = Column(Integer)
    dns = Column(String)
    public_key = Column(String)
    preshared_key = Column(String)
    endpoint = Column(String)
    allowed_ips = Column(String)
    sub_status = Column(Integer)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    status = Column(Integer)
    balance = Column(Integer)
    key_id = Column(Integer, ForeignKey('keys.id'))
    c_date = Column(Date)
    auto_subscription = Column(Boolean)
    channel_sub = Column(Boolean)


class Key(Base):
    __tablename__ = 'keys'

    id = Column(Integer, primary_key=True)
    number = Column(String)
    bot_code = Column(Integer) # код для партнеров
    status = Column(String) #free or activated
    c_date = Column(Date)
    e_date = Column(Date) # + 3 месяца от c_date


# class License(Base):
#     __tablename__ = 'licenses'
#
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey(User.id))
#     key_id = Column(Integer, ForeignKey(Key.id))


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    vpn_id = Column(Integer, ForeignKey(VPNConfig.id))
    c_date = Column(Date)
    e_date = Column(Date)


class Admin(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, unique=True)


class Server(Base):
    __tablename__ = 'servers'

    id = Column(Integer, primary_key=True)
    country = Column(String)
    host = Column(String)
    port = Column(Integer)
    username = Column(String)
    password = Column(String)


class Stats(Base):
    __tablename__ = 'stats'

    id = Column(Integer, primary_key=True)
    total_earned_money = Column(Integer)
    cancelled_subs = Column(Integer)