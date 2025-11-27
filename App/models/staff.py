from App.database import db
from .user import User

class Staff(User):
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "staff",
    }

    def __init__(self, username, password):
        super().__init__(username, password, "staff")

    # UML: viewRoster()
    def view_roster(self):
        """Return the roster (list of shifts) assigned to this staff member."""
        from App.models.shift import Shift

        shifts = Shift.query.filter_by(staff_id=self.id).all()
        return [s.get_json() for s in shifts]

    # UML: clockIn()
    def clock_in(self, shift_id: int):
        from datetime import datetime
        from App.models.shift import Shift
        shift = db.session.get(Shift, shift_id)
        if not shift:
            raise ValueError("Shift not found")
        if shift.staff_id != self.id:
            raise PermissionError("Cannot clock in to a shift not assigned to this staff member")
        shift.clock_in = datetime.utcnow()
        db.session.commit()
        return shift

    # UML: clockOut()
    def clock_out(self, shift_id: int):
        from datetime import datetime
        from App.models.shift import Shift
        shift = db.session.get(Shift, shift_id)
        if not shift:
            raise ValueError("Shift not found")
        if shift.staff_id != self.id:
            raise PermissionError("Cannot clock out of a shift not assigned to this staff member")
        shift.clock_out = datetime.utcnow()
        db.session.commit()
        return shift

    # Provide `shifts` property mapping to shifts for this staff member
    @property
    def shifts(self):
        from App.models.shift import Shift
        return Shift.query.filter_by(staff_id=self.id).all()
