import pyodbc
#Driver={ODBC Driver 18 for SQL Server};Server=tcp:appropriate-server.database.windows.net,1433;Database=appropriate-db;Uid=jrod;Pwd={your_password_here};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
# Define the connection string components
server = 'appropriate-server.database.windows.net'
database = 'appropriate-db'
username = 'jrod'
password = 'yourpass'  # Make sure this is the correct password
driver = '{ODBC Driver 18 for SQL Server}'

# Create the connection string
connection_string = (
    f'DRIVER={driver};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;'
)

# Try to connect to the database
try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Test the connection with a simple query
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    
    if result:
        print("Connection successful!")
    else:
        print("Connection failed, no result from query.")

except Exception as e:
    print(f"Connection failed: {e}")
