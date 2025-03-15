from flask import Blueprint, jsonify, request, session
import mysql.connector
from datetime import datetime

guard_bp = Blueprint('guard', __name__, url_prefix='/guard')

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'project',
    'port': '3333'  # Verify this matches your MySQL setup
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        print("Database connected successfully")
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection failed: {str(e)}")
        raise Exception(f"Database connection failed: {str(e)}")

@guard_bp.route('/profile', methods=['GET'])
def get_guard_profile():
    if 'logged_in' not in session or session.get('role') != 'guard':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    guard_id = session.get('user_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, email, whatsapp 
            FROM guard 
            WHERE id = %s
        """, (guard_id,))
        guard = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if guard:
            return jsonify({
                'success': True,
                'guard': {
                    'id': guard['id'],
                    'name': guard['name'],
                    'email': guard['email'],
                    'whatsapp': guard['whatsapp'],
                    'shift': 'Day Shift'
                }
            })
        return jsonify({'success': False, 'message': 'Guard not found'}), 404
    except Exception as e:
        print(f"Error in get_guard_profile: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/stats', methods=['GET'])
def get_guard_stats():
    if 'logged_in' not in session or session.get('role') != 'guard':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM visitors WHERE status = 'approved' AND exit_time IS NULL")
        active_visitors = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM visitors WHERE DATE(entry_time) = CURDATE()")
        today_entries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM visitors WHERE status = 'pre-approved'")
        pre_approved = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM visitors WHERE status = 'pending'")
        pending_approvals = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'activeVisitors': active_visitors,
                'todayEntries': today_entries,
                'preApproved': pre_approved,
                'pendingApprovals': pending_approvals
            }
        })
    except Exception as e:
        print(f"Error in get_guard_stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/active-visitors', methods=['GET'])
def get_active_visitors():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.id, v.visitor_name AS name, v.contact_number AS phone, v.purpose, 
                   fo.flat_number AS flatNumber, v.entry_time AS entryTime, v.status, v.id_proof AS idProofUrl
            FROM visitors v
            JOIN flat_owner fo ON v.owner_id = fo.id
            WHERE v.status IN ('approved', 'pending') AND v.exit_time IS NULL
        """)
        visitors = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for visitor in visitors:
            if visitor['entryTime']:
                visitor['entryTime'] = visitor['entryTime'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'visitors': visitors
        })
    except Exception as e:
        print(f"Error in get_active_visitors: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/pre-approved', methods=['GET'])
def get_pre_approved():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.id, v.visitor_name AS name, fo.flat_number AS flatNumber, 
                   v.expected_date AS expectedTime, v.purpose
            FROM visitors v
            JOIN flat_owner fo ON v.owner_id = fo.id
            WHERE v.status = 'pre-approved'
        """)
        visitors = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for visitor in visitors:
            if visitor['expectedTime']:
                visitor['expectedTime'] = visitor['expectedTime'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'visitors': visitors
        })
    except Exception as e:
        print(f"Error in get_pre_approved: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/visitor-records', methods=['GET'])
def get_visitor_records():
    time_filter = request.args.get('filter', 'today')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT v.visitor_name AS visitorName, fo.flat_number AS flatNumber, v.purpose,
                   v.entry_time AS entryTime, v.exit_time AS exitTime, v.status
            FROM visitors v
            JOIN flat_owner fo ON v.owner_id = fo.id
            WHERE v.exit_time IS NOT NULL
        """
        if time_filter == 'today':
            query += " AND DATE(v.entry_time) = CURDATE()"
        elif time_filter == 'week':
            query += " AND v.entry_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif time_filter == 'month':
            query += " AND v.entry_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
            
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for record in records:
            if record['entryTime']:
                record['entryTime'] = record['entryTime'].strftime('%Y-%m-%d %H:%M:%S')
            if record['exitTime']:
                record['exitTime'] = record['exitTime'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'records': records
        })
    except Exception as e:
        print(f"Error in get_visitor_records: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/add-visitor', methods=['POST'])
def add_visitor():
    if 'logged_in' not in session or session.get('role') != 'guard':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        visitor_name = request.form['visitorName']
        contact_number = request.form['contactNumber']
        flat_number = request.form['flatNumber']
        purpose = request.form['purpose']
        id_proof = request.form.get('idProof')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM flat_owner WHERE flat_number = %s", (flat_number,))
        owner = cursor.fetchone()
        if not owner:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Flat number not found'}), 404
        
        owner_id = owner[0]
        
        cursor.execute("""
            INSERT INTO visitors (owner_id, visitor_name, contact_number, purpose, status, id_proof)
            VALUES (%s, %s, %s, %s, 'pending', %s)
        """, (owner_id, visitor_name, contact_number, purpose, id_proof))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Visitor added successfully'})
    except Exception as e:
        print(f"Error in add_visitor: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/mark-exit/<visitor_id>', methods=['POST'])
def mark_exit(visitor_id):
    if 'logged_in' not in session or session.get('role') != 'guard':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE visitors 
            SET exit_time = NOW(), status = 'approved'
            WHERE id = %s AND exit_time IS NULL
        """, (visitor_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({'success': True, 'message': 'Exit marked'})
        return jsonify({'success': False, 'message': 'Visitor not found or already exited'}), 404
    except Exception as e:
        print(f"Error in mark_exit: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/mark-entry/<request_id>', methods=['POST'])
def mark_entry(request_id):
    if 'logged_in' not in session or session.get('role') != 'guard':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE visitors 
            SET entry_time = NOW(), status = 'approved'
            WHERE id = %s AND status = 'pre-approved'
        """, (request_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({'success': True, 'message': 'Entry marked'})
        return jsonify({'success': False, 'message': 'Visitor not found or not pre-approved'}), 404
    except Exception as e:
        print(f"Error in mark_entry: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/deny-visitor/<visitor_id>', methods=['POST'])
def deny_visitor(visitor_id):
    if 'logged_in' not in session or session.get('role') != 'guard':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE visitors 
            SET status = 'denied'
            WHERE id = %s AND status IN ('pending', 'approved')
        """, (visitor_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({'success': True, 'message': 'Visitor denied'})
        return jsonify({'success': False, 'message': 'Visitor not found or already denied'}), 404
    except Exception as e:
        print(f"Error in deny_visitor: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/approve-visitor/<visitor_id>', methods=['POST'])
def approve_visitor(visitor_id):
    if 'logged_in' not in session or session.get('role') != 'guard':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE visitors 
            SET status = 'approved', entry_time = NOW()
            WHERE id = %s AND status = 'pending'
        """, (visitor_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({'success': True, 'message': 'Visitor approved'})
        return jsonify({'success': False, 'message': 'Visitor not found or not pending'}), 404
    except Exception as e:
        print(f"Error in approve_visitor: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/visitor/<visitor_id>', methods=['GET'])
def get_visitor(visitor_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.id, v.visitor_name AS name, v.contact_number AS phone, v.purpose, 
                   fo.flat_number AS flatNumber, v.id_proof AS idProofUrl
            FROM visitors v
            JOIN flat_owner fo ON v.owner_id = fo.id
            WHERE v.id = %s
        """, (visitor_id,))
        visitor = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if visitor:
            return jsonify({'success': True, 'visitor': visitor})
        return jsonify({'success': False, 'message': 'Visitor not found'}), 404
    except Exception as e:
        print(f"Error in get_visitor: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500