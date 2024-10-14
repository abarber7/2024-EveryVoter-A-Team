# Connection String 1
#connection_string_1 = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:appropriate-server.database.windows.net,1433;Database=appropriate-db;Uid=jerrod.estell@wsu.edu;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;Authentication=ActiveDirectoryIntegrated"

# Connection String 2
#connection_string_2 = "Server=tcp:appropriate-server.database.windows.net,1433;Initial Catalog=appropriate-db;Persist Security Info=False;User ID=jerrod.estell@wsu.edu;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Authentication=Active Directory Integrated;"

# Connection String 3
#connection_string_3 = "Server=tcp:appropriate-server.database.windows.net,1433;Initial Catalog=appropriate-db;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;Authentication=Active Directory Default;"

import urllib.parse
from sqlalchemy import create_engine, text
import pyodbc

# Updated Connection String 2
connection_string_2 = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=tcp:appropriate-server.database.windows.net,1433;"
    "Database=appropriate-db;"
    "Uid=antonio.barber@wsu.edu;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
    "Authentication=ActiveDirectoryInteractive"
)

params = urllib.parse.quote_plus(connection_string_2)
DATABASE_CONNECTION_STRING = f"mssql+pyodbc:///?odbc_connect={params}"

def test_connection(connection_string):
    try:
        # Create the SQLAlchemy engine
        engine = create_engine(connection_string, echo=True)

        # Try to connect and execute a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Connection successful!")
            print("Query result:", result.scalar())

    except Exception as e:
        print("Connection failed.")
        print("Error:", str(e))
        
        # Additional error information
        print("\nAdditional troubleshooting information:")
        print("Available ODBC drivers:")
        drivers = [driver for driver in pyodbc.drivers()]
        print(drivers)

if __name__ == "__main__":
    print("Testing database connection...")
    test_connection(DATABASE_CONNECTION_STRING)

    # If the above fails, try connecting directly with pyodbc
    print("\nAttempting direct pyodbc connection...")
    try:
        conn = pyodbc.connect(connection_string_2)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print("Direct pyodbc connection successful!")
        conn.close()
    except pyodbc.Error as e:
        print("Direct pyodbc connection failed.")
        print("Error:", str(e))