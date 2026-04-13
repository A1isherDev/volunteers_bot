import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.models import User
from app.handlers.filters import IsAdmin
from app.i18n import t
from app.keyboards.common import faq_list_inline
from app.services.faq_service import FAQService
from app.states.forms import FAQAdminStates

logger = logging.getLogger(__name__)
router = Router(name="faq_fsm")


@router.message(
    F.chat.type == "private",
    IsAdmin(),
    StateFilter(FAQAdminStates.add_question_uz),
    F.text,
)
async def faq_add_q_uz(message: Message, state: FSMContext, db_user: User):
    lang = db_user.language
    await state.update_data(faq_q_uz=message.text.strip())
    await state.set_state(FAQAdminStates.add_answer_uz)
    await message.answer(t(lang, "faq.enter_a_uz"))


@router.message(F.chat.type == "private", IsAdmin(), StateFilter(FAQAdminStates.add_answer_uz), F.text)
async def faq_add_a_uz(message: Message, state: FSMContext, db_user: User):
    lang = db_user.language
    await state.update_data(faq_a_uz=message.text.strip())
    await state.set_state(FAQAdminStates.add_question_ru)
    await message.answer(t(lang, "faq.enter_q_ru"))


@router.message(F.chat.type == "private", IsAdmin(), StateFilter(FAQAdminStates.add_question_ru), F.text)
async def faq_add_q_ru(message: Message, state: FSMContext, db_user: User):
    lang = db_user.language
    text = (message.text or "").strip()
    if text == "/skip":
        await state.update_data(faq_q_ru=None)
    else:
        await state.update_data(faq_q_ru=text)
    await state.set_state(FAQAdminStates.add_answer_ru)
    await message.answer(t(lang, "faq.enter_a_ru"))


@router.message(F.chat.type == "private", IsAdmin(), StateFilter(FAQAdminStates.add_answer_ru), F.text)
async def faq_add_a_ru(message: Message, state: FSMContext, db_user: User, session):
    lang = db_user.language
    data = await state.get_data()
    q_ru = data.get("faq_q_ru")
    text = (message.text or "").strip()
    if text == "/skip":
        a_ru = None
    else:
        a_ru = text or None
    await FAQService(session).create(
        question_uz=data["faq_q_uz"],
        answer_uz=data["faq_a_uz"],
        question_ru=q_ru,
        answer_ru=a_ru,
    )
    await state.clear()
    await message.answer(t(lang, "faq.saved"))
    logger.info("FAQ created by admin telegram_id=%s", db_user.telegram_id)


@router.callback_query(IsAdmin(), F.data.startswith("faqed:"), StateFilter(FAQAdminStates.edit_pick))
async def faq_edit_pick(query: CallbackQuery, state: FSMContext, db_user: User):
    lang = db_user.language
    try:
        fid = int(query.data.split(":", 1)[1])
    except ValueError:
        await query.answer()
        return
    await state.update_data(faq_edit_id=fid)
    await state.set_state(FAQAdminStates.edit_question)
    await query.message.answer(t(lang, "faq.new_question"))
    await query.answer()


@router.message(F.chat.type == "private", IsAdmin(), StateFilter(FAQAdminStates.edit_question), F.text)
async def faq_edit_q(message: Message, state: FSMContext, db_user: User):
    lang = db_user.language
    await state.update_data(faq_new_q=message.text.strip())
    await state.set_state(FAQAdminStates.edit_answer)
    await message.answer(t(lang, "faq.new_answer"))


@router.message(F.chat.type == "private", IsAdmin(), StateFilter(FAQAdminStates.edit_answer), F.text)
async def faq_edit_a(message: Message, state: FSMContext, db_user: User, session):
    lang = db_user.language
    data = await state.get_data()
    fid = data["faq_edit_id"]
    ok = await FAQService(session).update_qa(
        fid,
        question_uz=data["faq_new_q"],
        answer_uz=message.text.strip(),
    )
    await state.clear()
    if ok:
        await message.answer(t(lang, "faq.saved"))
    else:
        await message.answer(t(lang, "errors.generic"))


@router.callback_query(IsAdmin(), F.data.startswith("faqd:"), StateFilter(FAQAdminStates.delete_pick))
async def faq_delete_do(query: CallbackQuery, state: FSMContext, db_user: User, session):
    lang = db_user.language
    try:
        fid = int(query.data.split(":", 1)[1])
    except ValueError:
        await query.answer()
        return
    ok = await FAQService(session).delete(fid)
    await state.clear()
    await query.message.answer(t(lang, "faq.deleted") if ok else t(lang, "errors.generic"))
    await query.answer()
