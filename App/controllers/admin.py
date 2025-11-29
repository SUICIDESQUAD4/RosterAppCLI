from App.controllers.scheduling_logic import ScheduleStrategyFactory, AutoScheduler
from datetime import datetime, timedelta
import random
from App.models import Admin, Staff, Shift
from App.database import db
from App.controllers.user import get_user


def random_shift_time(start_hour=6, end_hour=22, min_duration=4, max_duration=8):
    """
    Generate a random start and end time between the given hour range.
    Duration in hours is random between min_duration and max_duration.
    Returns datetime objects.
    """
    day = datetime.now().date()

    start = datetime.combine(day, datetime.min.time()) + timedelta(hours=random.randint(start_hour, end_hour - min_duration))
    duration = timedelta(hours=random.randint(min_duration, max_duration))
    end = start + duration

    return start, end

def generate_random_templates(schedule_id, num_templates=10):
    shifts = []

    for _ in range(num_templates):
        start, end = random_shift_time()
        shift = Shift(
            staff_id=None,
            schedule_id=schedule_id,
            start_time=start,
            end_time=end
        )
        shifts.append(shift)

    db.session.add_all(shifts)
    db.session.commit()

def auto_schedule(schedule_id: int, method_type: str):
    """
    Executes the automatic scheduling logic using the Strategy pattern
    by leveraging the StrategyFactory and AutoScheduler directly in the Controller.

    The logic now flows: Controller -> StrategyFactory (select strategy) -> AutoScheduler (execute strategy).

    Args:
        schedule_id (str): The ID of the schedule to be processed.
        method_type (str): The strategy to use (e.g., 'priority', 'random').

    Returns:
        dict: The result of the scheduling operation.
    """
    # collect staff and unassigned shift templates for the schedule
    
    
    staff_list = Staff.query.all()
    
    generate_random_templates(schedule_id, num_templates=10)
    
    shift_templates = Shift.query.filter_by(schedule_id=schedule_id, staff_id=None).all()

    try:
        strategy = ScheduleStrategyFactory.create_strategy(method_type)
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    
    scheduler = AutoScheduler(strategy, staff_list, [{"start_time": s.start_time, "end_time": s.end_time} for s in shift_templates], schedule_id)
    result = scheduler.generate_schedule()
    
    try:
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": f"Auto-scheduling failed: {e}"}


def schedule_shift(admin_id: int, staff_id: int, schedule_id: int, start_time, end_time):
    """Create a shift under a schedule assigned to a staff member.

    This is a thin controller wrapper that persists the Shift.
    """
    # enforce admin permission
    actor = get_user(admin_id)
    if not actor or actor.role != "admin":
        raise PermissionError("Only admins can schedule shifts")
    if not staff_id or not schedule_id:
        raise ValueError("staff_id and schedule_id are required")

    # parse datetimes if strings
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time)
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time)

    shift = Shift(
        staff_id=staff_id,
        schedule_id=schedule_id,
        start_time=start_time,
        end_time=end_time,
    )
    db.session.add(shift)
    db.session.commit()
    return shift.get_json()


def get_shift_report(admin_id: int):
    """Return all shifts (simple report) for an admin dashboard.

    No strict admin checks are enforced here; controllers that call this
    should ensure permissions.
    """
    actor = get_user(admin_id)
    if not actor or actor.role != "admin":
        raise PermissionError("Only admins can view shift reports")

    shifts = Shift.query.order_by(Shift.start_time).all()
    return [s.get_json() for s in shifts]