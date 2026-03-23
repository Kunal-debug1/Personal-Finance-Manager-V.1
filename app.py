"""Main application entry point for PFMS Pro.

This version uses SQLite with Flask-SQLAlchemy and Flask-Login.
The UI templates remain largely unchanged, while backend storage now
uses a proper relational database instead of JSON files.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import Account, Bill, Category, SavingsGoal, Transaction, User, db


def create_app() -> Flask:
    """Application factory used by local runs and WSGI deployments."""
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    # Initialize extensions.
    db.init_app(flask_app)
    login_manager.init_app(flask_app)

    register_routes(flask_app)
    return flask_app


login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Load the authenticated user for Flask-Login."""
    return db.session.get(User, int(user_id))


def init_db(flask_app: Flask | None = None) -> None:
    """Create database tables.

    Run this once after deployment, or whenever you need to initialize a fresh
    SQLite database. An app instance can be passed explicitly for CLI or tests.
    """
    target_app = flask_app or app
    with target_app.app_context():
        db.create_all()


def to_decimal(raw_value: str, field_name: str, *, allow_zero: bool = False) -> Decimal:
    """Validate and normalize decimal input from forms."""
    try:
        value = Decimal(raw_value)
    except (InvalidOperation, TypeError):
        raise ValueError(f"{field_name} must be a valid number.")

    minimum = Decimal("0.00") if allow_zero else Decimal("0.01")
    if value < minimum or (not allow_zero and value == 0):
        comparator = "zero or greater" if allow_zero else "greater than zero"
        raise ValueError(f"{field_name} must be {comparator}.")
    return value.quantize(Decimal("0.01"))


def parse_date(raw_value: str, field_name: str) -> date:
    """Validate form date strings using the app's standard format."""
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.")


def currency(value: Decimal | float | int | str | None) -> str:
    """Format currency values consistently in templates."""
    numeric_value = Decimal(str(value or 0))
    return f"₹{numeric_value:,.2f}"


def get_or_create_category(user_id: int, name: str) -> Category:
    """Return an existing category or create a new one for the user."""
    normalized_name = name.strip().title()
    category = Category.query.filter_by(user_id=user_id, name=normalized_name).first()
    if category:
        return category

    category = Category(user_id=user_id, name=normalized_name)
    db.session.add(category)
    db.session.flush()
    return category


def update_account_balance(account: Account, transaction_type: str, amount: Decimal, *, reverse: bool = False) -> None:
    """Update account balance when a transaction is added or removed."""
    signed_amount = amount if transaction_type == "income" else -amount
    if reverse:
        signed_amount *= -1
    account.balance = Decimal(str(account.balance)) + signed_amount


