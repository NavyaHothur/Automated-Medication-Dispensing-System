# Automated Medication Dispensing System

A web-based medication dispensing and inventory management system designed for two hospital emergency departments.

## Project Overview

This project automates the management of patients, doctors, medicines, prescriptions and department-wise inventory. It provides separate access for Admin, Doctors and Pharmacists.

## Features

- Role-based login and authentication
- Patient management
- Doctor management
- Medicine management
- Prescription creation and tracking
- Department-wise inventory management
- Automatic stock deduction during dispensing
- Low-stock monitoring
- Dispensing history
- Department-based access restrictions

## User Roles

| Role | Responsibilities |
|---|---|
| Admin | Manage records across departments |
| Doctor | View department patients and medicines, create prescriptions |
| Pharmacist | View prescriptions, update inventory and dispense medicines |

## Technologies Used

- Python
- Flask
- MySQL
- HTML
- CSS
- MySQL Connector
- Werkzeug

## Database Design

The system uses eight relational tables:

1. Departments
2. Patients
3. Doctors
4. Medicines
5. Inventory
6. Prescriptions
7. Dispensing
8. Users

The database uses primary keys, foreign keys and relational constraints to maintain data integrity.

## Project Structure

```text
Medication_Dispensing_System/
│
├── app.py
├── database.py
├── create_doctor_users.py
├── create_passwords.py
├── test_login.py
├── requirements.txt
├── .gitignore
│
├── static/
│   └── style.css
│
└── templates/
    ├── login.html
    ├── dashboard.html
    ├── doctor_dashboard.html
    ├── pharmacist_dashboard.html
    ├── patients.html
    ├── medicines.html
    ├── prescriptions.html
    ├── inventory.html
    └── dispensing.html
```

## Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/NavyaHothur/Automated-Medication-Dispensing-System.git
```

2. Open the project directory:

```bash
cd Automated-Medication-Dispensing-System
```

3. Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Create the MySQL database and configure the database connection using a local `.env` file.

Example `.env` configuration:

```env
DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=medication_dispensing_db
DB_PORT=3306
```

6. Set up the database tables and required application user records.

7. Run the Flask application:

```bash
python app.py
```

8. Open the application:

```text
http://127.0.0.1:5000
```

## Important Notes

- Do not upload `.env` files, database passwords or other credentials.
- This project is an academic prototype and is not clinically validated for real hospital deployment.

## Author

**NavyaHothur**

GitHub: https://github.com/NavyaHothur
