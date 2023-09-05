import os
from dotenv import load_dotenv

load_dotenv()

BOT_KEY = os.environ.get('BOT_KEY')
DB_NAME = os.environ.get('DB_NAME')
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')

BAZAR_VPN_BOT_KEY = os.environ.get('BAZAR_VPN_BOT_KEY')
YOOMONEY_TOKEN = os.environ.get('YOOMONEY_TOKEN')

AMOUNT = os.environ.get('AMOUNT')

TG_CHANNEL = os.environ.get('TG_CHANNEL')
TG_CHANNEL_ID = os.environ.get('TG_CHANNEL_ID')
SENTRY = os.environ.get('SENTRY')

DEBUG = os.environ.get('DEBUG')