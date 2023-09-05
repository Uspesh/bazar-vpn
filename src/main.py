import datetime
import re
import hashlib
import sentry_sdk
from aiogram import Dispatcher, Bot, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from yoomoney import Quickpay, Client
from aiogram.utils import executor
import configparser

from .keyboards import (main_keyboard, balance_keyboard, done_keyboard,
                        ok_keyboard, admin_keyboard, choose_keyboard, choose_country_keyboard, back_keyboard,
                        profile_keyboard, back_to_main_button)
from .config import BAZAR_VPN_BOT_KEY, YOOMONEY_TOKEN, AMOUNT, TG_CHANNEL, BOT_KEY, DEBUG, SENTRY, TG_CHANNEL_ID
from .db_work import (check_key, delete_sub_and_change_conf,
                     create_user, get_user_data, change_sub_e_date,
                     get_balance, change_balance, create_vpn_configs, delete_file,
                     get_admin_id, save_new_keys, add_new_admin, check_free_configs,
                     update_user_auto_sub, check_key_in_use_by_user, change_vpn_conf, get_user_subs,
                     change_channel_sub_status, count_all_users, count_new_users, change_total_earned,
                     get_total_earned, get_all_channel_subs, get_cancelled_subs_amount, generate_label)
from .states import (KeyState, ChannelState, PaymentState, AddKeysState, AddNewAdminState,
                     GetInfoAboutAutoSubState, ChooseCountryState, ChangeConfigState,
                     SetAutoSubState, ChangeBalanceState, ChangeEDateState, SetPaymentAmountState)

'''
    Импорты в докере работают только в таком формате .keyboard
'''


storage = MemoryStorage()

if DEBUG == 'True':
    bot = Bot(BOT_KEY)
elif DEBUG == 'False':
    bot = Bot(BAZAR_VPN_BOT_KEY)

    sentry_sdk.init(
      dsn=SENTRY,

      # Set traces_sample_rate to 1.0 to capture 100%
      # of transactions for performance monitoring.
      # We recommend adjusting this value in production.
      traces_sample_rate=1.0
    )

dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['help'])
async def help_func(message: types.Message):
    await message.answer(text='Привет, если у тебя что то не работает или просто есть вопросы можешь задать их - @bazarsup')


@dp.message_handler(commands=['start'])
async def init_func(message: types.Message):
    status = check_key_in_use_by_user(message.from_user.id)
    if status:
        await back_to_main_page(message)
    else:
        create_user(telegram_id=message.from_user.id, status=1, balance=0)
        await message.answer(text='Введите ключ:')
        await KeyState.key.set()


@dp.message_handler(state=KeyState.key)
async def check_key_num(message: types.Message, state: FSMContext):
    if check_key(key=message.text, telegram_id=message.from_user.id):
        await state.finish()
        user_channel_status = await bot.get_chat_member(chat_id=TG_CHANNEL_ID, user_id=message.from_user.id)
        # message = await bot.send_message(chat_id='@bazar_vpn_channel', text='Hello, channel!')
        # print(message)
        user_channel_status = re.findall(r"\w*", str(user_channel_status))
        if user_channel_status[user_channel_status.index('status') + 5] != 'left':
            #print(user_channel_status[user_channel_status.index('status') + 5])
            create_user(telegram_id=message.from_user.id, status=2, balance=100)
            change_channel_sub_status(telegram_id=message.from_user.id, status=True)
            await message.answer(text='Добро пожаловать, навигация осуществляется кнопками ниже.', reply_markup=main_keyboard)
        else:
            await ChannelState.status.set()
            await message.answer(text=f'Перед продолжением подпишитесь пожалуйста на канал, где будут все актульные новости связанные с сервисом - {TG_CHANNEL}', reply_markup=done_keyboard)
    else:
        await message.answer(text='Вы ввели что то не так. Попробуйте ввести ключ еще раз. Удостовертесь что у вас есть ключ. Если у вас нет ключа попросите его у @bazarsup')


