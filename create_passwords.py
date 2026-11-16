from werkzeug.security import generate_password_hash
from database import get_db_connection

users = {
    "admin": "Admin@12345",
    "pharmacist1": "Pharma1@12345",
    "pharmacist2": "Pharma2@12345"
}

connection = get_db_connection()

if connection:
    cursor = connection.cursor()

    for username, password in users.items():

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            UPDATE users
            SET password_hash = %s
            WHERE username = %s
            """,
            (password_hash, username)
        )

        print(username, "password updated successfully")

    connection.commit()

    cursor.close()
    connection.close()

    print("\nAll user passwords updated successfully!")