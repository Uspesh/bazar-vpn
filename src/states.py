from aiogram.dispatcher.filters.state import State, StatesGroup


class KeyState(StatesGroup):
    key = State()


class ChannelState(StatesGroup):
    status = State()


class PaymentState(StatesGroup):
    check = State()


class AddKeysState(StatesGroup):
    status = State()


class AddNewAdminState(StatesGroup):
    admin = State()


class GetInfoAboutAutoSubState(StatesGroup):
    status = State()


class SetAutoSubState(StatesGroup):
    set_sub = State()


class ChooseCountryState(StatesGroup):
    status = State()


class ReturnConfigState(StatesGroup):
    status = State()


class ChangeBalanceState(StatesGroup):
    status = State()
    result = State()


class ChangeEDateState(StatesGroup):
    status = State()
    result = State()


class ChangeConfigState(StatesGroup):
    status = State()


class SetPaymentAmountState(StatesGroup):
    status = State()