@dp.message_handler(text='Готово✅', state=ChannelState.status)
async def check_sub_to_channel(message: types.Message, state: FSMContext):
    user_channel_status = await bot.get_chat_member(chat_id=TG_CHANNEL_ID, user_id=message.from_user.id) #-1001675087517 id тестового канала
    user_channel_status = re.findall(r"\w*", str(user_channel_status))
    if user_channel_status[user_channel_status.index('status') + 5] != 'left' and message.text == 'Готово✅':
        await state.finish()
        change_channel_sub_status(telegram_id=message.from_user.id, status=True)
        create_user(telegram_id=message.from_user.id, status=2, balance=100)
        await message.answer(text='Добро пожаловать, навигация осуществляется кнопками ниже.',
                             reply_markup=main_keyboard)
    else:
        change_channel_sub_status(telegram_id=message.from_user.id, status=False)
        await message.answer(text=f'Вы еще не подписались либо что то пошло не так, попробуйте еще раз. Ссылка на канал - {TG_CHANNEL}', reply_markup=done_keyboard)


@dp.message_handler(text=['Назад', 'Назад в главную'])
async def back_to_main_page(message: types.Message):
    await message.answer(text='Вы на странице профиля.', reply_markup=main_keyboard)


@dp.message_handler(text='Конфигурации VPN')
async def get_info_about_user(message: types.Message):
    user_channel_status = await bot.get_chat_member(chat_id=TG_CHANNEL_ID,
                                                    user_id=message.from_user.id)  # -1001675087517 id тестового канала
    user_channel_status = re.findall(r"\w*", str(user_channel_status))
    if user_channel_status[user_channel_status.index('status') + 5] != 'left':
        change_channel_sub_status(telegram_id=message.from_user.id, status=True)
        user_balance = get_balance(telegram_id=message.from_user.id)
        if user_balance < int(AMOUNT):
            await message.answer(
                text='У Вас недостаточно средств для оплаты VPN. Пожалуйста нажмите кнопку Оплата для пополнения счета.',
                reply_markup=balance_keyboard)
        else:
            #filename = create_vpn_configs(telegram_id=message.from_user.id)
            status = check_free_configs()
            if status == 'Нет свободных конфигураций для VPN':
                await message.answer(
                    text=f'{status}. Попробуйте позже или обратитесь к @bazarsup для получения конфигураций - /help',
                    reply_markup=main_keyboard)
            else:
                await GetInfoAboutAutoSubState.status.set()
                await message.answer(text=f'Стоимость подписки {AMOUNT}.\nВы хотите автоматическое списание средств за подписку? Ответьте используя кнопки ниже. Спасибо.', reply_markup=choose_keyboard)
    else:
        change_channel_sub_status(telegram_id=message.from_user.id, status=False)
        await message.answer(text=f'Вы не подписаны на канал {TG_CHANNEL}. Для продолжения подпишитесь и после подписки заново нажмите на нужную кнопку. Спасибо.', reply_markup=main_keyboard)


@dp.message_handler(state=GetInfoAboutAutoSubState.status)
async def set_auto_sub(message: types.Message, state: FSMContext):
    await state.finish()
    status = bool()
    if message.text == 'Да':
        status = True
    elif message.text == 'Нет':
        status = False
    elif message.text == 'Назад':
        await state.finish()
        await back_to_main_page(message)

    result = update_user_auto_sub(telegram_id=message.from_user.id, status=status)
    if result:
        await choose_country(message)


@dp.message_handler(state=SetAutoSubState.set_sub)
async def choose_country(message: types.Message):
    await ChooseCountryState.status.set()
    await message.answer(text='Выберите страну', reply_markup=choose_country_keyboard)


