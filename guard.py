# from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app
# import os
# import mysql.connector
# import datetime
# from werkzeug.utils import secure_filename
# from whatsapp_api import send_whatsapp_approval_request  # Import from whatsapp_api.py
#
# # Create a blueprint for guard routes
# guard_bp = Blueprint('guard', __name__)
#
# # Database helper functions
# def get_db_connection():
#     conn = mysql.connector.connect(
#         host="localhost",
#         user="root",
#         password="root",  # Add your MySQL password here
#         database="securegate"
#     )
#     return conn
# 
# def dict_factory(cursor):
#     columns = [col[0] for col in cursor.description]
#     return [dict(zip(columns, row)) for row in cursor.fetchall()]
#
# # Routes
# @guard_bp.route('/')
# def guard_dashboard():
#     if 'logged_in' in session and session['role'] == 'guard':
#         return render_template('guard.html')
#     return redirect(url_for('index'))
#
# @guard_bp.route('/profile')
# def get_guard_profile():
#     if 'logged_in' not in session or session['role'] != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 401
#
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute('SELECT id, name, email, phone, shift FROM guards WHERE id = %s', (session['user_id'],))
#         guard = cursor.fetchone()
#         cursor.close()
#         conn.close()
#
#         if guard:
#             return jsonify({'success': True, 'guard': guard})
#         return jsonify({'success': False, 'message': 'Guard not found'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)})
#
# @guard_bp.route('/stats')
# def get_stats():
#     if 'logged_in' not in session or session['role'] != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 401
#
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         today = datetime.datetime.now().strftime('%Y-%m-%d')
#
#         cursor.execute('SELECT COUNT(*) FROM visitors WHERE exit_time IS NULL')
#         active_visitors = cursor.fetchone()[0]
#
#         cursor.execute('SELECT COUNT(*) FROM visitors WHERE DATE(entry_time) = %s', (today,))
#         today_entries = cursor.fetchone()[0]
#
#         cursor.execute('SELECT COUNT(*) FROM pre_approved_visitors WHERE DATE(expected_time) >= %s AND status = "approved"', (today,))
#         pre_approved = cursor.fetchone()[0]
#
#         cursor.execute('SELECT COUNT(*) FROM visitors WHERE status = "pending"')
#         pending_approvals = cursor.fetchone()[0]
#
#         cursor.close()
#         conn.close()
#
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
#         return jsonify({'success': False, 'message': str(e)})
#
# @guard_bp.route('/active-visitors')
# def get_active_visitors():
#     if 'logged_in' not in session or session['role'] != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 401
#
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute('''
#             SELECT v.id, v.name, v.phone, v.flat_number as flatNumber, v.purpose,
#                    v.entry_time as entryTime, v.status, v.photo_url as photo
#             FROM visitors v
#             WHERE v.exit_time IS NULL
#             ORDER BY v.entry_time DESC
#         ''')
#         visitors = cursor.fetchall()
#         cursor.close()
#         conn.close()
#
#         for visitor in visitors:
#             if visitor['entryTime']:
#                 visitor['entryTime'] = visitor['entryTime'].strftime('%I:%M %p') if isinstance(visitor['entryTime'], datetime.datetime) else datetime.datetime.fromisoformat(visitor['entryTime']).strftime('%I:%M %p')
#
#         return jsonify({'success': True, 'visitors': visitors})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)})
#
# @guard_bp.route('/pre-approved')
# def get_pre_approved():
#     if 'logged_in' not in session or session['role'] != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 401
#
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         today = datetime.datetime.now().strftime('%Y-%m-%d')
#         cursor.execute('''
#             SELECT id, visitor_name as name, flat_number as flatNumber,
#                    expected_time as expectedTime, purpose
#             FROM pre_approved_visitors
#             WHERE DATE(expected_time) >= %s AND status = "approved" AND entry_marked = 0
#             ORDER BY expected_time ASC
#         ''', (today,))
#         visitors = cursor.fetchall()
#         cursor.close()
#         conn.close()
#
#         for visitor in visitors:
#             if visitor['expectedTime']:
#                 visitor['expectedTime'] = visitor['expectedTime'].strftime('%I:%M %p') if isinstance(visitor['expectedTime'], datetime.datetime) else datetime.datetime.fromisoformat(visitor['expectedTime']).strftime('%I:%M %p')
#
#         return jsonify({'success': True, 'visitors': visitors})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)})
#
# @guard_bp.route('/visitor-records')
# def get_visitor_records():
#     if 'logged_in' not in session or session['role'] != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 401
#
#     time_filter = request.args.get('filter', 'today')
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         today = datetime.datetime.now().date()
#         start_date = today if time_filter == 'today' else today - datetime.timedelta(days=7 if time_filter == 'week' else 30)
#
#         cursor.execute('''
#             SELECT name as visitorName, flat_number as flatNumber, purpose,
#                    entry_time as entryTime, exit_time as exitTime,
#                    CASE
#                        WHEN exit_time IS NOT NULL THEN "Completed"
#                        WHEN status = "approved" THEN "Approved"
#                        WHEN status = "pending" THEN "Pending"
#                        ELSE status
#                    END as status
#             FROM visitors
#             WHERE DATE(entry_time) >= %s
#             ORDER BY entry_time DESC
#         ''', (start_date.isoformat(),))
#         records = cursor.fetchall()
#         cursor.close()
#         conn.close()
#
#         for record in records:
#             if record['entryTime']:
#                 record['entryTime'] = record['entryTime'].strftime('%I:%M %p') if isinstance(record['entryTime'], datetime.datetime) else datetime.datetime.fromisoformat(record['entryTime']).strftime('%I:%M %p')
#             if record['exitTime']:
#                 record['exitTime'] = record['exitTime'].strftime('%I:%M %p') if isinstance(record['exitTime'], datetime.datetime) else datetime.datetime.fromisoformat(record['exitTime']).strftime('%I:%M %p')
#
#         return jsonify({'success': True, 'records': records})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)})
#
# @guard_bp.route('/visitor/<visitor_id>')
# def get_visitor(visitor_id):
#     if 'logged_in' not in session or session['role'] != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 401
#
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute('''
#             SELECT id, name, phone, flat_number as flatNumber, purpose,
#                    id_proof_url as idProofUrl, photo_url as photoUrl,
#                    id_type as idType, id_number as idNumber
#             FROM visitors
#             WHERE id = %s
#         ''', (visitor_id,))
#         visitor = cursor.fetchone()
#         cursor.close()
#         conn.close()
#
#         if visitor:
#             return jsonify({'success': True, 'visitor': visitor})
#         return jsonify({'success': False, 'message': 'Visitor not found'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)})
#
# @guard_bp.route('/add-visitor', methods=['POST'])
# def add_visitor():
#     if 'logged_in' not in session or session['role'] != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 401
#
#     try:
#         visitor_name = request.form.get('visitorName')
#         contact_number = request.form.get('contactNumber')
#         flat_number = request.form.get('flatNumber')
#         purpose = request.form.get('purpose')
#         id_proof = request.files.get('idProof')
#         id_proof_url = ''
#
#         if id_proof and id_proof.filename:
#             filename = secure_filename(id_proof.filename)
#             uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
#             os.makedirs(uploads_dir, exist_ok=True)
#             file_path = os.path.join(uploads_dir, filename)
#             id_proof.save(file_path)
#             id_proof_url = f'/static/uploads/{filename}'
#
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#
#         cursor.execute('''
#             INSERT INTO visitors (name, phone, flat_number, purpose, id_proof_url, entry_time, status)
#             VALUES (%s, %s, %s, %s, %s, %s, %s)
#         ''', (visitor_name, contact_number, flat_number, purpose, id_proof_url, current_time, 'pending'))
#
#         conn.commit()
#         visitor_id = cursor.lastrowid
#
#         cursor.execute('SELECT phone FROM flat_owners WHERE flat_number = %s', (flat_number,))
#         owner = cursor.fetchone()
#
#         cursor.close()
#         conn.close()
#
#         if owner:
#             owner_phone = owner[0]
#             success = send_whatsapp_approval_request(owner_phone, visitor_name, flat_number, purpose, visitor_id)
#             if success:
#                 return jsonify({'success': True, 'message': 'Visitor added successfully. Approval request sent via WhatsApp.'})
#             else:
#                 return jsonify({'success': False, 'message': 'Visitor added but failed to send WhatsApp message'})
#         else:
#             return jsonify({'success': False, 'message': 'Flat owner not found'})
#
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)})
#
# @guard_bp.route('/mark-exit/<visitor_id>', methods=['POST'])
# def mark_exit(visitor_id):
#     if 'logged_in' not in session or session['role'] != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 401
#
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         cursor.execute('UPDATE visitors SET exit_time = %s, status = "completed" WHERE id = %s', (current_time, visitor_id))
#         conn.commit()
#         cursor.close()
#         conn.close()
#         return jsonify({'success': True, 'message': 'Visitor exit marked successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)})
#
# @guard_bp.route('/mark-entry/<request_id>', methods=['POST'])
# def mark_entry(request_id):
#     if 'logged_in' not in session or session['role'] != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 401
#
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute('SELECT visitor_name, flat_number, purpose, owner_id FROM pre_approved_visitors WHERE id = %s', (request_id,))
#         pre_approved = cursor.fetchone()
#
#         if not pre_approved:
#             cursor.close()
#             conn.close()
#             return jsonify({'success': False, 'message': 'Pre-approved visitor not found'})
#
#         current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         cursor.execute('''
#             INSERT INTO visitors (name, flat_number, purpose, entry_time, status, owner_id)
#             VALUES (%s, %s, %s, %s, %s, %s)
#         ''', (pre_approved['visitor_name'], pre_approved['flat_number'], pre_approved['purpose'], current_time, 'approved', pre_approved['owner_id']))
#
#         cursor.execute('UPDATE pre_approved_visitors SET entry_marked = 1 WHERE id = %s', (request_id,))
#         conn.commit()
#         cursor.close()
#         conn.close()
#         return jsonify({'success': True, 'message': 'Visitor entry marked successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)})
#
# @guard_bp.route('/approve-visitor/<visitor_id>', methods=['POST'])
# def approve_visitor(visitor_id):
#     if 'logged_in' not in session or session['role'] != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 401
#
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute('UPDATE visitors SET status = "approved" WHERE id = %s', (visitor_id,))
#         conn.commit()
#         cursor.close()
#         conn.close()
#         return jsonify({'success': True, 'message': 'Visitor approved successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)})
#
# @guard_bp.route('/deny-visitor/<visitor_id>', methods=['POST'])
# def deny_visitor(visitor_id):
#     if 'logged_in' not in session or session['role'] != 'guard':
#         return jsonify({'success': False, 'message': 'Unauthorized'}), 401
#
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         cursor.execute('UPDATE visitors SET status = "denied", exit_time = %s WHERE id = %s', (current_time, visitor_id))
#         conn.commit()
#         cursor.close()
#         conn.close()
#         return jsonify({'success': True, 'message': 'Visitor denied successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)})