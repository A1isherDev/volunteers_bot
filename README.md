# Volunteers Telegram Bot

Production-oriented volunteer management bot built with **Python 3.11+**, **aiogram 3**, and **SQLAlchemy 2** (async). PostgreSQL is supported via `DATABASE_URL`; SQLite is the default for local runs.

## Features

- Registration (name, contact, optional age, region) with FSM
- FAQ stored in DB; admins add/edit/delete; users browse via inline keyboard
- Support tickets: user messages go to one admin group; admins **reply** to the bot post to reach the user; `/close_<id>` closes tickets
- Broadcasts (text or photo, optional URL buttons) with batching
- Suggestions stored in DB and forwarded to the admin group
- Group commands: `/help`, `/volunteer_info`, `/link_group` (bot admins)
- Super-admin panel: list/search users, promote/demote admins (env super-admins cannot be demoted below env level)
- Uzbek / Russian UI strings
- DB session middleware, per-user rate limiting, creation cooldown for tickets/suggestions, centralized logging, global error handler

## Layout

- `app/handlers/` — routers (commands, callbacks, FSM steps)
- `app/services/` — business logic
- `app/database/` — models and async session
- `app/middlewares/` — DB transaction, user context, rate limit
- `app/states/` — FSM groups
- `app/locales/` — `uz.json`, `ru.json`
- `schema.sql` — reference DDL

## Setup

1. Create a virtualenv and install dependencies:

```bash
cd d:\projects\volunteers_bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and set:

   - `BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
   - `REDIS_URL` — required (FSM, rate limits, queues, metrics)
   - `ADMIN_IDS` — comma-separated numeric user IDs
   - `ADMIN_GROUP_ID` — numeric chat ID of the central admin group (the bot must be a member)
   - Optional `SUPER_ADMIN_IDS`; if omitted, every `ADMIN_IDS` entry is treated as a super-admin for the panel

3. Create the database schema (Alembic only; the app does not run `create_all`):

```bash
alembic upgrade head
```

For PostgreSQL, set `DATABASE_URL`, for example `postgresql://user:password@host:5432/dbname` (the app normalizes this to `postgresql+asyncpg://`).

4. Run the bot (from the project root):

```bash
python -m app.main
```

## Admin group

- Add the bot to the group; disable privacy mode in BotFather (`/setprivacy` → Disable) if you need the bot to see all messages for ticket replies.
- Ticket and suggestion posts include user id, name, username, and phone.
- Reply **to the bot’s ticket message** (or to any message in that reply thread) so the bot can `copy_to` the volunteer. Use `/close_<id>` on a line by itself to close.

## Roles

- **user** — default after registration
- **admin** — FAQ, stats, broadcast, `/link_group` in groups
- **super_admin** — user management panel; can assign roles in DB

Env-listed `ADMIN_IDS` / `SUPER_ADMIN_IDS` are merged on each update so configured operators keep at least the env-assigned role.

## Production notes

- Use a process manager (systemd, Docker, etc.) and one bot instance per token.
- **Redis** is required: FSM, rate limiting, news queue, and metrics assume `REDIS_URL` (multi-worker safe).
- Run `alembic upgrade head` on deploy before starting the bot.
- Tune `BROADCAST_*`, `RATE_LIMIT_*`, and `CREATION_COOLDOWN_SEC` for Telegram limits and your audience size.
