import mysql.connector
from mysql.connector import Error
from flask import jsonify, session, request

# ✅ Database Configuration
db_config = {
    'host': 'localhost',
    'database': 'project',
    'user': 'root',
    'password': 'root',
    'port' : "3333"
}

# ✅ Fetch Flat Owner Dashboard Stats
def get_flat_owner_dashboard_stats():
    connection = None
    cursor = None
    try:
        # ✅ Session Check
        email = session.get('email')
        if not email or session.get('role') != 'flat_owner':
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        # ✅ Connect to Database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # ✅ Fetch owner_id from email
        cursor.execute("SELECT id FROM flat_owner WHERE email = %s", (email,))
        owner = cursor.fetchone()

        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404

        owner_id = owner['id']

        # ✅ Fetch Family Members Count
        cursor.execute("SELECT COUNT(*) AS total_family FROM family_members WHERE owner_id = %s", (owner_id,))
        family_count = cursor.fetchone()
        family_count = family_count['total_family'] if family_count else 0

        # ✅ Fetch Today's Visitors Count
        cursor.execute("""
            SELECT COUNT(*) AS todays_visitors 
            FROM visitors 
            WHERE owner_id = %s AND DATE(entry_time) = CURDATE()
        """, (owner_id,))
        today_visitors = cursor.fetchone()
        today_visitors = today_visitors['todays_visitors'] if today_visitors else 0

        # ✅ Fetch Pre-approved Visitors Count
        cursor.execute("""
            SELECT COUNT(*) AS pre_approved_visitors 
            FROM visitors 
            WHERE owner_id = %s AND status = 'pre-approved'
        """, (owner_id,))
        preapproved_visitors = cursor.fetchone()
        preapproved_visitors = preapproved_visitors['pre_approved_visitors'] if preapproved_visitors else 0

        # ✅ Fetch Pending Visitors Count
        cursor.execute("""
            SELECT COUNT(*) AS pending_visitors 
            FROM visitors 
            WHERE owner_id = %s AND status = 'pending'
        """, (owner_id,))
        pending_visitors = cursor.fetchone()
        pending_visitors = pending_visitors['pending_visitors'] if pending_visitors else 0

        # ✅ Return JSON Response
        return jsonify({
            "success": True,
            "family_members": family_count,
            "todays_visitors": today_visitors,
            "preapproved_visitors": preapproved_visitors,
            "pending_visitors": pending_visitors
        })

    except Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# ✅ Add Family Member API
