import abc
from datetime import datetime
from App.database import db
from App.models.staff import Staff
from App.models.shift import Shift 

# --- Utility Function ---
def calculate_duration_hours(start_time_str, end_time_str):
    """Calculates the duration in hours between two time strings."""
    try:
        # Assuming ISO format like 'YYYY-MM-DD HH:MM:SS'
        # Note: You should enforce a strict date format in your API/route layer
        start = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        duration = end - start
        return duration.total_seconds() / 3600
    except Exception:
        return 0.0

# --- 1. ScheduleStrategy Abstract Interface/Class ---
class ScheduleStrategy(abc.ABC):
    """
    Abstract Base Class for all scheduling algorithms (Strategies).
    """
    @abc.abstractmethod
    def generate(self, staff_list: list[Staff], schedule_templates: list[dict], schedule_id: int) -> list[Shift]:
        """
        Generates a list of new Shift objects based on the strategy.
        """
        pass

# --- 4. EvenDistribution Concrete Strategy ---
class EvenDistribution(ScheduleStrategy):
    """
    Assigns shifts in a simple round-robin fashion.
    """
    def generate(self, staff_list: list[Staff], schedule_templates: list[dict], schedule_id: int) -> list[Shift]:
        new_shifts = []
        if not staff_list or not schedule_templates:
            return new_shifts

        num_staff = len(staff_list)
        
        # Round-robin assignment
        for i, template in enumerate(schedule_templates):
            staff_index = i % num_staff
            staff_id = staff_list[staff_index].id
            
            new_shifts.append(Shift(
                staff_id=staff_id,
                schedule_id=schedule_id,
                start_time=template['start_time'],
                end_time=template['end_time']
            ))
        
        return new_shifts

# --- 5. MinimalDays Concrete Strategy ---
class MinimalDays(ScheduleStrategy):
    """
    Minimizes the total count of shifts assigned to each staff member.
    """
    def generate(self, staff_list: list[Staff], schedule_templates: list[dict], schedule_id: int) -> list[Shift]:
        new_shifts = []
        if not staff_list or not schedule_templates:
            return new_shifts

        # Initialize shift count tracker {staff_id: count}
        staff_shift_counts = {staff.id: 0 for staff in staff_list}

        for template in schedule_templates:
            # Find the staff member with the minimum number of assigned shifts
            staff_id_to_assign = min(staff_shift_counts, key=staff_shift_counts.get)
            
            new_shifts.append(Shift(
                staff_id=staff_id_to_assign,
                schedule_id=schedule_id,
                start_time=template['start_time'],
                end_time=template['end_time']
            ))
            
            # Update the count for the assigned staff member
            staff_shift_counts[staff_id_to_assign] += 1
            
        return new_shifts

# --- 6. BalancedShift Concrete Strategy ---
class BalancedShift(ScheduleStrategy):
    """
    Balances the total duration (hours) assigned to each staff member.
    """
    def generate(self, staff_list: list[Staff], schedule_templates: list[dict], schedule_id: int) -> list[Shift]:
        new_shifts = []
        if not staff_list or not schedule_templates:
            if not staff_list:
                print("no staff")
            if not schedule_templates:
                print("no templates")
                
            return new_shifts

        # Initialize total hours tracker {staff_id: total_hours}
        staff_hour_totals = {staff.id: 0.0 for staff in staff_list}

        for template in schedule_templates:
            # Calculate the duration of the current template shift
            duration = calculate_duration_hours(template['start_time'], template['end_time']) 
            
            # Find the staff member with the minimum total hours
            staff_id_to_assign = min(staff_hour_totals, key=staff_hour_totals.get)
            
            new_shifts.append(Shift(
                staff_id=staff_id_to_assign,
                schedule_id=schedule_id,
                start_time=template['start_time'],
                end_time=template['end_time']
            ))
            
            # Update the total hours for the assigned staff member
            staff_hour_totals[staff_id_to_assign] += duration
            
        return new_shifts

# --- 3. ScheduleStrategyFactory ---
class ScheduleStrategyFactory:
    """ Factory method to create the appropriate scheduling strategy. """
    STRATEGY_MAP = {
        'even': EvenDistribution,
        'minimal': MinimalDays,
        'balanced': BalancedShift
    }

    @staticmethod
    def create_strategy(method_type: str) -> ScheduleStrategy:
        """ Instantiates and returns a concrete ScheduleStrategy object. """
        method_type = method_type.lower().strip()
        strategy_class = ScheduleStrategyFactory.STRATEGY_MAP.get(method_type)
        
        if not strategy_class:
            raise ValueError(f"Invalid scheduling method type: {method_type}. Must be one of {list(ScheduleStrategyFactory.STRATEGY_MAP.keys())}")
        
        return strategy_class()