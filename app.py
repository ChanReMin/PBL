from flask import Flask, request, jsonify, session
import mysql.connector
from user_model import user
from fruit_model import Fruit
from flask_cors import CORS
import bcrypt
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

from flask_session import Session
from functools import wraps
from datetime import datetime,date
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'chanremin'
app.config['SESSION_TYPE']='filesystem'
# Session(app)
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'fruits'
}
mysql = mysql.connector.connect(**mysql_config)
cursor = mysql.cursor()

#fruit route
@app.route('/addFruit', methods=['POST'])
def add_fruit():
    data = request.get_json()
    name = data['name']
    description = data.get('description', '')
    exist = data.get('exist', 0)
    image = data.get('image', '')
    price = data.get('price', 0.0)

    try:
        if 'logged_in' in session and session['logged_in']:
            cursor = mysql.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE ID = %s", (session['id'],))
            user = cursor.fetchone()
            if check_role(user):
                cursor = mysql.cursor(dictionary=True)
                cursor.execute("SELECT id FROM fruits WHERE name = %s", (name,))
                existing_fruit = cursor.fetchone()
                if existing_fruit:
                    cursor.close()
                    return jsonify({"message": "Fruit already exists. Please add a different one."})
                cursor.execute(
                    "INSERT INTO fruits (name, description, exist, image, price) VALUES (%s, %s, %s, %s, %s)",
                    (name, description, exist, image, price))
                mysql.commit()
                cursor.close()
                return jsonify({"message": "Fruit added successfully"}), 201
            else:
                return jsonify(message="Invalid route")
        else:
            return jsonify(message="Please login")
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/allFruits', methods=['GET'])
def show_fruits():
    try:
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM fruits")
        fruits = cursor.fetchall()
        cursor.close()
        return jsonify(fruits)
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/deleteFruit/<int:fruit_id>', methods=['DELETE'])
def delete_fruit(fruit_id):
    try:
        if 'logged_in' in session and session['logged_in']:
            cursor = mysql.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE ID = %s", (session['id'],))
            user = cursor.fetchone()
            if check_role(user):
                cursor = mysql.cursor(dictionary=True)
                cursor.execute("SELECT * FROM fruits WHERE id = %s", (fruit_id,))
                fruit = cursor.fetchone()

                if fruit is None:
                    cursor.close()
                    return jsonify({"message": "Fruit not found"}), 404

                # If the fruit exists, execute a DELETE query to remove it
                cursor.execute("DELETE FROM fruits WHERE id = %s", (fruit_id,))
                mysql.commit()
                cursor.close()
                return jsonify({"message": "Fruit deleted successfully"}), 200
            else:
                return jsonify(message="Invalid route")
        else:
            return jsonify(message="Please login")
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/updateFruit/<int:fruit_id>', methods=['PUT'])
def update_fruit(fruit_id):
    try:
        if 'logged_in' in session and session['logged_in']:
            cursor = mysql.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE ID = %s", (session['id'],))
            user = cursor.fetchone()
            if check_role(user):
                cursor = mysql.cursor(dictionary=True)
                cursor.execute("SELECT * FROM fruits WHERE id = %s", (fruit_id,))
                fruit = cursor.fetchone()

                if fruit is None:
                    cursor.close()
                    return jsonify({"message": "Fruit not found"}), 404

                data = request.get_json()
                new_name = data['name']
                new_description = data['description']
                new_exist = data['exist']
                new_image = data['image']
                new_price = data['price']

                cursor.execute(
                    "UPDATE fruits SET name = %s, description = %s,  exist = %s, image = %s, price = %s WHERE id = %s",
                    (new_name, new_description, new_exist, new_image, new_price, fruit_id))
                mysql.commit()
                cursor.close()
                return jsonify({"message": "Fruit updated successfully"})
            else:
                return jsonify(message="Invalid route")
        else:
            return jsonify(message="Please login")
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/viewFruit/<int:fruit_id>', methods=['GET'])
def view_fruit(fruit_id):
    try:
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM fruits WHERE id = %s", (fruit_id,))
        fruit = cursor.fetchone()
        if fruit is None:
            cursor.close()
            return jsonify({"message": "Fruit not found"}), 404

        cursor.close()
        return jsonify(fruit)
    except Exception as e:
        return jsonify(error=str(e)), 500
