import mysql.connector
from dotenv import load_dotenv
import os

# Load database credentials from .env
load_dotenv()

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306))
        )

        return connection

    except mysql.connector.Error as error:
        print("Database connection failed:", error)
        return None


# Test database connection
if __name__ == "__main__":
    connection = get_db_connection()

    if connection and connection.is_connected():
        print("Successfully connected to MySQL!")
        print("Database:", connection.database)
        connection.close()