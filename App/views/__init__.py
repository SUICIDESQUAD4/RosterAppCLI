# App/views/__init__.py
# blue prints are imported 
# explicitly instead of using *
from .user import user_views
from .index import index_views
from .auth import auth_views
from .admin import setup_admin
from .staffView import staff_views
from .adminView import admin_view
from .system import system_views


views = [user_views, index_views, auth_views, staff_views,admin_view, system_views] 
# blueprints must be added to this list