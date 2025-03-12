# from flask import Blueprint, jsonify, request, session
# from flask_cors import CORS
# import mysql.connector
# from datetime import datetime
# import os

# # Initialize Blueprint
# guard_bp = Blueprint('guard', __name__)
# CORS(guard_bp, supports_credentials=True)

# # Database Configuration
# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'root',  # Replace with your MySQL password
#     'database': 'project'
# }

# # Helper function to get database connection
# def get_db_connection():
#     return mysql.connector.connect(**db_config)

# # Guard Profile
# @guard_bp.route('/profile', methods=['GET'])
# def guard_profile():
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     guard_id = session.get('user_id')
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("SELECT id, name, email, whatsapp FROM guard WHERE id = %s", (guard_id,))
#         guard = cursor.fetchone()
#         cursor.close()
#         conn.close()

#         if guard:
#             return jsonify({'success': True, 'guard': guard})
#         return jsonify({'success': False, 'message': 'Guard not found'}), 404
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Guard Dashboard Stats
# @guard_bp.route('/stats', methods=['GET'])
# def guard_stats():
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)

#         cursor.execute("SELECT COUNT(*) as activeVisitors FROM visitors WHERE status = 'approved' AND exit_time IS NULL")
#         active_visitors = cursor.fetchone()['activeVisitors']

#         cursor.execute("SELECT COUNT(*) as todayEntries FROM visitors WHERE DATE(entry_time) = CURDATE() AND status = 'approved'")
#         today_entries = cursor.fetchone()['todayEntries']

#         cursor.execute("SELECT COUNT(*) as preApproved FROM visitors WHERE status = 'pre-approved'")
#         pre_approved = cursor.fetchone()['preApproved']

#         cursor.execute("SELECT COUNT(*) as pendingApprovals FROM visitors WHERE status = 'pending'")
#         pending_approvals = cursor.fetchone()['pendingApprovals']

#         cursor.close()
#         conn.close()

#         return jsonify({
#             'success': True,
#             'stats': {
#                 'activeVisitors': active_visitors,
#                 'todayEntries': today_entries,
#                 'preApproved': pre_approved,
#                 'pendingApprovals': pending_approvals
#             }
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Active Visitors
# @guard_bp.route('/active-visitors', methods=['GET'])
# def active_visitors():
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("""
#             SELECT v.id, v.visitor_name as name, v.contact_number as phone, f.flat_number as flatNumber, 
#                    v.purpose, v.entry_time as entryTime, v.status
#             FROM visitors v
#             JOIN flat_owner f ON v.owner_id = f.id
#             WHERE v.status = 'approved' AND v.exit_time IS NULL
#         """)
#         visitors = cursor.fetchall()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'visitors': visitors})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Pre-approved Visitors
# @guard_bp.route('/pre-approved', methods=['GET'])
# def pre_approved_visitors():
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("""
#             SELECT v.id, v.visitor_name as name, f.flat_number as flatNumber, v.purpose, 
#                    v.expected_date as expectedTime
#             FROM visitors v
#             JOIN flat_owner f ON v.owner_id = f.id
#             WHERE v.status = 'pre-approved'
#         """)
#         visitors = cursor.fetchall()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'visitors': visitors})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Visitor Records
# @guard_bp.route('/visitor-records', methods=['GET'])
# def visitor_records():
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     time_filter = request.args.get('filter', 'today')
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)

#         query = """
#             SELECT v.visitor_name as visitorName, f.flat_number as flatNumber, v.purpose, 
#                    v.entry_time as entryTime, v.exit_time as exitTime, v.status
#             FROM visitors v
#             JOIN flat_owner f ON v.owner_id = f.id
#             WHERE {}
#         """
#         if time_filter == 'today':
#             condition = "DATE(v.entry_time) = CURDATE()"
#         elif time_filter == 'week':
#             condition = "YEARWEEK(v.entry_time, 1) = YEARWEEK(CURDATE(), 1)"
#         elif time_filter == 'month':
#             condition = "MONTH(v.entry_time) = MONTH(CURDATE()) AND YEAR(v.entry_time) = YEAR(CURDATE())"
#         else:
#             condition = "1=1"  # Default to all records if filter is invalid

