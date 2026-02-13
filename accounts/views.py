from django.shortcuts import redirect, render
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from decimal import Decimal
from datetime import datetime

# ============================================
# HELPER FUNCTIONS FOR DATABASE OPERATIONS
# ============================================

def execute_query(query, params=None):
    """Execute a query and return results for SELECT statements"""
    cursor = connection.cursor()
    try:
        cursor.execute(query, params or [])
        if query.strip().upper().startswith('SELECT'):
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        connection.commit()
        return None
    except Exception as e:
        print(f"Database Error: {e}")
        connection.rollback()
        raise e
    finally:
        cursor.close()

def execute_single(query, params=None):
    """Execute query and return single row"""
    cursor = connection.cursor()
    try:
        cursor.execute(query, params or [])
        if query.strip().upper().startswith('SELECT'):
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        connection.commit()
        return None
    except Exception as e:
        print(f"Database Error: {e}")
        connection.rollback()
        raise e
    finally:
        cursor.close()

# ============================================
# AUTHENTICATION VIEWS
# ============================================

def base_view(request):
    return render(request, 'base.html')

def IBANK(request):
    return render(request, 'IBANK.html')



def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'register.html')
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long!')
            return render(request, 'register.html')
        
        # Check if username already exists
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM auth_user WHERE username = %s", [username])
        if cursor.fetchone():
            cursor.close()
            messages.error(request, 'Username already exists!')
            return render(request, 'register.html')
        
        # Check if email already exists
        cursor.execute("SELECT id FROM auth_user WHERE email = %s", [email])
        if cursor.fetchone():
            cursor.close()
            messages.error(request, 'Email already registered!')
            return render(request, 'register.html')
        
        cursor.close()
        
        # Create user using Django's UserCreationForm for password hashing
        from django.contrib.auth.models import User
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create customer record using raw SQL
            query = """
                INSERT INTO customer (user_id, phone, address)
                VALUES (%s, %s, %s)
            """
            execute_query(query, [user.id, phone, address])
            
            # Log the user in
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to IBANK!')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error during registration: {str(e)}')
            return render(request, 'register.html')
    
    return render(request, 'register.html')  

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            print(form.errors)
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})   

def logout_view(request):
    logout(request)
    return redirect('login')

# ============================================
# DASHBOARD VIEW
# ============================================

@login_required
def dashboard(request):
    user_id = request.user.id
    
    # Get customer details
    customer_query = """
        SELECT c.id, c.phone, c.address, u.username, u.email, u.first_name, u.last_name
        FROM customer c
        INNER JOIN auth_user u ON c.user_id = u.id
        WHERE c.user_id = %s
    """
    customer = execute_single(customer_query, [user_id])
    
    if not customer:
        messages.error(request, 'Customer profile not found!')
        return redirect('login')
    
    customer_id = customer['id']
    
    # Get all accounts for this customer
    accounts_query = """
        SELECT a.id, a.account_type, a.balance, a.created_at, a.is_active,
               b.name as branch_name, b.address as branch_address
        FROM account a
        LEFT JOIN branch b ON a.branch_id = b.id
        WHERE a.customer_id = %s AND a.is_active = TRUE
        ORDER BY a.created_at DESC
    """
    accounts = execute_query(accounts_query, [customer_id])
    
    # Calculate total balance
    total_balance = sum(Decimal(acc['balance']) for acc in accounts)
    
    # Get recent transactions (last 5)
    transactions_query = """
        SELECT t.id, t.transaction_type, t.amount, t.timestamp, t.description,
               a.account_type
        FROM transaction t
        INNER JOIN account a ON t.account_id = a.id
        WHERE a.customer_id = %s
        ORDER BY t.timestamp DESC
        LIMIT 5
    """
    recent_transactions = execute_query(transactions_query, [customer_id])
    
    # Get active loans
    loans_query = """
        SELECT l.id, l.amount, l.interest_rate, l.start_date, l.end_date, l.status,
               b.name as branch_name
        FROM loan l
        LEFT JOIN branch b ON l.branch_id = b.id
        WHERE l.customer_id = %s AND l.status IN ('pending', 'approved')
        ORDER BY l.start_date DESC
    """
    loans = execute_query(loans_query, [customer_id])
    
    context = {
        'customer': customer,
        'accounts': accounts,
        'total_balance': total_balance,
        'recent_transactions': recent_transactions,
        'loans': loans,
        'account_count': len(accounts),
    }
    
    return render(request, 'dashboard.html', context)

