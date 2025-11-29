import abc
from datetime import datetime
from App.database import db
from App.models.staff import Staff
from App.models.shift import Shift
from App.models.strategy import ScheduleStrategy, EvenDistribution, MinimalDays, BalancedShift

class AutoScheduler:
    """
    The Context class in the Strategy Pattern. Executes the schedule generation.
    """
    def __init__(self, strategy: ScheduleStrategy, staff_list: list[Staff], schedule_templates: list[dict], schedule_id: int):
        self._strategy = strategy
        self._staff_list = staff_list
        self._schedule_templates = schedule_templates
        self._schedule_id = schedule_id

    def generate_schedule(self) -> list[dict]:
        """
        Delegates the schedule generation to the configured strategy and persists it.
        """
        # Step 1: Generate the new shifts using the chosen strategy
        new_shifts = self._strategy.generate(
            self._staff_list, 
            self._schedule_templates, 
            self._schedule_id
        )
        
        # Step 2: Save the generated shifts to the database (Persistence)
        self.save_schedule(new_shifts)
        
        # Step 3: Return the JSON representation of the new shifts
        return [s.get_json() for s in new_shifts]

    def save_schedule(self, shifts_to_save: list[Shift]):
        """
        Persists the list of generated Shift objects to the database.
        """
        if shifts_to_save:
            # Before adding new shifts, optionally clear existing shifts for this schedule
            # Shift.query.filter_by(schedule_id=self._schedule_id).delete()
            db.session.add_all(shifts_to_save)
            db.session.commit()