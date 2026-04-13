from app.i18n import t


def label_set(*keys: str) -> set[str]:
    s: set[str] = set()
    for k in keys:
        s.add(t("uz", k))
        s.add(t("ru", k))
    return s


def all_registered_menu_labels() -> set[str]:
    return label_set(
        "menu.faq",
        "menu.support",
        "menu.suggestion",
        "menu.language",
        "menu.stats",
        "menu.broadcast",
        "menu.admin_panel",
    )
