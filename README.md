# PFMS Pro

PFMS Pro is a professional personal finance management system built with Flask and **database-free local file storage**. Instead of requiring MySQL, PostgreSQL, or SQLite services, the app stores its data in a JSON file so it is easier to deploy on small hosting environments, demos, and personal servers.

## Features

- Account and balance tracking
- Income and expense transaction history
- Expense analysis by category
- Bill scheduling and due-date monitoring
- Savings goal tracking
- File-based storage with no SQL database setup

## Technology

- Flask
- Flask-Login
- Werkzeug password hashing
- Bootstrap 5 UI
- JSON file persistence

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate
pip install flask flask-login
python app.py
```

## Storage model

The application stores all user and finance data in a JSON file.

- Default path: `data/store.json`
- Override path with: `PFMS_DATA_FILE=/path/to/store.json`

This means deployment does **not** require:

- MySQL
- PostgreSQL
- SQLite
- Any external database service

## Configuration

Optional environment variables:

- `SECRET_KEY`: Flask session secret
- `PFMS_DATA_FILE`: Path to the JSON data file

## Core workflows

1. Register a user account.
2. Add financial accounts and balances.
3. Record income and expense transactions.
4. Review expense analysis by category.
5. Track bills and savings goals from the dashboard.
