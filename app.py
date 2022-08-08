from flask import Flask, render_template, request, redirect, flash, url_for
from sqlalchemy import text, func
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from markupsafe import escape
from datetime import datetime
from json import loads
from db_schema import Category, db, User, Group, User_Group, Expense, Debt, dbinit, init_categories

app = Flask(__name__)

# Randomly generated with os.urandom(12).hex()
app.secret_key = 'ad11416739cbc31e3be75212'

# Select the database filename
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sharebill.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialise the database so it can connect with our app
db.init_app(app)

# Avoid resetting the database every time this app is restarted
resetdb = False

# Drop everything, create all tables, insert dummy data
if resetdb:
    with app.app_context():        
        db.drop_all()
        db.create_all()
        dbinit()
        init_categories()

# Create database and categories table
else:
    with app.app_context():        
        db.drop_all()
        db.create_all()
        init_categories()


# Set up flask login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = None

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Allows users to register for an account
@app.route('/register', methods=['GET', 'POST'])
def register():

    logout_user()

    if request.method == 'POST':

        # Get form data
        first_name = escape(request.form.get('first_name'))
        last_name = escape(request.form.get('last_name'))
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirmation = request.form.get('password_confirmation')

        # Ensure full name was entered
        if not first_name or not last_name:
            error = 'Please enter your full name'

        # Ensure email was entered
        elif not email:
            error = 'Please enter your email'

        # Ensure password was entered
        elif not password:
            error = 'Please enter a valid password'
        
        # Ensure email does not exist
        elif User.query.filter_by(email=email).first() is not None:
            error = 'Email address is already in use'

        # Ensure passwords match
        elif password != password_confirmation:
            error = 'Passwords do not match'

        # Insert new user into database and redirect to login page
        else:
            user = User(email, generate_password_hash(password), first_name.capitalize(), last_name.capitalize())
            db.session.add(user)
            db.session.commit()
            return redirect('/login')

        return render_template('register.html', error=error)
    
    # Request method is GET
    else:
        return render_template('register.html')


# Logs user in if credentials are valid
@app.route('/login', methods=['GET', 'POST'])
def login():

    # Logout user if previously logged in before this page
    logout_user()

    if request.method == 'POST':
        
        # Get form data
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Find user with this email
        user = User.query.filter_by(email=email).first()

        # Check if user with email does not exist or if password is incorrect
        if user is None or not check_password_hash(user.password_hash, password):
                error = 'Incorrect email/password'
                return render_template('login.html', error=error)
        
        # Log user in
        else:
            login_user(user)
            return redirect('/')
    
    # Request method is GET
    else:
        return render_template('login.html')


# Logs user out
@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


# Displays dashboard with relevant data for current user
@app.route('/')
@login_required
def index():
    
    # Get list of current user's groups for sidebar
    groups = db.session.query(Group).join(User_Group).filter(User_Group.user_id==current_user.id).all()

    # Get list of user's group IDs, formatted appropriately for SQL query
    if len(groups) == 1:
        group_ids = str((0, groups[0].id))
    else:
        group_ids = str(tuple([group.id for group in groups]))

    # Get total expenditure per group that the user is a member of
    qrytext = text(
        "SELECT groups.id, groups.name, SUM(expenses.amount) as amount \
        FROM groups JOIN expenses ON groups.id = expenses.group_id WHERE groups.id IN " + group_ids + "\
        GROUP BY groups.name ORDER BY amount DESC;")
    expenses_grouped = db.session.execute(qrytext).fetchall()

    # Get user's total amount of debt and credit
    debt_amount = Debt.query.with_entities(func.sum(Debt.amount).label('debt')).filter(Debt.user_id==current_user.id, Debt.settled==False).first().debt
    credit_amount = db.session.query(Debt).with_entities(func.sum(Debt.amount).label('credit')).join(Expense).filter(Expense.payer_id==current_user.id, Debt.settled==False).first().credit
    
    # Compute current user's balance
    if debt_amount is None: debt_amount = 0
    if credit_amount is None: credit_amount = 0
    balance = credit_amount - debt_amount

    # Get all of the user's current and unseen debts
    all_debts = db.session.query(Debt, Expense).join(Expense).filter(Debt.user_id==current_user.id, Debt.settled==False).order_by(Debt.id.desc()).all()
    new_debts = [debt for debt in all_debts if debt[0].seen==False]
    
    # Flash notification with number of new debts
    if new_debts:
        if len(new_debts) == 1:
            flash('You have 1 new pending debt')
        else:
            flash('You have {} new pending debts'.format(len(new_debts)))

    rendered = render_template('index.html', groups=groups, expenses_grouped=expenses_grouped, debt_amount=debt_amount, credit_amount=credit_amount, balance=balance, all_debts=all_debts)
    
    # Mark all unseen debts as seen
    for debt in new_debts:
        debt[0].seen = True
    db.session.commit()
    
    return rendered


