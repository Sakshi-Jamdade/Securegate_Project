import mysql.connector
from mysql.connector import Error
from flask import Blueprint, jsonify, request, session
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Blueprint for admin routes
admin_bp = Blueprint('admin', __name__)

# Database Configuration
db_config = {
    'host': 'localhost',
    'database': 'project',
    'user': 'root',
    'password': 'root',
    'port' : "3333"
}

# Database Connection Function
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Database connected successfully!")
            return connection
        else:
            print("Connection established but not active")
            return None
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Authentication Check
def check_admin_session():
    if 'logged_in' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    return None

# Admin Login
@admin_bp.route('/login', methods=['POST'])
def login_admin():
    data = request.get_json()
    email, password = data.get('email'), data.get('password')
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password required'}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin WHERE email = %s AND password = %s", (email, password))
        admin = cursor.fetchone()
        if admin:
            session['admin_id'] = admin['id']
            session['role'] = 'admin'
            session['logged_in'] = True
            return jsonify({'success': True, 'admin': {'id': admin['id'], 'name': admin['name'], 'email': admin['email']}})
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Error as e:
        print(f"Database error in login_admin: {e}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Admin Profile
@admin_bp.route('/profile', methods=['GET'])
def get_admin_profile():
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    admin_id = session.get('admin_id')
    if not admin_id:
        return jsonify({'success': False, 'message': 'No admin ID in session'}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, whatsapp FROM admin WHERE id = %s", (admin_id,))
        admin = cursor.fetchone()
        if admin:
            admin['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return jsonify({'success': True, 'admin': admin})
        return jsonify({'success': False, 'message': 'Admin not found'}), 404
    except Error as e:
        print(f"Database error in get_admin_profile: {e}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Dashboard Stats
@admin_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        stats = {
            'todayVisitors': 0,
            'monthlyVisitors': 0,
            'activeGuards': 0,
            'totalFlats': 0
        }
        cursor.execute("SELECT COUNT(*) as count FROM visitors WHERE DATE(entry_time) = CURDATE()")
        stats['todayVisitors'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM visitors WHERE entry_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)")
        stats['monthlyVisitors'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM guard")
        stats['activeGuards'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM flat_owner")
        stats['totalFlats'] = cursor.fetchone()['count']
        return jsonify({'success': True, 'stats': stats})
    except Error as e:
        print(f"Database error in get_dashboard_stats: {e}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Today's Visitors
@admin_bp.route('/today-visitors', methods=['GET'])
def get_today_visitors():
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, visitor_name as name, flat_number, purpose, 
                   entry_time, exit_time, status
            FROM visitors 
            WHERE DATE(entry_time) = CURDATE()
        """)
        visitors = cursor.fetchall()
        for visitor in visitors:
            visitor['entry_time'] = visitor['entry_time'].strftime('%H:%M %p') if visitor['entry_time'] else '-'
            visitor['exit_time'] = visitor['exit_time'].strftime('%H:%M %p') if visitor['exit_time'] else '-'
        return jsonify({'success': True, 'visitors': visitors})
    except Error as e:
        print(f"Database error in get_today_visitors: {e}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Guard Records
@admin_bp.route('/guard-records', methods=['GET'])
def get_guard_records():
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, whatsapp as contact, 'Morning' as shift, 'On Duty' as status FROM guard")
        guards = cursor.fetchall()
        return jsonify({'success': True, 'guards': guards})
    except Error as e:
        print(f"Database error in get_guard_records: {e}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Flat Owners
@admin_bp.route('/flat-owners', methods=['GET'])
def get_flat_owners():
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT fo.flat_number, fo.name, fo.whatsapp as contact, 
                   COUNT(fm.id) as members, 'Resident' as status
            FROM flat_owner fo
            LEFT JOIN family_members fm ON fo.id = fm.owner_id
            GROUP BY fo.id, fo.flat_number, fo.name, fo.whatsapp
        """)
        owners = cursor.fetchall()
        return jsonify({'success': True, 'owners': owners})
    except Error as e:
        print(f"Database error in get_flat_owners: {e}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Visitor Records with Filters
@admin_bp.route('/visitor-records', methods=['GET'])
def get_visitor_records():
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    date_range = request.args.get('dateRange')
    status = request.args.get('status')
    search = request.args.get('search', '')

    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT id, visitor_name as name, flat_number, purpose, 
                   entry_time, exit_time, status
            FROM visitors
            WHERE 1=1
        """
        params = []
        if date_range:
            start_date, end_date = date_range.split(' - ')
            query += " AND entry_time BETWEEN %s AND %s"
            params.extend([start_date, end_date + ' 23:59:59'])
        if status and status != '':
            query += " AND status = %s"
            params.append(status)
        if search:
            query += " AND (visitor_name LIKE %s OR flat_number LIKE %s OR purpose LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        cursor.execute(query, params)
        visitors = cursor.fetchall()
        for visitor in visitors:
            visitor['entry_time'] = visitor['entry_time'].strftime('%H:%M %p') if visitor['entry_time'] else '-'
            visitor['exit_time'] = visitor['exit_time'].strftime('%H:%M %p') if visitor['exit_time'] else '-'
        return jsonify({'success': True, 'visitors': visitors})
    except Error as e:
        print(f"Database error in get_visitor_records: {e}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Delete Visitor
@admin_bp.route('/delete-visitor/<int:visitor_id>', methods=['POST'])
def delete_visitor(visitor_id):
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM visitors WHERE id = %s", (visitor_id,))
        connection.commit()
        return jsonify({'success': True, 'message': 'Visitor deleted successfully'})
    except Error as e:
        print(f"Database error in delete_visitor: {e}")
        return jsonify({'success': False, 'message': f'Error deleting visitor: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Logout
@admin_bp.route('/logout', methods=['GET'])
def logout_admin():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# Test database connection on load (optional, remove after testing)
def test_db_connection():
    connection = get_db_connection()
    if connection:
        print("Admin database connection test: SUCCESS")
        connection.close()
    else:
        print("Admin database connection test: FAILED")


