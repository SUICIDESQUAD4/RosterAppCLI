from flask import Blueprint, redirect, render_template, request, send_from_directory, jsonify
from App.controllers import create_user, initialize

system_views = Blueprint('system_views', __name__, url_prefix="/api/system")

@system_views.route('/init', methods=['GET'])
def init():
    initialize()
    return jsonify(message='db initialized!')