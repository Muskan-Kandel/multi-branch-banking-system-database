import re 
from django.shortcuts import redirect, render
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from django.contrib.auth.models import User
from django.db import transaction


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



def base_view(request):
    return render(request, 'base.html')

def IBANK(request):
    return render(request, 'IBANK.html')


# ============================================
#  REGISTER VIEW
# ============================================
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

        errors = []
        #Username can contain letters, numbers and @/./+/-/_ characters
        if not re.match(r'^[\w.@+-_]+$', username):
            errors.append('Username contains invalid characters!')
        
        #Mail should be in valid format
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append('Invalid email format!')

        if len(password1) < 8:
            errors.append('Password must be at least 8 characters!')

        if not re.search(r'[A-Z]', password1):
            errors.append('Password must contain at least one uppercase letter!')

        if not re.search(r'[0-9]', password1):
            errors.append('Password must contain at least one digit!')

        if password1 != password2:
            errors.append('Passwords do not match!')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'register.html')
        
        
        # Check if username already exists
        # with block auto closes the cursor after execution, ensuring proper resource management
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM auth_user WHERE username = %s", [username])
            if cursor.fetchone():
                messages.error(request, 'Username already exists!')
                return render(request, 'register.html')
        
        # Check if email already exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM auth_user WHERE email = %s", [email])
            if cursor.fetchone():
                messages.error(request, 'Email already registered!')
                return render(request, 'register.html')
        
        
        # Create user using Django's UserCreationForm for password hashing
        
        try:
            with transaction.atomic():
                #create django user( for password hashing and authentication)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Create customer record using raw SQL
                with connection.cursor() as cursor:
                    cursor.execute("""INSERT INTO customer (user_id, phone, address) VALUES (%s, %s, %s)""", [user.id, phone, address])
                
                # Log the user in
                login(request, user)
                messages.success(request, 'Registration successful! Welcome to IBANK!')
                return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error during registration: {str(e)}')
            return render(request, 'register.html')
    
    return render(request, 'register.html')  


