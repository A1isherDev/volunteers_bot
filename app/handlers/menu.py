from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.database.models import User, UserRole
from app.handlers.filters import IsAdmin, IsRegistered
from app.i18n import other_lang, t
from app.keyboards.common import faq_admin_kb, faq_list_inline, main_menu_kb
from app.services.faq_service import FAQService
from app.services.user_service import UserService
from app.states.forms import FAQAdminStates

router = Router(name="menu")


def _labels(key: str) -> set[str]:
    return {t("uz", key), t("ru", key)}


@router.message(F.chat.type == "private", IsRegistered(), StateFilter(None), F.text.in_(_labels("menu.language")))
async def switch_language(message: Message, db_user: User, session):
    new_lang = other_lang(db_user.language)
    await UserService(session).set_language(db_user.telegram_id, new_lang)
    await session.refresh(db_user)
    await message.answer(
        "🇺🇿 / 🇷🇺" if new_lang == "ru" else "🇷🇺 / 🇺🇿",
        reply_markup=main_menu_kb(new_lang, db_user),
    )


@router.message(F.chat.type == "private", IsRegistered(), StateFilter(None), F.text.in_(_labels("menu.faq")))
async def open_faq(message: Message, db_user: User, session):
    lang = db_user.language
    faqs = await FAQService(session).list_all_ordered()
    if not faqs:
        await message.answer(t(lang, "faq.empty"))
        return
    rows = faq_list_inline(faqs, lang, prefix="faq").inline_keyboard
    extra: list[list[InlineKeyboardButton]] = []
    if db_user.role in (UserRole.admin.value, UserRole.super_admin.value):
        extra.append([InlineKeyboardButton(text=t(lang, "faq.admin_menu"), callback_data="faqadm:open")])
    extra.append([InlineKeyboardButton(text=t(lang, "common.back"), callback_data="faq:close")])
    await message.answer(
        t(lang, "faq.pick"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=list(rows) + extra),
    )


@router.callback_query(F.data.startswith("faq:"))
async def faq_callback(query: CallbackQuery, db_user: User | None, session):
    if not db_user:
        await query.answer()
        return
    lang = db_user.language
    if query.data == "faq:close":
        await query.message.edit_reply_markup(reply_markup=None)
        await query.answer()
        return
    if query.data == "faq:back":
        faqs = await FAQService(session).list_all_ordered()
        rows = faq_list_inline(faqs, lang, prefix="faq").inline_keyboard
        extra: list[list[InlineKeyboardButton]] = []
        if db_user.role in (UserRole.admin.value, UserRole.super_admin.value):
            extra.append([InlineKeyboardButton(text=t(lang, "faq.admin_menu"), callback_data="faqadm:open")])
        extra.append([InlineKeyboardButton(text=t(lang, "common.back"), callback_data="faq:close")])
        await query.message.edit_text(
            t(lang, "faq.pick"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=list(rows) + extra),
        )
        await query.answer()
        return
    _, sid = query.data.split(":", 1)
    try:
        fid = int(sid)
    except ValueError:
        await query.answer()
        return
    faq = await FAQService(session).get(fid)
    if not faq:
        await query.answer()
        return
    q = faq.question_ru if lang == "ru" and faq.question_ru else faq.question_uz
    a = faq.answer_ru if lang == "ru" and faq.answer_ru else faq.answer_uz
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t(lang, "common.back"), callback_data="faq:back")]]
    )
    await query.message.edit_text(f"<b>{q}</b>\n\n{a}", reply_markup=kb)
    await query.answer()


@router.callback_query(F.data == "faqadm:open", IsAdmin())
async def faq_admin_open(query: CallbackQuery, db_user: User):
    lang = db_user.language
    await query.message.edit_reply_markup(reply_markup=faq_admin_kb(lang))
    await query.answer()


@router.callback_query(F.data == "faqadm:close", IsAdmin())
async def faq_admin_close(query: CallbackQuery, db_user: User):
    await query.message.edit_reply_markup(reply_markup=None)
    await query.answer()


@router.callback_query(F.data == "faqadm:add", IsAdmin())
async def faq_admin_add_start(query: CallbackQuery, db_user: User, state: FSMContext):
    lang = db_user.language
    await state.set_state(FAQAdminStates.add_question_uz)
    await query.message.answer(t(lang, "faq.enter_q_uz"))
    await query.answer()


@router.callback_query(F.data == "faqadm:editlist", IsAdmin())
async def faq_edit_list(query: CallbackQuery, db_user: User, session, state: FSMContext):
    lang = db_user.language
    faqs = await FAQService(session).list_all_ordered()
    if not faqs:
        await query.answer(t(lang, "faq.empty"), show_alert=True)
        return
    await state.set_state(FAQAdminStates.edit_pick)
    kb = faq_list_inline(faqs, lang, prefix="faqed")
    await query.message.answer(t(lang, "faq.pick_to_edit"), reply_markup=kb)
    await query.answer()


@router.callback_query(F.data == "faqadm:dellist", IsAdmin())
async def faq_del_list(query: CallbackQuery, db_user: User, session, state: FSMContext):
    lang = db_user.language
    faqs = await FAQService(session).list_all_ordered()
    if not faqs:
        await query.answer(t(lang, "faq.empty"), show_alert=True)
        return
    await state.set_state(FAQAdminStates.delete_pick)
    kb = faq_list_inline(faqs, lang, prefix="faqd")
    await query.message.answer(t(lang, "faq.pick_to_delete"), reply_markup=kb)
    await query.answer()


@router.message(F.chat.type == "private", IsRegistered(), StateFilter(None), F.text.in_(_labels("menu.stats")), IsAdmin())
async def stats(message: Message, db_user: User, session):
    lang = db_user.language
    svc = UserService(session)
    total = await svc.count_users()
    active = await svc.count_active_users(7)
    await message.answer(
        f"{t(lang, 'stats.title')}\n{t(lang, 'stats.total', total=total)}\n{t(lang, 'stats.active', active=active)}"
    )


@router.message(F.chat.type == "private", ~IsRegistered(), StateFilter(None), F.text)
async def need_register(message: Message):
    lang = message.from_user.language_code or "uz"
    if lang.startswith("ru"):
        lang = "ru"
    else:
        lang = "uz"
    await message.answer(t(lang, "errors.need_register"))
