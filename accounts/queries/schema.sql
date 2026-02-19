-- branch table
--------------------------------
CREATE TABLE branch (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    contact_number VARCHAR(15) NOT NULL
);
-- account table
--------------------------------
CREATE TABLE account (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    branch_id INTEGER,
    account_type VARCHAR(20) NOT NULL,
    balance NUMERIC(12,2) DEFAULT 0 CHECK (balance >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    CONSTRAINT fk_account_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_account_branch
        FOREIGN KEY (branch_id)
        REFERENCES branch(id)
        ON DELETE SET NULL,

    CONSTRAINT chk_account_type
        CHECK (account_type IN ('savings', 'current'))
);

---customer table
--------------------------------
CREATE TABLE customer (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    address TEXT NOT NULL,

    CONSTRAINT fk_customer_user
        FOREIGN KEY (user_id)
        REFERENCES auth_user(id)
        ON DELETE CASCADE
);

-- transaction table
--------------------------------
CREATE TABLE transaction (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,

    CONSTRAINT fk_transaction_account
        FOREIGN KEY (account_id)
        REFERENCES account(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_transaction_type
        CHECK (transaction_type IN ('deposit', 'withdraw', 'transfer'))
);

-- loan table
--------------------------------
CREATE TABLE loan (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    branch_id INTEGER,
    amount NUMERIC(15,2) NOT NULL CHECK (amount > 0),
    interest_rate NUMERIC(5,2) NOT NULL CHECK (interest_rate > 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',

    CONSTRAINT fk_loan_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_loan_branch
        FOREIGN KEY (branch_id)
        REFERENCES branch(id)
        ON DELETE SET NULL,

    CONSTRAINT chk_loan_status
        CHECK (status IN ('pending', 'approved', 'rejected', 'closed'))
);

--beneficiary table
--------------------------------
CREATE TABLE beneficiary (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    account_number VARCHAR(20) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    ifsc_code VARCHAR(11) NOT NULL,

    CONSTRAINT fk_beneficiary_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer(id)
        ON DELETE CASCADE
);

--alter customer table
--------------------------------
ALTER TABLE customer
ADD COLUMN failed_attempts INTEGER DEFAULT 0,
ADD COLUMN locked_until TIMESTAMP NULL;
