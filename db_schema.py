from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from datetime import date

# Create database interface
db = SQLAlchemy()

# Model of a user for  database
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, unique=True)
    password_hash = db.Column(db.Text)
    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)

    def __init__(self, email, password_hash, first_name, last_name):
        self.email = email
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name


class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)

    def __init__(self, name):
        self.name = name


class User_Group(db.Model):
    __tablename__ = 'user_groups'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), primary_key=True)

    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id


class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    description = db.Column(db.Text)
    amount = db.Column(db.Float)
    category = db.Column(db.Text)
    date = db.Column(db.Date)
    status = db.Column(db.Text)

    def __init__(self, group_id, payer_id, description, amount, category, date, status):
        self.group_id = group_id
        self.payer_id = payer_id
        self.description = description
        self.amount = amount
        self.category = category
        self.date = date
        self.status = status


class Debt(db.Model):
    __tablename__ = 'debts'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    amount = db.Column(db.Float)
    settled = db.Column(db.Boolean)
    seen = db.Column(db.Boolean)

    def __init__(self, group_id, expense_id, user_id, amount, settled, seen):
        self.group_id = group_id
        self.expense_id = expense_id
        self.user_id = user_id
        self.amount = amount
        self.settled = settled
        self.seen = seen


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, db.ForeignKey('expenses.category'))
    icon = db.Column(db.Text)
    colour = db.Column(db.Text)

    def __init__(self, name, icon, colour):
        self.name = name
        self.icon = icon
        self.colour = colour
    

# Insert dummy data into tables
def dbinit():
    user_list = [
        User('jack@gmail.com', generate_password_hash('jack4'), 'Jack', 'Johnson'),
        User('john@gmail.com', generate_password_hash('john5'), 'John', 'Doe'),
        User('tom@gmail.com', generate_password_hash('tom6'), 'Thomas', 'Smith'),
        User('alex@gmail.com', generate_password_hash('alex7'), 'Alex', 'Jones')
    ]
    db.session.add_all(user_list)
    
    # Get ID of users
    jack_id = User.query.filter_by(email='jack@gmail.com').first().id
    john_id = User.query.filter_by(email='john@gmail.com').first().id
    tom_id = User.query.filter_by(email='tom@gmail.com').first().id

    # Create and add groups
    groups = [
        Group('Flat 71'),
        Group('Summer 2022'),
        Group('Leamington Flat')
    ]
    db.session.add_all(groups)

    # Get ID of groups
    flat71_id = Group.query.filter_by(name='Flat 71').first().id
    trip_id = Group.query.filter_by(name='Summer 2022').first().id
    leam_id = Group.query.filter_by(name='Leamington Flat').first().id

    # Create and add user-group associations
    user_groups = [
        User_Group(jack_id, flat71_id),
        User_Group(jack_id, trip_id),
        User_Group(john_id, flat71_id),
        User_Group(john_id, leam_id),
        User_Group(tom_id, flat71_id),
    ]
    db.session.add_all(user_groups)

    # Create and add expenses
    flat71_expenses = [
        Expense(flat71_id, tom_id,'Dinner', 30, 'Food', date.today(), 'Pending'),
        Expense(flat71_id, john_id, 'Uber', 12, 'Transport', date.today(), 'Pending'),
        Expense(flat71_id, jack_id,'Hotel deposit', 120, 'Housing', date.today(), 'Pending'),
        Expense(leam_id, john_id, 'Lunch', 10, 'Food', date.today(), 'Pending')
    ]
    db.session.add_all(flat71_expenses)

    # Get ID of expenses
    expense1_id = Expense.query.filter_by(description='Dinner').first().id
    expense2_id = Expense.query.filter_by(description='Uber').first().id
    expense3_id = Expense.query.filter_by(description='Hotel deposit').first().id
    expense4_id = Expense.query.filter_by(description='Lunch').first().id
    
    # Create and add debts
    flat71_debts = [
        Debt(flat71_id, expense1_id, jack_id, 10, False, False),
        Debt(flat71_id, expense1_id, john_id, 10, True, False),
        Debt(flat71_id, expense1_id, tom_id, 10, True, True),
        Debt(flat71_id, expense2_id, john_id, 4, False, False),
        Debt(flat71_id, expense2_id, jack_id, 4, False, False),
        Debt(flat71_id, expense2_id, tom_id, 4, True, True),
        Debt(flat71_id, expense3_id, jack_id, 20, True, False),
        Debt(flat71_id, expense3_id, tom_id, 60, False, True),
        Debt(flat71_id, expense3_id, john_id, 40, False, False),
        Debt(leam_id, expense4_id, john_id, 5, True, False)
    ]
    db.session.add_all(flat71_debts)

    # Commit all changes to database file
    db.session.commit()


# Insert category data (name, icon, colour)
def init_categories():
    
    categories = [
        Category('Housing', 'fas fa-home', '#ffa500'),
        Category('Utilities', 'fas fa-faucet', '#ffce56'),
        Category('Food', 'fas fa-utensils', '#a2de48'),
        Category('Transport', 'fas fa-bus', '#85cdff'),
        Category('Recreation', 'fas fa-gamepad', '#006eb9'),
        Category('Others', 'fas fa-coins', '#ca8dfd')
    ]
    db.session.add_all(categories)
    db.session.commit()