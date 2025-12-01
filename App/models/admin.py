from datetime import datetime
from App.database import db
from .user import User


class Admin(User):
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "admin",
    }

    def __init__(self, username, password):
        super().__init__(username, password, "admin")

    # UML: ScheduleShift()
    def schedule_shift(self, staff_id: int, schedule_id: int, start, end):
        """Create and persist a Shift assigned to staff under a schedule.

        start/end can be datetimes or ISO-8601 strings.
        Returns the created Shift object.
        """
        from App.models.shift import Shift

        if not isinstance(start, datetime):
            start_dt = datetime.fromisoformat(start)
        else:
            start_dt = start

        if not isinstance(end, datetime):
            end_dt = datetime.fromisoformat(end)
        else:
            end_dt = end

        shift = Shift(
            staff_id=staff_id,
            schedule_id=schedule_id,
            start_time=start_dt,
            end_time=end_dt,
        )
        db.session.add(shift)
        db.session.commit()
        return shift

    # UML: autoSchedule(methodType)
    def auto_schedule(self, schedule_id: int, method_type: str):
        """Run the AutoScheduler with the chosen strategy for a schedule.

        method_type should be one of: 'even', 'minimal', 'balanced'.
        Returns list of assigned shift JSON objects.
        """
        from App.models.auto_scheduler import AutoScheduler
        from App.models.strategy import (
            EvenDistributionStrategy,
            MinimalDaysStrategy,
            BalancedShiftStrategy,
        )
        from App.models.shift import Shift
        from App.models.staff import Staff

        staff_list = Staff.query.all()
        # Treat unassigned shifts for this schedule as templates to fill
        shift_templates = Shift.query.filter_by(schedule_id=schedule_id, staff_id=None).all()

        scheduler = AutoScheduler(staff_list, shift_templates)

        method = method_type.lower() if isinstance(method_type, str) else str(method_type)
        if method in ("even", "even_distribution", "even distribution"):
            strategy = EvenDistributionStrategy()
        elif method in ("minimal", "minimal_days", "minimal days"):
            strategy = MinimalDaysStrategy()
        else:
            strategy = BalancedShiftStrategy()

        scheduler.set_strategy(strategy)
        assigned = scheduler.generate_schedule(schedule_id)

        # Persist assigned shifts
        for s in assigned:
            db.session.add(s)
        db.session.commit()

        return [s.get_json() for s in assigned]

    # UML: viewShift()
    def view_shift(self, shift_id: int):
        from App.models.shift import Shift

        shift = db.session.get(Shift, shift_id)
        return shift.get_json() if shift else None
    
