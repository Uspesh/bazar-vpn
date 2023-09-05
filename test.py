import configparser

import paramiko

from src.db_work import add_new_conf

COUNTRY = 'vena'
SSH_HOST = '193.233.233.142'
SSH_PORT = 22
SSH_USERNAME = 'root'
SSH_PASSWORD = 'qPnKUlYljT36'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD)

i = 1
print(i)
while True:
    stdin, stdout, stderr = ssh.exec_command(f"cat config/peer{i}/peer{i}.conf")
    text = f'cat: config/peer{i}/peer{i}.conf: No such file or directory'

    if stdout.read().decode('utf-8') == text:
        break

    data_file = stdout.read().decode('utf-8')
    print(data_file)

    with open(f'./src/configs/{COUNTRY}/peer{i}.conf', 'w') as f:
        f.write(data_file)

    config = configparser.ConfigParser()
    config.read(f'./src/configs/{COUNTRY}/peer{i}.conf')
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

    status = add_new_conf(peer_id=peer_id, country=country, address=address, private_key=private_key, listen_port=listen_port, dns=dns, public_key=public_key, preshared_key=preshared_key, endpoint=endpoint, allowed_ips=allowed_ips)

    if not status:
        continue

    i += 1
