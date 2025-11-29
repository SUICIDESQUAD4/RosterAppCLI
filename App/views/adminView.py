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
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500
    
    
@admin_view.route('/autoSchedule', methods=['POST'])
@jwt_required()
def autoSchedule():
    try:
        data = request.get_json()
        scheduleID = data.get("scheduleID")
        methodType = data.get("methodType")
    
        return admin.auto_schedule(scheduleID, methodType)
    
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500


@admin_view.route('/viewShift', methods=['GET'])
@jwt_required()
def viewShift():
    try:
        admin_id = get_jwt_identity()
        report = admin.get_shift_report(admin_id)
        return jsonify(report), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500