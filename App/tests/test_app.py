import pytest
from datetime import datetime, timedelta

from App.main import create_app
from App.database import create_db, db
from App.controllers.user import create_user, get_user, update_user, get_all_users_json
from App.controllers.admin import schedule_shift, get_shift_report
from App.controllers.staff import get_combined_roster, clock_in, clock_out, get_shift
from App.controllers.auth import loginCLI
from App.controllers import scheduling_logic
from App.controllers.admin import generate_auto_schedule # Import for integration tests

from App.models import User, Admin, Staff, Schedule, Shift
from App.models.auto_scheduler import AutoScheduler as ModelAutoScheduler
from App.models.strategy import EvenDistributionStrategy, MinimalDaysStrategy, BalancedShiftStrategy


# --- FIXTURES ---

@pytest.fixture(scope='session', autouse=True)
def app_context_setup():
    """Sets up the application context once for the entire session."""
    # Use in-memory SQLite for fast, isolated tests
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        create_db()
        yield
        # Teardown at the end of the session
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function', autouse=True)
def db_cleaner_for_function(app_context_setup):
    """
    Clears all tables and recreates them before *each* test function.
    This ensures complete test isolation for integration tests.
    """
    db.session.remove()
    db.drop_all()
    create_db()
    db.session.commit()
    yield
    # No further teardown needed as the next function run will clean it up


# --- UNIT TESTS (Focus on individual component logic) ---

def test_create_user_admin():
    admin = create_user("bob", "bobpass", "admin")
    assert admin is not None
    assert admin.username == "bob"
    assert admin.role == "admin"
    assert isinstance(admin, Admin)


def test_create_user_staff():
    staff = create_user("amy", "amypass", "staff")
    assert staff is not None
    assert staff.username == "amy"
    assert staff.role == "staff"
    assert isinstance(staff, Staff)


def test_create_user_invalid_role():
    # Controller should raise ValueError for invalid role
    with pytest.raises(ValueError):
        create_user("tim", "1234", "manager")


def test_user_model_get_json_and_password_methods():
    u = User("bob", "bobpass", "admin")
    data = u.get_json()
    assert data["username"] == "bob"
    assert data["role"] == "admin"
    assert data.get("id") is None # Not yet committed to DB

    # password is hashed and check_password works
    u2 = User(username="tester", password="mypass")
    assert u2.password != "mypass"
    assert u2.check_password("mypass") is True


def test_schedule_shift_and_report():
    admin = create_user("sadmin", "apass", "admin")
    staff = create_user("sstaff", "spass", "staff")

    schedule = Schedule(name="Unit Schedule", created_by=admin.id)
    db.session.add(schedule)
    db.session.commit()

    start = datetime.now().replace(microsecond=0)
    end = start + timedelta(hours=8)

    # schedule_shift returns JSON/dict in the controller
    shift_json = schedule_shift(admin.id, staff.id, schedule.id, start, end)
    assert shift_json["staff_id"] == staff.id
    assert 'start_time' in shift_json and shift_json["start_time"] is not None

    report = get_shift_report(admin.id)
    assert isinstance(report, list)
    assert any(r["staff_id"] == staff.id for r in report)


def test_get_combined_roster_and_clocking():
    admin = create_user("admin_clock", "apass", "admin")
    staff = create_user("staff_clock", "spass", "staff")

    schedule = Schedule(name="Clock Schedule", created_by=admin.id)
    db.session.add(schedule)
    db.session.commit()

    start = datetime.now()
    end = start + timedelta(hours=8)
    shift_data = schedule_shift(admin.id, staff.id, schedule.id, start, end)
    shift_id = shift_data["id"]

    roster = get_combined_roster(staff.id)
    assert isinstance(roster, list)
    assert any(s["staff_id"] == staff.id for s in roster)

    # clock in/out via controllers
    s = get_shift(shift_id)
    assert s is not None

    clock_in(staff.id, s.id)
    updated = get_shift(s.id)
    assert updated.clock_in is not None

    clock_out(staff.id, s.id)
    updated2 = get_shift(s.id)
    assert updated2.clock_out is not None


