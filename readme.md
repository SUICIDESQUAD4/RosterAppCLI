![Tests](https://github.com/SUICIDESQUAD4/RosterAppCLI/actions/workflows/dev.yml/badge.svg)

# RosterAppCLI
A comprehensive command-line roster management application built with Flask, SQLAlchemy, and Click CLI framework. Manage staff schedules, shifts, clock-in/out tracking, and reporting through an intuitive CLI interface.

[Demo](https://roster-app-cli-demo.herokuapp.com/) | [Postman Collection](https://documenter.getpostman.com/view/roster-app-cli/collection)

# Dependencies
* Python 3.8+
* pip3 package manager
* Packages listed in requirements.txt

# Installing Dependencies
```bash
$ pip install -r requirements.txt
```

# Configuration Management

Configuration information such as database URL, credentials, and API keys are managed through environment variables and configuration files. This approach ensures security and flexibility across different environments.

## In Development

When running the project in a development environment, the app is configured via `default_config.py` file in the App folder. By default, the config for development uses a SQLite database.

default_config.py
```python
SQLALCHEMY_DATABASE_URI = "sqlite:///roster-app.db"
SECRET_KEY = "dev-secret-key-change-in-production"
JWT_ACCESS_TOKEN_EXPIRES = 24  # hours
ENV = "DEVELOPMENT"
DEBUG = True
```

These values are imported and added to the app in the `load_config()` function in config.py

config.py
```python
def load_config():
    config = {'ENV': os.environ.get('ENV', 'DEVELOPMENT')}
    if config['ENV'] == "DEVELOPMENT":
        from .default_config import JWT_ACCESS_TOKEN_EXPIRES, SQLALCHEMY_DATABASE_URI, SECRET_KEY
        config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
        config['SECRET_KEY'] = SECRET_KEY
        config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES
    return config
```

## In Production

When deploying your application to production/staging, you must pass configuration information via environment variables in your hosting platform's dashboard (Render, Heroku, etc.).

Required environment variables:
- `DATABASE_URL`: PostgreSQL database connection string
- `SECRET_KEY`: Secure random string for session management
- `ENV`: Set to "PRODUCTION"
- `JWT_SECRET_KEY`: Secret key for JWT token generation

# Flask Commands

The application uses Flask's built-in CLI system with custom commands for roster management. All commands are organized under the `roster` command group.

## User Management Commands

```python
# User CLI group setup in wsgi.py
user_cli = AppGroup('user', help='User management commands')

@user_cli.command("create")
@click.argument("username")
@click.argument("password")
@click.argument("role", default="user")
def create_user_command(username, password, role):
    """Create a new user with specified role"""
    create_user(username, password, role)
    print(f'{username} created successfully with role: {role}')

app.cli.add_command(user_cli)
```

## Available Commands

### User Management
```bash
# Create a new user
$ flask user create <username> <password> <role>

# List all users
$ flask user list

# List users in JSON format
$ flask user list --json

# Update user role
$ flask user update-role <username> <new-role>

# Delete user
$ flask user delete <username>
```

### Schedule Management
```bash
# Create a new schedule
$ flask schedule create "April Week 2"

# List all schedules
$ flask schedule list

# View schedule details
$ flask schedule view <schedule-id>

# Update schedule
$ flask schedule update <schedule-id> "New Schedule Name"

# Delete schedule
$ flask schedule delete <schedule-id>
```

### Shift Management
```bash
# Schedule a shift (Admin only)
$ flask shift schedule <staff-id> <schedule-id> <start-time> <end-time>
Example: flask shift schedule 2 1 2025-10-01T09:00:00 2025-10-01T17:00:00

# View roster (Staff only)
$ flask shift roster

# Clock in for a shift
$ flask shift clockin <shift-id>

# Clock out from a shift
$ flask shift clockout <shift-id>

# View shift details
$ flask shift view <shift-id>

# Generate shift report (Admin only)
$ flask shift report

# Cancel a shift
$ flask shift cancel <shift-id>
```

### System Commands
```bash
# Initialize database with sample data
$ flask init

# Reset database (WARNING: This will delete all data)
$ flask reset-db

# Generate sample data for testing
$ flask generate-sample-data

# Backup database
$ flask backup-db

# Restore database from backup
$ flask restore-db <backup-file>
```

# Running the Project

## Development Server
```bash
# Set Flask app environment variable
$ export FLASK_APP=wsgi.py

# Run development server
$ flask run

# Run with debug mode and hot reload
$ flask run --debug --reload
```

## Production Server
```bash
# Using Gunicorn (recommended for production)
$ gunicorn wsgi:app

# With specific workers and port
$ gunicorn wsgi:app -w 4 -b 0.0.0.0:5000
```

# Database Management

## Initial Setup
```bash
# Initialize the database (creates tables and sample data)
$ flask db init

# Create migration repository
$ flask db init-migration

# Create a new migration
$ flask db migrate -m "migration message"

# Apply migrations
$ flask db upgrade

# Downgrade to previous migration
$ flask db downgrade
```

## Sample Data
The `flask init` command creates the following sample data:
- **Admin User**: username: `admin`, password: `admin123`, role: `admin`
- **Staff Users**: 3 staff members with different schedules
- **Manager User**: username: `manager`, password: `manager123`, role: `manager`
- **Regular User**: username: `user`, password: `user123`, role: `user`
- **Sample Schedules**: Weekly schedules for different departments
- **Sample Shifts**: Pre-assigned shifts for testing

# User Roles and Permissions

## Role Hierarchy
- **Admin**: Full system access, user management, all shift operations
- **Manager**: Department management, staff scheduling, reporting
- **Staff**: Clock in/out, view personal roster, request time off
- **User**: Basic access, view schedules (read-only)

## Permission Matrix
| Action | Admin | Manager | Staff | User |
|--------|-------|---------|-------|------|
| Create Users | ✅ | ❌ | ❌ | ❌ |
| Manage Schedules | ✅ | ✅ | ❌ | ❌ |
| Assign Shifts | ✅ | ✅ | ❌ | ❌ |
| Clock In/Out | ✅ | ✅ | ✅ | ❌ |
| View Reports | ✅ | ✅ | ❌ | ❌ |
| View Roster | ✅ | ✅ | ✅ | ✅ |

# Testing

## Running Tests
```bash
# Run all tests
$ pytest

# Run specific test file
$ pytest tests/test_user.py

# Run with coverage
$ pytest --cov=App tests/

# Run unit tests only
$ pytest -k "unit"

# Run integration tests only
$ pytest -k "integration"
```

## Test Coverage
```bash
# Generate coverage report
$ coverage report

# Generate HTML coverage report
$ coverage html
# Report will be in htmlcov/index.html

# Generate XML coverage report
$ coverage xml
```

## Test Structure
```
tests/
├── conftest.py          # Pytest fixtures
├── test_user.py         # User management tests
├── test_shift.py        # Shift management tests
├── test_schedule.py     # Schedule management tests
├── test_auth.py         # Authentication tests
└── test_integration.py  # End-to-end integration tests
```

# API Endpoints

## Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh JWT token

## User Management
- `GET /api/users` - List all users (Admin only)
- `POST /api/users` - Create new user (Admin only)
- `GET /api/users/<id>` - Get user details
- `PUT /api/users/<id>` - Update user (Admin/Manager)
- `DELETE /api/users/<id>` - Delete user (Admin only)

## Schedule Management
- `GET /api/schedules` - List schedules
- `POST /api/schedules` - Create schedule (Admin/Manager)
- `GET /api/schedules/<id>` - Get schedule details
- `PUT /api/schedules/<id>` - Update schedule (Admin/Manager)
- `DELETE /api/schedules/<id>` - Delete schedule (Admin/Manager)

## Shift Management
- `GET /api/shifts` - List shifts (role-based filtering)
- `POST /api/shifts` - Create shift (Admin/Manager)
- `GET /api/shifts/<id>` - Get shift details
- `PUT /api/shifts/<id>` - Update shift (Admin/Manager)
- `DELETE /api/shifts/<id>` - Delete shift (Admin/Manager)
- `POST /api/shifts/<id>/clockin` - Clock in (Staff)
- `POST /api/shifts/<id>/clockout` - Clock out (Staff)

# Deployment

## Deploy to Render
You can deploy your version of this app to Render by clicking the button below:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## Environment Setup
1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the build command: `pip install -r requirements.txt`
4. Set the start command: `gunicorn wsgi:app`
5. Add environment variables in the Render dashboard

## Production Checklist
- [ ] Set `ENV=PRODUCTION`
- [ ] Configure PostgreSQL database
- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Disable debug mode
- [ ] Set up SSL/TLS certificates
- [ ] Configure backup strategy
- [ ] Set up monitoring and logging

# Troubleshooting

## Common Issues

### Database Connection
```bash
# If you get database connection errors
$ flask db upgrade
$ flask init
```

### Module Import Errors
```bash
# Ensure you're in the correct directory
$ export PYTHONPATH=.
$ export FLASK_APP=wsgi.py
```

### Permission Errors
```bash
# Check file permissions
$ chmod +x wsgi.py
$ chmod -R 755 App/
```

### Port Already in Use
```bash
# Kill process using port 5000
$ lsof -ti:5000 | xargs kill -9
# Or run on different port
$ flask run -p 5001
```

## Views 404ing
If your newly created views are returning 404, ensure they are added to the list in `main.py`:

```python
from App.views import (
    user_views,
    shift_views,
    schedule_views,
    auth_views
)

views = [
    user_views,
    shift_views,
    schedule_views,
    auth_views
]
```

## Database Migration Issues
If you encounter migration errors:
```bash
# Reset migrations
$ rm -rf migrations/
$ flask db init
$ flask db migrate
$ flask db upgrade
```

## GitHub Actions Workflow
If you cannot update the workflow file, ensure your GitHub permissions in Gitpod have workflow enabled:
1. Go to https://gitpod.io/integrations
2. Find GitHub integration
3. Enable "Workflow" permissions

# Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Acknowledgments

- Flask community for the excellent framework
- SQLAlchemy team for the ORM
- Click team for the CLI framework
- Render team for hosting platform
- All contributors and testers