@app.route('/calculate_price', methods=['POST'])
def calculate_total_price():
    try:
        cursor = mysql.cursor(dictionary=True)
        data = request.get_json()
        total_price = 0
        weight_by_id = {}

        for item in data:
            fruit_id = item["id"]
            weight_kg = item["weight"]

            if fruit_id in weight_by_id:
                weight_by_id[fruit_id] += weight_kg
            else:
                weight_by_id[fruit_id] = weight_kg

        for fruit_id, total_weight in weight_by_id.items():
            query = "SELECT price FROM fruits WHERE id = %s"
            cursor.execute(query, (fruit_id,))
            price_data = cursor.fetchone()
            if price_data:
                price = price_data['price']
                cost = price * total_weight
                total_price += cost

        cursor.close()
        # mysql.close()

        return jsonify(total_price=total_price)
    except Exception as e:
        return jsonify(error=str(e)), 400
@app.route('/searchFruit/<string:fruit_name>',methods=['GET'])
def search_fruit(fruit_name):
    try:
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM fruits WHERE name = %s",(fruit_name,))
        fruit = cursor.fetchone()
        if fruit is None:
            cursor.close()
            return jsonify({"message":"Fruit not found"}),404
        cursor.close()
        return jsonify(fruit)
    except Exception as e:
        return jsonify(error=str(e)),500
@app.route('/bill',methods=['POST'])
def bill():
    try:
        if 'logged_in' in session and session['logged_in']:
            cursor = mysql.cursor(dictionary=True)
            data = request.get_json()
            total_price = 0
            weight_by_id = {}
            fruit_costs = []
            user_id = session['id']
            bill_date = date.today()

            cursor.execute("INSERT INTO bill (Date,user_id) VALUES (%s, %s)",(bill_date, user_id))
            mysql.commit()
            # cursor.close()
            cursor.execute("SELECT MAX(bill_id) as max_id from bill")
            max_id = cursor.fetchone()
            bill_id = max_id['max_id']
            for item in data:
                fruit_id = item["id"]
                weight_kg = item["weight"]

                if fruit_id in weight_by_id:
                    weight_by_id[fruit_id] += weight_kg
                else:
                    weight_by_id[fruit_id] = weight_kg

            for fruit_id, total_weight in weight_by_id.items():
                cursor = mysql.cursor(dictionary=True)
                cursor.execute("SELECT price, name FROM fruits WHERE id = %s", (fruit_id,))
                fruit_data = cursor.fetchone()

                if fruit_data:
                    price = fruit_data['price']
                    cost = price * total_weight
                    rounded_cost = round(cost, 5)
                    total_price += cost
                    fruit_name = fruit_data['name']
                    fruit_costs.append({'name': fruit_name, 'cost': rounded_cost,'total weight':round(total_weight, 5),'price':price})
                    cursor.execute("INSERT INTO bill_detail (bill_id, fruit_id, weight) VALUES (%s, %s, %s)",
                               (bill_id, fruit_id, total_weight))

                mysql.commit()
                cursor.close()
            # mysql.close()

            return jsonify(total_price=total_price, fruit_costs=fruit_costs)
        else:
            return jsonify(message="Please login")
    except Exception as e:
        return jsonify(error=str(e)), 400
@app.route('/ViewBill/<int:bill_id>',methods=['GET'])
def view_bill(bill_id):
    try:
        cursor = mysql.cursor(dictionary=True)
        query="""SELECT bill.Date,bill.user_id,users.name,bill_detail.weight,fruits.price,fruits.name 
        FROM bill 
        JOIN users 
        ON bill.user_id = users.ID 
        JOIN bill_detail 
        ON bill.bill_id = bill_detail.bill_id 
        JOIN fruits 
        ON bill_detail.fruit_id = fruits.ID  
        WHERE bill_detail.bill_id = %s"""
        cursor.execute(query, (bill_id,))
        bill = cursor.fetchall()
        if bill is None:
            cursor.close()
            return jsonify({"message": "Bill not found"}), 404
        cursor.close()
        return jsonify(bill)
    except Exception as e:
        return jsonify(error=str(e)), 500