#         cursor.execute(query.format(condition))
#         records = cursor.fetchall()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'records': records})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Add New Visitor
# @guard_bp.route('/add-visitor', methods=['POST'])
# def add_visitor():
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     data = request.form
#     visitor_name = data.get('visitorName')
#     contact_number = data.get('contactNumber')
#     flat_number = data.get('flatNumber')
#     purpose = data.get('purpose')
#     id_proof = request.files.get('idProof')

#     if not all([visitor_name, contact_number, flat_number, purpose, id_proof]):
#         return jsonify({'success': False, 'message': 'All fields are required'}), 400

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Check if flat_number exists in flat_owner
#         cursor.execute("SELECT id FROM flat_owner WHERE flat_number = %s", (flat_number,))
#         owner = cursor.fetchone()
#         if not owner:
#             return jsonify({'success': False, 'message': 'Flat number does not exist'}), 404
#         owner_id = owner[0]

#         # Save ID proof file
#         upload_folder = 'static/uploads'
#         os.makedirs(upload_folder, exist_ok=True)
#         id_proof_path = os.path.join(upload_folder, id_proof.filename)
#         id_proof.save(id_proof_path)

#         cursor.execute("""
#             INSERT INTO visitors (owner_id, visitor_name, contact_number, purpose, id_proof, status)
#             VALUES (%s, %s, %s, %s, %s, 'pending')
#         """, (owner_id, visitor_name, contact_number, purpose, id_proof_path))

#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'message': 'Visitor added successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # View Visitor Details
# @guard_bp.route('/visitor/<int:visitor_id>', methods=['GET'])
# def get_visitor(visitor_id):
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("""
#             SELECT v.id, v.visitor_name as name, v.contact_number as phone, v.purpose, 
#                    v.id_proof as idProofUrl, v.status
#             FROM visitors v
#             WHERE v.id = %s
#         """, (visitor_id,))
#         visitor = cursor.fetchone()
#         cursor.close()
#         conn.close()

#         if visitor:
#             return jsonify({'success': True, 'visitor': visitor})
#         return jsonify({'success': False, 'message': 'Visitor not found'}), 404
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Mark Visitor Exit
# @guard_bp.route('/mark-exit/<int:visitor_id>', methods=['POST'])
# def mark_exit(visitor_id):
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("""
#             UPDATE visitors SET exit_time = %s WHERE id = %s AND status = 'approved'
#         """, (datetime.now(), visitor_id))
#         if cursor.rowcount == 0:
#             return jsonify({'success': False, 'message': 'Visitor not found or not approved'}), 404
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'message': 'Exit marked successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Mark Pre-approved Entry
# @guard_bp.route('/mark-entry/<int:request_id>', methods=['POST'])
# def mark_entry(request_id):
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("""
#             UPDATE visitors SET entry_time = %s, status = 'approved' 
#             WHERE id = %s AND status = 'pre-approved'
#         """, (datetime.now(), request_id))
#         if cursor.rowcount == 0:
#             return jsonify({'success': False, 'message': 'Pre-approved visitor not found'}), 404
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'message': 'Entry marked successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Deny Visitor
# @guard_bp.route('/deny-visitor/<int:visitor_id>', methods=['POST'])
# def deny_visitor(visitor_id):
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("""
#             UPDATE visitors SET status = 'denied' WHERE id = %s AND status = 'pending'
#         """, (visitor_id,))
#         if cursor.rowcount == 0:
#             return jsonify({'success': False, 'message': 'Pending visitor not found'}), 404
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'message': 'Visitor denied successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Approve Visitor
# @guard_bp.route('/approve-visitor/<int:visitor_id>', methods=['POST'])
# def approve_visitor(visitor_id):
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("""
#             UPDATE visitors SET status = 'approved', entry_time = %s 
#             WHERE id = %s AND status = 'pending'
#         """, (datetime.now(), visitor_id))
#         if cursor.rowcount == 0:
#             return jsonify({'success': False, 'message': 'Pending visitor not found'}), 404
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'message': 'Visitor approved successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500
# from flask_cors import CORS
# import mysql.connector
# from datetime import datetime
# import os

