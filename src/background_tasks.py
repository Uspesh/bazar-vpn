import asyncio
import base64
import os

from celery import Celery
from redis import asyncio as aio_redis
import datetime
from celery.schedules import crontab
import subprocess
import configparser
import paramiko

from .db_work import get_tg_ids, get_balance, change_balance, get_peer_id, update_conf, get_user_id_without_auto_sub, \
    get_servers_data, add_new_conf, get_user_vpn_country, delete_conf, delete_sub_and_change_conf, get_all_tg_ids, \
    change_channel_sub_status, change_total_earned, change_cancelled_subs_amount
from .main import bot
from .config import REDIS_HOST, REDIS_PORT, AMOUNT
from .keyboards import balance_keyboard, main_keyboard

redis = aio_redis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}/", encoding="utf-8", decode_responses=True)
celery = Celery('background_tasks', broker=f'redis://{REDIS_HOST}:{REDIS_PORT}/')


# ssh = paramiko.SSHClient()
# ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# ssh.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
# stdin, stdout, stderr = ssh.exec_command('ls -l')
# output = stdout.read().decode('utf-8')
# ssh.close()


@celery.task(name='celery.get_peers')
def get_peers():
    data = get_servers_data()
    SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD, COUNTRY = str(), str(), str(), str(), str()
    for el in data:
        SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD, COUNTRY = el[0], el[1], el[2], el[3], el[4]

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)

        i = 1
        while True:
            stdin, stdout, stderr = ssh.exec_command(f"cat config/peer{i}/peer{i}.conf")
            data_file = stdout.read().decode('utf-8')

            if not data_file:
                break

            with open(f'src/configs/{COUNTRY}/peer{i}.conf', 'w') as f:
                f.write(data_file)

            config = configparser.ConfigParser()
            config.read(f'src/configs/{COUNTRY}/peer{i}.conf')
            peer_id = i
            country = COUNTRY
            address = config['Interface']['Address']
            private_key = config['Interface']['PrivateKey']
            listen_port = config['Interface']['ListenPort']
            dns = config['Interface']['DNS']
            public_key = config['Peer']['PublicKey']
            preshared_key = config['Peer']['PresharedKey']
            endpoint = config['Peer']['Endpoint']
            allowed_ips = config['Peer']['AllowedIPs']

            status = add_new_conf(peer_id=peer_id, country=country, address=address, private_key=private_key,
                                  listen_port=listen_port, dns=dns, public_key=public_key, preshared_key=preshared_key,
                                  endpoint=endpoint, allowed_ips=allowed_ips)

            if not status:
                continue

            i += 1


