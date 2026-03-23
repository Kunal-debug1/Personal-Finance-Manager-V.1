# PFMS Pro

PFMS Pro is a professional personal finance management system built with Flask and SQLAlchemy, designed to work with a **free hosted PostgreSQL database service** such as Supabase or Neon.

## Features

- Account and balance tracking
- Income and expense transaction history
- Expense analysis by category
- Bill scheduling and due-date monitoring
- Savings goal tracking
- Hosted database support for deployment

## Technology

- Flask
- Flask-Login
- Flask-SQLAlchemy
- PostgreSQL-compatible `DATABASE_URL`
- Bootstrap 5 UI

## Recommended free database services

This app is now designed for a hosted PostgreSQL connection string.

Examples:

- Supabase free Postgres project
- Neon free Postgres project

Set the provider name in your environment for UI labeling:

```bash
export DB_PROVIDER="Supabase"
```

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate
pip install flask flask-login flask-sqlalchemy psycopg[binary]
export DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/postgres"
export DB_PROVIDER="Supabase"
python app.py
```

## Configuration

Optional environment variables:

- `SECRET_KEY`: Flask session secret
- `DATABASE_URL`: Hosted PostgreSQL connection string
- `DB_PROVIDER`: Friendly database provider label shown in the UI

## Local development fallback

If `DATABASE_URL` is not provided, the app falls back to a local SQLite file for development only. For deployment, use a hosted free database service.

## Core workflows

1. Register a user account.
2. Add financial accounts and balances.
3. Record income and expense transactions.
4. Review expense analysis by category.
5. Track bills and savings goals from the dashboard.
