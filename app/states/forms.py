from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    language = State()
    full_name = State()
    age = State()
    region = State()
    gender = State()
    bio = State()
    photo = State()


class AdminProjectStates(StatesGroup):
    title = State()
    description = State()


class SupportStates(StatesGroup):
    message = State()


class SuggestionStates(StatesGroup):
    text = State()


class RegionAdminStates(StatesGroup):
    add_name_uz = State()
    add_name_ru = State()
    edit_pick = State()
    edit_name_uz = State()
    edit_name_ru = State()
    delete_pick = State()


class FAQCategoryAdminStates(StatesGroup):
    add_name_uz = State()
    add_name_ru = State()
    edit_pick = State()
    edit_name_uz = State()
    edit_name_ru = State()
    delete_pick = State()


class FAQAdminStates(StatesGroup):
    add_question_uz = State()
    add_answer_uz = State()
    add_question_ru = State()
    add_answer_ru = State()
    edit_pick_category = State()
    edit_pick = State()
    edit_question = State()
    edit_answer = State()
    delete_pick_category = State()
    delete_pick = State()


class BroadcastStates(StatesGroup):
    content = State()
    buttons = State()
    confirm = State()


class SuperAdminStates(StatesGroup):
    search_query = State()
