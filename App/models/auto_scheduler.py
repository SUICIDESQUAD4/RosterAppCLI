import abc
from datetime import datetime
from App.database import db
from App.models.staff import Staff
from App.models.shift import Shift
from App.models.strategy import ScheduleStrategy, EvenDistribution, MinimalDays, BalancedShift

class AutoScheduler:
    def __init__(self, strategy: ScheduleStrategy, staff_list: list[Staff], schedule_templates: list[dict], schedule_id: int):
        self._strategy = strategy
        self._staff_list = staff_list
        self._schedule_templates = schedule_templates
        self._schedule_id = schedule_id

    def generate_schedule(self) -> list[dict]:
        new_shifts = self._strategy.generate(
            self._staff_list, 
            self._schedule_templates, 
            self._schedule_id
        )
        
        self.save_schedule(new_shifts)
        
        return [s.get_json() for s in new_shifts]

    def save_schedule(self, shifts_to_save: list[Shift]):
        if shifts_to_save:
            db.session.add_all(shifts_to_save)
            db.session.commit()