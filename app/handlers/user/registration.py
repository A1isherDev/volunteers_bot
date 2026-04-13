import logging
import re

from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database.models import User
from app.i18n import other_lang, t
from app.keyboards.common import (
    LANG_BTN_RU,
    LANG_BTN_UZ,
    LANG_PICK_LABELS,
    language_pick_kb,
    main_menu_kb,
    registration_phone_kb,
    registration_skip_age_kb,
    remove_kb,
)
from app.services.dynamic_keyboard import get_dynamic_keyboard
from app.services.region_service import RegionService
from app.services.user_service import UserService
from app.states.forms import RegistrationStates
from app.utils.phone import is_valid_phone, store_phone
from app.utils.telegram_user import effective_telegram_user

logger = logging.getLogger(__name__)
router = Router(name="registration")


def _is_skip(text: str | None, lang: str) -> bool:
    if not text:
        return False
    return text.strip() in (t(lang, "common.skip"), t(other_lang(lang), "common.skip"))


@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: Message, state: FSMContext, db_user: User | None):
    await state.clear()
    if db_user:
        lang = db_user.language
        await message.answer(t(lang, "start.welcome_back"), reply_markup=main_menu_kb(lang, db_user))
        return
    await state.set_state(RegistrationStates.language)
    await message.answer(t("uz", "start.pick_language"), reply_markup=language_pick_kb())


@router.message(StateFilter(RegistrationStates.language), F.chat.type == "private", F.text)
async def reg_language(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == LANG_BTN_UZ:
        lang = "uz"
    elif text == LANG_BTN_RU:
        lang = "ru"
    else:
        await message.answer(t("uz", "start.pick_language_retry"), reply_markup=language_pick_kb())
        return
    await state.update_data(lang=lang)
    await state.set_state(RegistrationStates.full_name)
    await message.answer(t(lang, "start.welcome"), reply_markup=remove_kb())


@router.message(StateFilter(RegistrationStates.full_name), F.chat.type == "private", F.text)
async def reg_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer(t(lang, "start.welcome"))
        return
    await state.update_data(full_name=name)
    await state.set_state(RegistrationStates.phone)
    await message.answer(t(lang, "start.ask_phone"), reply_markup=registration_phone_kb(lang))


@router.message(StateFilter(RegistrationStates.phone), F.chat.type == "private", F.contact)
async def reg_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    contact = message.contact
    fu = message.from_user
    if not contact or not fu or contact.user_id != fu.id:
        await message.answer(t(lang, "start.ask_phone"), reply_markup=registration_phone_kb(lang))
        return
    phone = store_phone(contact.phone_number or "")
    if not is_valid_phone(phone):
        await message.answer(t(lang, "start.phone_invalid"), reply_markup=registration_phone_kb(lang))
        return
    await state.update_data(phone=phone)
    await state.set_state(RegistrationStates.age)
    await message.answer(t(lang, "start.ask_age"), reply_markup=registration_skip_age_kb(lang))


@router.message(StateFilter(RegistrationStates.phone), F.chat.type == "private", F.text)
async def reg_phone_manual(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    raw = store_phone(message.text or "")
    if not is_valid_phone(raw):
        await message.answer(t(lang, "start.phone_invalid"), reply_markup=registration_phone_kb(lang))
        return
    await state.update_data(phone=raw)
    await state.set_state(RegistrationStates.age)
    await message.answer(t(lang, "start.ask_age"), reply_markup=registration_skip_age_kb(lang))


@router.message(StateFilter(RegistrationStates.age), F.chat.type == "private", F.text)
async def reg_age(message: Message, state: FSMContext, session):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    text = message.text or ""
    if text.strip() in LANG_PICK_LABELS:
        await message.answer(t(lang, "start.ask_age"), reply_markup=registration_skip_age_kb(lang))
        return
    if _is_skip(text, lang):
        await state.update_data(age=None)
    else:
        if not re.fullmatch(r"\d{1,3}", text.strip()):
            await message.answer(t(lang, "start.ask_age"), reply_markup=registration_skip_age_kb(lang))
            return
        age = int(text.strip())
        if age < 5 or age > 120:
            await message.answer(t(lang, "start.ask_age"), reply_markup=registration_skip_age_kb(lang))
            return
        await state.update_data(age=age)
    await state.set_state(RegistrationStates.region)
    kb = await get_dynamic_keyboard(session, "regions", lang)
    if kb is None:
        await message.answer(t(lang, "regions.none_contact_admin"), reply_markup=remove_kb())
    else:
        await message.answer(t(lang, "start.pick_region"), reply_markup=kb)


@router.message(StateFilter(RegistrationStates.region), F.chat.type == "private", F.text)
async def reg_region(message: Message, state: FSMContext, session, tg_user):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    kb = await get_dynamic_keyboard(session, "regions", lang)
    if kb is None:
        await message.answer(t(lang, "regions.none_contact_admin"))
        return
    if (message.text or "").strip() in LANG_PICK_LABELS:
        await message.answer(t(lang, "start.pick_region"), reply_markup=kb)
        return
    label = (message.text or "").strip()
    rsvc = RegionService(session)
    region = await rsvc.resolve_by_label(label, lang)
    if not region:
        await message.answer(t(lang, "regions.pick_valid"), reply_markup=kb)
        return
    actor = effective_telegram_user(message, tg_user)
    if actor is None:
        logger.warning("reg_region: missing from_user chat_id=%s", message.chat.id if message.chat else None)
        await state.clear()
        await message.answer(t(lang, "errors.generic"))
        return
    svc = UserService(session)
    user = await svc.create_user(
        telegram_id=actor.id,
        full_name=data["full_name"],
        phone=data["phone"],
        region_id=region.id,
        age=data.get("age"),
        language=lang,
        username=actor.username,
    )
    await session.flush()
    await state.clear()
    logger.info("Registered user telegram_id=%s", user.telegram_id)
    await message.answer(t(lang, "start.done"), reply_markup=main_menu_kb(lang, user))
