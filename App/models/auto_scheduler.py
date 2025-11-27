from typing import List, Optional
from App.models.strategy import ScheduleStrategy
from App.models.shift import Shift
from App.models.staff import Staff

class AutoScheduler:
    """
    The Context class in the Strategy Pattern. It holds a reference to a 
    ScheduleStrategy and delegates the schedule generation task to it.
    """
    def __init__(self, staff_list: Optional[List[Staff]] = None, shift_templates: Optional[List[Shift]] = None, shifts_to_fill: Optional[List[Shift]] = None, **kwargs):
        self._strategy: Optional[ScheduleStrategy] = None
        self.staff_list = staff_list or []
        self.shift_templates = shift_templates if shift_templates is not None else (shifts_to_fill or [])

    def set_strategy(self, strategy: ScheduleStrategy):
        """Sets the concrete strategy to be used for scheduling."""
        self._strategy = strategy

    def generate_schedule(self, schedule_id: int) -> List[Shift]:
        """
        Executes the chosen strategy to generate the schedule.
        
        It is the controller/service layer's responsibility to set the correct 
        strategy before calling this method.
        """
        if not self._strategy:
            raise ValueError("Scheduling strategy must be set before generating a schedule.")
        
        # Delegate the actual generation to the concrete strategy
        assigned_shifts = self._strategy.generate(
            schedule_id, 
            self.staff_list, 
            self.shift_templates
        )
        return assigned_shifts

    # NOTE: The saveSchedule() method from the UML will be implemented in the 
    # service/controller layer to handle database commit logic.