def register_routes(flask_app: Flask) -> None:
    """Attach routes and template helpers to the Flask app instance."""

    @flask_app.cli.command("init-db")
    def init_db_command() -> None:
        """CLI command for initializing the SQLite database."""
        init_db(flask_app)
        print("Database initialized.")

    @flask_app.context_processor
    def inject_helpers() -> dict[str, object]:
        """Helpers available to all Jinja templates."""
        return {
            "currency": currency,
            "today": date.today().isoformat(),
            "database_provider": "SQLite",
            "database_target": Config.SQLALCHEMY_DATABASE_URI,
        }

    @flask_app.route("/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("home.html")

    @flask_app.route("/health")
    def health() -> tuple[dict[str, str], int]:
        """Simple health endpoint for deployment checks."""
        return {"status": "ok"}, 200

    @flask_app.route("/register", methods=["GET", "POST"])
    def register():
        """Example route: create a new user account."""
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            errors: list[str] = []
            if len(username) < 3:
                errors.append("Username must be at least 3 characters long.")
            if "@" not in email or "." not in email:
                errors.append("Please enter a valid email address.")
            if len(password) < 8:
                errors.append("Password must be at least 8 characters long.")
            if password != confirm_password:
                errors.append("Passwords do not match.")
            if User.query.filter_by(email=email).first():
                errors.append("An account with that email already exists.")

            if errors:
                for error in errors:
                    flash(error, "danger")
                return render_template("register.html")

            user = User(username=username, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("Account created successfully. Please sign in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @flask_app.route("/login", methods=["GET", "POST"])
    def login():
        """Example route: authenticate an existing user."""
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()

            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash("Welcome back.", "success")
                return redirect(url_for("dashboard"))

            flash("Invalid email or password.", "danger")

        return render_template("login.html")

    @flask_app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    def build_dashboard_context() -> dict[str, object]:
        """Collect all data needed by the dashboard route."""
        accounts = Account.query.filter_by(user_id=current_user.id).order_by(Account.created_at.desc()).all()
        transactions = (
            Transaction.query.filter_by(user_id=current_user.id)
            .order_by(Transaction.entry_date.desc(), Transaction.created_at.desc())
            .all()
        )
        bills = Bill.query.filter_by(user_id=current_user.id).order_by(Bill.due_date.asc()).all()
        goals = SavingsGoal.query.filter_by(user_id=current_user.id).order_by(SavingsGoal.due_date.asc()).all()

        total_balance = sum((Decimal(str(item.balance)) for item in accounts), Decimal("0"))
        total_income = sum(
            (Decimal(str(item.amount)) for item in transactions if item.transaction_type == "income"),
            Decimal("0"),
        )
        total_expenses = sum(
            (Decimal(str(item.amount)) for item in transactions if item.transaction_type == "expense"),
            Decimal("0"),
        )
        upcoming_bills = [bill for bill in bills if bill.due_date >= date.today()][:5]

        expense_totals: dict[str, Decimal] = {}
        for item in transactions:
            if item.transaction_type != "expense":
                continue
            category_name = item.category.name if item.category else "Uncategorized"
            expense_totals[category_name] = expense_totals.get(category_name, Decimal("0")) + Decimal(str(item.amount))

        spending_by_category = sorted(expense_totals.items(), key=lambda entry: entry[1], reverse=True)

        return {
            "accounts": accounts,
            "transactions": transactions,
            "bills": bills,
            "goals": goals,
            "total_balance": total_balance,
            "monthly_income": total_income,
            "monthly_expenses": total_expenses,
            "net_cash_flow": total_income - total_expenses,
            "upcoming_bills": upcoming_bills,
            "spending_by_category": spending_by_category,
        }

    @flask_app.route("/dashboard")
    @login_required
    def dashboard():
        """Example route: main dashboard overview."""
        return render_template("dashboard.html", **build_dashboard_context())

    @flask_app.route("/balance", methods=["GET", "POST"])
    @login_required
    def balance():
        if request.method == "POST":
            institution = request.form.get("institution", "").strip()
            account_name = request.form.get("account_name", "").strip()
            account_type = request.form.get("account_type", "").strip() or "Checking"
            last_four = request.form.get("last_four", "").strip()

            try:
                starting_balance = to_decimal(request.form.get("balance", ""), "Balance")
                if len(institution) < 2 or len(account_name) < 2:
                    raise ValueError("Institution and account name must be at least 2 characters long.")
                if len(last_four) != 4 or not last_four.isdigit():
                    raise ValueError("Last four digits must contain exactly 4 numbers.")

                db.session.add(
                    Account(
                        user_id=current_user.id,
                        institution=institution,
                        account_name=account_name,
                        account_type=account_type,
                        last_four=last_four,
                        balance=starting_balance,
                    )
                )
                db.session.commit()
                flash("Account added successfully.", "success")
                return redirect(url_for("balance"))
            except ValueError as exc:
                flash(str(exc), "danger")

        accounts = Account.query.filter_by(user_id=current_user.id).order_by(Account.created_at.desc()).all()
        total_balance = sum((Decimal(str(account.balance)) for account in accounts), Decimal("0"))
        return render_template("balance.html", accounts=accounts, total_balance=total_balance)

    @flask_app.route("/transactions", methods=["GET", "POST"])
    @login_required
    def transactions():
        """Example route: add and list transactions using the database."""
        accounts = Account.query.filter_by(user_id=current_user.id).order_by(Account.account_name.asc()).all()
        categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name.asc()).all()

        if request.method == "POST":
            transaction_type = request.form.get("transaction_type", "").strip().lower()
            category_name = request.form.get("category", "").strip()
            description = request.form.get("description", "").strip()
            account_id = request.form.get("account_id", "").strip()

            try:
                if not accounts:
                    raise ValueError("Please add an account before recording transactions.")

                entry_date = parse_date(request.form.get("entry_date", ""), "Transaction date")
                amount = to_decimal(request.form.get("amount", ""), "Amount")
                if transaction_type not in {"income", "expense"}:
                    raise ValueError("Transaction type must be income or expense.")
                if len(category_name) < 2:
                    raise ValueError("Category must be at least 2 characters long.")
                if len(description) < 3:
                    raise ValueError("Description must be at least 3 characters long.")

                account = Account.query.filter_by(id=int(account_id), user_id=current_user.id).first()
                if not account:
                    raise ValueError("Please choose a valid account.")

                category = get_or_create_category(current_user.id, category_name)
                transaction = Transaction(
                    user_id=current_user.id,
                    account_id=account.id,
                    category_id=category.id,
                    entry_date=entry_date,
                    transaction_type=transaction_type,
                    amount=amount,
                    description=description,
                )
                update_account_balance(account, transaction_type, amount)
                db.session.add(transaction)
                db.session.commit()
                flash("Transaction recorded successfully.", "success")
                return redirect(url_for("transactions"))
            except ValueError as exc:
                db.session.rollback()
                flash(str(exc), "danger")

        transactions_list = (
            Transaction.query.filter_by(user_id=current_user.id)
            .order_by(Transaction.entry_date.desc(), Transaction.created_at.desc())
            .all()
        )
        return render_template(
            "transactions.html",
            transactions=transactions_list,
            accounts=accounts,
            categories=categories,
        )

    @flask_app.route("/delete_transaction/<int:transaction_id>", methods=["POST"])
    @login_required
    def delete_transaction(transaction_id: int):
        transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
        update_account_balance(transaction.account, transaction.transaction_type, Decimal(str(transaction.amount)), reverse=True)
        db.session.delete(transaction)
        db.session.commit()
        flash("Transaction deleted.", "info")
        return redirect(url_for("transactions"))

    @flask_app.route("/expenses")
    @login_required
    def expenses():
        transaction_rows = (
            Transaction.query.filter_by(user_id=current_user.id, transaction_type="expense")
            .order_by(Transaction.entry_date.desc(), Transaction.created_at.desc())
            .all()
        )

        expense_totals: dict[str, Decimal] = {}
        for row in transaction_rows:
            category_name = row.category.name if row.category else "Uncategorized"
            expense_totals[category_name] = expense_totals.get(category_name, Decimal("0")) + Decimal(str(row.amount))

        spending_by_category = sorted(expense_totals.items(), key=lambda entry: entry[1], reverse=True)
        total_expenses = sum((Decimal(str(item.amount)) for item in transaction_rows), Decimal("0"))
        return render_template(
            "expenses.html",
            spending_by_category=spending_by_category,
            transactions=transaction_rows,
            total_expenses=total_expenses,
        )

    @flask_app.route("/bills", methods=["GET", "POST"])
    @login_required
    def bills():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            category = request.form.get("category", "").strip()
            status = request.form.get("status", "Upcoming").strip()
            notes = request.form.get("notes", "").strip()

            try:
                amount = to_decimal(request.form.get("amount", ""), "Amount")
                due_date = parse_date(request.form.get("due_date", ""), "Due date")
                if len(title) < 2 or len(category) < 2:
                    raise ValueError("Title and category must be at least 2 characters long.")
                if status not in {"Upcoming", "Paid", "Overdue"}:
                    raise ValueError("Status must be Upcoming, Paid, or Overdue.")

                db.session.add(
                    Bill(
                        user_id=current_user.id,
                        title=title,
                        category=category,
                        amount=amount,
                        due_date=due_date,
                        status=status,
                        notes=notes,
                    )
                )
                db.session.commit()
                flash("Bill scheduled successfully.", "success")
                return redirect(url_for("bills"))
            except ValueError as exc:
                flash(str(exc), "danger")

        bills_list = Bill.query.filter_by(user_id=current_user.id).order_by(Bill.due_date.asc()).all()
        return render_template("bills.html", bills=bills_list)

    @flask_app.route("/delete_bill/<int:bill_id>", methods=["POST"])
    @login_required
    def delete_bill(bill_id: int):
        bill = Bill.query.filter_by(id=bill_id, user_id=current_user.id).first_or_404()
        db.session.delete(bill)
        db.session.commit()
        flash("Bill deleted.", "info")
        return redirect(url_for("bills"))

    @flask_app.route("/goals", methods=["GET", "POST"])
    @login_required
    def goals():
        if request.method == "POST":
            name = request.form.get("name", "").strip()

            try:
                target_amount = to_decimal(request.form.get("target_amount", ""), "Target amount")
                current_amount = to_decimal(request.form.get("current_amount", ""), "Current amount", allow_zero=True)
                due_date = parse_date(request.form.get("due_date", ""), "Target date")
                if len(name) < 2:
                    raise ValueError("Goal name must be at least 2 characters long.")
                if current_amount > target_amount:
                    raise ValueError("Current amount cannot exceed the target amount.")

                db.session.add(
                    SavingsGoal(
                        user_id=current_user.id,
                        name=name,
                        target_amount=target_amount,
                        current_amount=current_amount,
                        due_date=due_date,
                    )
                )
                db.session.commit()
                flash("Financial goal added successfully.", "success")
                return redirect(url_for("goals"))
            except ValueError as exc:
                flash(str(exc), "danger")

        goals_list = SavingsGoal.query.filter_by(user_id=current_user.id).order_by(SavingsGoal.due_date.asc()).all()
        return render_template("goals.html", goals=goals_list)

    @flask_app.route("/delete_goal/<int:goal_id>", methods=["POST"])
    @login_required
    def delete_goal(goal_id: int):
        goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
        db.session.delete(goal)
        db.session.commit()
        flash("Goal deleted.", "info")
        return redirect(url_for("goals"))


app = create_app()


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
