# Multi-Branch Banking System

> A full-stack, production-ready internet banking platform built with Django and raw SQL, designed for real-world multi-branch banking operations.

<div align="center">

![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)


# Hosted Application

![Live Dmeo](https://multi-branch-banking-system-database.onrender.com) 


</div>

---

## Table of Contents

<details open>
<summary>Click to navigate</summary>

- [Overview](#overview)
- [Problem and Solution](#problem-and-solution)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Database Design](#database-design)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [URL Routes](#url-routes)
- [Security Features](#security-features)
- [Contributing](#contributing)
- [Development Team](#development-team)

</details>

---

## Overview

**IBANK** is a comprehensive multi-branch banking management system that enables customers to manage their finances entirely online. Built on Django with raw SQL queries and PostgreSQL, it emphasizes direct database control, transactional integrity, and security for real-world banking scenarios.

From account creation to cross-branch money transfers, all operations are handled securely through a unified web interface.

---

## Problem and Solution

| Challenge | Solution |
|-----------|----------|
| Manual branch-based banking | Unified online portal accessible across all branches |
| No real-time transaction records | Full transaction history with filtering and pagination |
| Insecure login systems | Account lockout after repeated failed login attempts |
| ORM abstraction over SQL complexity | Raw SQL queries for full, transparent database control |
| Race conditions in concurrent transfers | Atomic transactions to prevent double-spending |

---

## Key Features

### Authentication
- **Secure Registration** — Validates username, email format, and password strength (uppercase letter and digit required)
- **Login with Lockout** — Tracks failed attempts and locks the account for 15 minutes after 5 consecutive failures
- **Session-based Authentication** — Secure Django sessions maintained throughout the user session

### Account Management
- **Multi-Account Support** — Create multiple savings or current accounts per customer
- **Branch Assignment** — Link accounts to specific bank branches
- **Deposit and Withdrawal** — With balance validation and atomic database writes

### Money Transfers
- **Inter-Account Transfers** — Send money between any two active accounts
- **Race Condition Protection** — Atomic SQL updates prevent simultaneous overdrafts
- **Dual Transaction Logging** — Both sender and recipient receive separate transaction records

### Transaction History
- **Full History** — Paginated view of all deposits, withdrawals, and transfers
- **Filters** — Filter by account, transaction type, and date range

### Beneficiary Management
- **Save Recipients** — Store trusted beneficiary account details for repeated transfers
- **IFSC Validation** — Basic format checking for bank codes
- **Duplicate Prevention** — Prevents adding the same account number more than once

### Profile and Settings
- **Profile Updates** — Update phone number and address
- **Account Statistics** — View total balance, account counts, and transaction totals

---

## Tech Stack

**Backend**
- Django 4.2
- PostgreSQL 15
- Raw SQL via `connection.cursor()`
- Django Auth for password hashing
- Django Sessions

**Frontend**
- Django Templates (HTML)
- Bootstrap 5
- Vanilla JavaScript
- Custom CSS

---

## Database Design

This project uses raw SQL for all data operations. Tables are created manually using the schema file — Django models are defined only for the Admin panel and serve as documentation of the schema.

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

## Prerequisites

Before you begin, ensure the following are installed:

- Python 3.9 or higher
- PostgreSQL 15.x
- pip
- Git

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Muskan-Kandel/Multi-Branch-Banking-System-DataBase.git
cd Multi-Branch-Banking-System-DataBase
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

### 4. Configure PostgreSQL

```sql
CREATE DATABASE ibank_db;
CREATE USER ibank_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE ibank_db TO ibank_user;
```

### 5. Configure Environment Variables

Create a `.env` file in the `bank_project/` directory:

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

### 9. Start the Development Server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000` and the admin panel at `http://localhost:8000/admin`.

---

## Project Structure

```
Multi-Branch-Banking-System-DataBase/
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
│   ├── settings.py                   # Application settings
│   ├── urls.py                       # Root URL configuration
│   ├── wsgi.py                       # WSGI configuration
│   └── asgi.py                       # ASGI configuration
│
├── frontend/
│   ├── templates/                    # HTML templates
│   │   ├── IBANK.html                # Landing page
│   │   ├── base.html                 # Base layout
│   │   ├── login.html                # Login page
│   │   ├── register.html             # Registration page
│   │   ├── dashboard.html            # Customer dashboard
│   │   ├── accounts.html             # Account management
│   │   ├── send money.html           # Transfer page
│   │   ├── transactions.html         # Transaction history
│   │   ├── beneficiaries.html        # Beneficiary management
│   │   └── profile and settings.html # Profile page
│   ├── static/
│   │   ├── style/                    # CSS files
│   │   └── script/                   # JavaScript files
│   └── extras/                       # Images and assets
│
├── manage.py                         # Django CLI
└── README.md                         # Project documentation
```

---

## URL Routes

| URL | View | Description |
|-----|------|-------------|
| `/` | `IBANK` | Landing page |
| `/register/` | `register_view` | Customer registration |
| `/login/` | `login_view` | Login with lockout protection |
| `/logout/` | `logout_view` | Logout |
| `/dashboard/` | `dashboard` | Customer dashboard |
| `/accounts/` | `accounts` | Account management and transactions |
| `/send money/` | `send_money` | Money transfer |
| `/transactions/` | `transactions` | Full transaction history |
| `/beneficiaries/` | `beneficiaries` | Manage saved recipients |
| `/profile and settings/` | `profile_and_settings` | User profile |

---

## Security Features

- **Brute-Force Protection** — Account locked for 15 minutes after 5 failed login attempts
- **Password Strength Enforcement** — Minimum 8 characters, requires at least one uppercase letter and one digit
- **CSRF Protection** — Enabled for all state-changing operations
- **Atomic Transactions** — All transfers use `transaction.atomic()` to prevent race conditions and double-spending
- **Input Validation** — Server-side validation on all form fields including types, lengths, and formats
- **Parameterized SQL** — All raw queries use `%s` placeholders to prevent SQL injection
- **Login Required** — All banking views are protected with the `@login_required` decorator
- **Balance Constraint** — Database-level `CHECK (balance >= 0)` prevents negative balances

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
- Use raw SQL for all database queries, consistent with the existing project approach
- Wrap all multi-step database operations in `transaction.atomic()`
- Validate all user inputs server-side before executing SQL

---

## Development Team

| Name | GitHub |
|------|--------|
| Abhishek Bhattarai | [github.com/](https://github.com/AbhishekBhattrai) |
| Muskan Kandel | [github.com/Muskan-Kandel](https://github.com/Muskan-Kandel) |
| Sneha Adhikari | [github.com/snehaadhikari005](https://github.com/Snehaa-28) |


---



