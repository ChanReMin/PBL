from flask import Flask, request, jsonify
import mysql.connector
from models import Fruit

app = Flask(__name__)

mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'fruits'
}
mysql = mysql.connector.connect(**mysql_config)
cursor = mysql.cursor()

@app.route('/addFruit', methods=['POST'])
def add_fruit():
    data = request.get_json()
    name = data['name']
    description = data.get('description', '')
    sold = data.get('sold', 0)
    exist = data.get('exist', 0)
    image = data.get('image', '')
    price = data.get('price', 0.0)

    try:
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT id FROM fruits WHERE name = %s", (name,))
        existing_fruit = cursor.fetchone()

        if existing_fruit:
            cursor.close()
            return jsonify({"message": "Fruit already exists. Please add a different one."})
        cursor.execute(
            "INSERT INTO fruits (name, description, sold, exist, image, price) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, description, sold, exist, image, price))
        mysql.commit()
        cursor.close()
        return jsonify({"message": "Fruit added successfully"}), 201
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
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/updateFruit/<int:fruit_id>', methods=['PUT'])
def update_fruit(fruit_id):
    try:
        cursor = mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM fruits WHERE id = %s", (fruit_id,))
        fruit = cursor.fetchone()

        if fruit is None:
            cursor.close()
            return jsonify({"message": "Fruit not found"}), 404

        data = request.get_json()
        new_name = data['name']
        new_description = data['description']
        new_sold = data['sold']
        new_exist = data['exist']
        new_image = data['image']
        new_price = data['price']

        cursor.execute(
            "UPDATE fruits SET name = %s, description = %s, sold = %s, exist = %s, image = %s, price = %s WHERE id = %s",
            (new_name, new_description, new_sold, new_exist, new_image, new_price, fruit_id))
        mysql.commit()
        cursor.close()
        return jsonify({"message": "Fruit updated successfully"})
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
        weight_by_id = {}  # Dictionary to store total weight by id

        for item in data:
            fruit_id = item["id"]
            weight_kg = item["weight"]

            if fruit_id in weight_by_id:
                weight_by_id[fruit_id] += weight_kg
            else:
                weight_by_id[fruit_id] = weight_kg

        for fruit_id, total_weight in weight_by_id.items():
            # Query the price from the database based on the fruit_id
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
        cursor = mysql.cursor(dictionary=True)
        data = request.get_json()
        total_price = 0
        weight_by_id = {}  # Dictionary to store total weight by id
        fruit_costs = []  # List to store fruit names and costs

        for item in data:
            fruit_id = item["id"]
            weight_kg = item["weight"]

            if fruit_id in weight_by_id:
                weight_by_id[fruit_id] += weight_kg
            else:
                weight_by_id[fruit_id] = weight_kg

        for fruit_id, total_weight in weight_by_id.items():
            # Query the price and name from the database based on the fruit_id
            query = "SELECT price, name FROM fruits WHERE id = %s"
            cursor.execute(query, (fruit_id,))
            fruit_data = cursor.fetchone()

            if fruit_data:
                price = fruit_data['price']
                cost = price * total_weight
                rounded_cost = round(cost, 5)
                total_price += cost

                fruit_name = fruit_data['name']
                fruit_costs.append({'name': fruit_name, 'cost': rounded_cost,'total weight':round(total_weight,5),'price':price})

        cursor.close()
        # mysql.close()

        return jsonify(total_price=total_price, fruit_costs=fruit_costs)
    except Exception as e:
        return jsonify(error=str(e)), 400

if __name__ == '__main__':
    app.run(debug=False)
