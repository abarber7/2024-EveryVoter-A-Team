from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
load_dotenv()
connection_string = os.getenv("DATABASE_CONNECTION_STRING")
# Create the SQLAlchemy engine
engine = create_engine(connection_string)

# Test the connection
try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT @@version"))
        for row in result:
            print(row)
    print("Connection successful.")
except Exception as e:
    print(f"Error occurred: {e}")
