from datetime import date, datetime
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Initialize Flask application with CORS enabled
app = Flask(__name__)
CORS(app)

# Configuration for SQLAlchemy with PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:1234@db:5432/chefbyte_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Inventory model
class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    expiration_date = db.Column(db.Date, nullable=True)

    # Convert Inventory object to dictionary format for JSON responses
    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None
        }

# Setup database and insert initial data if necessary
@app.before_first_request
def setup_database():
    # Create all tables
    db.create_all()
    # Insert initial data if the inventory table is empty
    if not Inventory.query.first():
        new_item = Inventory(item_name='Initial Item', quantity=5, expiration_date=date.today())
        db.session.add(new_item)
        db.session.commit()
        print("Initial data inserted into database!")

# Route to serve the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle inventory data retrieval and addition
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if request.method == 'GET':
        # Retrieve all inventory items and return them as a JSON list
        items = Inventory.query.all()
        return jsonify([item.to_dict() for item in items])
    elif request.method == 'POST':
        # Add a new inventory item from the provided JSON data
        data = request.get_json()
        new_item = Inventory(
            item_name=data.get('item_name'),
            quantity=data.get('quantity'),
            expiration_date=datetime.strptime(data['expiration_date'], '%Y-%m-%d').date() if data['expiration_date'] else None
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'message': 'New item added successfully', 'item': new_item.to_dict()}), 201

# Route to update an existing inventory item
@app.route('/inventory/<int:item_id>', methods=['PUT', 'PATCH'])
def update_item(item_id):
    # Update specified inventory item with provided JSON data
    item = Inventory.query.get(item_id)
    if not item:
        return jsonify({'message': 'Item not found'}), 404
    data = request.get_json()
    item.item_name = data.get('item_name', item.item_name)
    item.quantity = data.get('quantity', item.quantity)
    item.expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date() if 'expiration_date' in data and data['expiration_date'] else None
    db.session.commit()
    return jsonify({'message': 'Item updated successfully', 'item': item.to_dict()}), 200

# Route to delete an inventory item
@app.route('/inventory/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    # Delete specified inventory item
    item = Inventory.query.get(item_id)
    if not item:
        return jsonify({'message': 'Item not found'}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted successfully'}), 200

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
