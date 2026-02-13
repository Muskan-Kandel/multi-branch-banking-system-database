# accounts/models.py

"""
UNMANAGED MODELS - Raw SQL Project
====================================
These models describe existing database tables but DO NOT manage them.
All tables are created manually using SQL scripts.

managed = False means:
- Django will NOT create these tables
- Django will NOT modify these tables  
- Django will NOT delete these tables
- Django CAN read from them (for Admin panel)

Your views.py uses RAW SQL queries - NOT these models.
These models are ONLY for Django Admin panel access.
"""

from django.db import models
from django.contrib.auth.models import User


# ============================================
# BRANCH TABLE
# ============================================
class Branch(models.Model):
    """
    Maps to SQL table: branch
    CREATE TABLE branch (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        address TEXT NOT NULL,
        contact_number VARCHAR(15) NOT NULL
    );
    """
    # id field is auto-created by Django
    name = models.CharField(max_length=100)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    
    class Meta:
        managed = False  # Don't let Django manage this table
        db_table = 'branch'  # Use existing 'branch' table in database
    
    def __str__(self):
        return self.name


# ============================================
# CUSTOMER TABLE
# ============================================
class Customer(models.Model):
    """
    Maps to SQL table: customer
    CREATE TABLE customer (
        id SERIAL PRIMARY KEY,
        user_id INTEGER UNIQUE NOT NULL,
        phone VARCHAR(15) NOT NULL,
        address TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES auth_user(id)
    );
    """
    # id field is auto-created by Django
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    
    class Meta:
        managed = False
        db_table = 'customer'
    
    def __str__(self):
        return f"{self.user.username} - {self.phone}"


# ============================================
# ACCOUNT TABLE
# ============================================
class Account(models.Model):
    """
    Maps to SQL table: account
    CREATE TABLE account (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        branch_id INTEGER,
        account_type VARCHAR(20) NOT NULL,
        balance NUMERIC(12,2) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (customer_id) REFERENCES customer(id),
        FOREIGN KEY (branch_id) REFERENCES branch(id)
    );
    """
    ACCOUNT_TYPE_CHOICES = [
        ('savings', 'Savings'),
        ('current', 'Current'),
    ]
    
    # id field is auto-created by Django
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        managed = False
        db_table = 'account'
    
    def __str__(self):
        return f"Account #{self.id} - {self.customer.user.username} ({self.account_type})"


# ============================================
# TRANSACTION TABLE
# ============================================
class Transaction(models.Model):
    """
    Maps to SQL table: transaction
    CREATE TABLE transaction (
        id SERIAL PRIMARY KEY,
        account_id INTEGER NOT NULL,
        transaction_type VARCHAR(20) NOT NULL,
        amount NUMERIC(12,2) NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        FOREIGN KEY (account_id) REFERENCES account(id)
    );
    """
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
        ('transfer', 'Transfer'),
    ]
    
    # id field is auto-created by Django
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'transaction'
        ordering = ['-timestamp']  # Show newest first
    
    def __str__(self):
        return f"{self.transaction_type.upper()} - ${self.amount} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


# ============================================
# LOAN TABLE
# ============================================
class Loan(models.Model):
    """
    Maps to SQL table: loan
    CREATE TABLE loan (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        branch_id INTEGER,
        amount NUMERIC(15,2) NOT NULL,
        interest_rate NUMERIC(5,2) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        FOREIGN KEY (customer_id) REFERENCES customer(id),
        FOREIGN KEY (branch_id) REFERENCES branch(id)
    );
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed'),
    ]
    
    # id field is auto-created by Django
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        managed = False
        db_table = 'loan'
    
    def __str__(self):
        return f"Loan #{self.id} - {self.customer.user.username} - ${self.amount} ({self.status})"


# ============================================
# BENEFICIARY TABLE
# ============================================
class Beneficiary(models.Model):
    """
    Maps to SQL table: beneficiary
    CREATE TABLE beneficiary (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        name VARCHAR(100) NOT NULL,
        account_number VARCHAR(20) NOT NULL,
        bank_name VARCHAR(100) NOT NULL,
        ifsc_code VARCHAR(11) NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customer(id)
    );
    """
    # id field is auto-created by Django
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)
    ifsc_code = models.CharField(max_length=11)
    
    class Meta:
        managed = False
        db_table = 'beneficiary'
        verbose_name_plural = 'Beneficiaries'  # Correct plural form
    
    def __str__(self):
        return f"{self.name} - {self.bank_name} (A/C: {self.account_number})"


# ============================================
# IMPORTANT NOTES
# ============================================
"""
1. ALL models have managed = False
   - This means Django will NEVER create, modify, or delete these tables
   - You control the tables with manual SQL scripts

2. db_table specifies the exact table name in your database
   - Must match your SQL CREATE TABLE statements

3. These models are ONLY used for:
   - Django Admin panel (viewing/editing data)
   - Documentation (showing table structure)
   
4. Your views.py DOES NOT use these models
   - All queries in views.py use raw SQL with cursor.execute()
   
5. Foreign Keys are defined to show relationships
   - Helps Django Admin display related data nicely
   - Does NOT create foreign key constraints (managed = False)

6. __str__ methods make admin panel readable
   - Shows meaningful names instead of "Account object (1)"
"""