# Database Reference

This file replaces the old binary `db.docx` document with a Git-friendly text version.

## Database engine

The project uses SQLite through Flask-SQLAlchemy with the URI:

```text
sqlite:///pfms.db
```

## Tables

### users
- `id` - primary key
- `username` - user display name
- `email` - unique login email
- `password_hash` - hashed password
- `created_at` - account creation timestamp

### accounts
- `id` - primary key
- `user_id` - foreign key to `users.id`
- `institution` - bank/provider name
- `account_name` - account label
- `account_type` - checking/savings/etc.
- `balance` - current tracked balance
- `last_four` - masked account/card ending digits
- `created_at` - creation timestamp

### categories
- `id` - primary key
- `user_id` - foreign key to `users.id`
- `name` - category name
- `created_at` - creation timestamp

### transactions
- `id` - primary key
- `user_id` - foreign key to `users.id`
- `account_id` - foreign key to `accounts.id`
- `category_id` - foreign key to `categories.id`
- `entry_date` - transaction date
- `transaction_type` - income or expense
- `amount` - transaction amount
- `description` - notes/description
- `created_at` - creation timestamp

### bills
- `id` - primary key
- `user_id` - foreign key to `users.id`
- `title` - bill title
- `category` - bill category label
- `amount` - amount due
- `due_date` - due date
- `status` - upcoming/paid/overdue
- `notes` - optional notes
- `created_at` - creation timestamp

### savings_goals
- `id` - primary key
- `user_id` - foreign key to `users.id`
- `name` - goal name
- `target_amount` - target amount
- `current_amount` - saved amount so far
- `due_date` - target date
- `created_at` - creation timestamp

## Relationships

- One user has many accounts.
- One user has many categories.
- One user has many transactions.
- One account has many transactions.
- One category has many transactions.
- One user has many bills.
- One user has many savings goals.

## Source of truth

The current schema is implemented in `models.py`. If the models change, update this file as well.
