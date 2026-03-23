from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = Path(os.environ.get("PFMS_DATA_FILE", DATA_DIR / "store.json"))
COLLECTIONS = ("users", "accounts", "transactions", "bills", "goals")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


@dataclass
class User(UserMixin):
    id: str
    username: str
    email: str
    password_hash: str
    created_at: str


class JsonStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(self._empty_state())

    @staticmethod
    def _empty_state() -> dict[str, list[dict[str, Any]]]:
        return {name: [] for name in COLLECTIONS}

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        if not self.path.exists():
            return self._empty_state()
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def all(self, collection: str) -> list[dict[str, Any]]:
        return self._read().get(collection, [])

    def next_id(self, collection: str) -> str:
        rows = self.all(collection)
        if not rows:
            return "1"
        return str(max(int(row["id"]) for row in rows) + 1)

    def insert(self, collection: str, record: dict[str, Any]) -> dict[str, Any]:
        payload = self._read()
        payload.setdefault(collection, []).append(record)
        self._write(payload)
        return record

    def replace(self, collection: str, records: list[dict[str, Any]]) -> None:
        payload = self._read()
        payload[collection] = records
        self._write(payload)

    def delete(self, collection: str, record_id: str, *, user_id: str | None = None) -> bool:
        payload = self._read()
        original = payload.get(collection, [])
        filtered = [
            row
            for row in original
            if not (row.get("id") == record_id and (user_id is None or row.get("user_id") == user_id))
        ]
        removed = len(filtered) != len(original)
        if removed:
            payload[collection] = filtered
            self._write(payload)
        return removed


store = JsonStore(DATA_FILE)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    user_record = find_user_by_id(user_id)
    return user_from_record(user_record) if user_record else None


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


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


def currency(value: Decimal | float | int | str | None) -> str:
    numeric_value = Decimal(str(value or 0))
    return f"₹{numeric_value:,.2f}"


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def user_from_record(record: dict[str, Any]) -> User:
    return User(
        id=record["id"],
        username=record["username"],
        email=record["email"],
        password_hash=record["password_hash"],
        created_at=record["created_at"],
    )


def find_user_by_email(email: str) -> dict[str, Any] | None:
    return next((user for user in store.all("users") if user["email"] == email), None)


def find_user_by_id(user_id: str) -> dict[str, Any] | None:
    return next((user for user in store.all("users") if user["id"] == str(user_id)), None)


def records_for_user(collection: str, user_id: str) -> list[dict[str, Any]]:
    return [row for row in store.all(collection) if row.get("user_id") == str(user_id)]


def sort_by_date(records: list[dict[str, Any]], field_name: str, reverse: bool = False) -> list[dict[str, Any]]:
    return sorted(records, key=lambda row: (row.get(field_name, ""), row.get("created_at", "")), reverse=reverse)


