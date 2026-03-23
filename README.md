# IBANK — Multi-Branch Banking System

> A full-stack internet banking platform built with Django and raw SQL, designed for real-world multi-branch banking operations.

![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Database Design](#database-design)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [URL Routes](#url-routes)
- [Security](#security)
- [Contributing](#contributing)
- [Team](#team)

---

## Overview

**IBANK** is a comprehensive multi-branch banking management system that lets customers manage their finances entirely online. Built on Django with raw SQL queries and PostgreSQL, it emphasizes direct database control, transactional integrity, and security for real-world banking scenarios.

From account creation to cross-branch money transfers and loan management, all operations are handled securely through a unified web interface — without relying on Django ORM for data operations.

---

## Features

### Authentication
- **Secure Registration** — Validates username, email format, and password strength (minimum 8 characters, requires uppercase letter and digit)
- **Brute-Force Protection** — Accounts lock for 15 minutes after 5 consecutive failed login attempts
- **Session-based Auth** — Secure Django sessions throughout the user lifecycle

### Account Management
- Create multiple savings or current accounts per customer
- Link accounts to specific bank branches
- Deposit and withdrawal with balance validation and atomic writes

### Money Transfers
- Send money between any two active accounts
- Atomic SQL updates prevent simultaneous overdrafts and race conditions
- Both sender and recipient receive separate transaction records

### Transaction History
- Paginated view of all deposits, withdrawals, and transfers
- Filter by account, transaction type, and date range

### Beneficiary Management
- Save trusted recipient account details for repeated transfers
- IFSC format validation
- Duplicate prevention — cannot add the same account number twice

### Loan Management
- **Eligibility Checks** — Minimum balance of NPR 10,000 required across all active accounts
- **Loan-to-Balance Ratio** — Requested amount capped at 10× the user's total balance
- **Term Constraints** — Repayment window between 3 and 60 months
- **One Active Application** — Users are restricted to one active or pending loan at a time

### Automated Loan Decision Engine
| Condition | Outcome |
|---|---|
| Loan ≤ 500,000 + healthy minimum balance | ✅ Instant approval |
| Loan ≤ 2,000,000 + user holds ≥ 20% of loan value | ✅ Proportional approval |
| Falls outside above thresholds | ⏳ Routed to manual review |
| Balance or term limits not met | ❌ Rejected with specific feedback |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2, Python 3.9+ |
| Database | PostgreSQL 15, raw SQL via `connection.cursor()` |
| Auth | Django's built-in auth (password hashing, sessions) |
| Frontend | Django Templates, Bootstrap 5, Vanilla JS, Custom CSS |

**Why raw SQL?** This project deliberately avoids Django ORM for data operations to demonstrate direct database control, transparent query logic, and full understanding of SQL — important for academic and production contexts alike.

---

## Database Design

Tables are defined manually via `accounts/queries/schema.sql`. Django models exist only for the admin panel and serve as schema documentation.

### Entity Relationship Overview

```
auth_user (Django built-in)
    └── customer (1:1)
            ├── account (1:many) ──── branch (many:1)
            │       └── transaction (1:many)
            ├── loan (1:many) ──── branch (many:1)
            └── beneficiary (1:many)
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 15.x
- pip
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Muskan-Kandel/multi-branch-banking-system-database.git
cd multi-branch-banking-system-database
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL

```sql
CREATE DATABASE ibank_db;
CREATE USER ibank_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE ibank_db TO ibank_user;
```

### 5. Configure Environment Variables

Create a `.env` file inside the `bank_project/` directory:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DB_NAME=ibank_db
DB_USER=ibank_user
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

### 6. Apply Django Migrations

```bash
python manage.py migrate
```

### 7. Set Up the Database Schema

```bash
psql -U ibank_user -d ibank_db -f accounts/queries/schema.sql
```

### 8. Create a Superuser

```bash
python manage.py createsuperuser
```

### 9. Run the Development Server

```bash
python manage.py runserver
```

- App: [http://localhost:8000](http://localhost:8000)
- Admin panel: [http://localhost:8000/admin](http://localhost:8000/admin)

---

## Project Structure

```
multi-branch-banking-system-database/
│
├── accounts/                         # Main Django application
│   ├── migrations/                   # Django migrations (auth only)
│   ├── queries/
│   │   └── schema.sql                # Raw SQL table definitions
│   ├── templates/accounts/
│   │   └── login.html                # Auth-specific template
│   ├── admin.py                      # Admin panel registration
│   ├── models.py                     # Unmanaged models (admin use only)
│   ├── views.py                      # All application logic (raw SQL)
│   └── urls.py                       # URL routing
│
├── bank_project/                     # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── frontend/
│   ├── templates/                    # HTML templates
│   │   ├── IBANK.html                # Landing page
│   │   ├── base.html                 # Base layout
│   │   ├── dashboard.html
│   │   ├── loan.html
│   │   ├── accounts.html
│   │   ├── transactions.html
│   │   ├── beneficiaries.html
│   │   └── profile and settings.html
│   ├── static/
│   │   ├── style/                    # CSS files
│   │   └── script/                   # JavaScript files
│   └── extras/                       # Images and assets
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## URL Routes

| URL | View | Description |
|---|---|---|
| `/` | `IBANK` | Landing page |
| `/register/` | `register_view` | Customer registration |
| `/login/` | `login_view` | Login with lockout protection |
| `/logout/` | `logout_view` | Session logout |
| `/dashboard/` | `dashboard` | Customer dashboard |
| `/accounts/` | `accounts` | Account management |
| `/send-money/` | `send_money` | Money transfer |
| `/transactions/` | `transactions` | Full transaction history |
| `/beneficiaries/` | `beneficiaries` | Manage saved recipients |
| `/profile-and-settings/` | `profile_and_settings` | User profile |

---

## Security

| Feature | Implementation |
|---|---|
| Brute-force protection | Account locked for 15 min after 5 failed attempts |
| Password policy | Min 8 chars, requires uppercase + digit |
| CSRF protection | Enabled on all state-changing operations |
| SQL injection prevention | Parameterized queries (`%s` placeholders) throughout |
| Race condition prevention | `transaction.atomic()` on all transfers |
| Negative balance prevention | Database-level `CHECK (balance >= 0)` constraint |
| Route protection | `@login_required` on all banking views |
| Input validation | Server-side validation on all form fields |

---

## Contributing

Contributions are welcome. Please follow the steps below:

1. Fork the repository
2. Create a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Commit your changes
   ```bash
   git commit -m "Add: description of your feature"
   ```
4. Push to your branch
   ```bash
   git push origin feature/your-feature-name
   ```
5. Open a Pull Request

### Code Style Guidelines

- Follow PEP 8 for all Python code
- Use raw SQL for all database queries, consistent with the existing approach
- Wrap all multi-step database operations in `transaction.atomic()`
- Validate all user inputs server-side before executing SQL

---

## Team

| Name | GitHub |
|---|---|
| Muskan Kandel | [@Muskan-Kandel](https://github.com/Muskan-Kandel) |
| Abhishek Bhattarai | [@AbhishekBhattrai](https://github.com/AbhishekBhattrai) |
| Sneha Adhikari | [@Snehaa-28](https://github.com/Snehaa-28) |