@dp.message_handler(state=ChooseCountryState.status)
async def get_country_from_user(message: types.Message, state: FSMContext):
    if message.text == 'Назад':
        await state.finish()
        await back_to_main_page(message)
    else:
        await state.finish()
        global country
        country = message.text
        if country == 'Нидерланды':
            country = 'niderland'
        elif country == 'Вена':
            country = 'vena'

        user_balance = get_balance(telegram_id=message.from_user.id)
        filename = create_vpn_configs(telegram_id=message.from_user.id, country=country)

        await bot.send_document(chat_id=message.from_user.id, document=open(f'src/files/{filename}.txt', 'rb'))
        delete_file(filename=f'{filename}.txt')
        user_balance = user_balance - int(AMOUNT)
        change_balance(telegram_id=message.from_user.id, balance=user_balance)
        change_total_earned(sum = int(AMOUNT))
        await message.answer(text=f'Оплата за подписку будет списываться с вашего счета ежемесячно в размере {AMOUNT} рублей.',
                reply_markup=main_keyboard)
    #await state.finish()


@dp.message_handler(text='Профиль')
async def profile(message: types.Message):
    user_channel_status = await bot.get_chat_member(chat_id=TG_CHANNEL_ID,
                                                    user_id=message.from_user.id)  # -1001675087517 id тестового канала
    user_channel_status = re.findall(r"\w*", str(user_channel_status))
    if user_channel_status[user_channel_status.index('status') + 5] != 'left':
        change_channel_sub_status(telegram_id=message.from_user.id, status=True)
        data = get_user_data(message.from_user.id)
        await message.answer(text=data, reply_markup=profile_keyboard)
    else:
        change_channel_sub_status(telegram_id=message.from_user.id, status=False)
        await message.answer(text=f'Вы не подписаны на канал {TG_CHANNEL}. Для продолжения подпишитесь и после подписки заново нажмите на нужную кнопку. Спасибо.', reply_markup=main_keyboard)


@dp.message_handler(text='Мои подписки')
async def my_subs(message: types.Message):
    text = get_user_subs(message.from_user.id)
    await message.answer(text=text, reply_markup=main_keyboard)


@dp.message_handler(text='Оплата')
async def set_payment_amount(message: types.Message):
    await SetPaymentAmountState.status.set()
    await message.answer(text='Напишите сумму, на которую вы бы хотели пополнить баланс. Используйте формат 1000, 2000, 150 без приставки рублей, руб., и тп.', reply_markup=back_to_main_button)


@dp.message_handler(state=SetPaymentAmountState.status)
async def payment(message: types.Message, state: FSMContext):
    await state.finish()
    #amount = int()
    #try:
    global amount
    amount = int(message.text)
    #except

    global key_label
    key_label = generate_label()

    q_pay = Quickpay(
        receiver='4100118245836855',#номер счета
        quickpay_form='shop',
        targets='Пополнение баланса',
        paymentType='SB',
        sum=amount,
        label=key_label
    )
    await PaymentState.check.set()
    await message.answer(
        text=f'1-я ссылка - {q_pay.base_url}\n\n2-я ссылка - {q_pay.redirected_url}\n\nВы можете использовать любую ссылку, но 2-я имеет жизненный цикл.',
    reply_markup=ok_keyboard)


@dp.message_handler(state=PaymentState.check)
async def check_payment(message: types.Message, state: FSMContext):
    if message.text == 'Назад':
        await state.finish()
        await back_to_main_page(message)
    else:
        client = Client(YOOMONEY_TOKEN)
        history = client.operation_history(label=key_label)
        result = False

        for operation in history.operations:
            if operation.status == 'success':
                result = True
                change_balance(telegram_id=message.from_user.id, balance=amount)
                await state.finish()
                await message.answer(text='Оплата прошла успешно.', reply_markup=main_keyboard)
        if not result:
            await message.answer(text='Вы не оплатили, либо оплата еще не прошла. Рекомендуем немного подождать и нажать кнопку "Оплатил" заново.')