#user_route
@app.route('/Register', methods=['POST'])
def add():
    data = request.get_json()

    email = data['email']

    password = data['password']

    salt=bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'),salt)
    role = data['role']
    id = get_id(role)

    name = data.get('name','')
    phone = data.get('phone','')
    # address = data.get('address','')
    # birth = data.get('birth','')
    # sex = data.get('sex','')
    # username = data.get('username','')
    # try:
    #     birthdate = datetime.strptime(birth, "%Y-%m-%d").date()
    # except ValueError:
    #     return jsonify(message="Invalid birthdate format. Please use the format 'YYYY-MM-DD'")
    try:
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            return jsonify(message="User already exists. Please add a different one.")

        cursor.execute(
            "INSERT INTO users (id,email,password,name,phone,admin) VALUES (%s, %s, %s, %s, %s,%s)",
            (id, email, hashed_password, name, phone,role))
        mysql.commit()
        cursor.close()


        # cursor.execute(
        #     "INSERT INTO users (id,email,password,name,phone,address,birthdate,sex,username) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        #     (id,email,hashed_password,name,phone,address,birth,sex,username))
        # mysql.commit()
        # cursor.close()

        if role==0:
            return jsonify(message="User registered successfully"), 201
        elif role == 1:
            return jsonify(message="Admin registered successfully"),201
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/Login',methods=['POST'])
def login():

    data = request.get_json()

    email = data['email']

    password = data['password']

    try:

        if 'logged_in' in session and session['logged_in']:

            return jsonify(message="You are already logged in")

        cursor = mysql.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

        existing_user = cursor.fetchone()

        if existing_user == None:

            return jsonify(message="Cannot find email")

        user_id = existing_user['ID']

        existing_password = existing_user['password']

        if existing_user and bcrypt.checkpw(password.encode('utf-8'), existing_password.encode('utf-8')):

            session['logged_in'] = True

            session['id'] = user_id

            role = existing_user['Admin']

            session['Admin'] = role

            return jsonify(message='login sucessfully; current id ' + session['id'], role=session['Admin']), 201

        else:

            return jsonify(message="Password incorrect"), 201

    except Exception as e:

        return jsonify({"error": str(e)})

@app.route('/view',methods=['GET'])
def view():
    try:
        if 'logged_in' in session and session['logged_in']:
            cursor = mysql.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE ID = %s",(session['id'],))
            user = cursor.fetchone()
            cursor.close()
            return jsonify(user)
        else:
            return jsonify(message="Please login")
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/logout',methods=['POST'])
def logout():
    try:
        if 'logged_in' in session and session['logged_in']:
            session.clear()
            return jsonify(message='Logout successful')
        else:
            return jsonify(message='Please login first')
    except Exception as e:
        return jsonify(error=str(e)), 400
@app.route('/update',methods=['POST'])
def update():
    data = request.get_json()
    email = data.get('email', '')

    password = data['password']
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    name = data.get('name', '')
    phone = data.get('phone', '')
    address = data.get('address', '')
    birth = data.get('birth', '')
    sex = data.get('sex', '')
    username = data.get('username', '')

    try:
        birthdate = datetime.strptime(birth, "%Y-%m-%d").date()
    except ValueError:
        return jsonify(message="Invalid birthdate format. Please use the format 'YYYY-MM-DD'")

    try:
        if 'logged_in' in session and session['logged_in']:
            cursor = mysql.cursor(dictionary=True)
            cursor.execute(
                "UPDATE users SET email=%s, password=%s, name=%s, phone=%s, address=%s, birth=%s, sex=%s, username=%s WHERE id=%s",
                (email, hashed_password, name, phone, address, birthdate, sex, username, session['id']))

            return jsonify(message="Update success")
        else:
            return jsonify(message="Please login")
    except Exception as e:
        return jsonify({"error": str(e)})
def get_id(role):
    if role == 0:
        try:
            cursor = mysql.cursor(dictionary=True)
            cursor.execute("SELECT MAX(ID) FROM users where ID like'NV%'")
            result = cursor.fetchone()
            max_id = result['MAX(ID)']
            if max_id:
                num_id = int(max_id[2:]) + 1
                id = "NV{:03d}".format(num_id)
            else:
                id = "NV001"
            cursor.execute("SELECT ID FROM users WHERE ID = %s", (id,))
            existing_id = cursor.fetchone()

            while existing_id:
                num_id += 1
                id = "NV{:03d}".format(num_id)
                cursor.execute("SELECT ID FROM users WHERE ID = %s", (id,))
                existing_id = cursor.fetchone()

            cursor.close()
            return id
        except Exception as e:
            return jsonify(error=str(e)), 400
    elif role == 1:
        try:
            cursor = mysql.cursor(dictionary=True)
            cursor.execute("SELECT MAX(ID) FROM users where ID like'AD%'")
            result = cursor.fetchone()
            max_id = result['MAX(ID)']
            if max_id:
                num_id = int(max_id[2:]) + 1
                id = "AD{:03d}".format(num_id)
            else:
                id = "AD001"
            cursor.execute("SELECT ID FROM users WHERE ID = %s", (id,))
            existing_id = cursor.fetchone()

            while existing_id:
                num_id += 1
                id = "AD{:03d}".format(num_id)
                cursor.execute("SELECT ID FROM users WHERE ID = %s", (id,))
                existing_id = cursor.fetchone()

            cursor.close()
            return id
        except Exception as e:
            return jsonify(error=str(e)), 400
    else:
        return jsonify(error="Invalid role")
def check_role(user):
    try:
        cursor = mysql.cursor(dictionary=True)
        if user['Admin'] == 0:
            return False
        else:
            return True
    except Exception as e:
        return jsonify(error=str(e)), 400

if __name__ == '__main__':
    app.run(debug=False)