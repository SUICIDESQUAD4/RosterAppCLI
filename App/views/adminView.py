from flask import Blueprint, jsonify, request
from datetime import datetime
from App.controllers import staff, auth, admin
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

admin_view = Blueprint('admin_view', __name__, url_prefix="/api/admin")

@admin_view.route('/schedule_shift', methods=['POST'])
@jwt_required()
def createShift():
    try:
        admin_id = get_jwt_identity()
        data = request.get_json()
        scheduleID = data.get("scheduleID")
        staffID = data.get("staffID")
        startTime = data.get("start_time")
        endTime = data.get("end_time")

        try:
            start_time = datetime.fromisoformat(startTime)
            end_time = datetime.fromisoformat(endTime)
        except ValueError:
            start_time = datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(endTime, "%Y-%m-%d %H:%M:%S")

        return admin.schedule_shift(admin_id, staffID, scheduleID, start_time, end_time), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    
    
@admin_view.route('/autoSchedule', methods=['POST'])
@jwt_required()
def autoSchedule():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400
        scheduleID = data.get("scheduleID")
        methodType = data.get("methodType")
        if not scheduleID:
            return jsonify({"error": "Missing required field: scheduleID"}), 400
        if not methodType:
            return jsonify({"error": "Missing required field: methodType"}), 400
    
        return admin.auto_schedule(scheduleID, methodType)
    
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403

@admin_view.route('/viewSchedule', methods=['GET'])
@jwt_required()
def viewSchedule():
    try:
        admin_id = get_jwt_identity()
        report = admin.get_shift_report(admin_id)
        return jsonify(report), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    
@admin_view.route('/viewShift', methods=['POST'])
@jwt_required()
def viewShift():
    try:
        data = request.get_json()
        shift_id = data.get("shiftID")
        shift = admin.viewShift(shift_id)
        return jsonify(shift), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403