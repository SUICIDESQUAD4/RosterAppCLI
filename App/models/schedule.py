from datetime import datetime
from App.database import db

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # UML includes adminID/createdBy and (optionally) staffID. Keep existing
    # created_by for backward-compatibility and add explicit admin_id/staff_id
    # to match the UML diagram.
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    shifts = db.relationship("Shift", backref="schedule", lazy=True)

    def shift_count(self):
        return len(self.shifts)

    def get_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "admin_id": self.admin_id,
            "staff_id": self.staff_id,
            "shift_count": self.shift_count(),
            "shifts": [shift.get_json() for shift in self.shifts]
        }

