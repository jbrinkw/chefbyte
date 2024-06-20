import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests
from datetime import datetime

# Configuration for SQLAlchemy
DATABASE_URL = 'postgresql+psycopg2://postgres:1234@db:5432/chefbyte_db'
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Define the Inventory model
class Inventory(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True)
    item_name = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    expiration_date = Column(Date, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None
        }

# Create the table if it doesn't exist
Base.metadata.create_all(engine)

# Function to fetch current inventory
def fetch_inventory():
    items = session.query(Inventory).all()
    return [item.to_dict() for item in items]

# Function to send user input to LLM and get structured response
def send_to_llm(user_input, inventory_str):
    api_key = 'your_openai_api_key'  # Replace with your actual API key
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    prompt = f"The current inventory is:\n{inventory_str}\n\nUser input: {user_input}\n\nConvert the user's input into a SQL command."

    data = {
        'model': 'text-davinci-003',
        'prompt': prompt,
        'max_tokens': 150
    }
    response = requests.post('https://api.openai.com/v1/completions', headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to get response from LLM.")
        return {'command': None}

# Function to process the LLM response and update inventory
def process_llm_response(llm_response):
    command = llm_response.get('command')
    if command:
        if command['action'] == 'ADD':
            new_item = Inventory(
                item_name=command['item_name'],
                quantity=command['quantity'],
                expiration_date=datetime.strptime(command['expiration_date'], '%Y-%m-%d').date() if command['expiration_date'] else None
            )
            session.add(new_item)
            session.commit()
            st.success("Item added successfully.")
        elif command['action'] == 'UPDATE':
            item = session.query(Inventory).get(command['item_id'])
            if item:
                item.item_name = command.get('item_name', item.item_name)
                item.quantity = command.get('quantity', item.quantity)
                item.expiration_date = datetime.strptime(command['expiration_date'], '%Y-%m-%d').date() if command['expiration_date'] else item.expiration_date
                session.commit()
                st.success("Item updated successfully.")
            else:
                st.error("Item not found.")
        elif command['action'] == 'DELETE':
            item = session.query(Inventory).get(command['item_id'])
            if item:
                session.delete(item)
                session.commit()
                st.success("Item deleted successfully.")
            else:
                st.error("Item not found.")
    else:
        st.error("Invalid command from LLM.")

# Streamlit interface
def main():
    st.title("ChefByte Inventory System")

    # LLM Chatbox
    st.header("LLM Chatbox")
    user_input = st.text_input("Enter your command:")
    if st.button("Submit"):
        inventory_data = fetch_inventory()
        inventory_str = "\n".join([f"{item['item_name']}: {item['quantity']}" for item in inventory_data])
        llm_response = send_to_llm(user_input, inventory_str)
        if llm_response:
            process_llm_response(llm_response)

    # Display Inventory Table
    st.header("Inventory Table")
    inventory_data = fetch_inventory()
    if inventory_data:
        df = pd.DataFrame(inventory_data)
        st.dataframe(df)

if __name__ == '__main__':
    main()
