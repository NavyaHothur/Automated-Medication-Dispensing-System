
from database import get_db_connection
from werkzeug.security import generate_password_hash

connection = get_db_connection()

if connection is None:
    raise SystemExit("Database connection failed")

cursor = connection.cursor()

doctors = [
    ("doctor1", "Doctor1@12345", 1, 1),
    ("doctor2", "Doctor2@12345", 2, 2)
]

try:
    for username, password, department_id, doctor_id in doctors:
        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users
            (username, password_hash, role, department_id, doctor_id)
            VALUES (%s, %s, 'Doctor', %s, %s)
            ON DUPLICATE KEY UPDATE
                password_hash = %s,
                role = 'Doctor',
                department_id = %s,
                doctor_id = %s
        """, (
            username,
            password_hash,
            department_id,
            doctor_id,
            password_hash,
            department_id,
            doctor_id
        ))

    connection.commit()
    print("Doctor accounts created successfully!")

except Exception as error:
    connection.rollback()
    print("Error:", error)

finally:
    cursor.close()
    connection.close()