def add_family_member():
    try:
        email = session.get('email')
        if not email or session.get('role') != 'flat_owner':
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # ✅ Fetch Flat Owner ID
        cursor.execute("SELECT id FROM flat_owner WHERE email = %s", (email,))
        owner = cursor.fetchone()
        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404
        owner_id = owner['id']

        # ✅ Get Form Data
        name = request.form.get('name')
        relationship = request.form.get('relationship')
        contact = request.form.get('contact')
        email = request.form.get('email')
        id_type = request.form.get('id_type')
        id_number = request.form.get('id_number')
        photo = request.form.get('photo')  # Assume the frontend sends a file URL or base64 string
        id_proof = request.form.get('id_proof')  # Assume the frontend sends a file URL or base64 string

        # ✅ Validate Required Fields
        if not name or name.strip() == "":
            return jsonify({"success": False, "message": "Name cannot be empty!"}), 400
        if not relationship or relationship.strip() == "":
            return jsonify({"success": False, "message": "Relationship is required!"}), 400
        if not id_type or id_type.strip() == "":
            return jsonify({"success": False, "message": "ID Type is required!"}), 400
        if not id_number or id_number.strip() == "":
            return jsonify({"success": False, "message": "ID Number is required!"}), 400

        # ✅ Debugging: Print SQL Query Before Execution
        print(f"""INSERT INTO family_members (owner_id, name, relationship, contact, email, id_type, id_number, photo, id_proof) 
                  VALUES ({owner_id}, '{name}', '{relationship}', '{contact}', '{email}', '{id_type}', '{id_number}', '{photo}', '{id_proof}')""")

        # ✅ Insert Data into `family_members` Table
        query = """INSERT INTO family_members (owner_id, name, relationship, contact, email, id_type, id_number, photo, id_proof) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (owner_id, name, relationship, contact, email, id_type, id_number, photo, id_proof)

        cursor.execute(query, values)
        connection.commit()

        return jsonify({"success": True, "message": "Family member added successfully!"}), 200

    except Error as e:
        print("Database Error:", str(e))  # ✅ Print error for debugging
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_family_members():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        email = session.get('email')
        cursor.execute("SELECT id FROM flat_owner WHERE email = %s", (email,))
        owner = cursor.fetchone()
        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404

        owner_id = owner['id']
        cursor.execute("SELECT id, name, relationship, contact FROM family_members WHERE owner_id = %s", (owner_id,))
        members = cursor.fetchall()

        return jsonify({"success": True, "members": members})

    except Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

# ✅ Fetch Visitor Records
def get_visitor_records():
    connection = None
    cursor = None
    try:
        email = session.get('email')
        if not email or session.get('role') != 'flat_owner':
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id FROM flat_owner WHERE email = %s", (email,))
        owner = cursor.fetchone()
        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404

        owner_id = owner['id']

        query = """
            SELECT visitor_name, contact_number, purpose, entry_time, exit_time, status
            FROM visitors
            WHERE owner_id = %s
            ORDER BY entry_time DESC
        """
        cursor.execute(query, (owner_id,))
        visitor_records = cursor.fetchall()

        for record in visitor_records:
            if record['entry_time']:
                record['entry_time'] = record['entry_time'].strftime('%Y-%m-%d %H:%M:%S')
            if record['exit_time']:
                record['exit_time'] = record['exit_time'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(visitor_records)

    except Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# ✅ Fetch Pre-approved Visitor Records
def get_pre_approved_visitors():
    if 'email' not in session or session.get('role') != 'flat_owner':
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id FROM flat_owner WHERE email = %s", (session['email'],))
        owner = cursor.fetchone()
        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404

        owner_id = owner['id']

        # ✅ Fetch only pre-approved visitors
        cursor.execute("""
            SELECT visitor_name, contact_number, purpose, expected_date, status
            FROM visitors
            WHERE owner_id = %s AND status = 'pre-approved'
            ORDER BY expected_date ASC
        """, (owner_id,))

        records = cursor.fetchall()

        return jsonify({"success": True, "pre_approved_visitors": records})

    except Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def pre_approve_visitor():
    connection = None
    cursor = None
    try:
        email = session.get('email')
        if not email or session.get('role') != 'flat_owner':
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id FROM flat_owner WHERE email = %s", (email,))
        owner = cursor.fetchone()
        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404
        owner_id = owner['id']

        data = request.get_json()
        visitor_name = data.get('visitor_name')
        contact = data.get('contact_number')  # Frontend sends 'contact_number'
        purpose = data.get('purpose')
        expected_date = data.get('expected_date')  # Comes as "YYYY-MM-DD HH:MM:SS"
        additional_notes = data.get('additional_notes')

        # Validate Required Fields
        if not all([visitor_name, contact, purpose, expected_date]):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        # Extract only the date part (YYYY-MM-DD) if needed
        expected_date = expected_date.split(" ")[0]  # Strips time if present

        query = """
            INSERT INTO visitors (owner_id, visitor_name, contact_number, purpose, expected_date, status)
            VALUES (%s, %s, %s, %s, %s, 'pre-approved')
        """
        values = (owner_id, visitor_name, contact, purpose, expected_date)
        cursor.execute(query, values)
        connection.commit()

        return jsonify({"success": True, "message": "Visitor pre-approved successfully"}), 200

    except Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()