# # Initialize Blueprint
# guard_bp = Blueprint('guard', __name__)
# CORS(guard_bp, supports_credentials=True)

# # Database Configuration
# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'your_actual_password',  # Replace with your MySQL password
#     'database': 'project'
# }

# # Helper function to get database connection
# def get_db_connection():
#     return mysql.connector.connect(**db_config)

# # Guard Profile
# @guard_bp.route('/profile', methods=['GET'])
# def guard_profile():
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     guard_id = session.get('user_id')
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("SELECT id, name, email, whatsapp FROM guard WHERE id = %s", (guard_id,))
#         guard = cursor.fetchone()
#         cursor.close()
#         conn.close()

#         if guard:
#             return jsonify({'success': True, 'guard': guard})
#         return jsonify({'success': False, 'message': 'Guard not found'}), 404
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Guard Dashboard Stats
# @guard_bp.route('/stats', methods=['GET'])
# def guard_stats():
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)

#         cursor.execute("SELECT COUNT(*) as activeVisitors FROM visitors WHERE status = 'approved' AND exit_time IS NULL")
#         active_visitors = cursor.fetchone()['activeVisitors']

#         cursor.execute("SELECT COUNT(*) as todayEntries FROM visitors WHERE DATE(entry_time) = CURDATE() AND status = 'approved'")
#         today_entries = cursor.fetchone()['todayEntries']

#         cursor.execute("SELECT COUNT(*) as preApproved FROM visitors WHERE status = 'pre-approved'")
#         pre_approved = cursor.fetchone()['preApproved']

#         cursor.execute("SELECT COUNT(*) as pendingApprovals FROM visitors WHERE status = 'pending'")
#         pending_approvals = cursor.fetchone()['pendingApprovals']

#         cursor.close()
#         conn.close()

#         return jsonify({
#             'success': True,
#             'stats': {
#                 'activeVisitors': active_visitors,
#                 'todayEntries': today_entries,
#                 'preApproved': pre_approved,
#                 'pendingApprovals': pending_approvals
#             }
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Active Visitors
# @guard_bp.route('/active-visitors', methods=['GET'])
# def active_visitors():
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("""
#             SELECT v.id, v.visitor_name as name, v.contact_number as phone, f.flat_number as flatNumber, 
#                    v.purpose, v.entry_time as entryTime, v.status
#             FROM visitors v
#             JOIN flat_owner f ON v.owner_id = f.id
#             WHERE v.status = 'approved' AND v.exit_time IS NULL
#         """)
#         visitors = cursor.fetchall()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'visitors': visitors})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Pre-approved Visitors
# @guard_bp.route('/pre-approved', methods=['GET'])
# def pre_approved_visitors():
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("""
#             SELECT v.id, v.visitor_name as name, f.flat_number as flatNumber, v.purpose, 
#                    v.expected_date as expectedTime
#             FROM visitors v
#             JOIN flat_owner f ON v.owner_id = f.id
#             WHERE v.status = 'pre-approved'
#         """)
#         visitors = cursor.fetchall()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'visitors': visitors})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Visitor Records
# @guard_bp.route('/visitor-records', methods=['GET'])
# def visitor_records():
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     time_filter = request.args.get('filter', 'today')
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)

#         query = """
#             SELECT v.visitor_name as visitorName, f.flat_number as flatNumber, v.purpose, 
#                    v.entry_time as entryTime, v.exit_time as exitTime, v.status
#             FROM visitors v
#             JOIN flat_owner f ON v.owner_id = f.id
#             WHERE {}
#         """
#         if time_filter == 'today':
#             condition = "DATE(v.entry_time) = CURDATE()"
#         elif time_filter == 'week':
#             condition = "YEARWEEK(v.entry_time, 1) = YEARWEEK(CURDATE(), 1)"
#         elif time_filter == 'month':
#             condition = "MONTH(v.entry_time) = MONTH(CURDATE()) AND YEAR(v.entry_time) = YEAR(CURDATE())"
#         else:
#             condition = "1=1"  # Default to all records if filter is invalid

