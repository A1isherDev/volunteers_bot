import logging
import re

from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database.models import User
from app.handlers.filters import IsRegistered
from app.i18n import other_lang, t
from app.keyboards.common import (
    main_menu_kb,
    registration_contact_kb,
    registration_skip_age_kb,
    remove_kb,
)
from app.services.user_service import UserService
from app.states.forms import RegistrationStates
from app.utils.telegram_user import effective_telegram_user

logger = logging.getLogger(__name__)
router = Router(name="registration")


def _is_skip(text: str | None, lang: str) -> bool:
    if not text:
        return False
    return text.strip() in (t(lang, "common.skip"), t(other_lang(lang), "common.skip"))


@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: Message, state: FSMContext, db_user: User | None, session):
    await state.clear()
    if db_user:
        lang = db_user.language
        await message.answer(t(lang, "start.already"), reply_markup=main_menu_kb(lang, db_user))
        return
    lang = "uz"
    await state.update_data(lang=lang)
    await state.set_state(RegistrationStates.full_name)
    await message.answer(t(lang, "start.welcome"))


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
    await message.answer(t(lang, "start.ask_phone"), reply_markup=registration_contact_kb(lang))


@router.message(StateFilter(RegistrationStates.phone), F.chat.type == "private", F.contact)
async def reg_contact(message: Message, state: FSMContext, session):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    contact = message.contact
    fu = message.from_user
    if not contact or not fu or contact.user_id != fu.id:
        await message.answer(t(lang, "start.ask_phone"), reply_markup=registration_contact_kb(lang))
        return
    phone = contact.phone_number or ""
    await state.update_data(phone=phone)
    await state.set_state(RegistrationStates.age)
    await message.answer(t(lang, "start.ask_age"), reply_markup=registration_skip_age_kb(lang))


@router.message(StateFilter(RegistrationStates.age), F.chat.type == "private", F.text)
async def reg_age(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    text = message.text or ""
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
    await message.answer(t(lang, "start.ask_region"), reply_markup=remove_kb())


@router.message(StateFilter(RegistrationStates.region), F.chat.type == "private", F.text)
async def reg_region(message: Message, state: FSMContext, session, tg_user):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    region = (message.text or "").strip()
    if len(region) < 2:
        await message.answer(t(lang, "start.ask_region"))
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
        region=region,
        age=data.get("age"),
        language=lang,
        username=actor.username,
    )
    await session.flush()
    await state.clear()
    logger.info("Registered user telegram_id=%s", user.telegram_id)
    await message.answer(t(lang, "start.done"), reply_markup=main_menu_kb(lang, user))
