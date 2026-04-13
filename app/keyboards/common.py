from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from app.config import get_settings
from app.database.models import FAQ, User, UserRole
from app.i18n import t


def main_menu_kb(lang: str, user: User | None) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = [
        [KeyboardButton(text=t(lang, "menu.faq"))],
        [KeyboardButton(text=t(lang, "menu.support")), KeyboardButton(text=t(lang, "menu.suggestion"))],
        [KeyboardButton(text=t(lang, "menu.language"))],
    ]
    if user and user.role in (UserRole.admin.value, UserRole.super_admin.value):
        rows.append([KeyboardButton(text=t(lang, "menu.stats")), KeyboardButton(text=t(lang, "menu.broadcast"))])
    s = get_settings()
    super_ids = s.parsed_super_admin_ids()
    if user and (user.role == UserRole.super_admin.value or user.telegram_id in super_ids):
        rows.append([KeyboardButton(text=t(lang, "menu.admin_panel"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def registration_contact_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "common.share_contact"), request_contact=True)]],
        resize_keyboard=True,
    )


def registration_skip_age_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "common.skip"))]],
        resize_keyboard=True,
    )


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def faq_list_inline(faqs: list[FAQ], lang: str, prefix: str = "faq") -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for f in faqs:
        title = f.question_ru if lang == "ru" and f.question_ru else f.question_uz
        buttons.append([InlineKeyboardButton(text=title[:64], callback_data=f"{prefix}:{f.id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def faq_admin_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "faq.add"), callback_data="faqadm:add")],
            [
                InlineKeyboardButton(text=t(lang, "faq.list_edit"), callback_data="faqadm:editlist"),
                InlineKeyboardButton(text=t(lang, "faq.list_delete"), callback_data="faqadm:dellist"),
            ],
            [InlineKeyboardButton(text=t(lang, "common.back"), callback_data="faqadm:close")],
        ]
    )


def super_admin_user_actions(lang: str, telegram_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "admin.promote"), callback_data=f"sadm:adm:{telegram_id}"),
                InlineKeyboardButton(text=t(lang, "admin.demote"), callback_data=f"sadm:user:{telegram_id}"),
            ],
            [InlineKeyboardButton(text=t(lang, "admin.super_promote"), callback_data=f"sadm:super:{telegram_id}")],
            [InlineKeyboardButton(text=t(lang, "common.back"), callback_data="sadm:back")],
        ]
    )


def users_page_kb(lang: str, page: int, pages: int) -> InlineKeyboardMarkup:
    nav: list[InlineKeyboardButton] = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="«", callback_data=f"sadm:page:{page-1}"))
    nav.append(InlineKeyboardButton(text=t(lang, "admin.page", page=page, pages=pages), callback_data="sadm:noop"))
    if page < pages:
        nav.append(InlineKeyboardButton(text="»", callback_data=f"sadm:page:{page+1}"))
    return InlineKeyboardMarkup(inline_keyboard=[nav])
