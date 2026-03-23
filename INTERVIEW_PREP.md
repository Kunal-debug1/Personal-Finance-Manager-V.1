# PFMS Pro Interview Preparation Guide

## 1. Project summary

**Project name:** PFMS Pro (Personal Finance Management System).

This guide is stored in Markdown so it stays repository-friendly. You can open it directly in GitHub or copy it into Microsoft Word/Google Docs when you need a document version.

This project is a full-stack Flask web application built to help users manage personal finances in one place. It allows users to register, log in securely, add financial accounts, record income and expenses, organize transactions by category, track bills, and monitor savings goals.

The project started as a simpler finance manager and was upgraded into a cleaner, more maintainable application using SQLite and SQLAlchemy. It now follows a more production-friendly structure and includes deployment support for PythonAnywhere.

## 2. Problem statement

Many users track money manually in spreadsheets or disconnected mobile apps. The goal of PFMS Pro was to build a web-based system where a user could:

- manage multiple accounts,
- track income and expenses,
- categorize spending,
- monitor upcoming bills,
- define savings goals,
- and view all this data from a single dashboard.

## 3. Main objectives

The project was designed with these goals:

1. Provide a centralized personal finance dashboard.
2. Use secure authentication with password hashing.
3. Store structured data in a real relational database.
4. Keep the interface simple and professional.
5. Make the project easy to explain in interviews and easy to deploy on PythonAnywhere.

## 4. Technology stack

### Backend
- Python
- Flask
- Flask-Login
- Flask-SQLAlchemy
- Werkzeug security helpers
- SQLite (`sqlite:///pfms.db`)

### Frontend
- HTML
- Bootstrap 5
- Jinja2 templates

### Deployment
- PythonAnywhere
- WSGI configuration
- Virtual environment (`pfms-env`)

## 5. Application architecture

The project is split into clear layers:

### `app.py`
This is the main application entrypoint. It creates the Flask app, configures SQLite, initializes extensions, registers routes, and provides helper functions for validation, formatting, and dashboard aggregation.

### `models.py`
This file contains all SQLAlchemy ORM models. It separates database design from route logic, which makes the code easier to maintain and explain.

### `templates/`
This folder contains the UI. Templates are rendered using Jinja2. A shared `base.html` gives the app a consistent layout, and feature-specific templates are used for dashboard, balances, transactions, expenses, bills, goals, login, and registration.

### `requirements.txt`
Contains the Python dependencies needed to run or deploy the app.

### `pythonanywhere_wsgi.py`
Provides an example WSGI file for PythonAnywhere deployment.

### `DEPLOY_ON_PYTHONANYWHERE.md`
Contains a deployment checklist and deployment steps.

## 6. Database design

The project uses SQLAlchemy models to represent relational data.

### User
Represents an authenticated application user.
- `id`
- `username`
- `email`
- `password_hash`
- `created_at`

### Account
Represents a financial account such as checking, savings, investment, or credit card.
- `id`
- `user_id`
- `institution`
- `account_name`
- `account_type`
- `balance`
- `last_four`
- `created_at`

### Category
Represents a spending or income category owned by a specific user.
- `id`
- `user_id`
- `name`
- `created_at`

### Transaction
Represents a financial transaction linked to a user, account, and category.
- `id`
- `user_id`
- `account_id`
- `category_id`
- `entry_date`
- `transaction_type`
- `amount`
- `description`
- `created_at`

### Bill
Represents a due payment.
- `id`
- `user_id`
- `title`
- `category`
- `amount`
- `due_date`
- `status`
- `notes`
- `created_at`

### SavingsGoal
Represents a savings target.
- `id`
- `user_id`
- `name`
- `target_amount`
- `current_amount`
- `due_date`
- `created_at`

## 7. Relationships

Important relationships in the system:

- One user → many accounts
- One user → many transactions
- One user → many categories
- One user → many bills
- One user → many savings goals
- One account → many transactions
- One category → many transactions

This relational design helps avoid duplication and makes reporting easier.

## 8. Authentication design

The project uses Flask-Login for session management.

### Registration flow
1. User submits username, email, password, and confirm password.
2. Input is validated.
3. Password is hashed using Werkzeug.
4. User record is stored in SQLite.

### Login flow
1. User submits email and password.
2. App fetches the user by email.
3. Password hash is checked using `check_password_hash`.
4. If valid, Flask-Login creates the session.

### Logout flow
- Flask-Login clears the session and redirects to login.

## 9. Validation and helper logic

The backend includes helper functions to keep route logic cleaner.

### `to_decimal()`
Used to validate money input and ensure values are numeric and positive.

### `parse_date()`
Ensures all dates follow `YYYY-MM-DD` format.

### `currency()`
Formats numbers consistently as currency for display in templates.

