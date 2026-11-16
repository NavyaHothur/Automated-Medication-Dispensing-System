from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import get_db_connection
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-before-deployment"


# Home page - Display login
@app.route('/')
def home():
    return render_template('login.html')


# Login authentication


@app.route('/login', methods=['POST'])
def login():

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user and check_password_hash(user['password_hash'], password):

        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['department_id'] = user['department_id']
        session['doctor_id'] = user['doctor_id']

        if user['role'] == 'Admin':
            return redirect(url_for('dashboard'))

        elif user['role'] == 'Pharmacist':
            return redirect(url_for('pharmacist_dashboard'))

        elif user['role'] == 'Doctor':
            return redirect(url_for('doctor_dashboard'))

    flash("Invalid username or password")
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!")
    return redirect(url_for('home'))
# Dashboard page

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    if session.get('role') != 'Admin':
        return redirect(url_for('pharmacist_dashboard'))
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM patients")
    total_patients = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM medicines")
    total_medicines = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM prescriptions")
    total_prescriptions = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM prescriptions
        WHERE status = 'Pending'
    """)
    pending_prescriptions = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM dispensing")
    total_dispensing = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM inventory
        WHERE quantity_available <= minimum_stock
    """)
    low_stock_count = cursor.fetchone()['total']

    cursor.execute("""
        SELECT d.department_name,
               SUM(i.quantity_available) AS total_stock
        FROM inventory i
        JOIN departments d
        ON i.department_id = d.department_id
        GROUP BY d.department_id, d.department_name
    """)
    department_stock = cursor.fetchall()
    cursor.execute("""
    SELECT
        m.medicine_name,
        SUM(CASE WHEN i.department_id = 1
            THEN i.quantity_available ELSE 0 END) AS Department_1_Stock,
        SUM(CASE WHEN i.department_id = 2
            THEN i.quantity_available ELSE 0 END) AS Department_2_Stock
    FROM inventory i
    JOIN medicines m
        ON i.medicine_id = m.medicine_id
    GROUP BY m.medicine_id, m.medicine_name
    ORDER BY m.medicine_name
""")

    medicine_comparison = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        'dashboard.html',
        total_patients=total_patients,
        total_medicines=total_medicines,
        total_prescriptions=total_prescriptions,
        pending_prescriptions=pending_prescriptions,
        total_dispensing=total_dispensing,
        low_stock_count=low_stock_count,
        department_stock=department_stock,
        medicine_comparison=medicine_comparison
    )





@app.route('/patients', methods=['GET', 'POST'])
def patients():

    if 'user_id' not in session:
        return redirect(url_for('home'))

    role = session.get('role')
    department_id = session.get('department_id')

    if role not in ['Admin', 'Pharmacist', 'Doctor']:
        return redirect(url_for('home'))

    # Doctors can only view patients, not add them
    if role == 'Doctor' and request.method == 'POST':
        flash("Doctors can only view patient records.")
        return redirect(url_for('patients'))

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':

        patient_name = request.form['patient_name']
        age = request.form['age']
        gender = request.form['gender']
        phone = request.form['phone']

        if role == 'Admin':
            patient_department = request.form['department_id']
        else:
            patient_department = department_id

        cursor.execute("""
            INSERT INTO patients
            (patient_name, age, gender, phone, department_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            patient_name,
            age,
            gender,
            phone,
            patient_department
        ))

        connection.commit()
        cursor.close()
        connection.close()

        flash("Patient added successfully!")
        return redirect(url_for('patients'))

    if role == 'Admin':

        cursor.execute("SELECT * FROM patients")
        patients = cursor.fetchall()

        cursor.execute("SELECT * FROM departments")
        departments = cursor.fetchall()

    else:

        cursor.execute("""
            SELECT * FROM patients
            WHERE department_id = %s
        """, (department_id,))
        patients = cursor.fetchall()

        cursor.execute("""
            SELECT * FROM departments
            WHERE department_id = %s
        """, (department_id,))
        departments = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        'patients.html',
        patients=patients,
        departments=departments,
        role=role
    )



@app.route('/medicines', methods=['GET', 'POST'])
def medicines():

    if 'user_id' not in session:
        return redirect(url_for('home'))

    role = session.get('role')
    department_id = session.get('department_id')

    if role not in ['Admin', 'Pharmacist', 'Doctor']:
        return redirect(url_for('home'))

    # Only Admin can add medicines
    if role != 'Admin' and request.method == 'POST':
        flash("Only Admin can add new medicines.")
        return redirect(url_for('medicines'))

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':

        medicine_name = request.form['medicine_name']
        category = request.form['category']
        manufacturer = request.form['manufacturer']
        unit_price = request.form['unit_price']
        expiry_date = request.form['expiry_date']

        cursor.execute("""
            INSERT INTO medicines
            (medicine_name, category, manufacturer, unit_price, expiry_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            medicine_name,
            category,
            manufacturer,
            unit_price,
            expiry_date
        ))

        connection.commit()
        cursor.close()
        connection.close()

        flash("Medicine added successfully!")
        return redirect(url_for('medicines'))

    if role == 'Doctor':

        cursor.execute("""
            SELECT DISTINCT m.*
            FROM medicines m
            INNER JOIN inventory i
                ON m.medicine_id = i.medicine_id
            WHERE i.department_id = %s
              AND i.quantity_available > 0
        """, (department_id,))

    else:

        cursor.execute("SELECT * FROM medicines")

    medicines = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        'medicines.html',
        medicines=medicines,
        role=role
    )