@app.context_processor
def inject_helpers() -> dict[str, object]:
    return {"currency": currency, "today": date.today().isoformat()}


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
        if find_user_by_email(email):
            errors.append("An account with that email already exists.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html")

        store.insert(
            "users",
            {
                "id": store.next_id("users"),
                "username": username,
                "email": email,
                "password_hash": generate_password_hash(password),
                "created_at": now_iso(),
            },
        )
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
        user_record = find_user_by_email(email)

        if user_record and check_password_hash(user_record["password_hash"], password):
            login_user(user_from_record(user_record))
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
    user_id = str(current_user.id)
    accounts = sort_by_date(records_for_user("accounts", user_id), "created_at", reverse=True)
    transactions = sort_by_date(records_for_user("transactions", user_id), "entry_date", reverse=True)
    bills = sort_by_date(records_for_user("bills", user_id), "due_date")
    goals = sort_by_date(records_for_user("goals", user_id), "due_date")

    total_balance = sum((Decimal(item["balance"]) for item in accounts), Decimal("0"))
    total_income = sum(
        (Decimal(item["amount"]) for item in transactions if item["transaction_type"] == "income"),
        Decimal("0"),
    )
    total_expenses = sum(
        (Decimal(item["amount"]) for item in transactions if item["transaction_type"] == "expense"),
        Decimal("0"),
    )
    upcoming_bills = [bill for bill in bills if bill["due_date"] >= date.today().isoformat()][:5]

    expense_totals: dict[str, Decimal] = {}
    for item in transactions:
        if item["transaction_type"] != "expense":
            continue
        expense_totals[item["category"]] = expense_totals.get(item["category"], Decimal("0")) + Decimal(item["amount"])

    spending_by_category = sorted(
        ((category, decimal_string(amount)) for category, amount in expense_totals.items()),
        key=lambda entry: Decimal(entry[1]),
        reverse=True,
    )

    return {
        "accounts": accounts,
        "transactions": transactions,
        "bills": bills,
        "goals": goals,
        "total_balance": decimal_string(total_balance),
        "monthly_income": decimal_string(total_income),
        "monthly_expenses": decimal_string(total_expenses),
        "net_cash_flow": decimal_string(total_income - total_expenses),
        "upcoming_bills": upcoming_bills,
        "spending_by_category": spending_by_category,
        "storage_mode": "Local JSON file storage",
        "storage_path": str(DATA_FILE.relative_to(BASE_DIR)) if DATA_FILE.is_relative_to(BASE_DIR) else str(DATA_FILE),
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
        account_type = request.form.get("account_type", "").strip() or "Checking"
        last_four = request.form.get("last_four", "").strip()

        try:
            starting_balance = to_decimal(request.form.get("balance", ""), "Balance")
            if len(institution) < 2 or len(account_name) < 2:
                raise ValueError("Institution and account name must be at least 2 characters long.")
            if len(last_four) != 4 or not last_four.isdigit():
                raise ValueError("Last four digits must contain exactly 4 numbers.")

            store.insert(
                "accounts",
                {
                    "id": store.next_id("accounts"),
                    "user_id": str(current_user.id),
                    "institution": institution,
                    "account_name": account_name,
                    "account_type": account_type,
                    "last_four": last_four,
                    "balance": decimal_string(starting_balance),
                    "created_at": now_iso(),
                },
            )
            flash("Account added successfully.", "success")
            return redirect(url_for("balance"))
        except ValueError as exc:
            flash(str(exc), "danger")

    accounts = sort_by_date(records_for_user("accounts", str(current_user.id)), "created_at", reverse=True)
    total_balance = sum((Decimal(account["balance"]) for account in accounts), Decimal("0"))
    return render_template("balance.html", accounts=accounts, total_balance=decimal_string(total_balance))


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

            store.insert(
                "transactions",
                {
                    "id": store.next_id("transactions"),
                    "user_id": str(current_user.id),
                    "entry_date": entry_date.isoformat(),
                    "transaction_type": transaction_type,
                    "category": category,
                    "amount": decimal_string(amount),
                    "description": description,
                    "created_at": now_iso(),
                },
            )
            flash("Transaction recorded successfully.", "success")
            return redirect(url_for("transactions"))
        except ValueError as exc:
            flash(str(exc), "danger")

    transactions_list = sort_by_date(records_for_user("transactions", str(current_user.id)), "entry_date", reverse=True)
    return render_template("transactions.html", transactions=transactions_list)


@app.route("/delete_transaction/<record_id>", methods=["POST"])
@login_required
def delete_transaction(record_id: str):
    removed = store.delete("transactions", record_id, user_id=str(current_user.id))
    flash("Transaction deleted." if removed else "Transaction not found.", "info" if removed else "warning")
    return redirect(url_for("transactions"))


@app.route("/expenses")
@login_required
def expenses():
    transaction_rows = [
        row for row in records_for_user("transactions", str(current_user.id)) if row["transaction_type"] == "expense"
    ]
    transaction_rows = sort_by_date(transaction_rows, "entry_date", reverse=True)

    expense_totals: dict[str, Decimal] = {}
    for row in transaction_rows:
        expense_totals[row["category"]] = expense_totals.get(row["category"], Decimal("0")) + Decimal(row["amount"])

    spending_by_category = sorted(
        ((category, decimal_string(amount)) for category, amount in expense_totals.items()),
        key=lambda entry: Decimal(entry[1]),
        reverse=True,
    )
    total_expenses = sum((Decimal(item["amount"]) for item in transaction_rows), Decimal("0"))
    return render_template(
        "expenses.html",
        spending_by_category=spending_by_category,
        transactions=transaction_rows,
        total_expenses=decimal_string(total_expenses),
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

            store.insert(
                "bills",
                {
                    "id": store.next_id("bills"),
                    "user_id": str(current_user.id),
                    "title": title,
                    "category": category,
                    "amount": decimal_string(amount),
                    "due_date": due_date.isoformat(),
                    "status": status,
                    "notes": notes,
                    "created_at": now_iso(),
                },
            )
            flash("Bill scheduled successfully.", "success")
            return redirect(url_for("bills"))
        except ValueError as exc:
            flash(str(exc), "danger")

    bills_list = sort_by_date(records_for_user("bills", str(current_user.id)), "due_date")
    return render_template("bills.html", bills=bills_list)


@app.route("/delete_bill/<record_id>", methods=["POST"])
@login_required
def delete_bill(record_id: str):
    removed = store.delete("bills", record_id, user_id=str(current_user.id))
    flash("Bill deleted." if removed else "Bill not found.", "info" if removed else "warning")
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

            store.insert(
                "goals",
                {
                    "id": store.next_id("goals"),
                    "user_id": str(current_user.id),
                    "name": name,
                    "target_amount": decimal_string(target_amount),
                    "current_amount": decimal_string(current_amount),
                    "due_date": due_date.isoformat(),
                    "created_at": now_iso(),
                },
            )
            flash("Financial goal added successfully.", "success")
            return redirect(url_for("goals"))
        except ValueError as exc:
            flash(str(exc), "danger")

    goals_list = sort_by_date(records_for_user("goals", str(current_user.id)), "due_date")
    return render_template("goals.html", goals=goals_list)


@app.route("/delete_goal/<record_id>", methods=["POST"])
@login_required
def delete_goal(record_id: str):
    removed = store.delete("goals", record_id, user_id=str(current_user.id))
    flash("Goal deleted." if removed else "Goal not found.", "info" if removed else "warning")
    return redirect(url_for("goals"))


if __name__ == "__main__":
    app.run(debug=True)