@celery.task(name='celery.auto_subs')
def auto_subs():
    telegram_ids = get_tg_ids()

    if not telegram_ids:
        return None

    for tg_id in telegram_ids:
        balance = get_balance(telegram_id=tg_id[0])
        if balance >= int(AMOUNT):
            new_balance = balance - int(AMOUNT)
            change_balance(telegram_id=tg_id[0], balance=new_balance)
            change_total_earned(sum=int(AMOUNT))
            asyncio.run(bot.send_message(chat_id=tg_id[0], text=f'Продление подписки произошло успешно. Нынешний баланс - {new_balance}.', reply_markup=main_keyboard))
        else:
            change_cancelled_subs_amount(num=1)
            peer_id = get_peer_id(telegram_id=tg_id[0])
            delete_sub_and_change_conf(peer_id)

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            user_country = get_user_vpn_country(telegram_id=tg_id[0])
            data = get_servers_data(country=user_country)
            SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD, COUNTRY = str()
            for el in data:
                SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD, COUNTRY = el[0], el[1], el[2], el[3], el[4]

            ssh.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)
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
            with open(f'./src/configs/{COUNTRY}/peer{peer_id}.conf', 'w') as f:
                f.write(data_file)

            config = configparser.ConfigParser()
            config.read(f'./src/configs/{COUNTRY}/peer{peer_id}.conf')

            address = config['Interface']['Address']
            private_key = config['Interface']['PrivateKey']
            listen_port = config['Interface']['ListenPort']
            dns = config['Interface']['DNS']
            public_key = config['Peer']['PublicKey']
            preshared_key = config['Peer']['PresharedKey']
            endpoint = SSH_HOST + config['Peer']['Endpoint'] if config['Peer']['Endpoint'] == ':51820' else \
            config['Peer']['Endpoint']
            allowed_ips = config['Peer']['AllowedIPs']

            delete_conf(peer_id=peer_id)
            status = add_new_conf(peer_id=peer_id, country=COUNTRY, address=address, private_key=private_key,
                                  listen_port=listen_port, dns=dns, public_key=public_key, preshared_key=preshared_key,
                                  endpoint=endpoint, allowed_ips=allowed_ips)

            ssh.close()
            asyncio.run(bot.send_message(chat_id=tg_id[0], text=f'У Вас недостаточно денег для продления подписки на VPN.', reply_markup=balance_keyboard))


    #         stdin, stdout, stderr = ssh.exec_command("docker stop wireguard")
    #         stdin, stdout, stderr = ssh.exec_command(f"echo {private_key_b64} > config/peer{peer_id}/privatekey-peer{peer_id}")
    #         stdin, stdout, stderr = ssh.exec_command(f"cat config/peer{peer_id}/peer{peer_id}.conf")
    #         # subprocess.run([f'docker stop wireguard && echo {private_key_b64} > config/peer{peer_id}/privatekey-peer{peer_id}'])
    #         # output = subprocess.check_output([f'cat config/peer{peer_id}/peer{peer_id}.conf'])
    #
    #         file_data = stdout.read().decode('utf-8')
    #
    #         with open(f'src/configs/peer{peer_id}.conf', 'w') as f:
    #             f.write(file_data)
    #
    #         config = configparser.ConfigParser()
    #         config.read(f'src/configs/peer{peer_id}.conf')
    #
    #         # меняем значения PrivateKey и PublicKey
    #         config['Interface']['PrivateKey'] = private_key_b64
    #         config['Peer']['PresharedKey'] = preshared_key_b64
    #
    #         # сохраняем изменения в файл
    #         with open(f'vpn/src/configs/peer{peer_id}.conf', 'w') as configfile:
    #             config.write(configfile)
    #
    #         with open(f'vpn/src/configs/peer{peer_id}.conf', 'r') as file:
    #             text = file.read()
    #
    #         stdin, stdout, stderr = ssh.exec_command(f"echo \"{text}\" > config/peer{peer_id}/peer{peer_id}.conf")
    #         #subprocess.run([f'echo \"{text}\" > config/peer{peer_id}/peer{peer_id}.conf'])
    #
    #         # записываем измененные ключи в бд
    #         update_conf(peer_id=peer_id, private_key=private_key_b64, preshared_key=preshared_key_b64)
    #
    #         asyncio.run(bot.send_message(chat_id=tg_id[0], text=f'У Вас недостаточно денег для продления подписки на VPN.', reply_markup=balance_keyboard))
    #
    #         # stdin, stdout, stderr = ssh.exec_command("docker compose down")
    #         # stdin, stdout, stderr = ssh.exec_command("docker compose up --detach wireguard")
    #         stdin, stdout, stderr = ssh.exec_command("docker start wireguard")
    # #output = subprocess.check_output(["docker start wireguard"])


@celery.task(name='celery.check_subs_without_auto_sub')
def check_subs_without_auto_sub():
    tg_ids = get_user_id_without_auto_sub()

    if not tg_ids:
        return None

    for tg_id in tg_ids:
        asyncio.run(bot.send_message(chat_id=tg_id[0], text='Завтра у Вас закончится подписка на VPN.', reply_markup=balance_keyboard))


celery.conf.beat_schedule = {
    'check-auto-subs': {
        'task': 'celery.auto_subs',
        'schedule': crontab(hour=0, minute=0),
    },
    'check-subs-without-auto-sub': {
        'task': 'celery.check_subs_without_auto_sub',
        'schedule': crontab(hour=21, minute=0),
    },
    'get_peers_from_servers': {
        'task': 'celery.get_peers',
        'schedule': crontab(hour=1, minute=0),
    }
}

celery.conf.timezone = 'Europe/Moscow'