# Displays expense/debt data for a given group
@app.route('/group-<int:group_id>')
@login_required
def group(group_id):

    # Get list of current user's groups for sidebar
    groups = db.session.query(Group).join(User_Group).filter(User_Group.user_id==current_user.id).all()
    
    # Redirect user to dashboard if they are not part of this group
    if group_id not in (group.id for group in groups):
        return redirect('/')

    # Get data for current group
    current_group = Group.query.filter_by(id=group_id).first()
    categories = Category.query.all()
    expenses = db.session.query(Expense, Category).join(Category).filter(Expense.group_id==group_id).order_by(Expense.date.desc(), Expense.id.desc()).all()
    debts = Debt.query.filter_by(group_id=group_id).all()
    members = db.session.query(User).join(User_Group).filter(User_Group.group_id==group_id).all()

    # Get sum of expenses per category with corresponding icons/colours
    qrytext = text(
        "SELECT expenses.category, SUM(expenses.amount) as amount_categorised, categories.icon, categories.colour \
        FROM expenses JOIN categories ON expenses.category = categories.name WHERE expenses.group_id =:group_id \
        GROUP BY expenses.category ORDER BY amount_categorised DESC;")
    qry = qrytext.bindparams(group_id=group_id)
    expenses_categorised = db.session.execute(qry).fetchall()

    # Get total amount spent by group for 
    total_amount = sum(category.amount_categorised for category in expenses_categorised)
    
    return render_template('group.html', groups=groups, group=current_group, categories=categories, expenses=expenses, 
        debts=debts, members=members, expenses_categorised=expenses_categorised, total_amount=total_amount)


# Creates a new group with data from JS (AJAX)
@app.route('/create_group', methods=['POST'])
@login_required
def create_group():
    
    # Get form data
    group_name = request.form.get('group_name')
    
    # Ensure a group name was entered
    if len(group_name) == 0:
        return 'Please enter a group name'

    else:
        # Create new group, add to database
        new_group = Group(group_name)
        db.session.add(new_group)
        db.session.commit()
    
        # Create new association between current user and new group
        user_group = User_Group(current_user.id, new_group.id)
        db.session.add(user_group)
        db.session.commit()

        return ''


# Adds a member to a group with data from JS (AJAX)
@app.route('/add_member', methods=['POST'])
@login_required
def add_member():

    # Get form data
    email = request.form.get('email')
    group_id = request.form.get('group_id')

    # Get user with corresponding email
    user = User.query.filter_by(email=email).first()

    # Ensure user to be added has an account
    if user is None:
        return 'No account is associated with this email'
    
    # Ensure user to be added is not already a part of this group
    elif User_Group.query.filter_by(user_id=user.id, group_id=group_id).first() is not None:
        return 'User is already a member of this group'

    # Add member to group, return data to JS
    else:
        member_group = User_Group(user.id, group_id)
        db.session.add(member_group)
        db.session.commit()
        return {'id' : user.id, 'name' : user.first_name}


