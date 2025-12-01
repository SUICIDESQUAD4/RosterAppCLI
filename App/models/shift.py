from datetime import datetime
from App.database import db

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # staff_id is nullable because the Strategy Pattern needs to create shifts 
    # as unassigned templates first.
    staff_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True) 
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedule.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    clock_in = db.Column(db.DateTime, nullable=True)
    clock_out = db.Column(db.DateTime, nullable=True)

    # Renamed backref for clarity to avoid collision if Staff had other relationships
    staff = db.relationship("Staff", backref="scheduled_shifts", foreign_keys=[staff_id]) 

    def get_json(self):
        return {
            "id": self.id,
            "staff_id": self.staff_id,
            "staff_name": self.staff.username if self.staff else None,
            "schedule_id": self.schedule_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "clock_in": self.clock_in.isoformat() if self.clock_in else None,
            "clock_out": self.clock_out.isoformat() if self.clock_out else None
        }