from App.database import db
from .user import User

class Staff(User):
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "staff",
    }

    def __init__(self, username, password):
        super().__init__(username, password, "staff")

    def view_roster(self):
        from App.models.shift import Shift

        shifts = Shift.query.filter_by(staff_id=self.id).all()
        return [s.get_json() for s in shifts]

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

