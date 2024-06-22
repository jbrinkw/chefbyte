import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests
import difflib
import base64

# Configuration for SQLAlchemy
DATABASE_URL = 'postgresql+psycopg2://myuser:mypassword@postgres/mydatabase'
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Define the Inventory model
class Inventory(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True)
    item_name = Column(String(50), nullable=False, unique=True)
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

# Ensure the inventory starts with one item "milk"
def initialize_inventory():
    if not session.query(Inventory).filter_by(item_name='milk').first():
        milk = Inventory(item_name='milk', quantity=1, expiration_date=None)
        session.add(milk)
        session.commit()

initialize_inventory()

# Function to fetch current inventory
def fetch_inventory():
    items = session.query(Inventory).all()
    return [item.to_dict() for item in items]

# Function to find the closest match for an item in the inventory
def find_closest_match(item_name, inventory_list):
    item_names = [item['item_name'] for item in inventory_list]
    closest_matches = difflib.get_close_matches(item_name, item_names, n=1, cutoff=0.8)
    return closest_matches[0] if closest_matches else None

# Function to send user input to LLM and get structured response
def send_to_llm(user_input, inventory_str, debug):
    api_key = 'sk-proj-yXOIDRxrvdPGBWtosq3CT3BlbkFJ3PmpejJQwhe4eLi0V8ok'  # Replace with your actual API key
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    prompt = (f"The current inventory is:\n{inventory_str}\n\nUser input: {user_input}\n\n"
              "Generate a structured list of items to be added, updated, or deleted. "
              "Check if an item already exists in the inventory, accounting for case differences and similar names. "
              "If an item does not exist, mark it for insertion with the given quantity. "
              "If the item already exists, mark it for updating the quantity. If the quantity of an item is going to be zero or less, mark it for deletion. "
              "For items with long names, provide an abbreviated name that fits within 50 characters. "
              "Provide the structured list in JSON format with fields: 'action' (add, update, delete), 'item_name', 'quantity'. Don't return it in a code block this will go straight to python eval.")

    if debug:
        st.write(f"Prompt: {prompt}")

    data = {
        'model': 'gpt-4o',
        'messages': [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        'max_tokens': 300,
        'temperature': 0
    }
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    if response.status_code == 200:
        response_json = response.json()
        structured_list = response_json['choices'][0]['message']['content'].strip()
        if debug:
            st.write(f"LLM Response: {structured_list}")
        return structured_list
    else:
        st.error(f"Failed to get response from LLM. Status code: {response.status_code}, Response: {response.text}")
        return None

# Function to send image to LLM and get structured response
def send_image_to_llm(image_data, inventory_str, debug):
    api_key = 'sk-proj-yXOIDRxrvdPGBWtosq3CT3BlbkFJ3PmpejJQwhe4eLi0V8ok'  # Replace with your actual API key
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    base64_image = base64.b64encode(image_data).decode('utf-8')

    prompt = (f"The current inventory is:\n{inventory_str}\n\nExtract the items from this image and convert them "
              "into a structured list of items to be added, updated, or deleted. "
              "Check if an item already exists in the inventory, accounting for case differences and similar names. "
              "If an item does not exist, mark it for insertion with the given quantity. "
              "If the item already exists, mark it for updating the quantity. If the quantity of an item is going to be zero or less, mark it for deletion. "
              "For items with long names, provide an abbreviated name that fits within 50 characters. "
              "Provide the structured list in JSON format with fields: 'action' (add, update, delete), 'item_name', 'quantity'. "
              "Provide only the structured list without any explanations. Don't return it in a code block this will go straight to python eval.")

    if debug:
        st.write(f"Prompt: {prompt}")

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300,
        'temperature': 0
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        response_json = response.json()
        structured_list = response_json['choices'][0]['message']['content'].strip()
        if debug:
            st.write(f"LLM Response: {structured_list}")
        return structured_list
    else:
        st.error(f"Failed to get response from LLM. Status code: {response.status_code}, Response: {response.text}")
        return None

# Function to process the LLM response and update inventory
def process_llm_response(structured_list, inventory_data, debug):
    if debug:
        st.write(f"LLM Response: {structured_list}")
    try:
        actions = eval(structured_list)
        for action in actions:
            item_name = action['item_name']
            quantity = action['quantity']
            closest_match = find_closest_match(item_name, inventory_data)
            if action['action'] == 'add':
                if closest_match:
                    st.warning(f"Item '{item_name}' is similar to existing item '{closest_match}'. Consider updating instead.")
                else:
                    new_item = Inventory(item_name=item_name, quantity=quantity, expiration_date=None)
                    session.add(new_item)
                    session.commit()
                    st.success(f"Item '{item_name}' added successfully.")
            elif action['action'] == 'update':
                if closest_match:
                    item = session.query(Inventory).filter_by(item_name=closest_match).first()
                    item.quantity = quantity  # Set the quantity to the new value
                    session.commit()
                    st.success(f"Item '{closest_match}' updated successfully.")
                else:
                    st.error(f"Item '{item_name}' not found in inventory for updating.")
            elif action['action'] == 'delete':
                if closest_match:
                    item = session.query(Inventory).filter_by(item_name=closest_match).first()
                    if item:
                        session.delete(item)
                        session.commit()
                        st.success(f"Item '{closest_match}' deleted successfully.")
                    else:
                        st.error(f"Item '{closest_match}' not found in inventory for deletion.")
    except Exception as e:
        st.error(f"Error processing LLM response: {e}")

# Function to send user input to LLM and get recipe suggestions
def get_recipe_suggestions(user_input, profile, inventory_str, use_inventory_only, debug):
    api_key = 'sk-proj-yXOIDRxrvdPGBWtosq3CT3BlbkFJ3PmpejJQwhe4eLi0V8ok'  # Replace with your actual API key
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    restriction = "You must only suggest recipes that use items from the inventory." if use_inventory_only else ""
    prompt = (f"This is a personalized chef recipe suggestion service. The user profile is:\n{profile}\n\n"
              f"The current inventory is:\n{inventory_str}\n\n"
              f"User input: {user_input}\n\n"
              f"{restriction}\n"
              "Based on the profile and the input, suggest a recipe that fits the user's preferences. "
              "Provide the recipe in a structured format including ingredients and steps.")

    if debug:
        st.write(f"Prompt: {prompt}")

    data = {
        'model': 'gpt-4o',
        'messages': [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        'max_tokens': 300,
        'temperature': 1  # Set temperature to 1 for more creative responses
    }
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    if response.status_code == 200:
        response_json = response.json()
        recipe_suggestion = response_json['choices'][0]['message']['content'].strip()
        if debug:
            st.write(f"LLM Response: {recipe_suggestion}")
        return recipe_suggestion
    else:
        st.error(f"Failed to get response from LLM. Status code: {response.status_code}, Response: {response.text}")
        return None

# Streamlit interface for Inventory Management
def inventory_management():
    st.title("ChefByte Inventory System")

    # Debugging switch
    debug = st.checkbox("Show Debugging Information")

    # Fetch inventory data for both LLM chatbox and image upload
    if 'inventory_data' not in st.session_state:
        st.session_state.inventory_data = fetch_inventory()

    inventory_data = st.session_state.inventory_data
    inventory_str = "\n".join([f"{item['item_name']}: {item['quantity']}" for item in inventory_data])

    # Layout setup
    col1, col2 = st.columns([1, 1])

    with col1:
        # LLM Chatbox
        st.header("LLM Chatbox")
        user_input = st.text_input("Enter your command:")
        if st.button("Submit"):
            structured_list = send_to_llm(user_input, inventory_str, debug)
            if structured_list:
                process_llm_response(structured_list, inventory_data, debug)
                st.session_state.inventory_data = fetch_inventory()

        # Image upload
        st.header("Upload an Image")
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            bytes_data = uploaded_file.read()
            st.image(bytes_data, caption='Uploaded Image.', use_column_width=True)
            st.success("Image uploaded successfully.")
            # Send image to LLM
            structured_list = send_image_to_llm(bytes_data, inventory_str, debug)
            if structured_list:
                process_llm_response(structured_list, inventory_data, debug)
                st.session_state.inventory_data = fetch_inventory()

    with col2:
        # Display Inventory Table
        st.header("Inventory Table")
        inventory_data = st.session_state.inventory_data
        if inventory_data:
            df = pd.DataFrame(inventory_data).drop(columns=['id'])
            st.dataframe(df)
        else:
            st.info("Inventory is empty.")

# Streamlit interface for Recipe Suggestion
def recipe_suggestion():
    st.title("Personal Chef Recipe Suggestion Service")

    # Debugging switch
    debug = st.checkbox("Show Debugging Information")

    # Button to enter taste profile
    if 'profile' not in st.session_state:
        if st.button("Enter Taste Profile"):
            st.session_state.show_profile_input = True

    if st.session_state.get('show_profile_input', False):
        profile = st.text_area("Paste your taste profile here:")
        if st.button("Save Profile"):
            st.session_state.profile = profile
            st.session_state.show_profile_input = False
            st.success("Profile saved successfully.")
    
    # Fetch inventory data
    if 'inventory_data' not in st.session_state:
        st.session_state.inventory_data = fetch_inventory()

    inventory_data = st.session_state.inventory_data
    inventory_str = "\n".join([f"{item['item_name']}: {item['quantity']}" for item in inventory_data])

    # Layout setup
    col1, col2 = st.columns([1, 2])

    with col1:
        # Recipe Suggestion Chatbox and Inventory Table
        st.header("Recipe Suggestion Chatbox")
        user_input = st.text_input("What do you want to eat today?")
        use_inventory_only = st.checkbox("Only use items from inventory")
        if st.button("Get Recipe Suggestion"):
            if 'profile' in st.session_state:
                recipe_suggestion = get_recipe_suggestions(user_input, st.session_state.profile, inventory_str, use_inventory_only, debug)
                if recipe_suggestion:
                    st.session_state.recipe_suggestion = recipe_suggestion
            else:
                st.warning("Please enter your taste profile first.")

        st.header("Inventory Table")
        if inventory_data:
            df = pd.DataFrame(inventory_data).drop(columns=['id'])
            st.dataframe(df)
        else:
            st.info("Inventory is empty.")

    with col2:
        # Display Recipe Suggestion
        st.header("Recipe Suggestion")
        if 'recipe_suggestion' in st.session_state:
            st.write(st.session_state.recipe_suggestion)
        else:
            st.info("Enter a prompt to get a recipe suggestion.")

# Main function to run the multipage app
def main():
    # Set the layout to wide mode
    st.set_page_config(layout="wide")

    # Page navigation buttons at the top
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Inventory Management", "Recipe Suggestion"])

    if page == "Inventory Management":
        inventory_management()
    elif page == "Recipe Suggestion":
        recipe_suggestion()

if __name__ == '__main__':
    main()