#         cursor.execute(query.format(condition))
#         records = cursor.fetchall()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'records': records})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Add New Visitor
# @guard_bp.route('/add-visitor', methods=['POST'])
# def add_visitor():
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     data = request.form
#     visitor_name = data.get('visitorName')
#     contact_number = data.get('contactNumber')
#     flat_number = data.get('flatNumber')
#     purpose = data.get('purpose')
#     id_proof = request.files.get('idProof')

#     if not all([visitor_name, contact_number, flat_number, purpose, id_proof]):
#         return jsonify({'success': False, 'message': 'All fields are required'}), 400

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Check if flat_number exists in flat_owner
#         cursor.execute("SELECT id FROM flat_owner WHERE flat_number = %s", (flat_number,))
#         owner = cursor.fetchone()
#         if not owner:
#             return jsonify({'success': False, 'message': 'Flat number does not exist'}), 404
#         owner_id = owner[0]

#         # Save ID proof file
#         upload_folder = 'static/uploads'
#         os.makedirs(upload_folder, exist_ok=True)
#         id_proof_path = os.path.join(upload_folder, id_proof.filename)
#         id_proof.save(id_proof_path)

#         cursor.execute("""
#             INSERT INTO visitors (owner_id, visitor_name, contact_number, purpose, id_proof, status)
#             VALUES (%s, %s, %s, %s, %s, 'pending')
#         """, (owner_id, visitor_name, contact_number, purpose, id_proof_path))

#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'message': 'Visitor added successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # View Visitor Details
# @guard_bp.route('/visitor/<int:visitor_id>', methods=['GET'])
# def get_visitor(visitor_id):
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("""
#             SELECT v.id, v.visitor_name as name, v.contact_number as phone, v.purpose, 
#                    v.id_proof as idProofUrl, v.status
#             FROM visitors v
#             WHERE v.id = %s
#         """, (visitor_id,))
#         visitor = cursor.fetchone()
#         cursor.close()
#         conn.close()

#         if visitor:
#             return jsonify({'success': True, 'visitor': visitor})
#         return jsonify({'success': False, 'message': 'Visitor not found'}), 404
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Mark Visitor Exit
# @guard_bp.route('/mark-exit/<int:visitor_id>', methods=['POST'])
# def mark_exit(visitor_id):
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("""
#             UPDATE visitors SET exit_time = %s WHERE id = %s AND status = 'approved'
#         """, (datetime.now(), visitor_id))
#         if cursor.rowcount == 0:
#             return jsonify({'success': False, 'message': 'Visitor not found or not approved'}), 404
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'message': 'Exit marked successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Mark Pre-approved Entry
# @guard_bp.route('/mark-entry/<int:request_id>', methods=['POST'])
# def mark_entry(request_id):
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("""
#             UPDATE visitors SET entry_time = %s, status = 'approved' 
#             WHERE id = %s AND status = 'pre-approved'
#         """, (datetime.now(), request_id))
#         if cursor.rowcount == 0:
#             return jsonify({'success': False, 'message': 'Pre-approved visitor not found'}), 404
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'message': 'Entry marked successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Deny Visitor
# @guard_bp.route('/deny-visitor/<int:visitor_id>', methods=['POST'])
# def deny_visitor(visitor_id):
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("""
#             UPDATE visitors SET status = 'denied' WHERE id = %s AND status = 'pending'
#         """, (visitor_id,))
#         if cursor.rowcount == 0:
#             return jsonify({'success': False, 'message': 'Pending visitor not found'}), 404
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'message': 'Visitor denied successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# # Approve Visitor
# @guard_bp.route('/approve-visitor/<int:visitor_id>', methods=['POST'])
# def approve_visitor(visitor_id):
#     if 'logged_in' not in session or session.get('role') != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("""
#             UPDATE visitors SET status = 'approved', entry_time = %s 
#             WHERE id = %s AND status = 'pending'
#         """, (datetime.now(), visitor_id))
#         if cursor.rowcount == 0:
#             return jsonify({'success': False, 'message': 'Pending visitor not found'}), 404
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({'success': True, 'message': 'Visitor approved successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500