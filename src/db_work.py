import asyncio
import configparser
import os
import time
import random

import paramiko
from sqlalchemy import select, insert, update, delete

from .database import engine
from .models import *

import datetime
import hashlib


def generate_label():
    rand_num = random.randint(0, 1000000)
    current_time = str(time.time())
    return hashlib.sha256((str(rand_num) + current_time).encode()).hexdigest()


def get_all_channel_subs():
    with engine.begin() as db:
        stmt = select(User.id).filter(User.channel_sub == 1)
        res = db.execute(stmt)
        channel_subs = res.fetchall()
    return len(channel_subs)


def change_cancelled_subs_amount(num):
    with engine.begin() as db:
        stmt_get_all_cancelled_subs = select(Stats.cancelled_subs).filter(Stats.id == 1)
        res_cancelled_subs = db.execute(stmt_get_all_cancelled_subs)
        all_cancelled_subs = res_cancelled_subs.scalar()
        stmt = update(Stats).values(cancelled_subs=all_cancelled_subs + num).filter(Stats.id == 1)
        db.execute(stmt)
        db.commit()


def get_cancelled_subs_amount():
    with engine.begin() as db:
        stmt = select(Stats.cancelled_subs).filter(Stats.id == 1)
        res = db.execute(stmt)
        cancelled_subs = res.scalar()
    return cancelled_subs


def change_total_earned(sum):
    with engine.begin() as db:
        stmt = update(Stats).values(total_earned_money=sum).filter(Stats.id == 1)
        db.execute(stmt)
        db.commit()


def get_total_earned():
    with engine.begin() as db:
        stmt = select(Stats.total_earned_money).filter(Stats.id == 1)
        res = db.execute(stmt)
        total_earned_money = res.scalar()
    return total_earned_money


def count_new_users(date):
    with engine.begin() as db:
        stmt = select(User.id).filter(User.c_date >= date, User.c_date <= datetime.date.today())
        res = db.execute(stmt)
        users = res.fetchall()
    return len(users)


def count_all_users():
    with engine.begin() as db:
        stmt = select(User.id)
        res = db.execute(stmt)
        users = res.fetchall()
    return len(users)


def get_all_tg_ids():
    with engine.begin() as db:
        stmt = select(User.telegram_id)
        res = db.execute(stmt)
        tg_ids = res.fetchall()
    return tg_ids


def change_channel_sub_status(telegram_id, status):
    with engine.begin() as db:
        stmt = update(User).values(channel_sub=status).filter(User.telegram_id == telegram_id)
        db.execute(stmt)
        db.commit()

    return True


def get_user_subs(telegram_id):
    with engine.begin() as db:
        stmt = select(Subscription.c_date, Subscription.e_date, VPNConfig.country, VPNConfig.peer_id).join(User, Subscription.user_id == User.id).join(VPNConfig, Subscription.vpn_id == VPNConfig.id).filter(User.telegram_id == telegram_id)
        #try:
        res = db.execute(stmt)
        data = res.fetchall()
        # except NoResultFound as ex:
        #     return 'У вас еще нет подписки'

    c_date = str()
    e_date = str()
    country = str()
    peer_id = str()
    text = ''''''

    for el in data:
        c_date = el[0]
        e_date = el[1]
        country = el[2]
        peer_id = el[3]

        if country == 'niderland':
            country = 'Нидерланды'
        elif country == 'vena':
            country = 'Вена'

        text += f"""
ID VPN конфигурации - {peer_id}
Страна VPN - {country}
Начало подписки - {c_date}
Конец подписки - {e_date}

"""
    if not text:
        return 'У вас еще нет подписки'
    return text


def get_user_country(peer_id):
    with engine.begin() as db:
        stmt = select(VPNConfig.country).filter(VPNConfig.peer_id == peer_id)
        res_country = db.execute(stmt)
        country = res_country.scalar()
    return country


