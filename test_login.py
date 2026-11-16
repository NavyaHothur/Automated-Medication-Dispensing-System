from database import get_db_connection
from werkzeug.security import check_password_hash

connection = get_db_connection()
cursor = connection.cursor(dictionary=True)

cursor.execute(
    "SELECT * FROM users WHERE username = %s",
    ("admin",)
)

user = cursor.fetchone()

if user:
    print("Admin user found!")

    result = check_password_hash(
        user["password_hash"],
        "Admin@12345"
    )

    print("Password verification:", result)

else:
    print("Admin user not found!")

cursor.close()
connection.close()