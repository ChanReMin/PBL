from flask import Flask,request,jsonify,session
import mysql.connector
from flask_cors import CORS
import bcrypt
from flask_session import Session
from datetime import datetime
app = Flask(__name__)
CORS(app)
app.config['SECRET KEY'] = 'chanremin'
app.config['SESSION_TYPE']='filesystem'
Session(app)
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'fruits'
}
mysql = mysql.connector.connect(**mysql_config)
cursor = mysql.cursor()

@app.route('/Register', methods=['POST'])
def add():
    data = request.get_json()

    email = data['email']

    password = data['password']
    salt=bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'),salt)

    id = get_id()

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
            "INSERT INTO users (id,email,password,name,phone) VALUES (%s, %s, %s, %s, %s)",
            (id, email, hashed_password, name, phone))
        mysql.commit()
        cursor.close()


        # cursor.execute(
        #     "INSERT INTO users (id,email,password,name,phone,address,birthdate,sex,username) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        #     (id,email,hashed_password,name,phone,address,birth,sex,username))
        # mysql.commit()
        # cursor.close()


        return jsonify(message="User registered successfully"), 201
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

            role = existing_user['role']

            session['role'] = role

            return jsonify(message='login sucessfully; current id ' + session['id'], role=session['role']), 201

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
    email = data.get('email','')

    password = data['password']
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    name = data.get('name','')
    phone = data.get('phone','')
    address = data.get('address','')
    birth = data.get('birth','')
    sex = data.get('sex','')
    username = data.get('username','')

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

def get_id():
    try:
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT MAX(ID) FROM users")
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
if __name__ == '__main__':
    app.run(debug=False)