def test_clock_in_invalid_user_and_shift():
    admin = create_user("admin_inv", "apass", "admin")
    staff = create_user("staff_inv", "spass", "staff")

    schedule = Schedule(name="Inv Schedule", created_by=admin.id)
    db.session.add(schedule)
    db.session.commit()

    start = datetime.now()
    end = start + timedelta(hours=8)
    shift_data = schedule_shift(admin.id, staff.id, schedule.id, start, end)
    shift_id = shift_data["id"]

    # admin trying to clock in -> PermissionError
    with pytest.raises(PermissionError, match="Only staff can clock in"):
        clock_in(admin.id, shift_id)

    # invalid shift id
    with pytest.raises(ValueError, match="Invalid shift for staff"):
        clock_in(staff.id, 99999)


def test_scheduling_strategies_and_factory():
    # factory creates valid strategies
    s = scheduling_logic.ScheduleStrategyFactory.create_strategy("minimal")
    assert isinstance(s, MinimalDaysStrategy)

    # Setup for strategy logic test
    staff1 = create_user("a1", "p", "staff")
    staff2 = create_user("a2", "p", "staff")

    schedule = Schedule(name="StratSchedule", created_by=staff1.id)
    db.session.add(schedule)
    db.session.commit()

    # Create unassigned shift templates (staff_id=None)
    t1 = Shift(staff_id=None, schedule_id=schedule.id, start_time=datetime.now(), end_time=datetime.now()+timedelta(hours=8))
    t2 = Shift(staff_id=None, schedule_id=schedule.id, start_time=datetime.now()+timedelta(days=1), end_time=datetime.now()+timedelta(days=1,hours=8))
    db.session.add_all([t1, t2])
    db.session.commit()

    staff_list = [staff1, staff2]
    templates = [t1, t2]

    # Test EvenDistributionStrategy
    even = EvenDistributionStrategy()
    assigned = even.generate(schedule.id, staff_list, templates)
    assert len(assigned) == 2
    assert assigned[0].staff_id in (staff1.id, staff2.id)

    # Test MinimalDaysStrategy
    minimal = MinimalDaysStrategy()
    assigned2 = minimal.generate(schedule.id, staff_list, templates)
    assert len(assigned2) == 2

    # Test BalancedShiftStrategy
    balanced = BalancedShiftStrategy()
    assigned3 = balanced.generate(schedule.id, staff_list, templates)
    assert len(assigned3) == 2


def test_models_autoscheduler_calls_strategy():
    # ensure ModelAutoScheduler delegates to provided strategy
    class DummyStrategy:
        def __init__(self):
            self.called = False

        def generate(self, schedule_id, staff_list, shifts_to_fill):
            self.called = True
            return []

    dummy = DummyStrategy()
    sched = ModelAutoScheduler(staff_list=[], shifts_to_fill=[])
    sched.set_strategy(dummy)
    result = sched.generate_schedule(1)
    assert dummy.called is True
    assert result == []


# --- INTEGRATION TESTS (Focus on controller interactions and persistence) ---

def test_user_authentication():
    create_user("alice", "alicepass", "staff")
    
    # Successful login
    assert loginCLI("alice", "alicepass") is not None
    
    # Failed login
    assert loginCLI("alice", "wrongpass") is None


def test_get_all_users_json_integration():
    create_user("bot", "bobpass", "admin")
    create_user("pam", "pampass", "staff")
    users_json = get_all_users_json()
    
    expected = [
        {"id": 1, "username": "bot", "role": "admin"},
        {"id": 2, "username": "pam", "role": "staff"},
    ]
    assert users_json == expected


def test_update_user_integration():
    user = create_user("bot", "bobpass", "admin")
    
    update_user(user.id, "ronnie")
    updated_user = get_user(user.id)
    assert updated_user.username == "ronnie"


def test_admin_schedule_shift_for_staff_integration():
    admin = create_user("admin1", "adminpass", "admin")
    staff = create_user("staff1", "staffpass", "staff")

    schedule = Schedule(name="Week 1 Schedule", created_by=admin.id)
    db.session.add(schedule)
    db.session.commit()

    start = datetime.now()
    end = start + timedelta(hours=8)

    shift_data = schedule_shift(admin.id, staff.id, schedule.id, start, end)
    shift = get_shift(shift_data['id'])
        
    retrieved_staff = get_user(staff.id)

    # Check if the shift is associated with the staff and the correct IDs
    assert shift.id in [s.id for s in retrieved_staff.shifts]
    assert shift.staff_id == staff.id
    assert shift.schedule_id == schedule.id


