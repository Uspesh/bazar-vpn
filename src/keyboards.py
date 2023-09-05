from aiogram import types

main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton('Конфигурации VPN'),
    types.KeyboardButton('Профиль'),
    types.KeyboardButton('Баланс'),
    types.KeyboardButton('FAQ'),
    types.KeyboardButton('Правила'),
    types.KeyboardButton('Админ панель')
)

profile_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton('Мои подписки'),
    types.KeyboardButton('Назад'),
)

done_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton('Готово✅')
)

balance_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton('Оплата'),
    types.KeyboardButton('Назад')
)

admin_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton('Добавить ключи'),
    types.KeyboardButton('Изменить баланс'),
    types.KeyboardButton('База данных'),
    types.KeyboardButton('Статистика'),
    types.KeyboardButton('Добавить админа'),
    types.KeyboardButton('Продлить срок подписки'),
    types.KeyboardButton('Изменить конфигурацию'),
    types.KeyboardButton('Назад в главную'),
)

back_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton('Назад в админ панель')
)

ok_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton('Оплатил'),
    types.KeyboardButton('Назад')
)

choose_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton('Да'),
    types.KeyboardButton('Нет'),
    types.KeyboardButton('Назад')
)

choose_country_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton('Нидерланды'),
    types.KeyboardButton('Вена'),
    types.KeyboardButton('Назад')
)

back_to_main_button = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton('Назад в главную')
)