import html

from app.database.models import User


def format_ticket_header(ticket_id: int, db_user: User, username: str | None) -> str:
    uline = f"@{username}" if username else "—"
    return (
        f"🎫 <b>Support ticket</b> #{ticket_id} <code>open</code>\n"
        f"User ID: <code>{db_user.telegram_id}</code>\n"
        f"Name: {html.escape(db_user.full_name)}\n"
        f"Username: {html.escape(uline)}\n"
        f"Phone: {html.escape(db_user.phone)}\n"
        f"────────\n"
    )


def format_suggestion_header(suggestion_id: int, db_user: User, username: str | None) -> str:
    uline = f"@{username}" if username else "—"
    return (
        f"💡 <b>Suggestion</b> #{suggestion_id}\n"
        f"User ID: <code>{db_user.telegram_id}</code>\n"
        f"Name: {html.escape(db_user.full_name)}\n"
        f"Username: {html.escape(uline)}\n"
        f"────────\n"
    )