def test_staff_view_combined_roster_integration():
    admin = create_user("admin", "adminpass", "admin")
    staff = create_user("jane", "janepass", "staff")
    other_staff = create_user("mark", "markpass", "staff")

    schedule = Schedule(name="Shared Roster", created_by=admin.id)
    db.session.add(schedule)
    db.session.commit()

    start = datetime.now()
    end = start + timedelta(hours=8)

    schedule_shift(admin.id, staff.id, schedule.id, start, end)
    schedule_shift(admin.id, other_staff.id, schedule.id, start, end)

    roster = get_combined_roster(staff.id)
    
    # Check if shifts for both staff members appear in the combined roster
    assert any(s["staff_id"] == staff.id for s in roster)
    assert any(s["staff_id"] == other_staff.id for s in roster)
    assert len(roster) >= 2


def test_staff_clock_in_and_out_integration():
    admin = create_user("admin", "adminpass", "admin")
    staff = create_user("lee", "leepass", "staff")

    schedule = Schedule(name="Daily Schedule", created_by=admin.id)
    db.session.add(schedule)
    db.session.commit()

    start = datetime.now()
    end = start + timedelta(hours=8)

    shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)
    shift_id = shift.id if not isinstance(shift, dict) else shift['id']

    clock_in(staff.id, shift_id)
    clock_out(staff.id, shift_id)

    updated_shift = get_shift(shift_id)
    assert updated_shift.clock_in is not None
    assert updated_shift.clock_out is not None
    assert updated_shift.clock_in < updated_shift.clock_out


def test_permission_restrictions_integration():
    admin = create_user("admin", "adminpass", "admin")
    staff = create_user("worker", "workpass", "staff")

    schedule = Schedule(name="Restricted Schedule", created_by=admin.id)
    db.session.add(schedule)
    db.session.commit()

    start = datetime.now()
    end = start + timedelta(hours=8)

    # 1. Non-admin attempting to schedule
    with pytest.raises(PermissionError):
        schedule_shift(staff.id, staff.id, schedule.id, start, end)

    # 2. Admin attempting to view staff-only roster
    with pytest.raises(PermissionError, match="Only staff can view roster"):
        get_combined_roster(admin.id)

    # 3. Staff attempting to view admin-only shift report
    with pytest.raises(PermissionError, match="Only admins can view shift reports"):
        get_shift_report(staff.id)

def test_admin_generate_auto_schedule_integration():
    """Integration test: admin auto-populates a schedule from templates."""
    admin = create_user("auto_admin", "adminpass", "admin")
    create_user("auto_staff1", "pass1", "staff") # staff ID 2
    create_user("auto_staff2", "pass2", "staff") # staff ID 3

    schedule = Schedule(name="AutoSchedule", created_by=admin.id)
    db.session.add(schedule)
    db.session.commit()

    # create unassigned shift templates (staff_id=None)
    t1 = Shift(schedule_id=schedule.id, staff_id=None, start_time=datetime.now(), end_time=datetime.now() + timedelta(hours=8))
    t2 = Shift(schedule_id=schedule.id, staff_id=None, start_time=datetime.now() + timedelta(days=1), end_time=datetime.now() + timedelta(days=1, hours=8))
    db.session.add_all([t1, t2])
    db.session.commit()

    # call auto-scheduler (method 'even')
    res = generate_auto_schedule(schedule.id, 'even')
    
    assigned = res.get('data', []) if isinstance(res, dict) else res
        
    assert len(assigned) == 2
    
    # After auto-schedule, shifts for the schedule should have staff assigned
    shifts_after = db.session.execute(db.select(Shift).filter_by(schedule_id=schedule.id)).scalars().all()
    assert all(s.staff_id is not None for s in shifts_after)
    assert len(shifts_after) == 2

    # Test failure case (non-existent schedule)
    res = generate_auto_schedule(99999, 'even')
    if isinstance(res, dict):
        assert res.get('status') == 'error'