@dp.message_handler(text='Баланс')
async def balance(message: types.Message):
    user_channel_status = await bot.get_chat_member(chat_id=TG_CHANNEL_ID,
                                                    user_id=message.from_user.id)  # -1001675087517 id тестового канала
    user_channel_status = re.findall(r"\w*", str(user_channel_status))
    if user_channel_status[user_channel_status.index('status') + 5] != 'left':
        change_channel_sub_status(telegram_id=message.from_user.id, status=True)
        balance = get_balance(message.from_user.id)
        await message.answer(text=f'Ваш баланс - {balance}', reply_markup=balance_keyboard)
    else:
        change_channel_sub_status(telegram_id=message.from_user.id, status=False)
        await message.answer(text=f'Вы не подписаны на канал {TG_CHANNEL}. Для продолжения подпишитесь и после подписки заново нажмите на нужную кнопку. Спасибо.', reply_markup=main_keyboard)


@dp.message_handler(text=['Админ панель', 'Назад в админ панель'])
async def admin_panel(message: types.Message):
    admin_id = get_admin_id(message.from_user.id)
    if admin_id:
        await message.answer(text='Вы в админ панеле.', reply_markup=admin_keyboard)
    else:
        await message.answer(text='У Вас нет достаточного уровня доступа.', reply_markup=main_keyboard)


@dp.message_handler(text='Добавить ключи')
async def add_keys(message: types.Message):
    text = """
Введите ключи в формате:

Код партнера - код
значение ключа
значение ключа

P.S. Если кода нет, то это свободные ключи, без партнеров.
"""
    await AddKeysState.status.set()
    await message.answer(text=text, reply_markup=back_keyboard)


@dp.message_handler(state=AddKeysState.status)
async def save_keys(message: types.Message, state: FSMContext):
    if message.text == 'Назад в админ панель':
        await state.finish()
        await admin_panel(message)
    else:
        try:
            text = list(message.text.replace(' ', '').split('\n'))
            bot_code = text[0].split('-')[1]
            nums = text[1:]
            save_new_keys(bot_code=bot_code, numbers=nums)
            await state.finish()
            await message.answer(text='Вы успешно сохранили ключи в базу данных.', reply_markup=admin_keyboard)
        except IndexError as ex:
            await state.finish()
            await message.answer(text='Вы ввели Код партнера неправильно, попробуйте еще раз.', reply_markup=admin_keyboard)


@dp.message_handler(text='Изменить баланс')
async def change_user_balance(message: types.Message):
    await ChangeBalanceState.status.set()
    await message.answer(text='Введите телеграм id пользователя которому нужно сменить баланс.\n\nP.S. получить id можно в этом боте, пусть нужный пользователь перейдет в этот бот и даст вам свой id - https://t.me/userinfobot', reply_markup=back_keyboard)


@dp.message_handler(state=ChangeBalanceState.status)
async def change_balance_by_id(message: types.Message, state: FSMContext):
    if message.text == 'Назад в админ панель':
        await state.finish()
        await admin_panel(message)
    else:
        global telegram_id_for_change_balance
        telegram_id_for_change_balance = message.text
        await message.answer(text='Введите сумму нового баланса в формате - 1000 или 10000. Без приставки рублей или другой валюты.')
        await ChangeBalanceState.result.set()


@dp.message_handler(state=ChangeBalanceState.result)
async def change_balance_finish(message: types.Message, state: FSMContext):
        status = change_balance(telegram_id=telegram_id_for_change_balance, balance=message.text)
        if status:
            await state.finish()
            await message.answer(text='Вы успешно сменили баланс', reply_markup=admin_keyboard)
        else:
            await state.finish()
            await message.answer(text='Что то пошло не так, возможно вы ввели id юзера, который еще не зарегестрирован в боте. Попробуйте снова.', reply_markup=admin_keyboard)


