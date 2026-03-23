# PFMS Pro

PFMS Pro is a beginner-friendly personal finance management system built with Flask, Flask-Login, and Flask-SQLAlchemy.

This version uses a local SQLite database file exactly as requested:

- `sqlite:///pfms.db`

## What changed

- JSON storage was replaced with SQLite.
- SQLAlchemy models now manage all persistent data.
- Flask-Login authentication uses a `User` model that inherits from `UserMixin`.
- Passwords are hashed with Werkzeug.
- Relationships are now properly defined between users, accounts, transactions, categories, bills, and savings goals.
- The app now includes a PythonAnywhere deployment example and a `requirements.txt` file.

## Required deployment files

Before deploying on PythonAnywhere, make sure your GitHub repository root contains:

- `app.py`
- `models.py`
- `requirements.txt`
- `pythonanywhere_wsgi.py`
- `templates/`

A dedicated deployment checklist is also included in `DEPLOY_ON_PYTHONANYWHERE.md`.

## Project structure

- `app.py` – Flask app factory, routes, validation helpers, and database initialization helper
- `models.py` – SQLAlchemy models and relationships
- `pythonanywhere_wsgi.py` – example WSGI entry point for PythonAnywhere
- `requirements.txt` – Python dependencies for deployment
- `templates/` – Existing Bootstrap UI templates
- `DATABASE_REFERENCE.md` – Text-based database schema/reference document

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

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

On first run, the application creates `pfms.db` using `db.create_all()`. You can also initialize it explicitly with `python -c "from app import init_db; init_db()"` or `flask --app app init-db`.

## Deploying on PythonAnywhere

These steps follow PythonAnywhere's Flask deployment approach using **Manual configuration**, a **virtualenv**, and a **WSGI file**.

1. Upload this project to your PythonAnywhere account.
2. Open a Bash console and create a virtualenv:

   ```bash
   mkvirtualenv --python=/usr/bin/python3.13 pfms-env
   workon pfms-env
   pip install -r /home/yourusername/Personal-Finance-Manager-V.1/requirements.txt
   ```

3. In the **Web** tab, create a new web app using **Manual configuration** and select the same Python version.
4. In the **Virtualenv** section, point the web app to:

   ```bash
   /home/yourusername/.virtualenvs/pfms-env
   ```

5. Open the PythonAnywhere WSGI configuration file and adapt the example from `pythonanywhere_wsgi.py`:

   ```python
   import sys
   path = '/home/yourusername/Personal-Finance-Manager-V.1'
   if path not in sys.path:
       sys.path.insert(0, path)

   from app import app as application
   ```

6. Initialize the SQLite database once from a Bash console:

   ```bash
   workon pfms-env
   cd /home/yourusername/Personal-Finance-Manager-V.1
   python -c "from app import init_db; init_db()"
   ```

7. Reload the web app from the **Web** tab.

## Important PythonAnywhere note

Do **not** rely on `app.run()` for deployment there. PythonAnywhere serves Flask apps through the WSGI file, and `app.run()` should only be used for local development.

## Notes for future scalability

If you want to upgrade later:

- move configuration into a separate `config.py`
- use Flask-Migrate for schema migrations
- switch `SQLALCHEMY_DATABASE_URI` to MySQL or PostgreSQL
- split routes into blueprints
- add WTForms or Flask-WTF for stronger form handling
- introduce service layers and repositories for larger projects


## Interview preparation

Use `INTERVIEW_PREP.md` as the text-based interview handout for this project. It is intentionally stored in Markdown instead of a binary Word file so it stays review-friendly in Git repositories.
