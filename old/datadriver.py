from sqlalchemy import create_engine

engine = create_engine('postgresql+psycopg2://postgres:1234@localhost/chefbytebite_db')