@dp.message_handler(text='Статистика')
async def stats(message: types.Message):
    today_date = datetime.date.today()
    prev_month = today_date - datetime.timedelta(days=30)
    prev_prev_month = today_date - datetime.timedelta(days=60)
    prev_prev_prev_month = today_date - datetime.timedelta(days=90)
    text = f'''
Всего пользователей - {count_all_users()}

Новых пользователей:
- за 1 месяц - {count_new_users(prev_month)}
- за 2 месяца - {count_new_users(prev_prev_month)}
- за 3 месяца - {count_new_users(prev_prev_prev_month)}

Всего заработано - {get_total_earned()}
Всего отменных подписок по неуплате - {get_cancelled_subs_amount()}
Всего подписано на канал - {get_all_channel_subs()}
'''
    await message.answer(text=text, reply_markup=admin_keyboard)


@dp.message_handler(text='База данных')
async def database(message: types.Message):
    await bot.send_document(chat_id=message.from_user.id, document=open('./db.db', 'rb'))


@dp.message_handler(text='Добавить админа')
async def add_admin(message: types.Message):
    await AddNewAdminState.admin.set()
    await message.answer(text='Напишите telegram id нового админа. Чтобы узнать id воспользуйтесь ботом - https://t.me/userinfobot', reply_markup=admin_keyboard)


@dp.message_handler(state=AddNewAdminState.admin)
async def save_new_admin(message: types.Message, state: FSMContext):
    if message.text == 'Назад в главную':
        await state.finish()
        await back_to_main_page(message)
    elif message.text == 'Назад в админ панель':
        await state.finish()
        await admin_panel(message)
    else:
        await state.finish()
        add_new_admin(telegram_id=message.text)
        await message.answer(text='Вы успешно добавили нового админа.', reply_markup=admin_keyboard)


@dp.message_handler(text='Продлить срок подписки')
async def change_e_date(message: types.Message):
    await ChangeEDateState.status.set()
    await message.answer(text='Введите id подписки', reply_markup=back_keyboard)


@dp.message_handler(state=ChangeEDateState.status)
async def change_e_date_by_id(message: types.Message, state: FSMContext):
    if message.text == 'Назад в админ панель':
        await state.finish()
        await admin_panel(message)
    else:
        await state.finish()
        global subs_id
        subs_id = message.text
        await ChangeEDateState.result.set()
        await message.answer(text='Укажите новый срок действия в формате - 2023-08-05(г-м-д)', reply_markup=back_keyboard)


@dp.message_handler(state=ChangeEDateState.result)
async def change_e_date_finish(message: types.Message, state: FSMContext):
    if message.text == 'Назад в админ панель':
        await state.finish()
        await admin_panel(message)
    else:
        date = message.text
        await state.finish()
        if change_sub_e_date(sub_id=subs_id, date=date):
            await message.answer(text=f'Вы успешно сменили дату подписки N{subs_id}', reply_markup=admin_keyboard)
        else:
            await message.answer(text='Что то пошло не так, возможно вы не правильно ввели id подписки или дату', reply_markup=admin_keyboard)


@dp.message_handler(text='Изменить конфигурацию')
async def change_config(message: types.Message):
    await ChangeConfigState.status.set()
    await message.answer(text='Введите id конфигурации которую нужно удалить(peer_id) и страну конфигурации. Пример 1 Нидерланды', reply_markup=back_keyboard)


@dp.message_handler(state=ChangeConfigState.status)
async def del_config(message: types.Message, state: FSMContext):
    if message.text == 'Назад в админ панель':
        await state.finish()
        await admin_panel(message)
    else:
        text = message.text.split(' ')
        peer_id = text[0]
        country = ''
        if text[1] == 'Вена':
            country = 'vena'
        elif text[1] == 'Нидерланды':
            country = 'niderland'

        await state.finish()
        if delete_sub_and_change_conf(peer_id=peer_id) and change_vpn_conf(peer_id, country):
            await message.answer(text='Вы успешно изменили конфигурацию и удалили подписку выбранного пользователя из бд.', reply_markup=admin_keyboard)


@dp.message_handler(text='FAQ')
async def faq(message: types.Message):
    pass


@dp.message_handler(text='Правила')
async def rules(message: types.Message):
    pass


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