### `get_or_create_category()`
Avoids duplicate category records for the same user.

### `update_account_balance()`
Automatically adjusts account balances when a transaction is added or removed.

## 10. Core features explained

### Dashboard
The dashboard gives an overview of:
- total balance,
- total income,
- total expenses,
- net cash flow,
- upcoming bills,
- savings goals,
- and expense distribution by category.

### Accounts
Users can add accounts and maintain opening balances.

### Transactions
Users can add income or expense transactions and link them to an account and category.

### Expense analysis
Expense transactions are grouped by category to help users understand spending patterns.

### Bills
Users can add upcoming bills, record due dates, and mark payment status.

### Savings goals
Users can define target savings amounts and track progress.

## 11. UI design approach

The UI was designed around a shared layout pattern:

- `base.html` provides sidebar navigation and reusable structure.
- Flash messages are centralized in a partial template.
- Bootstrap is used for responsive design.
- Each major module has its own template page.

This makes the app easier to maintain and improves the overall user experience.

## 12. Why SQLite was chosen

SQLite was used because:

- it is lightweight,
- easy for local development,
- requires no external database server,
- works well for small to medium portfolio/demo projects,
- and is supported easily on platforms like PythonAnywhere.

## 13. Why SQLAlchemy was chosen

SQLAlchemy was chosen because it provides:

- ORM-based data access,
- better maintainability than raw SQL,
- easier model relationships,
- cleaner code,
- and a migration path to MySQL/PostgreSQL later.

## 14. Deployment process

The project was prepared for PythonAnywhere.

### Deployment flow
1. Clone the repository.
2. Create a Python virtualenv.
3. Install dependencies from `requirements.txt`.
4. Configure the web app in PythonAnywhere.
5. Point the WSGI file to the project path.
6. Run `init_db()` once to create the SQLite database.
7. Reload the app.

### Important deployment files
- `requirements.txt`
- `pythonanywhere_wsgi.py`
- `DEPLOY_ON_PYTHONANYWHERE.md`
- `README.md`

## 15. Interview explanation: how to present the project

A strong way to explain the project in an interview is:

> “I built a personal finance management system using Flask, SQLAlchemy, and SQLite. The app supports secure authentication, account management, transaction tracking, expense categorization, bill reminders, and savings goals. I structured it with a dedicated model layer, reusable templates, and deployment support for PythonAnywhere. I also used helper functions to centralize validation and balance updates so the code stayed maintainable.”

## 16. Common interview questions and sample answers

### Q1. Why did you use Flask instead of Django?
**Answer:** Flask gave me more control over the project structure and was lightweight enough for a focused personal finance application.

### Q2. Why did you use SQLAlchemy?
**Answer:** SQLAlchemy helped model relationships cleanly and made the persistence layer easier to maintain than using raw SQL or file storage.

### Q3. Why did you move away from JSON/file-based storage?
**Answer:** JSON storage works for prototypes, but it becomes difficult to maintain data integrity, relationships, and concurrent updates. SQLite with SQLAlchemy gives a more reliable structure.

### Q4. How is security handled?
**Answer:** Passwords are hashed with Werkzeug, authentication is managed using Flask-Login, and user-specific data is filtered by the logged-in user’s ID.

### Q5. How would you scale this project?
**Answer:** I would move configuration into separate config classes, add Flask-Migrate for schema migrations, use PostgreSQL or MySQL, split routes into blueprints, and possibly add REST APIs for mobile integration.

## 17. Challenges in the project

Possible technical challenges to discuss:

- Migrating from simple storage to relational storage.
- Designing proper relationships between accounts, transactions, and categories.
- Keeping account balances synchronized when transactions are created or deleted.
- Organizing templates into reusable components.
- Preparing the project for deployment while keeping it beginner-friendly.

## 18. Future enhancements

You can mention these as future scope in interviews:

- monthly budget planning,
- recurring bill automation,
- charts using Chart.js,
- export to PDF or Excel,
- email reminders,
- admin analytics,
- mobile-responsive advanced dashboard,
- and migration to PostgreSQL for larger production use.

## 19. Resume-ready project description

**PFMS Pro – Personal Finance Management System**  
Built a full-stack finance management web application using Flask, Flask-Login, Flask-SQLAlchemy, and SQLite. Implemented secure user authentication, account and transaction tracking, category-based expense analysis, bill management, and savings goal monitoring. Structured the application with ORM models, reusable Bootstrap templates, and deployment-ready configuration for PythonAnywhere.

## 20. Final preparation tip

Before interviews, be ready to explain:

- what problem the project solves,
- why you chose Flask + SQLAlchemy + SQLite,
- how authentication works,
- how relationships are modeled,
- how account balances stay consistent,
- and how you deployed it on PythonAnywhere.