# ============================================
# ACCOUNTS MANAGEMENT
# ============================================

@login_required
def accounts(request):
    user_id = request.user.id
    
    # Get customer ID
    customer_query = "SELECT id FROM customer WHERE user_id = %s"
    customer = execute_single(customer_query, [user_id])
    customer_id = customer['id']
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # CREATE NEW ACCOUNT
        if action == 'create_account':
            account_type = request.POST.get('account_type')
            branch_id = request.POST.get('branch_id')
            initial_balance = request.POST.get('initial_balance', 0)
            
            query = """
                INSERT INTO account (customer_id, branch_id, account_type, balance, created_at, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            try:
                execute_query(query, [customer_id, branch_id or None, account_type, initial_balance])
                messages.success(request, f'{account_type.capitalize()} account created successfully!')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
            
            return redirect('accounts')
        
        # DEPOSIT MONEY
        elif action == 'deposit':
            account_id = request.POST.get('account_id')
            amount = Decimal(request.POST.get('amount'))
            description = request.POST.get('description', 'Deposit')
            
            try:
                # Update account balance
                update_query = """
                    UPDATE account 
                    SET balance = balance + %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND customer_id = %s
                """
                execute_query(update_query, [amount, account_id, customer_id])
                
                # Record transaction
                transaction_query = """
                    INSERT INTO transaction (account_id, transaction_type, amount, timestamp, description)
                    VALUES (%s, 'deposit', %s, CURRENT_TIMESTAMP, %s)
                """
                execute_query(transaction_query, [account_id, amount, description])
                
                messages.success(request, f'Successfully deposited ${amount}!')
            except Exception as e:
                messages.error(request, f'Deposit failed: {str(e)}')
            
            return redirect('accounts')
        
        # WITHDRAW MONEY
        elif action == 'withdraw':
            account_id = request.POST.get('account_id')
            amount = Decimal(request.POST.get('amount'))
            description = request.POST.get('description', 'Withdrawal')
            
            try:
                # Check balance
                balance_query = "SELECT balance FROM account WHERE id = %s AND customer_id = %s"
                account = execute_single(balance_query, [account_id, customer_id])
                
                if Decimal(account['balance']) < amount:
                    messages.error(request, 'Insufficient balance!')
                    return redirect('accounts')
                
                # Update account balance
                update_query = """
                    UPDATE account 
                    SET balance = balance - %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND customer_id = %s
                """
                execute_query(update_query, [amount, account_id, customer_id])
                
                # Record transaction
                transaction_query = """
                    INSERT INTO transaction (account_id, transaction_type, amount, timestamp, description)
                    VALUES (%s, 'withdraw', %s, CURRENT_TIMESTAMP, %s)
                """
                execute_query(transaction_query, [account_id, amount, description])
                
                messages.success(request, f'Successfully withdrawn ${amount}!')
            except Exception as e:
                messages.error(request, f'Withdrawal failed: {str(e)}')
            
            return redirect('accounts')
    
    # GET request - display accounts
    accounts_query = """
        SELECT a.id, a.account_type, a.balance, a.created_at, a.is_active,
               b.name as branch_name, b.id as branch_id
        FROM account a
        LEFT JOIN branch b ON a.branch_id = b.id
        WHERE a.customer_id = %s
        ORDER BY a.created_at DESC
    """
    accounts_list = execute_query(accounts_query, [customer_id])
    
    # Get all branches for dropdown
    branches_query = "SELECT id, name, address FROM branch ORDER BY name"
    branches = execute_query(branches_query)
    
    context = {
        'accounts': accounts_list,
        'branches': branches,
    }
    
    return render(request, 'accounts.html', context)

# ============================================
# SEND MONEY / TRANSFER
# ============================================

@login_required
def send_money(request):
    user_id = request.user.id
    
    # Get customer ID
    customer_query = "SELECT id FROM customer WHERE user_id = %s"
    customer = execute_single(customer_query, [user_id])
    customer_id = customer['id']
    
    if request.method == 'POST':
        from_account_id = request.POST.get('from_account')
        to_account_number = request.POST.get('to_account')
        amount = Decimal(request.POST.get('amount'))
        description = request.POST.get('description', 'Transfer')
        
        try:
            cursor = connection.cursor()
            
            # Check sender's balance
            cursor.execute("""
                SELECT balance FROM account 
                WHERE id = %s AND customer_id = %s
            """, [from_account_id, customer_id])
            
            sender_account = cursor.fetchone()
            if not sender_account:
                messages.error(request, 'Invalid account!')
                return redirect('send_money')
            
            if Decimal(sender_account[0]) < amount:
                messages.error(request, 'Insufficient balance!')
                return redirect('send_money')
            
            # Find recipient account by account number (using account ID as account number for simplicity)
            cursor.execute("""
                SELECT id, customer_id FROM account WHERE id = %s
            """, [to_account_number])
            
            recipient = cursor.fetchone()
            if not recipient:
                messages.error(request, 'Recipient account not found!')
                return redirect('send_money')
            
            to_account_id = recipient[0]
            
            # Deduct from sender
            cursor.execute("""
                UPDATE account 
                SET balance = balance - %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, [amount, from_account_id])
            
            # Add to recipient
            cursor.execute("""
                UPDATE account 
                SET balance = balance + %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, [amount, to_account_id])
            
            # Record sender's transaction
            cursor.execute("""
                INSERT INTO transaction (account_id, transaction_type, amount, timestamp, description)
                VALUES (%s, 'transfer', %s, CURRENT_TIMESTAMP, %s)
            """, [from_account_id, amount, f'Transfer to Account #{to_account_id}: {description}'])
            
            # Record recipient's transaction
            cursor.execute("""
                INSERT INTO transaction (account_id, transaction_type, amount, timestamp, description)
                VALUES (%s, 'deposit', %s, CURRENT_TIMESTAMP, %s)
            """, [to_account_id, amount, f'Transfer from Account #{from_account_id}: {description}'])
            
            connection.commit()
            cursor.close()
            
            messages.success(request, f'Successfully transferred ${amount}!')
            return redirect('send_money')
            
        except Exception as e:
            connection.rollback()
            messages.error(request, f'Transfer failed: {str(e)}')
            return redirect('send_money')
    
    # GET request
    accounts_query = """
        SELECT id, account_type, balance 
        FROM account 
        WHERE customer_id = %s AND is_active = TRUE
    """
    my_accounts = execute_query(accounts_query, [customer_id])
    
    context = {
        'my_accounts': my_accounts,
    }
    
    return render(request, 'send money.html', context)

# ============================================
# TRANSACTIONS HISTORY
# ============================================

@login_required
def transactions(request):
    user_id = request.user.id
    
    # Get customer ID
    customer_query = "SELECT id FROM customer WHERE user_id = %s"
    customer = execute_single(customer_query, [user_id])
    customer_id = customer['id']
    
    # Get filter parameters
    account_filter = request.GET.get('account', '')
    transaction_type = request.GET.get('type', '')
    
    # Base query
    query = """
        SELECT t.id, t.transaction_type, t.amount, t.timestamp, t.description,
               a.id as account_id, a.account_type, a.balance
        FROM transaction t
        INNER JOIN account a ON t.account_id = a.id
        WHERE a.customer_id = %s
    """
    params = [customer_id]
    
    # Add filters
    if account_filter:
        query += " AND a.id = %s"
        params.append(account_filter)
    
    if transaction_type:
        query += " AND t.transaction_type = %s"
        params.append(transaction_type)
    
    query += " ORDER BY t.timestamp DESC LIMIT 50"
    
    transactions_list = execute_query(query, params)
    
    # Get accounts for filter dropdown
    accounts_query = """
        SELECT id, account_type, balance 
        FROM account 
        WHERE customer_id = %s
    """
    accounts_list = execute_query(accounts_query, [customer_id])
    
    context = {
        'transactions': transactions_list,
        'accounts': accounts_list,
        'selected_account': account_filter,
        'selected_type': transaction_type,
    }
    
    return render(request, 'transactions.html', context)

# ============================================
# BENEFICIARIES MANAGEMENT
# ============================================

@login_required
def beneficiaries(request):
    user_id = request.user.id
    
    # Get customer ID
    customer_query = "SELECT id FROM customer WHERE user_id = %s"
    customer = execute_single(customer_query, [user_id])
    customer_id = customer['id']
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # ADD BENEFICIARY
        if action == 'add':
            name = request.POST.get('name')
            account_number = request.POST.get('account_number')
            bank_name = request.POST.get('bank_name')
            ifsc_code = request.POST.get('ifsc_code')
            
            query = """
                INSERT INTO beneficiary (customer_id, name, account_number, bank_name, ifsc_code)
                VALUES (%s, %s, %s, %s, %s)
            """
            try:
                execute_query(query, [customer_id, name, account_number, bank_name, ifsc_code])
                messages.success(request, f'Beneficiary {name} added successfully!')
            except Exception as e:
                messages.error(request, f'Error adding beneficiary: {str(e)}')
        
        # DELETE BENEFICIARY
        elif action == 'delete':
            beneficiary_id = request.POST.get('beneficiary_id')
            
            query = "DELETE FROM beneficiary WHERE id = %s AND customer_id = %s"
            try:
                execute_query(query, [beneficiary_id, customer_id])
                messages.success(request, 'Beneficiary deleted successfully!')
            except Exception as e:
                messages.error(request, f'Error deleting beneficiary: {str(e)}')
        
        return redirect('beneficiaries')
    
    # GET request - display beneficiaries
    beneficiaries_query = """
        SELECT id, name, account_number, bank_name, ifsc_code
        FROM beneficiary
        WHERE customer_id = %s
        ORDER BY name
    """
    beneficiaries_list = execute_query(beneficiaries_query, [customer_id])
    
    context = {
        'beneficiaries': beneficiaries_list,
    }
    
    return render(request, 'beneficiaries.html', context)

# ============================================
# PROFILE AND SETTINGS
# ============================================

@login_required
def profile_and_settings(request):
    user_id = request.user.id
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # UPDATE PROFILE
        if action == 'update_profile':
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            
            query = """
                UPDATE customer 
                SET phone = %s, address = %s
                WHERE user_id = %s
            """
            try:
                execute_query(query, [phone, address, user_id])
                messages.success(request, 'Profile updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
        
        return redirect('profile_and_settings')
    
    # GET request
    customer_query = """
        SELECT c.id, c.phone, c.address, 
               u.username, u.email, u.first_name, u.last_name, u.date_joined
        FROM customer c
        INNER JOIN auth_user u ON c.user_id = u.id
        WHERE c.user_id = %s
    """
    customer = execute_single(customer_query, [user_id])
    
    # Get account statistics
    stats_query = """
        SELECT 
            COUNT(*) as total_accounts,
            SUM(balance) as total_balance,
            COUNT(CASE WHEN account_type = 'savings' THEN 1 END) as savings_accounts,
            COUNT(CASE WHEN account_type = 'current' THEN 1 END) as current_accounts
        FROM account
        WHERE customer_id = %s AND is_active = TRUE
    """
    stats = execute_single(stats_query, [customer['id']])
    
    # Get transaction count
    transaction_count_query = """
        SELECT COUNT(*) as transaction_count
        FROM transaction t
        INNER JOIN account a ON t.account_id = a.id
        WHERE a.customer_id = %s
    """
    transaction_stats = execute_single(transaction_count_query, [customer['id']])
    
    context = {
        'customer': customer,
        'stats': stats,
        'transaction_count': transaction_stats['transaction_count'],
    }
    
    return render(request, 'profile and settings.html', context)