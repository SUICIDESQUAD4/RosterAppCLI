#app/controllers/initialize.py
from .user import create_user
from App.database import db


def initialize():
    db.drop_all()
    db.create_all()
    create_user('bob', 'bobpass', 'admin')
    create_user('jane', 'janepass', 'staff')
    create_user('alice', 'alicepass', 'staff')
    create_user('tim', 'timpass', 'user')

# db.session.commit()

# # adding dummy schedule data for testing Jane
# schedule = Schedule (
#     name = "Morning Shift",
#     created_by = 1
# )
# db.session.add(schedule)
# db.session.commit()

# # adding dummy shifts for Jane
# shift1 = Shift (
#     schedule_id = schedule.id,
#     staff_id = 2,
#     start_time = "2024-10-01 08:00:00",
#     end_time = "2024-10-01 12:00:00"
# )
# db.session.add(shift1)