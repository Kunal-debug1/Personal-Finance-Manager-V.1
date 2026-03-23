from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "finance_manager.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{DATABASE_PATH}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    institution = db.Column(db.String(120), nullable=False)
    account_name = db.Column(db.String(120), nullable=False)
    account_type = db.Column(db.String(40), nullable=False)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    last_four = db.Column(db.String(4), nullable=False, default="0000")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    entry_date = db.Column(db.Date, nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Upcoming")
    notes = db.Column(db.String(255), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    target_amount = db.Column(db.Numeric(12, 2), nullable=False)
    current_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    due_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))


def to_decimal(raw_value: str, field_name: str, *, allow_zero: bool = False) -> Decimal:
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
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.")


def currency(value: Decimal | float | int | None) -> str:
    numeric_value = Decimal(value or 0)
    return f"₹{numeric_value:,.2f}"


@app.context_processor
def inject_helpers() -> dict[str, object]:
    return {"currency": currency, "today": date.today()}


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
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

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully. Please sign in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
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


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


def build_dashboard_context() -> dict[str, object]:
    accounts = (
        Account.query.filter_by(user_id=current_user.id)
        .order_by(Account.created_at.desc())
        .all()
    )
    transactions = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.entry_date.desc(), Transaction.created_at.desc())
        .all()
    )
    bills = (
        Bill.query.filter_by(user_id=current_user.id)
        .order_by(Bill.due_date.asc())
        .all()
    )
    goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.due_date.asc()).all()

    total_balance = sum((Decimal(account.balance) for account in accounts), Decimal("0"))
    monthly_income = sum(
        (Decimal(item.amount) for item in transactions if item.transaction_type == "income"),
        Decimal("0"),
    )
    monthly_expenses = sum(
        (Decimal(item.amount) for item in transactions if item.transaction_type == "expense"),
        Decimal("0"),
    )
    upcoming_bills = [bill for bill in bills if bill.due_date >= date.today()][:5]

    spending_by_category = (
        db.session.query(Transaction.category, func.sum(Transaction.amount))
        .filter_by(user_id=current_user.id, transaction_type="expense")
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    return {
        "accounts": accounts,
        "transactions": transactions,
        "bills": bills,
        "goals": goals,
        "total_balance": total_balance,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "net_cash_flow": monthly_income - monthly_expenses,
        "upcoming_bills": upcoming_bills,
        "spending_by_category": spending_by_category,
    }


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", **build_dashboard_context())


@app.route("/balance", methods=["GET", "POST"])
@login_required
def balance():
    if request.method == "POST":
        institution = request.form.get("institution", "").strip()
        account_name = request.form.get("account_name", "").strip()
        account_type = request.form.get("account_type", "").strip()
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
                    account_type=account_type or "Checking",
                    balance=starting_balance,
                    last_four=last_four,
                )
            )
            db.session.commit()
            flash("Account added successfully.", "success")
            return redirect(url_for("balance"))
        except ValueError as exc:
            flash(str(exc), "danger")

    accounts = (
        Account.query.filter_by(user_id=current_user.id)
        .order_by(Account.created_at.desc())
        .all()
    )
    total_balance = sum((Decimal(account.balance) for account in accounts), Decimal("0"))
    return render_template("balance.html", accounts=accounts, total_balance=total_balance)


@app.route("/transactions", methods=["GET", "POST"])
@login_required
def transactions():
    if request.method == "POST":
        transaction_type = request.form.get("transaction_type", "").strip().lower()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()

        try:
            entry_date = parse_date(request.form.get("entry_date", ""), "Transaction date")
            amount = to_decimal(request.form.get("amount", ""), "Amount")
            if transaction_type not in {"income", "expense"}:
                raise ValueError("Transaction type must be income or expense.")
            if len(category) < 2:
                raise ValueError("Category must be at least 2 characters long.")
            if len(description) < 3:
                raise ValueError("Description must be at least 3 characters long.")

            db.session.add(
                Transaction(
                    user_id=current_user.id,
                    entry_date=entry_date,
                    transaction_type=transaction_type,
                    category=category,
                    amount=amount,
                    description=description,
                )
            )
            db.session.commit()
            flash("Transaction recorded successfully.", "success")
            return redirect(url_for("transactions"))
        except ValueError as exc:
            flash(str(exc), "danger")

    transactions_list = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.entry_date.desc(), Transaction.created_at.desc())
        .all()
    )
    return render_template("transactions.html", transactions=transactions_list)


@app.route("/delete_transaction/<int:transaction_id>", methods=["POST"])
@login_required
def delete_transaction(transaction_id: int):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    flash("Transaction deleted.", "info")
    return redirect(url_for("transactions"))


@app.route("/expenses")
@login_required
def expenses():
    spending_by_category = (
        db.session.query(Transaction.category, func.sum(Transaction.amount))
        .filter_by(user_id=current_user.id, transaction_type="expense")
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )
    transactions_list = (
        Transaction.query.filter_by(user_id=current_user.id, transaction_type="expense")
        .order_by(Transaction.entry_date.desc())
        .all()
    )
    total_expenses = sum((Decimal(item.amount) for item in transactions_list), Decimal("0"))
    return render_template(
        "expenses.html",
        spending_by_category=spending_by_category,
        transactions=transactions_list,
        total_expenses=total_expenses,
    )


@app.route("/bills", methods=["GET", "POST"])
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


@app.route("/delete_bill/<int:bill_id>", methods=["POST"])
@login_required
def delete_bill(bill_id: int):
    bill = Bill.query.filter_by(id=bill_id, user_id=current_user.id).first_or_404()
    db.session.delete(bill)
    db.session.commit()
    flash("Bill deleted.", "info")
    return redirect(url_for("bills"))


@app.route("/goals", methods=["GET", "POST"])
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
                Goal(
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

    goals_list = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.due_date.asc()).all()
    return render_template("goals.html", goals=goals_list)


@app.route("/delete_goal/<int:goal_id>", methods=["POST"])
@login_required
def delete_goal(goal_id: int):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    flash("Goal deleted.", "info")
    return redirect(url_for("goals"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