def change_vpn_conf(peer_id, country):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # COUNTRY = get_user_country(peer_id)
    data = get_servers_data(country=country)
    SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD = str(), str(), str(), str()

    for el in data:
        SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD = el[0], el[1], el[2], el[3]

    ssh.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD, allow_agent=False, look_for_keys=False)
    # получаем id конкретного конфига

    stdin, stdout, stderr = ssh.exec_command('docker stop wireguard')
    stdin, stdout, stderr = ssh.exec_command(f'rm -r config/peer{peer_id}')
    stdin, stdout, stderr = ssh.exec_command('docker start wireguard')
    data_file = ''
    while True:
        stdin, stdout, stderr = ssh.exec_command(f'cat config/peer{peer_id}/peer{peer_id}.conf')
        data_file = stdout.read().decode('utf-8')
        if len(data_file) < 1:
            continue
        else:
            break
    with open(f'./src/configs/{country}/peer{peer_id}.conf', 'w') as f:
        f.write(data_file)

    config = configparser.ConfigParser()
    config.read(f'./src/configs/{country}/peer{peer_id}.conf')

    address = config['Interface']['Address']
    private_key = config['Interface']['PrivateKey']
    listen_port = config['Interface']['ListenPort']
    dns = config['Interface']['DNS']
    public_key = config['Peer']['PublicKey']
    preshared_key = config['Peer']['PresharedKey']
    endpoint = SSH_HOST + config['Peer']['Endpoint'] if config['Peer']['Endpoint'] == ':51820' else config['Peer']['Endpoint']
    allowed_ips = config['Peer']['AllowedIPs']


    delete_conf(peer_id=peer_id)
    status = add_new_conf(peer_id=peer_id, country=country, address=address, private_key=private_key,
                          listen_port=listen_port, dns=dns, public_key=public_key, preshared_key=preshared_key,
                          endpoint=endpoint, allowed_ips=allowed_ips)

    ssh.close()
    return True


def delete_sub_and_change_conf(peer_id):
    with engine.begin() as db:
        try:
            stmt_get_subs_id = select(VPNConfig.subscription_id).filter(VPNConfig.peer_id == peer_id)
            res_sub_id = db.execute(stmt_get_subs_id)
            subs_id = res_sub_id.fetchone()[0] #как fetchone()

            stmt_upd_conf = update(VPNConfig).values(subscription_id=None, sub_status='free').filter(VPNConfig.peer_id == peer_id)

            stmt_del_user_sub = delete(Subscription).filter(Subscription.id == subs_id)

            db.execute(stmt_upd_conf)
            db.execute(stmt_del_user_sub)
            db.commit()
        except TypeError as ex:
            return False
    return True


def change_sub_e_date(sub_id, date):
    with engine.begin() as db:
        new_date = datetime.datetime.strptime(date,'%Y-%m-%d')
        stmt = update(Subscription).values(e_date=new_date).filter(Subscription.id == sub_id)
        try:
            db.execute(stmt)
            db.commit()
        except TypeError as e:#InvalidRequestError as e:
            return False
    return True


def check_key_in_use_by_user(telegram_id):
    with engine.begin() as db:
        stmt = select(User.id).join(Key, User.key_id == Key.id).filter(User.telegram_id == telegram_id, Key.status == 'activated')
        res = db.execute(stmt)
        # try:
        status = res.scalar()
        if status is None:
            return False
        else:
            return True
        # except InvalidRequestError as e:
        #     if 'NoneType' in str(e):
        #         return False
        #     else:
        #         raise e


def get_user_vpn_country(telegram_id):
    with engine.begin() as db:
        stmt = select(VPNConfig.country).join(Subscription, Subscription.id == VPNConfig.subscription_id).join(User, User.id == Subscription.user_id).filter(User.telegram_id == telegram_id)
        res = db.execute(stmt)
        country = res.scalar()
    return country


def get_servers_data(country = ''):
    with engine.begin() as db:
        if country:
            stmt = select(Server.host, Server.port, Server.username, Server.password).filter(Server.country == country)
        else:
            stmt = select(Server.host, Server.port, Server.username, Server.password, Server.country)
        res = db.execute(stmt)
        data = res.fetchall()
    return data


def delete_conf(peer_id):
    with engine.begin() as db:
        stmt = delete(VPNConfig).filter(VPNConfig.peer_id == peer_id)
        db.execute(stmt)
        db.commit()
    return True


def add_new_conf(peer_id, country, address, private_key, listen_port, dns, public_key, preshared_key, endpoint, allowed_ips, sub_status = 'free'):
    with engine.begin() as db:
        try:
            stmt = insert(VPNConfig).values(peer_id=peer_id, country=country, address=address, private_key=private_key, listen_port=listen_port, dns=dns, public_key=public_key, preshared_key=preshared_key, endpoint=endpoint, allowed_ips=allowed_ips, sub_status=sub_status)
            db.execute(stmt)
            db.commit()
        except Exception as ex:
            return False
    return True


