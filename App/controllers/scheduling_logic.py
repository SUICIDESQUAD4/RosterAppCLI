# App/controllers/scheduling_logic.py
import abc
from datetime import datetime
from App.database import db
from App.models import Staff, Shift, Schedule # Required for type hinting and database interaction

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


# --- 2. AutoScheduler (Context) Class ---
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