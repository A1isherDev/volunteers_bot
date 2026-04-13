from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    full_name = State()
    phone = State()
    age = State()
    region = State()


class SupportStates(StatesGroup):
    message = State()


class SuggestionStates(StatesGroup):
    text = State()


class FAQAdminStates(StatesGroup):
    add_question_uz = State()
    add_answer_uz = State()
    add_question_ru = State()
    add_answer_ru = State()
    edit_pick = State()
    edit_question = State()
    edit_answer = State()
    delete_pick = State()


class BroadcastStates(StatesGroup):
    content = State()
    buttons = State()
    confirm = State()


class SuperAdminStates(StatesGroup):
    search_query = State()
