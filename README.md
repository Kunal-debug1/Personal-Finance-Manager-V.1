# PFMS Pro

PFMS Pro is a professional personal finance management system built with Flask. It provides a clean dashboard for managing:

- Accounts and balances
- Income and expense transactions
- Expense category analysis
- Bills and due dates
- Savings goals

## Technology

- Flask
- Flask-Login
- Flask-SQLAlchemy
- SQLite by default (configurable with `DATABASE_URL`)
- Bootstrap 5 UI

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate
pip install flask flask-login flask-sqlalchemy
python app.py
```

The app automatically creates a local SQLite database file named `finance_manager.db` in the project root.

## Configuration

Optional environment variables:

- `SECRET_KEY`: Flask session secret
- `DATABASE_URL`: SQLAlchemy database URL

## Core workflows

1. Register a user account.
2. Add financial accounts and opening balances.
3. Record income and expense transactions.
4. Review expense analysis by category.
5. Track bills and savings goals from the dashboard.
