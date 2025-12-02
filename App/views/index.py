from flask import Blueprint, redirect, render_template, request, send_from_directory, jsonify
from App.controllers import create_user, initialize

index_views = Blueprint('index_views', __name__)

@index_views.route('/')
def index_page():
    return render_template('index.html')