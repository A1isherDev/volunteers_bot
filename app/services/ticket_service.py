from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Ticket, TicketStatus, User


class TicketService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User, body_text: str) -> Ticket:
        t = Ticket(user_id=user.id, body_text=body_text, status=TicketStatus.open.value)
        self.session.add(t)
        await self.session.flush()
        return t

    async def set_admin_message_id(self, ticket_id: int, message_id: int) -> None:
        await self.session.execute(
            update(Ticket).where(Ticket.id == ticket_id).values(admin_message_id=message_id)
        )

    async def get_by_admin_root_message(self, message_id: int) -> Ticket | None:
        r = await self.session.execute(select(Ticket).where(Ticket.admin_message_id == message_id))
        return r.scalar_one_or_none()

    async def get_by_admin_message_chain(self, message_ids: list[int]) -> Ticket | None:
        """Match a ticket whose admin post is anywhere in the reply chain (nearest first)."""
        if not message_ids:
            return None
        r = await self.session.execute(select(Ticket).where(Ticket.admin_message_id.in_(message_ids)))
        tickets = list(r.scalars().all())
        if not tickets:
            return None
        pos = {mid: i for i, mid in enumerate(message_ids)}
        tickets.sort(key=lambda t: pos.get(t.admin_message_id or 0, 9999))
        return tickets[0]

    async def close(self, ticket_id: int) -> bool:
        r = await self.session.execute(
            update(Ticket)
            .where(Ticket.id == ticket_id)
            .values(status=TicketStatus.closed.value, updated_at=datetime.now(timezone.utc))
        )
        return r.rowcount > 0

    async def get(self, ticket_id: int) -> Ticket | None:
        r = await self.session.execute(select(Ticket).where(Ticket.id == ticket_id))
        return r.scalar_one_or_none()

    async def load_user(self, ticket: Ticket) -> User | None:
        r = await self.session.execute(select(User).where(User.id == ticket.user_id))
        return r.scalar_one_or_none()