# ============================================
# LOGIN VIEW
# ============================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')

        #check lockout status
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT c.failed_attempts, c.locked_until
            FROM customer c
            JOIN auth_user u ON c.user_id = u.id
            WHERE u.username = %s """, [username])
            row = cursor.fetchone()
        
        if row:
            failed_attempts, locked_until = row
            if locked_until and locked_until > datetime.now():
                messages.error(request, f'Account is locked until {locked_until.strftime("%Y-%m-%d %H:%M:%S")} due to multiple failed login attempts!')
                return render(request, 'login.html')

            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                
                # Reset failed attempts on successful login
                with connection.cursor() as cursor:
                    cursor.execute("""
                    UPDATE customer 
                    SET failed_attempts = 0, locked_until = NULL
                    WHERE user_id = %s
                    """, [user.id])
                
                login(request, user)
                return redirect('dashboard')
        
            else:
                with connection.cursor() as cursor:
                    cursor.execute("""
                    UPDATE customer 
                    SET failed_attempts = failed_attempts + 1,
                        locked_until = CASE 
                            WHEN failed_attempts >= 4 THEN NOW() + INTERVAL '15 MINUTE'
                            ELSE NULL
                        END
                    WHERE user_id = (
                                   SELECT id FROM auth_user WHERE username = %s)
                    """, [username])

                    messages.error(request, 'Invalid username or password!')
                    form = AuthenticationForm(request)

    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})   


# ============================================
# LOGOUT VIEW
# ============================================

def logout_view(request):
    logout(request)
    messages.success(request, "You've been logged out.")
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
    my_loans = execute_query(loans_query, [customer_id])
    
    context = {
        'customer': customer,
        'accounts': accounts,
        'total_balance': total_balance,
        'recent_transactions': recent_transactions,
        'account_count': len(accounts),
    }
    
    return render(request, 'dashboard.html', context)


# ============================================
# ACCOUNTS VIEW
# ============================================

@login_required
def accounts(request):
    user_id = request.user.id
    
    # Get customer ID
    customer_query = "SELECT id FROM customer WHERE user_id = %s"
    customer = execute_single(customer_query, [user_id])
    
    if not customer:
        messages.error(request, 'Customer profile not found!')
        return redirect('login')
    customer_id = customer['id']
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # CREATE NEW ACCOUNT
        if action == 'create_account':
            account_type = request.POST.get('account_type')
            branch_id = request.POST.get('branch_id')
            initial_balance = request.POST.get('initial_balance', 0)

            # Validate account type and initial balance
            VALID_ACCOUNT_TYPES = ['savings', 'current']
            if account_type not in VALID_ACCOUNT_TYPES:
                messages.error(request, 'Invalid account type selected!')
                return redirect('accounts')
            try:
                initial_balance = Decimal(initial_balance)
                if initial_balance < 0:
                    raise ValueError('Initial balance cannot be negative!')
            except (ValueError, InvalidOperation):
                messages.error(request, 'Invalid initial balance format.')
                return redirect('accounts')
            
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
            amount = request.POST.get('amount')
            description = request.POST.get('description', 'Deposit')

            # Validate amount
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    raise ValueError('Deposit amount must be positive!')
            except (ValueError, InvalidOperation) as e:
                messages.error(request, f'Invalid deposit amount: {str(e)}')
                return redirect('accounts')
            
            try:
                # Update account balance
                update_query = """
                    UPDATE account 
                    SET balance = balance + %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND customer_id = %s
                """
                 
                # Record transaction
                transaction_query = """
                    INSERT INTO transaction (account_id, transaction_type, amount, timestamp, description)
                    VALUES (%s, 'deposit', %s, CURRENT_TIMESTAMP, %s)
                """
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(update_query, [amount, account_id, customer_id])
                        cursor.execute(transaction_query, [account_id, amount, description])
                messages.success(request, f'Successfully deposited ${amount}!')

            except Exception as e:
                messages.error(request, f'Deposit failed: {str(e)}')
            
            return redirect('accounts')
        
        # WITHDRAW MONEY
        elif action == 'withdraw':
            account_id = request.POST.get('account_id')
            amount = Decimal(request.POST.get('amount'))
            description = request.POST.get('description', 'Withdrawal')

            # Validate withdrawal amount
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    raise ValueError('Withdrawal amount must be positive!')
            except (ValueError, InvalidOperation) as e:
                messages.error(request, f'Invalid withdrawal amount: {str(e)}')
                return redirect('accounts')
            
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
                    WHERE id = %s AND customer_id = %s AND balance >= %s
                """
                
                
                # Record transaction
                transaction_query = """
                    INSERT INTO transaction (account_id, transaction_type, amount, timestamp, description)
                    VALUES (%s, 'withdraw', %s, CURRENT_TIMESTAMP, %s)
                """
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(update_query, [amount, account_id, customer_id, amount])
                        cursor.execute(transaction_query, [account_id, amount, description])
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

    # If customer profile is not found, log out the user and redirect to login page
    if not customer:
        messages.error(request, 'Customer profile not found!')
        return redirect('login')
    customer_id = customer['id']
    
    if request.method == 'POST':
        from_account_id = request.POST.get('from_account')
        to_account_number = request.POST.get('to_account')
        amount = (request.POST.get('amount'))
        description = request.POST.get('description', 'Transfer')
        
        # Validate transfer amount
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError('Transfer amount must be positive!')
        except (ValueError, InvalidOperation) as e:
            messages.error(request, f'Invalid transfer amount: {str(e)}')
            return redirect('send money')
        
        # Prevent transferring to the same account
        if str(from_account_id) == str(to_account_number):
            messages.error(request, 'Cannot transfer to the same account!')
            return redirect('send money')
        
        try:
            with transaction.atomic():
                 with connection.cursor() as cursor:
                        
                    # Find recipient account by account number (using account ID as account number for simplicity)
                    cursor.execute("""
                        SELECT id, customer_id FROM account 
                        WHERE id = %s AND is_active = TRUE
                    """, [to_account_number])
                    
                    recipient = cursor.fetchone()
                    if not recipient:
                        messages.error(request, 'Recipient account not found!')
                        return redirect('send money')
                    
                    to_account_id = recipient[0]
                    
                    # Deduct from sender(atomic balance check + deduction to prevent race conditions)
                    cursor.execute("""
                        UPDATE account 
                        SET balance = balance - %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND customer_id = %s AND balance >= %s AND is_active = TRUE
                    """, [amount, from_account_id, customer_id, amount])
                    
                    if cursor.rowcount == 0:
                        messages.error(request, 'Transfer failed due to insufficient balance or inactive account!')
                        return redirect('send money')
                    
                    # Add to recipient
                    cursor.execute("""
                        UPDATE account 
                        SET balance = balance + %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND is_active = TRUE
                    """, [amount, to_account_id])

                    if cursor.rowcount == 0:
                        messages.error(request, 'Transfer failed: Recipient account not found or inactive!')
                        return redirect('send money')
                    
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
                    
                    messages.success(request, f'Successfully transferred NPR{amount}!')
                    return redirect('send money')
            
        except Exception as e:
            messages.error(request, f'Transfer failed: {str(e)}')
        return redirect('send money')
    
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

    # If customer profile is not found, log out the user and redirect to login page
    if not customer:
        messages.error(request, 'Customer profile not found!')
        return redirect('login')

    customer_id = customer['id']
    
    # Validate and get filter parameters
    
    account_filter = request.GET.get('account', '').strip()
    transaction_type = request.GET.get('type', '').strip()
    date_from = request.GET.get('from_date', '').strip()
    date_to = request.GET.get('to_date', '').strip()
    VALID_TRANSACTION_TYPES = ['deposit', 'withdraw', 'transfer']

    if transaction_type and transaction_type not in VALID_TRANSACTION_TYPES:
        messages.error(request, 'Invalid transaction type filter!')
        return redirect('transactions')
    
    if account_filter:
        try:
            account_filter = int(account_filter)
        except ValueError:
            messages.error(request, 'Invalid account filter!')
            return redirect('transactions')
        
    # Add pagination for large transaction history
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except ValueError:
        page = 1
    limit = 20
    offset = (page - 1) * limit

    
    # Base query
    query = """
        SELECT t.id, t.transaction_type, t.amount, t.timestamp, t.description,
               a.id as account_id, a.account_type, a.balance
        FROM transaction t
        INNER JOIN account a ON t.account_id = a.id
        WHERE a.customer_id = %s AND a.is_active = TRUE
    """
    params = [customer_id]
    
    # Add filters
    if account_filter:
        query += " AND a.id = %s"
        params.append(account_filter)
    
    if transaction_type:
        query += " AND t.transaction_type = %s"
        params.append(transaction_type)

    #add date range filter
    
    if date_from:
        query += " AND t.timestamp >= %s"
        params.append(date_from)

    if date_to:
        query += " AND t.timestamp <= %s"
        params.append(date_to)

    # Order by most recent and add pagination
    query += f" ORDER BY t.timestamp DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])  
    
    transactions_list = execute_query(query, params)
   
    # Get accounts for filter dropdown
    accounts_query = """
        SELECT id, account_type, balance 
        FROM account 
        WHERE customer_id = %s AND is_active = TRUE
    """
    accounts_list = execute_query(accounts_query, [customer_id])
    
    context = {
        'transactions': transactions_list,
        'accounts': accounts_list,
        'selected_account': str(account_filter),
        'selected_type': transaction_type,
        'from_date': date_from,
        'to_date': date_to,
        'page': page,
        'has_next': len(transactions_list) == limit,  # Simple check for next page
        'has_previous': page > 1,
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

    if not customer:
        messages.error(request, 'Customer profile not found!')
        return redirect('login')
    customer_id = customer['id']
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # ADD BENEFICIARY
        if action == 'add':
            name = request.POST.get('name').strip()
            account_number = request.POST.get('account_number').strip()
            bank_name = request.POST.get('bank_name').strip()
            

            if not all([name, account_number, bank_name]):
                messages.error(request, 'All beneficiary fields are required!')
                return redirect('beneficiaries')
            
            if len(name) > 100:
                messages.error(request, 'Beneficiary name cannot exceed 100 characters!')
                return redirect('beneficiaries')
            
            
            #check if beneficiary with same account number already exists for this customer
            existing_query = """
                SELECT id FROM beneficiary 
                WHERE customer_id = %s AND account_number = %s
            """
            existing_beneficiary = execute_single(existing_query, [customer_id, account_number])
            if existing_beneficiary:
                messages.error(request, f'Beneficiary with account number {account_number} already exists!')
                return redirect('beneficiaries')

            #insert new beneficiary
            query = """
                INSERT INTO beneficiary (customer_id, name, account_number, bank_name)
                VALUES (%s, %s, %s, %s)
            """
            try:
                execute_query(query, [customer_id, name, account_number, bank_name])
                messages.success(request, f'Beneficiary {name} added successfully!')
            except Exception as e:
                messages.error(request, f'Error adding beneficiary: {str(e)}')
        
        # DELETE BENEFICIARY
        elif action == 'delete':
            beneficiary_id = request.POST.get('beneficiary_id')
            # Validating beneficiary ID
            try:
                beneficiary_id = int(beneficiary_id)
            except (ValueError, TypeError):
                messages.error(request, 'Invalid beneficiary ID!')
                return redirect('beneficiaries')
            
            #Delete beneficiary 
            try:
                with connection.cursor() as cursor:
                    query = "DELETE FROM beneficiary WHERE id = %s AND customer_id = %s"
                    cursor.execute(query, [beneficiary_id, customer_id])
                    if cursor.rowcount == 0:
                        messages.error(request, 'Beneficiary not found or already deleted!')
                    else:
                        messages.success(request, 'Beneficiary deleted successfully!')
            except Exception as e:
                messages.error(request, f'Error deleting beneficiary: {str(e)}')  
        
        return redirect('beneficiaries')
    
    # GET request - display beneficiaries
    beneficiaries_query = """
        SELECT id, name, account_number, bank_name
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

from django.contrib.auth import update_session_auth_hash

@login_required
def profile_and_settings(request):
    user_id = request.user.id
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # UPDATE PROFILE
        if action == 'update_profile':
            phone = request.POST.get('phone', '').strip()
            address = request.POST.get('address', '').strip()

            if not phone and not address:
                messages.error(request, 'Please provide at least one field to update!')
                return redirect('profile and settings')
            
            if len(phone) > 15:
                messages.error(request, 'Invalid phone number!')
                return redirect('profile and settings')
            
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
            
            return redirect('profile and settings')

        # CHANGE PASSWORD
        elif action == 'change_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect!')
                return redirect('profile and settings')

            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match!')
                return redirect('profile and settings')

            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters!')
                return redirect('profile and settings')

            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile and settings')

        if not phone and not address:
            messages.error(request, 'Please provide at least one field to update!')
            return redirect('profile and settings')
        
        if len(phone) > 15:
            messages.error(request, 'Invalid phone number!')
            return redirect('profile and settings')
        
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
        
        return redirect('profile and settings')
    
    # GET request
    customer_query = """
        SELECT c.id, c.phone, c.address, 
               u.username, u.email, u.first_name, u.last_name, u.date_joined
        FROM customer c
        INNER JOIN auth_user u ON c.user_id = u.id
        WHERE c.user_id = %s
    """
    customer = execute_single(customer_query, [user_id])
    
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
        'transaction_count': transaction_stats['transaction_count'] if transaction_stats else 0,
    }
    
    return render(request, 'profile and settings.html', context)

# ============================================
# LOAN APPLICATION
# ============================================

@login_required
def apply_loan(request):
    user_id = request.user.id
    
    # Get customer ID
    customer_query = """
        SELECT id FROM customer 
        WHERE user_id = %s
    """
    customer = execute_single(customer_query, [user_id])

    # Customer account check
    if not customer:
        messages.error(request, 'Customer profile not found!')
        return redirect('login')
    customer_id = customer['id']

    if request.method == 'POST':
        amount = request.POST.get('amount')
        interest_rate = request.POST.get('interest_rate')
        branch_id = request.POST.get('branch_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Validate amount and interest rate
        try:
            amount = Decimal(amount)
            interest_rate = Decimal(interest_rate)

            if amount <= 0 or interest_rate <= 0:
                raise ValueError('All fields must be positive numbers!')
        except (ValueError, InvalidOperation) as e:
            messages.error(request, f'Invalid input: {str(e)}')
            return redirect('loan.html')
        
        #Validate dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            if start_date >= end_date:
                raise ValueError('End date must be after start date!')
            if start_date < date.today():
                raise ValueError('Start date must be in the future!')
        except ValueError as e:
            messages.error(request, f'Invalid date format : {str(e)}')
            return redirect('loan.html')

        query = """
            INSERT INTO loan (customer_id, branch_id, amount, interest_rate, start_date, end_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
        """
        try:
            execute_query(query, [customer_id, branch_id or None, amount, interest_rate, start_date, end_date])
            messages.success(request, 'Loan application submitted successfully! Status: Pending')
        except Exception as e:
            messages.error(request, f'Error applying for loan: {str(e)}')
            
        return redirect('loan.html')
    
    # GET request - display loan application form
    branches_query = """
        SELECT id, name, address FROM branch 
        ORDER BY name"""
    branches = execute_query(branches_query)

    # Get existing loans for display
    loans_query = """
        SELECT l.id, l.amount, l.interest_rate, l.start_date, l.end_date, l.status,
               b.name as branch_name
        FROM loan l
        LEFT JOIN branch b ON l.branch_id = b.id
        WHERE l.customer_id = %s
        ORDER BY l.start_date DESC
    """
    my_loans = execute_query(loans_query, [customer_id])
    
    context = {
        'branches': branches,
        'my_loans': my_loans,
    }
    
    return render(request, 'loan.html', context)

