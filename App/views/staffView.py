from flask import Blueprint, jsonify, request
from App.controllers import staff, auth
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

staff_views = Blueprint('staff_views', __name__, template_folder='../templates')

@staff_views.route('/staff/roster', methods=['GET'])
@jwt_required()
def view_roster():
    try:
        staff_id = get_jwt_identity()
        roster = staff.get_combined_roster(staff_id)
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

@staff_views.route('/staff/shift', methods=['GET'])
@jwt_required()
def view_shift():
    try:
        data = request.get_json()
        shift_id = data.get("shiftID")
        shift = staff.get_shift(shift_id)
        if not shift:
            return jsonify({"error": "Shift not found"}), 404
        return jsonify(shift.get_json()), 200
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

@staff_views.route('/staff/clock_in', methods=['POST'])
@jwt_required()
def clockIn():
    try:
        staff_id = int(get_jwt_identity())
        data = request.get_json()
        shift_id = data.get("shiftID")
        shiftOBJ = staff.clock_in(staff_id, shift_id)
        return jsonify(shiftOBJ.get_json()), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500


@staff_views.route('/staff/clock_out/', methods=['POST'])
@jwt_required()
def clock_out():
    try:
        staff_id = int(get_jwt_identity())
        data = request.get_json()
        shift_id = data.get("shiftID")
        shift = staff.clock_out(staff_id, shift_id)
        return jsonify(shift.get_json()), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500