@app.route('/prescriptions', methods=['GET', 'POST'])
def prescriptions():

    if 'user_id' not in session:
        return redirect(url_for('home'))

    role = session.get('role')
    department_id = session.get('department_id')
    doctor_id = session.get('doctor_id')

    if role not in ['Admin', 'Pharmacist', 'Doctor']:
        return redirect(url_for('home'))

    # Pharmacists cannot create prescriptions
    if role == 'Pharmacist' and request.method == 'POST':
        flash("Pharmacists can only view prescriptions.")
        return redirect(url_for('prescriptions'))

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':

        patient_id = request.form['patient_id']
        medicine_id = request.form['medicine_id']
        dosage = request.form['dosage']
        frequency = request.form['frequency']
        duration_days = request.form['duration_days']
        prescribed_quantity = request.form['prescribed_quantity']

        if role == 'Admin':
            prescription_doctor_id = request.form['doctor_id']

            cursor.execute("""
                SELECT patient_id
                FROM patients
                WHERE patient_id = %s
            """, (patient_id,))

        else:
            prescription_doctor_id = doctor_id

            cursor.execute("""
                SELECT patient_id
                FROM patients
                WHERE patient_id = %s
                AND department_id = %s
            """, (patient_id, department_id))

        patient = cursor.fetchone()

        if not patient:
            cursor.close()
            connection.close()
            flash("You cannot create a prescription for this patient.")
            return redirect(url_for('prescriptions'))

        # Check medicine is stocked in the patient's department
        if role != 'Admin':
            cursor.execute("""
                SELECT inventory_id
                FROM inventory
                WHERE department_id = %s
                AND medicine_id = %s
            """, (department_id, medicine_id))

            if not cursor.fetchone():
                cursor.close()
                connection.close()
                flash("This medicine is not available in your department inventory.")
                return redirect(url_for('prescriptions'))

        cursor.execute("""
            INSERT INTO prescriptions
            (patient_id, doctor_id, medicine_id, dosage,
             frequency, duration_days, prescribed_quantity)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            patient_id,
            prescription_doctor_id,
            medicine_id,
            dosage,
            frequency,
            duration_days,
            prescribed_quantity
        ))

        connection.commit()
        cursor.close()
        connection.close()

        flash("Prescription added successfully!")
        return redirect(url_for('prescriptions'))

    # Fetch prescription records according to role
    if role == 'Admin':

        cursor.execute("SELECT * FROM prescriptions")
        prescription_records = cursor.fetchall()

        cursor.execute("SELECT * FROM patients")
        patients = cursor.fetchall()

        cursor.execute("SELECT * FROM doctors")
        doctors = cursor.fetchall()

        cursor.execute("SELECT * FROM medicines")
        medicines = cursor.fetchall()

    elif role == 'Doctor':

        cursor.execute("""
            SELECT *
            FROM prescriptions
            WHERE doctor_id = %s
        """, (doctor_id,))
        prescription_records = cursor.fetchall()

        cursor.execute("""
            SELECT *
            FROM patients
            WHERE department_id = %s
        """, (department_id,))
        patients = cursor.fetchall()

        cursor.execute("""
            SELECT *
            FROM doctors
            WHERE doctor_id = %s
        """, (doctor_id,))
        doctors = cursor.fetchall()

        cursor.execute("""
            SELECT DISTINCT m.*
            FROM medicines m
            JOIN inventory i ON m.medicine_id = i.medicine_id
            WHERE i.department_id = %s
        """, (department_id,))
        medicines = cursor.fetchall()

    else:

        cursor.execute("""
            SELECT p.*
            FROM prescriptions p
            JOIN patients pt ON p.patient_id = pt.patient_id
            WHERE pt.department_id = %s
        """, (department_id,))
        prescription_records = cursor.fetchall()

        patients = []
        doctors = []
        medicines = []

    cursor.close()
    connection.close()

    return render_template(
        'prescriptions.html',
        prescriptions=prescription_records,
        patients=patients,
        doctors=doctors,
        medicines=medicines,
        role=role
    )


@app.route('/dispensing', methods=['GET', 'POST'])
def dispensing():

    if 'user_id' not in session:
        return redirect(url_for('home'))

    role = session.get('role')
    department_id = session.get('department_id')

    if role not in ['Admin', 'Pharmacist']:
        return redirect(url_for('home'))

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':

        if role != 'Pharmacist' and role != 'Admin':
            cursor.close()
            connection.close()
            return redirect(url_for('home'))

        prescription_id = request.form['prescription_id']

        try:
            connection.start_transaction()

            # Get prescription and patient department
            cursor.execute("""
                SELECT p.*, pt.department_id
                FROM prescriptions p
                JOIN patients pt
                    ON p.patient_id = pt.patient_id
                WHERE p.prescription_id = %s
                FOR UPDATE
            """, (prescription_id,))

            prescription = cursor.fetchone()

            if not prescription:
                flash("Prescription not found!")

            elif (
                role == 'Pharmacist'
                and prescription['department_id'] != department_id
            ):
                flash("You cannot dispense prescriptions from another department!")

            elif prescription['status'] != 'Pending':
                flash("This prescription has already been processed!")

            else:

                # Find and lock the correct department inventory
                cursor.execute("""
                    SELECT inventory_id, quantity_available
                    FROM inventory
                    WHERE department_id = %s
                    AND medicine_id = %s
                    FOR UPDATE
                """, (
                    prescription['department_id'],
                    prescription['medicine_id']
                ))

                stock = cursor.fetchone()

                if not stock:
                    flash("No matching inventory found!")

                elif stock['quantity_available'] < prescription['prescribed_quantity']:
                    flash("Insufficient medicine stock!")

                else:
                    quantity = prescription['prescribed_quantity']

                    # Reduce available stock
                    cursor.execute("""
                        UPDATE inventory
                        SET quantity_available = quantity_available - %s
                        WHERE inventory_id = %s
                    """, (quantity, stock['inventory_id']))

                    # Record dispensing
                    cursor.execute("""
                        INSERT INTO dispensing
                        (prescription_id, inventory_id,
                         quantity_dispensed, dispensed_by, status)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        prescription_id,
                        stock['inventory_id'],
                        quantity,
                        session.get('username'),
                        'Dispensed'
                    ))

                    # Update prescription status
                    cursor.execute("""
                        UPDATE prescriptions
                        SET status = 'Dispensed'
                        WHERE prescription_id = %s
                    """, (prescription_id,))

                    connection.commit()
                    flash("Medicine dispensed successfully!")

            # Commit read-only or rejected attempts
            if connection.in_transaction:
                connection.commit()

        except Exception as error:
            connection.rollback()
            print("Dispensing error:", error)
            flash("Dispensing failed. Please try again.")

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('dispensing'))

    # Fetch dispensing history
    if role == 'Admin':

        cursor.execute("""
            SELECT
                d.dispensing_id,
                d.prescription_id,
                d.quantity_dispensed,
                d.dispensed_by,
                d.dispensing_date,
                d.status,
                p.patient_id,
                m.medicine_name
            FROM dispensing d
            JOIN prescriptions p
                ON d.prescription_id = p.prescription_id
            JOIN patients pt
                ON p.patient_id = pt.patient_id
            JOIN medicines m
                ON p.medicine_id = m.medicine_id
            ORDER BY d.dispensing_id
        """)

        dispensing_records = cursor.fetchall()

        cursor.execute("""
            SELECT
                p.prescription_id,
                p.patient_id,
                p.medicine_id,
                p.prescribed_quantity
            FROM prescriptions p
            WHERE p.status = 'Pending'
            AND NOT EXISTS (
                SELECT 1
                FROM dispensing d
                WHERE d.prescription_id = p.prescription_id
            )
        """)

        pending_prescriptions = cursor.fetchall()

    else:

        cursor.execute("""
            SELECT
                d.dispensing_id,
                d.prescription_id,
                d.quantity_dispensed,
                d.dispensed_by,
                d.dispensing_date,
                d.status,
                p.patient_id,
                m.medicine_name
            FROM dispensing d
            JOIN prescriptions p
                ON d.prescription_id = p.prescription_id
            JOIN patients pt
                ON p.patient_id = pt.patient_id
            JOIN medicines m
                ON p.medicine_id = m.medicine_id
            WHERE pt.department_id = %s
            ORDER BY d.dispensing_id
        """, (department_id,))

        dispensing_records = cursor.fetchall()

        cursor.execute("""
            SELECT
                p.prescription_id,
                p.patient_id,
                p.medicine_id,
                p.prescribed_quantity
            FROM prescriptions p
            JOIN patients pt
                ON p.patient_id = pt.patient_id
            WHERE p.status = 'Pending'
            AND pt.department_id = %s
            AND NOT EXISTS (
                SELECT 1
                FROM dispensing d
                WHERE d.prescription_id = p.prescription_id
            )
        """, (department_id,))

        pending_prescriptions = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        'dispensing.html',
        dispensing=dispensing_records,
        pending_prescriptions=pending_prescriptions,
        role=role
    )




