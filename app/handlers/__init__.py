from aiogram import Dispatcher


def register_handlers(dp: Dispatcher) -> None:
    from app.handlers import (
        admin_inbox,
        broadcast,
        errors,
        faq_fsm,
        group_commands,
        menu,
        registration,
        suggestion,
        super_admin,
        support,
    )

    dp.include_router(errors.router)
    dp.include_router(admin_inbox.router)
    dp.include_router(group_commands.router)
    dp.include_router(registration.router)
    dp.include_router(faq_fsm.router)
    dp.include_router(broadcast.router)
    dp.include_router(super_admin.router)
    dp.include_router(support.router)
    dp.include_router(suggestion.router)
    dp.include_router(menu.router)
