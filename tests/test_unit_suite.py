import pytest
from datetime import datetime, timedelta

from App.main import create_app
from App.database import create_db, db
from App.controllers.user import create_user, get_all_users_json, get_user
from App.controllers.admin import schedule_shift, get_shift_report
from App.controllers.staff import get_combined_roster, clock_in, clock_out, get_shift
from App.controllers import scheduling_logic

from App.models import User, Admin, Staff, Schedule, Shift
from App.models.auto_scheduler import AutoScheduler as ModelAutoScheduler
from App.models.strategy import EvenDistributionStrategy, MinimalDaysStrategy, BalancedShiftStrategy


@pytest.fixture(autouse=True, scope='module')
def app_and_db():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    create_db()
    yield app
    db.drop_all()


def test_create_user_admin():
    admin = create_user("bob", "bobpass", "admin")
    assert admin is not None
    assert admin.role == "admin"
    assert isinstance(admin, Admin)


def test_create_user_staff():
    staff = create_user("amy", "amypass", "staff")
    assert staff is not None
    assert staff.role == "staff"
    assert isinstance(staff, Staff)


def test_create_user_invalid_role():
    # Controller should raise ValueError for invalid role
    with pytest.raises(ValueError):
        create_user("tim", "1234", "manager")


def test_get_json_and_password_methods():
    u = User("bob", "bobpass", "admin")
    data = u.get_json()
    assert data["username"] == "bob"
    assert data["role"] == "admin"
    assert data["id"] is None

    # password is hashed and check_password works
    u2 = User(username="tester", password="mypass")
    assert u2.password != "mypass"
    assert u2.check_password("mypass") is True


def test_check_password_direct():
    u = User("bob", "mypass")
    assert u.check_password("mypass")


def test_schedule_shift_and_report():
    admin = create_user("sadmin", "apass", "admin")
    staff = create_user("sstaff", "spass", "staff")

    schedule = Schedule(name="Unit Schedule", created_by=admin.id)
    db.session.add(schedule)
    db.session.commit()

    start = datetime.now()
    end = start + timedelta(hours=8)

    shift_json = schedule_shift(admin.id, staff.id, schedule.id, start, end)
    assert shift_json["staff_id"] == staff.id
    assert shift_json["schedule_id"] == schedule.id
    assert shift_json["start_time"] is not None

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
    shift_json = schedule_shift(admin.id, staff.id, schedule.id, start, end)

    roster = get_combined_roster(staff.id)
    assert isinstance(roster, list)
    assert any(s["staff_id"] == staff.id for s in roster)

    # clock in/out via controllers
    s = db.session.get(Shift, shift_json["id"])
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
    shift_json = schedule_shift(admin.id, staff.id, schedule.id, start, end)

    # admin trying to clock in -> PermissionError
    with pytest.raises(PermissionError):
        clock_in(admin.id, shift_json["id"])

    # invalid shift id
    with pytest.raises(ValueError):
        clock_in(staff.id, 99999)


def test_strategy_factory_and_strategies():
    # factory creates valid strategies
    s = scheduling_logic.ScheduleStrategyFactory.create_strategy("minimal")
    assert isinstance(s, scheduling_logic.MinimalDays)

    # EvenDistribution logic: create staffs and templates
    staff1 = create_user("a1", "p", "staff")
    staff2 = create_user("a2", "p", "staff")

    schedule = Schedule(name="StratSchedule", created_by=staff1.id)
    db.session.add(schedule)
    db.session.commit()

    # create templates (unassigned shifts) using Shift model directly
    t1 = Shift(staff_id=None, schedule_id=schedule.id, start_time=datetime.now(), end_time=datetime.now()+timedelta(hours=8))
    t2 = Shift(staff_id=None, schedule_id=schedule.id, start_time=datetime.now()+timedelta(days=1), end_time=datetime.now()+timedelta(days=1,hours=8))
    db.session.add_all([t1, t2])
    db.session.commit()

    staff_list = [staff1, staff2]
    templates = [t1, t2]

    even = EvenDistributionStrategy()
    assigned = even.generate(schedule.id, staff_list, templates)
    assert len(assigned) == 2
    assert assigned[0].staff_id in (staff1.id, staff2.id)

    minimal = MinimalDaysStrategy()
    assigned2 = minimal.generate(schedule.id, staff_list, templates)
    assert len(assigned2) == 2

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
    sched = ModelAutoScheduler([], [])
    sched.set_strategy(dummy)
    result = sched.generate_schedule(1)
    assert dummy.called is True
    assert result == []