def check_key(key, telegram_id):
    '''[('Artem',)]'''

    check_key_e_date()

    with engine.begin() as db:
        stmt = select(Key.number)
        res = db.execute(stmt)
        keys = res.fetchall()

        for el in keys:
            if el[0] == key:
                try:
                    stmt_check_user_key_id = select(User.key_id).join(Key, Key.id == User.key_id).filter(User.telegram_id == telegram_id, User.key_id == Key.id, Key.number == key, Key.status == 'activated')
                    res_check_user_key_id = db.execute(stmt_check_user_key_id)
                    check_user_key_id = res_check_user_key_id.fetchone()[0]
                    return True
                except TypeError as ex:
                    stmt_key_id = select(Key.id).filter(Key.number == key, Key.status == 'free')
                    key_res = db.execute(stmt_key_id)
                    key_id = key_res.scalar()

                    stmt_update_key_id = update(User).values(key_id=key_id).filter(User.telegram_id == telegram_id)
                    stmt_update_key_status = update(Key).values(status='activated').filter(Key.id == key_id)
                    db.execute(stmt_update_key_id)
                    db.execute(stmt_update_key_status)
                    db.commit()
                    return True
        return False


def check_key_e_date():
    with engine.begin() as db:
        stmt = select(Key.e_date, Key.id).filter(Key.status == 'free')
        res = db.execute(stmt)
        e_dates = res.fetchall()

        #date: datetime.date = datetime.date.today()
        #date.isoformat()

        today = datetime.date.today()
        for e_date, key_id in e_dates:
            if today >= datetime.datetime.strptime(e_date.isoformat(), "%Y-%m-%d").date():
                stmt_update_key_status = update(Key).values(status='expired').filter(Key.id == key_id)
                db.execute(stmt_update_key_status)

        db.commit()
    return True


def create_user(telegram_id, status, balance):
    with engine.begin() as db:
        stmt_check_id = select(User.telegram_id).filter(User.telegram_id == telegram_id)
        stmt_check_status = select(User.status).filter(User.telegram_id == telegram_id)
        id = db.execute(stmt_check_id)
        try:
            exist = bool(id.scalar())
            statuses = db.execute(stmt_check_status)
            old_status = statuses.scalar()
            if int(old_status) == status:
                return 'User already exist'
            else:
                stmt_insert_status = update(User).values(status=status, balance=balance).filter(User.telegram_id == telegram_id)
                db.execute(stmt_insert_status)
                db.commit()
                return 'Change status'
        except Exception as ex:
            stmt_create_user = insert(User).values(telegram_id=telegram_id, status=status, balance=0, key_id=0, c_date=datetime.date.today())
            db.execute(stmt_create_user)
            db.commit()
            return 'Create new user'


def get_user_data(telegram_id):
    with engine.begin() as db:
        stmt = select(User).filter(User.telegram_id == telegram_id)
        res = db.execute(stmt)
        data = res.fetchall()

    status = str()
    data_reg = str()
    key_id = str()
    balance = str()

    for i in data:
        status = i[2]
        data_reg = i[5]
        key_id = i[4]
        balance = i[3]

    if status == 1:
        status = 'Гость'
    elif status == 2:
        status = 'Активный'
    elif status == 3:
        status = 'Забаненный'

    user_data_message = f'''
ID - {telegram_id}
Статус - {status}
Баланс - {balance}
Дата регистрации - {data_reg}
ID использованного ключа - {key_id}
'''
    return user_data_message


def get_admin_id(telegram_id):
    with engine.begin() as db:
        try:
            stmt = select(Admin.admin_id).filter(Admin.admin_id == telegram_id)
            res = db.execute(stmt)
            admin_id = res.fetchone()[0]
        except TypeError as ex:
            return False
    return admin_id


def get_balance(telegram_id):
    with engine.begin() as db:
        stmt = select(User.balance).filter(User.telegram_id == telegram_id)
        res = db.execute(stmt)
        balance = res.scalar()
    return balance


def change_balance(telegram_id, balance):
    with engine.begin() as db:
        stmt = update(User).values(balance=balance).filter(User.telegram_id == telegram_id)
        db.execute(stmt)
        db.commit()
    return True


def check_free_configs():
    with engine.begin() as db:
        stmt = select(VPNConfig.peer_id).filter(VPNConfig.sub_status == 'free')
        res = db.execute(stmt)
        status = res.fetchall()[0]

    if status:
        return True
    else:
        return 'Нет свободных конфигураций для VPN'


