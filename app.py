from datetime import date, datetime
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Initialize the Flask application and enable Cross-Origin Resource Sharing (CORS)
app = Flask(__name__)
CORS(app)

# Configuration for SQLAlchemy to use PostgreSQL as the database with specific URI and disable track modifications for performance
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:1234@db:5432/chefbyte_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the model for Inventory, which maps to the 'inventory' table in the database
class Inventory(db.Model):
    __tablename__ = 'inventory'  # Database table name
    id = db.Column(db.Integer, primary_key=True)  # Primary key column
    item_name = db.Column(db.String(50), nullable=False)  # Column for item name, cannot be NULL
    quantity = db.Column(db.Integer, nullable=False)  # Column for item quantity, cannot be NULL
    expiration_date = db.Column(db.Date, nullable=True)  # Column for expiration date, can be NULL

    # Method to convert Inventory object properties into a dictionary for JSON responses
    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None
        }

# Before the first request, setup the database by creating tables and inserting initial data
@app.before_first_request
def setup_database():
    db.create_all()  # Create all tables
    if not Inventory.query.first():  # Check if the inventory table is empty
        new_item = Inventory(item_name='Initial Item', quantity=5, expiration_date=date.today())
        db.session.add(new_item)  # Add new item
        db.session.commit()  # Commit the transaction
        print("Initial data inserted into database!")

# Route to serve the home page, which uses an HTML template
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle both retrieving and adding inventory data
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if request.method == 'GET':
        items = Inventory.query.all()  # Retrieve all items from the database
        return jsonify([item.to_dict() for item in items])  # Convert items to JSON and return
    elif request.method == 'POST':
        data = request.get_json()  # Get data sent with POST request
        new_item = Inventory(
            item_name=data.get('item_name'),
            quantity=data.get('quantity'),
            expiration_date=datetime.strptime(data['expiration_date'], '%Y-%m-%d').date() if data['expiration_date'] else None
        )
        db.session.add(new_item)  # Add new item to database session
        db.session.commit()  # Commit the transaction
        return jsonify({'message': 'New item added successfully', 'item': new_item.to_dict()}), 201

# Route to update an existing inventory item
@app.route('/inventory/<int:item_id>', methods=['PUT', 'PATCH'])
def update_item(item_id):
    item = Inventory.query.get(item_id)  # Get item by ID
    if not item:
        return jsonify({'message': 'Item not found'}), 404  # Item not found, return error
    data = request.get_json()
    # Update item properties from the data provided
    item.item_name = data.get('item_name', item.item_name)
    item.quantity = data.get('quantity', item.quantity)
    item.expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date() if 'expiration_date' in data and data['expiration_date'] else item.expiration_date
    db.session.commit()  # Commit changes
    return jsonify({'message': 'Item updated successfully', 'item': item.to_dict()}), 200

# Route to delete an inventory item
@app.route('/inventory/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Inventory.query.get(item_id)  # Get item by ID
    if not item:
        return jsonify({'message': 'Item not found'}), 404  # Item not found, return error
    db.session.delete(item)  # Delete the item
    db.session.commit()  # Commit the transaction
    return jsonify({'message': 'Item deleted successfully'}), 200

# Main check to run the Flask application if this script is executed as the main program
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
