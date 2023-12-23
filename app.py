import os

from flask import Flask, request, jsonify, session
import mysql.connector
from CameraWebServer import (capture, predict)
from Loadcell import (get_weight, Loadcell_WebSockets_URL)

from user_model import user
from fruit_model import Fruit
from flask_cors import CORS
import bcrypt
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

from flask_jwt_extended import *
from functools import wraps
from datetime import datetime, date

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'chanremin'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['JWT_SECRET_KEY'] = 'chanremin'
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'fruits'
}
mysql = mysql.connector.connect(**mysql_config)
cursor = mysql.cursor()
jwt = JWTManager(app)
# fruit route
@app.route('/addFruit', methods=['POST'])
@jwt_required()
def add_fruit():
    data = request.get_json()
    name = data['name']
    description = data.get('description', '')
    exist = data.get('exist', 0)
    image = data.get('image', '')
    price = data.get('price', 0.0)
    id = get_fruit_id()

    try:
        identity = get_jwt_identity()
        if check_role(identity):
            cursor = mysql.cursor(dictionary=True)
            cursor.execute("SELECT id FROM fruits WHERE name = %s", (name,))
            existing_fruit = cursor.fetchone()
            if existing_fruit:
                cursor.close()
                return jsonify({"message": "Fruit already exists. Please add a different one."})
            cursor.execute(
                "INSERT INTO fruits (ID,name, description, exist, image, price) VALUES (%s, %s, %s, %s, %s,%s)",
                (id,name, description, exist, image, price))
            mysql.commit()
            cursor.close()
            return jsonify({"message": "Fruit added successfully"}), 201
        else:
            return jsonify(message="Invalid route")
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/allFruits', methods=['GET'])
@jwt_required()
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
@jwt_required()
def delete_fruit(fruit_id):
    try:
        identity = get_jwt_identity()
        if check_role(identity):
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
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/updateFruit/<int:fruit_id>', methods=['PUT'])
@jwt_required()
def update_fruit(fruit_id):
    try:
        identity = get_jwt_identity()
        if check_role(identity):
            cursor = mysql.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE ID = %s", (identity,))
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
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/viewFruit/<int:fruit_id>', methods=['GET'])
@jwt_required()
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
@app.route('/searchFruit/<string:fruit_name>', methods=['GET'])
@jwt_required()
def search_fruit(fruit_name):
    try:
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM fruits WHERE name = %s", (fruit_name,))
        fruit = cursor.fetchone()
        if fruit is None:
            cursor.close()
            return jsonify({"message": "Fruit not found"}), 404
        cursor.close()
        return jsonify(fruit)
    except Exception as e:
        return jsonify(error=str(e)), 500
@app.route('/bill', methods=['POST'])
@jwt_required()
def bill():
    try:
        identity = get_jwt_identity()
        cursor = mysql.cursor(dictionary=True)
        data = request.get_json()
        total_price = 0
        weight_by_id = {}
        fruit_costs = []
        user_id = identity
        bill_date = date.today()
        fruit_out = []
        # cursor.close()
        cursor.execute("SELECT MAX(bill_id) as max_id from bill")
        max_id = cursor.fetchone()
        if not max_id['max_id']:
            bill_id = 1
        else:
            bill_id = max_id['max_id']
            bill_id += 1
        for item in data:
            fruit_id = item['id']
            weight_kg = item['weight']

            if fruit_id in weight_by_id:
                weight_by_id[fruit_id] += weight_kg
            else:
                weight_by_id[fruit_id] = weight_kg

        for fruit_id, total_weight in weight_by_id.items():
            cursor = mysql.cursor(dictionary=True)
            cursor.execute("SELECT price, name FROM fruits WHERE id = %s", (fruit_id,))
            # cursor.execute("SELECT price, name, exist FROM fruits WHERE id = %s", (fruit_id,))
            fruit_data = cursor.fetchone()

            if fruit_data:
                price = fruit_data['price']
                # if total_weight > fruit_data['exist']:
                #     # fruit_out.append({'name':fruit_data['name']})
                #     return jsonify(message="fruit name:"+fruit_data['name']+" Out of stock")
                # else:
                # fruit_data['exist']-=total_weight
                cost = price * total_weight
                rounded_cost = round(cost, 5)
                total_price += cost
                fruit_name = fruit_data['name']
                fruit_costs.append(
                    {'name': fruit_name, 'cost': rounded_cost, 'total weight': round(total_weight, 5), 'price': price})
                cursor.execute("INSERT INTO bill_detail (bill_id, fruit_id, weight,price) VALUES (%s, %s, %s, %s)",
                               (bill_id, fruit_id, total_weight, price))

            mysql.commit()
        # mysql.close()
        cursor.execute("INSERT INTO bill (bill_id,Date,user_id,total_cost) VALUES (%s, %s,%s,%s)",
                       (bill_id, bill_date, user_id, total_price))
        mysql.commit()
        return jsonify(total_price=total_price, fruit_costs=fruit_costs)
    except Exception as e:
        return jsonify(error=str(e)), 400
