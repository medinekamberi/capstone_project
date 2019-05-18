from flask import Flask, request, jsonify,render_template, flash , redirect, url_for, session, logging, json, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow #is an ORM/ODM/framework-agnostic library for converting complex datatypes, such as objects, to and from native Python datatypes.
from flask_cors import CORS,cross_origin
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import exc
from functools import wraps
import jwt
import os #python module deals with file path
import datetime

#Init app
app = Flask(__name__)
#Setup sqlalchemy database URI
basedir= os.path.abspath(os.path.dirname(__file__))
#Database
app.config['SECRET_KEY'] = 'mySecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://test:test@localhost/testapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app)
#Init db
db= SQLAlchemy(app)
marshmallow= Marshmallow(app)

#User class/Model, model gives some predefined methods
class User(db.Model):
    id= db.Column(db.Integer(),primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    surname=db.Column(db.String(64))
    email=db.Column(db.String(64), unique=True)
    password=db.Column(db.String(256))
    role= db.Column(db.String(64))
    active=db.Column(db.Boolean)
    created_at=db.Column(db.DateTime)
    updated_at=db.Column(db.DateTime)
    accounts=db.relationship('Account', backref='user', lazy=True)
    def __init__(self,name,surname,email,password,role,active,created_at,updated_at):
        self.name=name
        self.surname=surname
        self.email=email
        self.password=password
        self.role=role
        self.active=active
        self.created_at=created_at
        self.updated_at=updated_at

#User schema
class UserSchema(marshmallow.Schema):
    class Meta:
        fields=('name','surname','email','password','role','active','created_at','updated_at')
#Init schema 
user_schema=UserSchema(strict=True)
users_schema = UserSchema(many=True, strict=True)
#Class Account
class Account(db.Model):
    id= db.Column(db.Integer(),primary_key=True, autoincrement=True)
    balance=db.Column(db.Float(8))
    currency=db.Column(db.String(5))
    created_at=db.Column(db.DateTime)
    updated_at=db.Column(db.DateTime)
    transactions=db.relationship('Transaction', backref='account', lazy=True)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    def __init__(self,balance,currency,created_at,updated_at, user_id):
        self.balance=balance
        self.currency=currency
        self.created_at=created_at
        self.updated_at=updated_at
        self.user_id=user_id

#Account Schema
class AccountSchema(marshmallow.Schema):
    class Meta:
        fields=('id','balance','currency','created_at','updated_at', 'user_id')

#init account schema
account_schema=AccountSchema(strict=True)
accounts_schema=AccountSchema(many=True, strict= True)
#Class Category
class Category(db.Model):
    id=db.Column(db.Integer(), primary_key=True, autoincrement=True)
    title=db.Column(db.String(64))
    def __init__(self,title):
        self.title=title

#Category Schema
class CategorySchema(marshmallow.Schema):
    class Meta:
        fields=('id','title')

category_schema=CategorySchema(strict=True)
categories_schema= CategorySchema(many=True, strict=True)
#Create table Transaction, Transaction/Model
class Transaction(db.Model):
    id=db.Column(db.Integer(),primary_key=True, autoincrement=True)
    title=db.Column(db.String(32))
    amount= db.Column(db.Float(8))
    transaction_type=db.Column(db.String(64))
    created_at=db.Column(db.DateTime)
    updated_at=db.Column(db.DateTime)
    account_id=db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    def __init__(self,title,amount,transaction_type,created_at,updated_at, account_id):
        self.title=title
        self.amount=amount
        self.transaction_type=transaction_type
        self.created_at=created_at
        self.updated_at=updated_at
        self.account_id=account_id

#Transaction Schema
class TransactionSchema(marshmallow.Schema):
    class Meta:
        fields=('id','title','amount','transaction_type','created_at','updated_at', 'account_id')

#Init schema
transaction_schema=TransactionSchema(strict=True)
transactions_schema= TransactionSchema(many=True, strict=True)

@app.route('/')
def index():
    return render_template('index.html')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message' : 'Token is missing'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(id=data['id']).first()
        except:
            return jsonify({'message' : 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated
#Create a user
@app.route('/users',methods=['POST'])
def create_user():
    name=request.json['name']
    surname=request.json['surname']
    email=request.json['email']
    # password=request.json['password']
    password = generate_password_hash(request.json['password'], method='sha256')
    role=request.json['role']
    active=request.json['active']
    created_at=datetime.datetime.now()
    updated_at=datetime.datetime.now()
    new_user= User(name,surname,email,password,role,active,created_at,updated_at)
    
    db.session.add(new_user)
    try:
        db.session.commit()
    except exc.SQLAlchemyError:
        print('something happened')
        return json.dumps({'error': 'duplicate user', 'status': 409})
    return user_schema.jsonify(new_user)

#Get all users
@app.route('/users', methods=['GET'])
@token_required
def get_users(current_user):
    all_users = User.query.all()
    result = users_schema.dump(all_users)

    return jsonify(result.data)
#Get user by ID
@app.route('/users/<id>', methods=['GET'])
@token_required
def get_user(current_user,id):
    user= User.query.get(id)
    return user_schema.jsonify(user)

#Delete user by ID
@app.route('/users/<id>', methods=['DELETE'])
@token_required
def delete_user(current_user,id):
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    
    return user_schema.jsonify(user)
#Update a user
@app.route('/users/<id>', methods=['PUT'])
@token_required
def update_user(current_user,id):
    user = User.query.get(id)
    print(user)
    name=request.json['name']
    surname=request.json['surname']
    email=request.json['email']
    password=request.json['password']
    role=request.json['role']
    active=request.json['active']
    accounts=request.json['accounts']
    
    user.name=name
    user.surname=surname
    user.email=email
    user.password=password
    user.role=role
    user.active=active
    user.accounts=accounts

    db.session.commit()

    return user_schema.jsonify(user)
#login method
@app.route('/login')
def login():
    auth = request.authorization
    
    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})
    user = User.query.filter_by(email=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})
    if check_password_hash(user.password, auth.password):
        token= jwt.encode({'id' : user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        return jsonify({'token' :token.decode('UTF-8')})
    return make_response('Could not verify', 401, {'WWW-Authentication' : 'Basic realm="Login required!'})


#Create an account
@app.route('/accounts', methods=['POST'])
def create_account():
    balance = 0
    currency=request.json['currency']
    created_at=datetime.datetime.now()
    updated_at=datetime.datetime.now()
    user_id=request.json['user_id']
    
    new_account=Account(balance,currency, created_at, updated_at,user_id)
    
    db.session.add(new_account)
    db.session.commit()
    
    return account_schema.jsonify(new_account)

#Get all accounts
@app.route('/accounts', methods=['GET'])
def get_accounts():
    all_accounts = Account.query.all()
    result = accounts_schema.dump(all_accounts)
    
    return jsonify(result.data)

#Get account by id
@app.route('/accounts/<id>', methods=['GET'])
def get_account(id):
    account = Account.query.get(id)
    
    return account_schema.jsonify(account)
#Update an account
@app.route('/accounts/<id>', methods=['PUT'])
def update_account(id):
    account = Account.query.get(id)

    balance= request.json['balance']
    currency = request.json['currency']
    user_id=request.json['user_id']

    account.balance=balance
    account.currency=currency
    account.user_id=user_id

    db.session.commit()

    return account_schema.jsonify(account)
#Delete an account
@app.route('/accounts/<id>', methods=['DELETE'])
def delete_account(id):
    account = Account.query.get(id)
    db.session.delete(account)
    db.session.commit()

    return account_schema.jsonify(account)


#Create a transaction
@app.route('/transactions', methods=['POST'])
def create_transaction():
    title= request.json['title']
    amount= request.json['amount']
    transaction_type= request.json['transaction_type']
    created_at=datetime.datetime.now()
    updated_at=datetime.datetime.now()
    account_id = request.json['account_id']
    if transaction_type == 'income':
        acc = db.session.query(Account).filter(Account.id == account_id).first()
        print(acc)
        print(acc.balance)
        acc.balance = acc.balance + amount
    if transaction_type == 'expense':
        acc = db.session.query(Account).filter(Account.id == account_id).first()
        acc.balance = acc.balance - amount
        print(acc)
    new_transaction= Transaction(title,amount,transaction_type,created_at,updated_at,account_id)

    db.session.add(new_transaction)
    db.session.commit()

    return transaction_schema.jsonify(new_transaction)      
#Update a transaction 
@app.route('/transactions/<id>', methods=['PUT'])
def update_transaction(id):
    transaction = Transaction.query.get(id)
    title = request.json['title']
    amount = request.json['amount']
    transaction_type = request.json['transaction_type']

    transaction.transaction=transaction
    transaction.title=title
    transaction.amount = amount
    transaction.transaction_type= transaction_type

    db.session.commit()

    return transaction_schema.jsonify(transaction)
    
#Get all transactions
@app.route('/transactions', methods=['GET'])
def get_transactions():
    all_transactions = Transaction.query.all()
    result = transactions_schema.dump(all_transactions)
    return jsonify(result.data)

#Get single transaction
@app.route('/transactions/<id>', methods=['GET'])
def get_transaction(id):
    transaction = Transaction.query.get(id)
    return transaction_schema.jsonify(transaction)

#Create a category
@app.route('/categories', methods=['POST'])
def create_category():
    title = request.json['title']
    
    new_category = Category(title)
    
    db.session.add(new_category)
    db.session.commit()

    return category_schema.jsonify(new_category)

#Get a category
@app.route('/categories/<id>', methods=["GET"])
def get_category(id):
    category = Category.query.get(id)
    return category_schema.jsonify(category)
#Get all categories
@app.route('/categories', methods=['GET'])
def get_categories():
    all_categories= Category.query.all()
    result= categories_schema.dump(all_categories)
    return jsonify(result.data)
#Update a category
@app.route('/categories/<id>', methods=['PUT'])
def update_category(id):
    category = Category.query.get(id)

    title = request.json['title']

    category.title = title

    db.session.commit()

    return category_schema.jsonify(category)

#Delete a category
@app.route('/categories/<id>', methods=['DELETE'])
def delete_category(id):
    category = Category.query.get(id)
    db.session.delete(category)
    db.session.commit()

    return category_schema,jsonify(category)
#Run server
if __name__=='__main__':
    app.run(debug=True)