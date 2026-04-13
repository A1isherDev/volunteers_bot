import html
import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import get_settings
from app.database.models import User
from app.handlers.filters import IsRegistered
from app.handlers.labels import all_registered_menu_labels, label_set
from app.i18n import t
from app.keyboards.common import main_menu_kb
from app.services.ticket_service import TicketService
from app.states.forms import SupportStates
from app.utils.cooldown import UserCooldown
from app.utils.formatting import format_ticket_header
from app.utils.telegram_user import effective_telegram_user

logger = logging.getLogger(__name__)
router = Router(name="support")

_support_cooldown = UserCooldown()


@router.message(
    F.chat.type == "private",
    IsRegistered(),
    StateFilter(None),
    F.text.in_(label_set("menu.support")),
)
async def support_entry(message: Message, state: FSMContext, db_user: User):
    await state.set_state(SupportStates.message)
    await message.answer(t(db_user.language, "support.prompt"))


@router.message(F.chat.type == "private", IsRegistered(), StateFilter(SupportStates.message), F.text.startswith("/"))
async def support_ignore_commands(message: Message, db_user: User):
    await message.answer(t(db_user.language, "support.prompt"))


@router.message(F.chat.type == "private", IsRegistered(), StateFilter(SupportStates.message), F.text)
async def support_text(message: Message, state: FSMContext, db_user: User, session, bot, tg_user):
    settings = get_settings()
    lang = db_user.language
    body = (message.text or "").strip()
    if body in all_registered_menu_labels():
        await state.clear()
        await message.answer(t(lang, "common.menu_hint"), reply_markup=main_menu_kb(lang, db_user))
        return
    if _support_cooldown.is_throttled(tg_user.id, settings.creation_cooldown_sec):
        await message.answer(t(lang, "errors.cooldown"))
        return
    ts = TicketService(session)
    ticket = await ts.create(db_user, body)
    await session.flush()
    header = format_ticket_header(ticket.id, db_user, sender.username)
    full = header + html.escape(body)
    try:
        sent = await bot.send_message(settings.admin_group_id, full, parse_mode="HTML")
        await ts.set_admin_message_id(ticket.id, sent.message_id)
    except Exception as e:
        logger.exception("Forward ticket to admin group: %s", e)
        await message.answer(t(lang, "errors.generic"))
        return
    _support_cooldown.record(sender.id)
    await state.clear()
    await message.answer(t(lang, "support.sent"))


@router.message(F.chat.type == "private", IsRegistered(), StateFilter(SupportStates.message), F.photo)
async def support_photo(message: Message, state: FSMContext, db_user: User, session, bot, tg_user):
    settings = get_settings()
    lang = db_user.language
    sender = effective_telegram_user(message, tg_user)
    if sender is None:
        await message.answer(t(lang, "errors.generic"))
        return
    if _support_cooldown.is_throttled(sender.id, settings.creation_cooldown_sec):
        await message.answer(t(lang, "errors.cooldown"))
        return
    cap = message.caption or "[photo]"
    ts = TicketService(session)
    ticket = await ts.create(db_user, cap)
    await session.flush()
    header = format_ticket_header(ticket.id, db_user, sender.username)
    caption = header + html.escape(cap)
    try:
        sent = await bot.send_photo(
            settings.admin_group_id,
            message.photo[-1].file_id,
            caption=caption[:1024],
            parse_mode="HTML",
        )
        await ts.set_admin_message_id(ticket.id, sent.message_id)
    except Exception as e:
        logger.exception("Forward ticket photo: %s", e)
        await message.answer(t(lang, "errors.generic"))
        return
    _support_cooldown.record(sender.id)
    await state.clear()
    await message.answer(t(lang, "support.sent"))


@router.message(
    F.chat.type == "private",
    IsRegistered(),
    StateFilter(SupportStates.message),
    ~F.text,
    ~F.photo,
)
async def support_other_media(message: Message, state: FSMContext, db_user: User, session, bot, tg_user):
    settings = get_settings()
    lang = db_user.language
    sender = effective_telegram_user(message, tg_user)
    if sender is None:
        await message.answer(t(lang, "errors.generic"))
        return
    if _support_cooldown.is_throttled(sender.id, settings.creation_cooldown_sec):
        await message.answer(t(lang, "errors.cooldown"))
        return
    cap = (message.caption or "").strip() or f"[{message.content_type}]"
    ts = TicketService(session)
    ticket = await ts.create(db_user, cap)
    await session.flush()
    header = format_ticket_header(ticket.id, db_user, sender.username)
    full_caption = (header + html.escape(cap))[:1024]
    try:
        sent = await bot.copy_message(
            chat_id=settings.admin_group_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            caption=full_caption,
            parse_mode="HTML",
        )
        await ts.set_admin_message_id(ticket.id, sent.message_id)
    except Exception as e:
        logger.warning("copy_message ticket fallback to text: %s", e)
        try:
            sent = await bot.send_message(
                settings.admin_group_id,
                header + html.escape(cap),
                parse_mode="HTML",
            )
            await ts.set_admin_message_id(ticket.id, sent.message_id)
        except Exception as e2:
            logger.exception("Forward ticket (fallback): %s", e2)
            await message.answer(t(lang, "errors.generic"))
            return
    _support_cooldown.record(sender.id)
    await state.clear()
    await message.answer(t(lang, "support.sent"))
