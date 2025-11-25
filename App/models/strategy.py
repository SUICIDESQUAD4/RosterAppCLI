from abc import ABC, abstractmethod
from typing import List
from App.models.shift import Shift
from App.models.staff import Staff # Use the concrete Staff model for type hinting

# The Strategy Interface (Defines the contract for all scheduling algorithms)
class ScheduleStrategy(ABC):
    """Abstract Base Class for all scheduling strategies."""

    @abstractmethod
    def generate(self, schedule_id: int, staff_list: List[Staff], shifts_to_fill: List[Shift]) -> List[Shift]:
        """
        Generates a list of assigned shifts based on the specific strategy logic.
        
        :param schedule_id: The ID of the schedule being generated.
        :param staff_list: List of available staff members.
        :param shifts_to_fill: List of unassigned Shift templates (start/end times).
        :return: List of completed Shift objects with staff_id assigned.
        """
        pass

# Concrete Strategy 1: Evenly Distribute Shifts
class EvenDistributionStrategy(ScheduleStrategy):
    """
    Distributes shifts among staff as evenly as possible based on shift count.
    """
    def generate(self, schedule_id: int, staff_list: List[Staff], shifts_to_fill: List[Shift]) -> List[Shift]:
        print(f"Applying Even Distribution Strategy for Schedule {schedule_id}...")
        assigned_shifts = []
        
        # Simple round-robin assignment placeholder for model definition:
        staff_count = len(staff_list)
        if staff_count > 0:
            for i, shift in enumerate(shifts_to_fill):
                staff_member = staff_list[i % staff_count]
                shift.staff_id = staff_member.id
                shift.schedule_id = schedule_id
                assigned_shifts.append(shift)
        
        return assigned_shifts

# Concrete Strategy 2: Minimize Working Days
class MinimalDaysStrategy(ScheduleStrategy):
    """
    Distributes shifts to minimize the total number of working days per staff member.
    """
    def generate(self, schedule_id: int, staff_list: List[Staff], shifts_to_fill: List[Shift]) -> List[Shift]:
        print(f"Applying Minimal Days Strategy for Schedule {schedule_id}...")
        assigned_shifts = []
        
        # Simple round-robin assignment placeholder:
        staff_count = len(staff_list)
        if staff_count > 0:
            for i, shift in enumerate(shifts_to_fill):
                staff_member = staff_list[i % staff_count]
                shift.staff_id = staff_member.id
                shift.schedule_id = schedule_id
                assigned_shifts.append(shift)

        return assigned_shifts

# Concrete Strategy 3: Balance Day/Night Shifts
class BalancedShiftStrategy(ScheduleStrategy):
    """
    Distributes shifts to ensure a balance of day and night shifts per staff member.
    """
    def generate(self, schedule_id: int, staff_list: List[Staff], shifts_to_fill: List[Shift]) -> List[Shift]:
        print(f"Applying Balanced Shift Strategy for Schedule {schedule_id}...")
        assigned_shifts = []
        
        # Simple round-robin assignment placeholder:
        staff_count = len(staff_list)
        if staff_count > 0:
            for i, shift in enumerate(shifts_to_fill):
                staff_member = staff_list[i % staff_count]
                shift.staff_id = staff_member.id
                shift.schedule_id = schedule_id
                assigned_shifts.append(shift)

        return assigned_shifts
    