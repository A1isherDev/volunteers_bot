import logging

from aiogram import F, Router
from aiogram.filters import Command

from app.database.models import User
from app.handlers.filters import IsAdmin
from app.i18n import t
from app.services.group_service import GroupService

logger = logging.getLogger(__name__)
router = Router(name="group_commands")


def _chat_lang(message) -> str:
    lc = (message.from_user.language_code or "uz").lower()
    return "ru" if lc.startswith("ru") else "uz"


@router.message(Command("help"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_help(message):
    await message.reply(t(_chat_lang(message), "group.help"))


@router.message(Command("volunteer_info"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_volunteer_info(message, session):
    lang = _chat_lang(message)
    g = await GroupService(session).get_by_chat_id(message.chat.id)
    if not g:
        await message.reply(t(lang, "group.volunteer_none"))
        return
    await message.reply(
        t(lang, "group.volunteer", name=g.project_name, desc=g.description or "—"),
    )


@router.message(Command("link_group"), F.chat.type.in_({"group", "supergroup"}), IsAdmin())
async def cmd_link_group(message, db_user: User | None, session):
    lang = db_user.language if db_user else _chat_lang(message)
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(t(lang, "group.link_usage"))
        return
    rest = parts[1].strip()
    name, sep, desc = rest.partition("\n")
    name = name.strip()
    desc = desc.strip() or None
    if len(name) < 2:
        await message.reply(t(lang, "group.link_usage"))
        return
    await GroupService(session).upsert_link(message.chat.id, name, desc)
    await message.reply(t(lang, "group.link_ok", name=name))
    logger.info("Group %s linked to project %s", message.chat.id, name)
