# PFMS Pro

PFMS Pro is a beginner-friendly personal finance management system built with Flask, Flask-Login, and Flask-SQLAlchemy.

`Live Link` : https://kunalgaikwad2023.pythonanywhere.com

This version uses a local SQLite database file exactly as requested:

- `sqlite:///pfms.db`

## What changed

- JSON storage was replaced with SQLite.
- SQLAlchemy models now manage all persistent data.
- Flask-Login authentication uses a `User` model that inherits from `UserMixin`.
- Passwords are hashed with Werkzeug.
- Relationships are now properly defined between users, accounts, transactions, categories, bills, and savings goals.

## Project structure

- `app.py` – Flask app, routes, validation helpers, and database initialization
- `models.py` – SQLAlchemy models and relationships
- `templates/` – Existing Bootstrap UI templates

## Database models

The project now includes these models:

- `User`
- `Account`
- `Category`
- `Transaction`
- `Bill`
- `SavingsGoal`

## Relationships

- One user → many accounts
- One user → many transactions
- One account → many transactions
- One user → many bills
- One user → many savings goals
- One user → many categories

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install flask flask-login flask-sqlalchemy
python app.py
```

On first run, the application automatically creates `pfms.db` using `db.create_all()`.

## Notes for future scalability

If you want to upgrade later:

- move configuration into a separate `config.py`
- use Flask-Migrate for schema migrations
- switch `SQLALCHEMY_DATABASE_URI` to MySQL or PostgreSQL
- split routes into blueprints
- add WTForms or Flask-WTF for stronger form handling
- introduce service layers and repositories for larger projects