# Adds new expense with data from JS (AJAX)
@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():

    # Get form data
    payer_id = request.form.get('payer_id')
    group_id = request.form.get('group_id')
    description = request.form.get('description')
    amount = request.form.get('amount')
    category = request.form.get('category')
    date = request.form.get('date')
    split_option1 = request.form.get('split_option1')
    split_option2 = request.form.get('split_option2')
    debtor_ids = loads(request.form.get('debtor_ids'))
    debtor_amounts = loads(request.form.get('debtor_amounts'))

    # Get all members in current group
    members = db.session.query(User).join(User_Group).filter(User_Group.group_id==group_id).all()

    # Ensure payer was selected
    if payer_id == 'none':
        return 'Please select the payer of the expense'

    # Ensure description was entered
    elif not description:
        return 'Please enter a description'

    # Ensure amount was entered
    elif not amount:
        return 'Please enter a valid amount'

    # Ensure category was entered
    elif not category:
        return 'Please select a category'
    
    # Ensure date was entered
    elif not date:
        return 'Please enter a date'

    # Convert numeric value from string to float
    amount = float(amount)

    # Insert new expense into database
    expense = Expense(group_id, payer_id, description, amount, category, datetime.strptime(date, '%Y-%m-%d'), 'Pending')
    db.session.add(expense)
    
    new_debts = []

    # Split bill equally between all group members
    if split_option1 == 'split-equally':

        # Commit new expense to database
        db.session.commit()
        
        # Store new debts for each selected member, calculating amounts owed
        for member in members:
            new_debts.append(Debt(group_id, expense.id, member.id, (amount/len(members)), False, False))
    
    # Reject expense if no debtors were selected
    elif len(debtor_ids) == 0:
        return 'No group members selected'
    
    # If expense is to be split equally between a subset of members
    elif split_option2 == 'equal':

        # Commit new expense to database
        db.session.commit()
        
        # Store new debts for each selected member, calculating amounts owed
        for id in debtor_ids:
            new_debts.append(Debt(group_id, expense.id, id, (amount/len(debtor_ids)), False, False))

    # If expense is to be split by amounts
    elif split_option2 == 'amount':

        # Ensure amounts paid by selected members were entered
        if (len(debtor_ids) != len(debtor_amounts)):
            return 'Please enter the amounts paid by selected members'
        
        # Convert numeric values from strings to floats
        debtor_amounts = [float(x) for x in debtor_amounts]

        # Ensure the total paid by selected group members matches the expense amount
        if (sum(debtor_amounts) != amount):
            return 'Sum of amounts must equal total amount spent'
        
        # Commit new expense to database
        db.session.commit()

        # Combine debt data into single list of tuples
        debt_info = list(zip(debtor_ids, debtor_amounts))

        # Store new debts for each selected member with amounts entered in form
        for id, amt in debt_info:
            new_debts.append(Debt(group_id, expense.id, id, amt, False, False))
    
    # If expense is to be split by percentages
    elif split_option2 == 'percentage':

        # Ensure percentages paid by selected members were entered
        if (len(debtor_ids) != len(debtor_amounts)):
            return 'Please enter the amounts paid by selected members'
        
        # Convert numeric values from strings to floats
        debtor_amounts = [float(x) for x in debtor_amounts]

        # Ensure the sum of the percentages is exactly 100
        if (sum(debtor_amounts) != 100):
            return 'Sum of percentages must equal 100%'
        
        # Combine debt data into single list of tuples
        debt_info = list(zip(debtor_ids, debtor_amounts))
        
        # Commit new expense to database
        db.session.commit()

        # Store new debts for each selected member, calculating amounts owed
        for id, percentage in debt_info:
            new_debts.append(Debt(group_id, expense.id, id, ((percentage/100)*amount), False, False))

    # Insert new debts into database
    db.session.add_all(new_debts)

    # Mark the expense payer's debt as settled if it exists
    payer_debt = Debt.query.filter_by(expense_id=expense.id, user_id=payer_id).first()
    if payer_debt is not None:
        payer_debt.settled = True
    
    # Mark expense as settled if the only debtor is the payer
    if (len(debtor_ids) == 1) and (debtor_ids[0] == payer_id):
        expense.status = 'Settled'
    
    db.session.commit()

    return ""


# Deletes expense and associated debts when delete button is pressed
@app.route('/delete_expense/<int:group_id>/<int:expense_id>')
@login_required
def delete_expense(group_id, expense_id):

    # Get list of current user's groups
    groups = db.session.query(Group).join(User_Group).filter(User_Group.user_id==current_user.id).all()
    
    # Redirect user to dashboard if they are not part of this group
    if group_id not in (group.id for group in groups):
        return redirect('/')

    # Delete expense from database
    expense = Expense.query.filter_by(id=expense_id).first()
    db.session.delete(expense)

    # Delete all debts associated with expense from database
    debts = Debt.query.filter_by(expense_id=expense_id).all()
    for debt in debts:
        db.session.delete(debt)

    db.session.commit()
        
    # Reload page to update expense data (i.e. expenditure by categories)
    return redirect(url_for('group', group_id=group_id))


# Marks a given debt as settled/pending with data from JS (AJAX)
@app.route('/settle_debt', methods=['POST'])
@login_required
def settle_debt():
    
    # Get debt data
    debt_id = request.form.get('debt_id')
    expense_id = request.form.get('expense_id')
    
    # Update status of debt in database
    debt = Debt.query.filter_by(id=debt_id).first()
    debt.settled = not debt.settled
    db.session.commit()

    # Get expense corresponding to given debt
    expense = Expense.query.filter_by(id=expense_id).first()

    # Update expense status if all debts have been paid
    if len(Debt.query.filter_by(expense_id=expense_id, settled=False).all()) == 0:
        expense.status = 'Settled'
    else:
        expense.status = 'Pending'

    db.session.commit()

    return expense.status