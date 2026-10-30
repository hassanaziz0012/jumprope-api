# Jumprope Tracker — API

The backend for [Jumprope Tracker](https://jumprope.hassandev.me), a free, offline-first, open-source jump rope workout tracker.

Website: [jumprope.hassandev.me](https://jumprope.hassandev.me) · API: [jumprope-api.vercel.app](https://jumprope-api.vercel.app)

The app works fully offline. This API only powers the optional features, both off by default:

- **Cloud Sync** (`routes/sync.py`, `routes/auth.py`): account sign-up and backup of your workouts, goals, and streaks.
- **AI Training Coach** (`routes/ai.py`, `routes/conversations.py`): personalized coaching chats and the weekly digest.

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: PostgreSQL (NeonDB) via SQLAlchemy + Alembic migrations
- **Hosting**: Vercel

## See Also

- [Website](https://jumprope.hassandev.me)
- [Mobile App](https://github.com/hassanaziz0012/jumprope-app)
- [Landing Page](https://github.com/hassanaziz0012/jumprope-landing-page)
