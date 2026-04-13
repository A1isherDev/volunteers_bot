import logging
import re

from aiogram import Router
from aiogram.types import Message

from app.database.models import TicketStatus
from app.handlers.filters import InAdminGroup
from app.services.ticket_service import TicketService

logger = logging.getLogger(__name__)
router = Router(name="admin_inbox")

CLOSE_RE = re.compile(r"^/close_(\d+)\s*$")


def _reply_chain_message_ids(msg: Message | None) -> list[int]:
    out: list[int] = []
    cur: Message | None = msg
    depth = 0
    while cur is not None and depth < 50:
        out.append(cur.message_id)
        cur = cur.reply_to_message
        depth += 1
    return out


@router.message(InAdminGroup())
async def admin_inbox(message: Message, session):
    text = (message.text or "").strip()
    if text:
        m_close = CLOSE_RE.match(text)
        if m_close:
            ticket_id = int(m_close.group(1))
            ts = TicketService(session)
            ticket = await ts.get(ticket_id)
            if not ticket:
                await message.reply("Ticket not found")
                return
            await ts.close(ticket_id)
            await message.reply(f"Ticket #{ticket_id} closed.")
            return

    if not message.reply_to_message:
        return
    if not message.from_user or message.from_user.is_bot:
        return

    chain_ids = _reply_chain_message_ids(message.reply_to_message)
    ts = TicketService(session)
    ticket = await ts.get_by_admin_message_chain(chain_ids)
    if not ticket:
        return
    if ticket.status != TicketStatus.open.value:
        await message.reply("Ticket is closed.")
        return
    user = await ts.load_user(ticket)
    if not user:
        return
    try:
        await message.copy_to(chat_id=user.telegram_id)
    except Exception as e:
        logger.warning("copy_to user %s: %s", user.telegram_id, e)
        await message.reply(f"Could not deliver: {e}")