@app.route('/ViewBill/<int:bill_id>', methods=['GET'])
@jwt_required()
def view_bill(bill_id):
    try:
        cursor = mysql.cursor(dictionary=True)
        query = """
        SELECT bill.Date,bill.user_id,users.name,bill_detail.weight,fruits.price,fruits.name , 
                bill_detail.weight*bill_detail.price AS cost
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

        query2 = """SELECT SUM( bill_detail.weight*bill_detail.price)  AS cost FROM bill_detail WHERE bill_detail.bill_id = %s"""
        cursor.execute(query2,(bill_id,))
        result = cursor.fetchone()


        if not bill:
            cursor.close()
            return jsonify({"message": "Bill not found"}), 404
        cursor.close()
        return jsonify(bill=bill,total_price=round(result['cost'],3))
    except Exception as e:
        return jsonify(error=str(e)), 500
@app.route('/ViewAllBill',methods=['GET'])
@jwt_required()
def view_all_bill():
    try:
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bill")
        result=cursor.fetchall()
        return (result)
    except Exception as e:
        return jsonify(error=str(e)), 500
@app.route('/Sales/', methods=['GET'])
@jwt_required()
def sales():
    try:
        fruit_sales = []
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("""SELECT name, fruit_id AS fruit_id , SUM(weight*bill_detail.price) AS sales FROM bill_detail JOIN fruits
                    WHERE fruits.ID = bill_detail.fruit_id
                    GROUP BY fruit_id
                    """)
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            name = row['name']
            fruit_id = row['fruit_id']
            sales = row['sales']
            fruit_sales.append({"Name": name, "ID": fruit_id, "sales": sales})
        return (fruit_sales)
    except Exception as e:
        return jsonify(error=str(e)), 500
# user_route
@app.route('/Register', methods=['POST'])
@jwt_required()
def add():
    data = request.get_json()
    email = data['email']
    password = data['password']

    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    role = data['role']
    id = get_id(role)

    name = data.get('name', '')
    phone = data.get('phone', '')
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
            (id, email, hashed_password, name, phone, role))
        mysql.commit()
        cursor.close()

        # cursor.execute(
        #     "INSERT INTO users (id,email,password,name,phone,address,birthdate,sex,username) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        #     (id,email,hashed_password,name,phone,address,birth,sex,username))
        # mysql.commit()
        # cursor.close()

        if role == 0:
            return jsonify(message="User registered successfully"), 201
        elif role == 1:
            return jsonify(message="Admin registered successfully"), 201
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/Login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']
    try:
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user == None:
            return jsonify(message="Cannot find email")
        user_id = existing_user['ID']
        role = existing_user['Admin']
        existing_password = existing_user['password']
        if existing_user and bcrypt.checkpw(password.encode('utf-8'), existing_password.encode('utf-8')):
            access_token = create_access_token(identity=user_id)
            return jsonify(message='Login Successful', access_token=access_token, identity=user_id)
        else:
            return jsonify('Wrong Password'), 401
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/view', methods=['GET'])
@jwt_required()
def view():
    try:
        identity = get_jwt_identity()
        if identity is not None:
            cursor = mysql.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE ID = %s", (identity,))
            user = cursor.fetchone()
            cursor.close()
            return jsonify(user)
        else:
            return jsonify(message="Please login")
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/ViewAll', methods=['GET'])
@jwt_required()
def view_all():
    try:
        identity = get_jwt_identity()
        if check_role(identity):
            cursor = mysql.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users")
            result = cursor.fetchall()
            cursor.close()
            return jsonify(result)
        else:
            return jsonify(message="Unauthorized route")
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/update', methods=['POST'])
@jwt_required()
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
        id = get_jwt_identity()
        cursor = mysql.cursor(dictionary=True)
        cursor.execute(
            "UPDATE users SET email=%s, password=%s, name=%s, phone=%s, address=%s, birth=%s, sex=%s, username=%s WHERE id=%s",
            (email, hashed_password, name, phone, address, birthdate, sex, username, id))
        return jsonify(message="Update success")
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/getWeight', methods=['GET'])
def getWEIGHT():
    return jsonify({"weight":round(get_weight.get_weight(Loadcell_WebSockets_URL) / 1000, 3)})
@app.route('/getID',methods=['GET'])
def getID():
    capture_path = capture.capture()
    img_path, label_path = predict.predict(capture_path)
    # label_path = r"D:\PBL\W-P_BE\WebServer\capture_predict\predicts\2023.11.14\2.txt"
    if os.path.exists(label_path):
        label_file = open(label_path)
        content = list(label_file)
        label_file.close()
        labels = []
        for label in content:
            labels.append(label.split()[0])

        if labels.count(labels[0]) != len(labels):
            return jsonify(message="Too much fruits!")
        else:
            id = labels[0]
            cursor = mysql.cursor(dictionary=True)
            cursor.execute("SELECT ID,name,price FROM fruits WHERE ID = %s", (id,))
            result=cursor.fetchone()
            return jsonify(result)
    else:
        return jsonify(message="Fruit not Found!")
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
def check_role(ID):
    try:
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT Admin FROM users WHERE ID=%s", (ID,))
        result = cursor.fetchone()
        if result['Admin'] == 0:
            return False
        else:
            return True
    except Exception as e:
        return jsonify(error=str(e)), 400

def get_fruit_id():
    try:
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT MAX(ID) FROM fruits")
        result = cursor.fetchone()
        max_id = result['MAX(ID)']
        if max_id:
            id = max_id + 1
        else:
            id = 0
        cursor.execute("SELECT ID FROM fruits WHERE ID = %s", (id,))
        existing_id = cursor.fetchone()
        cursor.close()
        return id
    except Exception as e:
        return jsonify(error=str(e)), 400
if __name__ == '__main__':
    from waitress import serve
    # app.run(debug=False)
    serve(app, host="0.0.0.0", port=8080)
