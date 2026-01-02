import os
from flask import Flask, request, jsonify
import psycopg2
from psycopg2 import extras
from datetime import datetime, UTC
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Neon Database Connection String
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def format_response(status_code, error, path, payload=None, message=None):
    """
    Helper function to format consistent API responses.
    """
    response = {
        "statusCode": status_code,
        "error": error,
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "path": path,
    }
    if payload is not None:
        response["payload"] = payload
    if message is not None:
        response["message"] = message
    return jsonify(response), status_code

@app.route('/employee/<string:email>', methods=['GET'])
def get_employee_by_email(email):
    conn = get_db_connection()
    if conn is None:
        return format_response(500, True, request.path, message="Database connection failed")

    cur = None
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id, email, company_id, company_name FROM employees WHERE email = %s", (email,))
        employee = cur.fetchone()

        if employee:
            payload = {
                "id": str(employee["id"]),
                "email": employee["email"],
                "companyId": str(employee["company_id"]),
                "companyName": employee["company_name"]
            }
            return format_response(200, False, request.path, payload=payload)
        else:
            return format_response(404, True, request.path, message=f"Employee with email '{email}' not found")
    except Exception as e:
        print(f"Error fetching employee: {e}")
        return format_response(500, True, request.path, message=f"Internal server error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/employees', methods=['GET'])
def get_all_employees():
    conn = get_db_connection()
    if conn is None:
        return format_response(500, True, request.path, message="Database connection failed")
    
    cur = None
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id, email, company_id, company_name FROM employees")
        employees = cur.fetchall()

        payload = [
            {
                "id": str(employee["id"]),
                "email": employee["email"],
                "companyId": str(employee["company_id"]),
                "companyName": employee["company_name"]
            }
            for employee in employees
        ]
        return format_response(200, False, request.path, payload=payload)
    except Exception as e:
        print(f"Error fetching employees: {e}")
        return format_response(500, True, request.path, message=f"Internal server error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/companies', methods=['GET'])
def get_all_companies():
    conn = get_db_connection()
    if conn is None:
        return format_response(500, True, request.path, message="Database connection failed")
    
    cur = None
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT company_id, name FROM companies")
        companies = cur.fetchall()

        payload = [
            {
                "companyId": str(company["company_id"]),
                "name": company["name"]
            }
            for company in companies
        ]
        return format_response(200, False, request.path, payload=payload)
    except Exception as e:
        print(f"Error fetching companies: {e}")
        return format_response(500, True, request.path, message=f"Internal server error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/companies/<string:company_id>', methods=['GET'])
def get_company_by_id(company_id):
    conn = get_db_connection()
    if conn is None:
        return format_response(500, True, request.path, message="Database connection failed")

    cur = None
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT company_id, name FROM companies WHERE company_id = %s", (company_id,))
        company = cur.fetchone()

        if company:
            payload = {
                "companyId": str(company["company_id"]),
                "name": company["name"]
            }
            return format_response(200, False, request.path, payload=payload)
        else:
            return format_response(404, True, request.path, message=f"Company with ID '{company_id}' not found")
    except Exception as e:
        print(f"Error fetching company: {e}")
        return format_response(500, True, request.path, message=f"Internal server error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/companies', methods=['POST'])
def create_company():
    data = request.get_json()
    if not data:
        return format_response(400, True, request.path, message="Request body must be JSON")

    company_id = data.get('company_id')
    name = data.get('name')

    if not company_id or not name:
        return format_response(400, True, request.path, message="Missing 'company_id' or 'name' in request body")

    try:
        # Validate company_id is a valid UUID
        uuid.UUID(company_id)
    except ValueError:
        return format_response(400, True, request.path, message="Invalid 'company_id' format (must be a valid UUID)")

    conn = get_db_connection()
    if conn is None:
        return format_response(500, True, request.path, message="Database connection failed")

    cur = None
    try:
        cur = conn.cursor()
        # Check if company_id already exists
        cur.execute("SELECT COUNT(*) FROM companies WHERE company_id = %s", (company_id,))
        if cur.fetchone()[0] > 0:
            return format_response(409, True, request.path, message=f"Company with ID '{company_id}' already exists")

        # Insert new company
        cur.execute(
            "INSERT INTO companies (company_id, name) VALUES (%s, %s)",
            (company_id, name)
        )
        conn.commit()

        # For the POST response, we need to mimic the provided structure.
        # Some fields like 'id', 'app_id', 'monthly_spend', etc., are not
        # directly stored in our simple `companies` table. We'll generate/mock them.
        # In a real-world scenario, these would come from an external service or a more complex schema.

        # Generate a unique ID (example for `id` field in the response)
        generated_id = uuid.uuid4().hex[:24] # 24 characters as in the example

        response_payload = {
            "type": "company",
            "company_id": company_id,
            "id": generated_id, # Mocked ID
            "app_id": "w9shsv7c", # Hardcoded/Mocked
            "name": name,
            "created_at": int(datetime.now().timestamp()), # Current timestamp
            "updated_at": int(datetime.now().timestamp()), # Current timestamp
            "monthly_spend": 0,
            "session_count": 0,
            "user_count": 0, # Assuming 0 for a newly created company
            "tags": {
                "type": "tag.list",
                "tags": []
            },
            "segments": {
                "type": "segment.list",
                "segments": []
            },
            "plan": {},
            "custom_attributes": {
                "creation_source": "api"
            }
        }
        return jsonify(response_payload), 201 # 201 Created
    except Exception as e:
        conn.rollback()
        print(f"Error creating company: {e}")
        return format_response(500, True, request.path, message=f"Internal server error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    # For development, you can run with debug=True
    app.run(debug=True, port=5000)

@app.route('/order-status', methods=['GET'])
def get_order_status():
    payload = {
        "eligibleForRefund": True
    }
    return format_response(
        status_code=200,
        error=False,
        path=request.path,
        payload=payload
    )