@app.route('/inventory', methods=['GET', 'POST'])
def inventory():

    if 'user_id' not in session:
        return redirect(url_for('home'))

    role = session.get('role')
    department_id = session.get('department_id')

    if role not in ['Admin', 'Pharmacist']:
        return redirect(url_for('home'))

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':

        inventory_id = request.form['inventory_id']
        quantity = request.form['quantity_available']

        try:
            quantity = int(quantity)

            if quantity < 0:
                flash("Quantity cannot be negative!")

            else:
                if role == 'Admin':
                    cursor.execute("""
                        UPDATE inventory
                        SET quantity_available = %s
                        WHERE inventory_id = %s
                    """, (quantity, inventory_id))

                else:
                    cursor.execute("""
                        UPDATE inventory
                        SET quantity_available = %s
                        WHERE inventory_id = %s
                        AND department_id = %s
                    """, (quantity, inventory_id, department_id))

                if cursor.rowcount == 0:
                    flash("You cannot update inventory from another department!")
                else:
                    connection.commit()
                    flash("Stock updated successfully!")

        except ValueError:
            flash("Please enter a valid quantity!")

        cursor.close()
        connection.close()

        return redirect(url_for('inventory'))

    if role == 'Admin':

        cursor.execute("""
            SELECT
                inventory.inventory_id,
                departments.department_name,
                medicines.medicine_name,
                inventory.quantity_available,
                inventory.minimum_stock,
                inventory.last_updated
            FROM inventory
            JOIN departments
                ON inventory.department_id = departments.department_id
            JOIN medicines
                ON inventory.medicine_id = medicines.medicine_id
            ORDER BY departments.department_id, medicines.medicine_name
        """)

        inventory_records = cursor.fetchall()

        cursor.execute("""
            SELECT
                departments.department_name,
                medicines.medicine_name,
                inventory.quantity_available,
                inventory.minimum_stock
            FROM inventory
            JOIN departments
                ON inventory.department_id = departments.department_id
            JOIN medicines
                ON inventory.medicine_id = medicines.medicine_id
            WHERE inventory.quantity_available <= inventory.minimum_stock
        """)

        low_stock_records = cursor.fetchall()

    else:

        cursor.execute("""
            SELECT
                inventory.inventory_id,
                departments.department_name,
                medicines.medicine_name,
                inventory.quantity_available,
                inventory.minimum_stock,
                inventory.last_updated
            FROM inventory
            JOIN departments
                ON inventory.department_id = departments.department_id
            JOIN medicines
                ON inventory.medicine_id = medicines.medicine_id
            WHERE inventory.department_id = %s
            ORDER BY medicines.medicine_name
        """, (department_id,))

        inventory_records = cursor.fetchall()

        cursor.execute("""
            SELECT
                departments.department_name,
                medicines.medicine_name,
                inventory.quantity_available,
                inventory.minimum_stock
            FROM inventory
            JOIN departments
                ON inventory.department_id = departments.department_id
            JOIN medicines
                ON inventory.medicine_id = medicines.medicine_id
            WHERE inventory.department_id = %s
            AND inventory.quantity_available <= inventory.minimum_stock
        """, (department_id,))

        low_stock_records = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        'inventory.html',
        inventory=inventory_records,
        low_stock_records=low_stock_records,
        role=role
    )