def create_vpn_configs(telegram_id, country):
    with engine.begin() as db:
        stmt = select(VPNConfig.address, VPNConfig.private_key,
                        VPNConfig.listen_port, VPNConfig.dns,
                        VPNConfig.public_key, VPNConfig.preshared_key,
                        VPNConfig.endpoint, VPNConfig.allowed_ips).filter(VPNConfig.sub_status == 'free', VPNConfig.country == country)
        res = db.execute(stmt)
        data = res.fetchone()

    address = data[0]
    private_key = data[1]
    listen_port = data[2]
    dns = data[3]
    public_key = data[4]
    preshared_key = data[5]
    endpoint = data[6]
    allowed_ips = data[7]

    filename = hashlib.sha256().hexdigest()

    with open(f'src/files/{filename}.txt', 'w') as file:
        file_data = f'''[Interface]
Address = {address}
PrivateKey = {private_key}
ListenPort = {listen_port}
DNS = {dns}
        
[Peer]
PublicKey = {public_key}
PresharedKey = {preshared_key}
Endpoint = {endpoint}
AllowedIPs = {allowed_ips}
'''
        file.write(file_data)

    change_vpn_config_sub_status(private_key=private_key, telegram_id=telegram_id)
    return filename


def delete_file(filename):
    file_path = f'./src/files/{filename}'
    if os.path.isfile(file_path):
        os.remove(file_path)
        return True
    else:
        return False


def change_vpn_config_sub_status(private_key, telegram_id):
    with engine.begin() as db:
        stmt_get_user_id = select(User.id).filter(User.telegram_id == telegram_id)
        res_user_id = db.execute(stmt_get_user_id)
        user_id = res_user_id.scalar()

        stmt_get_vpn_id = select(VPNConfig.id).filter(VPNConfig.private_key == private_key)
        res_vpn_id = db.execute(stmt_get_vpn_id)
        vpn_id = res_vpn_id.scalar()

        c_date = datetime.date.today()
        e_date = c_date + datetime.timedelta(days=30)

        stmt_insert_sub = insert(Subscription).values(user_id=user_id, vpn_id=vpn_id, c_date=c_date, e_date=e_date)
        db.execute(stmt_insert_sub)
        db.commit()

    with engine.begin() as database:
        stmt_subs_id = select(Subscription.id).join(User, Subscription.user_id == User.id).filter(User.telegram_id == telegram_id)
        res_subs_id = database.execute(stmt_subs_id)
        sub_id = res_subs_id.scalar()
        stmt = update(VPNConfig).values(sub_status='activated', subscription_id=sub_id).filter(VPNConfig.private_key == private_key)
        database.execute(stmt)
        database.commit()
    return True


def get_tg_ids():
    '''Получение id пользователя у которого стоит флаг авто подписки'''
    with engine.begin() as db:
        date = f"{datetime.date.today()}"# 00:00:00.000000"
        stmt_ids = select(User.telegram_id).join(Subscription, User.id == Subscription.user_id).filter(Subscription.e_date == date, User.auto_subscription == True)
        res_tg_ids = db.execute(stmt_ids)
        telegram_ids = res_tg_ids.fetchall()

    return telegram_ids


def get_user_id_without_auto_sub():
    post_data = datetime.date.today() + datetime.timedelta(days=1)
    with engine.begin() as db:
        stmt = select(User.telegram_id).join(Subscription, User.id == Subscription.user_id).filter(Subscription.e_date == post_data, User.auto_subscription == False)
        res = db.execute(stmt)
        telegram_ids = res.fetchall()

    return telegram_ids


def get_peer_id(telegram_id):
    with engine.begin() as db:
        stmt = select(VPNConfig.peer_id).join(Subscription, VPNConfig.subscription_id == Subscription.id).join(User, Subscription.user_id == User.id).filter(User.telegram_id == telegram_id)
        res_peer = db.execute(stmt)
        peer_id = res_peer.scalar()

    return peer_id


def update_conf(peer_id, private_key, preshared_key):
    with engine.begin() as db:
        stmt = update(VPNConfig).values(private_key=private_key, preshared_key = preshared_key, sub_status='free').filter(VPNConfig.peer_id == peer_id)
        db.execute(stmt)
        db.commit()
    return True


def save_new_keys(numbers, bot_code):
    with engine.begin() as db:
        for number in numbers:
            stmt = insert(Key).values(number=number, bot_code=bot_code, c_date = datetime.date.today(), e_date = datetime.date.today() + datetime.timedelta(days=90), status='free')
            db.execute(stmt)
        db.commit()
    return True


def add_new_admin(telegram_id):
    with engine.begin() as db:
        stmt = insert(Admin).values(admin_id=telegram_id)
        db.execute(stmt)
        db.commit()
    return True


def update_user_auto_sub(telegram_id, status: bool):
    with engine.begin() as db:
        stmt = update(User).values(auto_subscription=status).filter(User.telegram_id == telegram_id)
        db.execute(stmt)
        db.commit()
    return True