@app.route('/pharmacist-dashboard')
def pharmacist_dashboard():

    if 'user_id' not in session:
        return redirect(url_for('home'))

    if session.get('role') != 'Pharmacist':
        return redirect(url_for('dashboard'))

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    department_id = session.get('department_id')

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM patients
        WHERE department_id = %s
    """, (department_id,))
    total_patients = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM inventory
        WHERE department_id = %s
    """, (department_id,))
    total_medicines = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM prescriptions p
        JOIN patients pt ON p.patient_id = pt.patient_id
        WHERE pt.department_id = %s
    """, (department_id,))
    total_prescriptions = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM prescriptions p
        JOIN patients pt ON p.patient_id = pt.patient_id
        WHERE pt.department_id = %s
        AND p.status = 'Pending'
    """, (department_id,))
    pending_prescriptions = cursor.fetchone()['total']

    cursor.close()
    connection.close()

    return render_template(
        'pharmacist_dashboard.html',
        total_patients=total_patients,
        total_medicines=total_medicines,
        total_prescriptions=total_prescriptions,
        pending_prescriptions=pending_prescriptions
    )


@app.route('/doctor-dashboard')
def doctor_dashboard():

    if 'user_id' not in session:
        return redirect(url_for('home'))

    if session.get('role') != 'Doctor':
        return redirect(url_for('home'))

    connection = get_db_connection()

    if connection is None:
        return "Database connection failed"

    cursor = connection.cursor(dictionary=True)

    doctor_id = session.get('doctor_id')
    department_id = session.get('department_id')

    cursor.execute("""
        SELECT doctor_name, specialization
        FROM doctors
        WHERE doctor_id = %s
    """, (doctor_id,))

    doctor = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM patients
        WHERE department_id = %s
    """, (department_id,))

    total_patients = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM prescriptions
        WHERE doctor_id = %s
    """, (doctor_id,))

    total_prescriptions = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM prescriptions
        WHERE doctor_id = %s
        AND status = 'Pending'
    """, (doctor_id,))

    pending_prescriptions = cursor.fetchone()['total']

    cursor.close()
    connection.close()

    return render_template(
        'doctor_dashboard.html',
        doctor=doctor,
        total_patients=total_patients,
        total_prescriptions=total_prescriptions,
        pending_prescriptions=pending_prescriptions
    )

if __name__ == '__main__':
    app.run(debug=True)