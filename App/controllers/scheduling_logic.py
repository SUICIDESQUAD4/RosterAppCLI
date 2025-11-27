# App/controllers/scheduling_logic.py
from App.database import db
from App.models import Staff, Shift
from App.models.strategy import (
    EvenDistributionStrategy,
    MinimalDaysStrategy,
    BalancedShiftStrategy,
)


# --- ScheduleStrategyFactory ---
# Factory returns the model-layer strategy classes so tests importing from models work.
class ScheduleStrategyFactory:
    """Factory method to create the appropriate scheduling strategy."""
    STRATEGY_MAP = {
        'even': EvenDistributionStrategy,
        'minimal': MinimalDaysStrategy,
        'balanced': BalancedShiftStrategy,
    }

    @staticmethod
    def create_strategy(method_type: str):
        """Instantiates and returns a concrete ScheduleStrategy object."""
        method_type = method_type.lower().strip()
        strategy_class = ScheduleStrategyFactory.STRATEGY_MAP.get(method_type)
        
        if not strategy_class:
            raise ValueError(f"Invalid scheduling method type: {method_type}. Must be one of {list(ScheduleStrategyFactory.STRATEGY_MAP.keys())}")
        
        return strategy_class()


# --- AutoScheduler (Context) Class ---
class AutoScheduler:
    """
    The Context class in the Strategy Pattern. Executes the schedule generation.
    """
    def __init__(self, strategy, staff_list, schedule_templates, schedule_id):
        self._strategy = strategy
        self._staff_list = staff_list
        self._schedule_templates = schedule_templates
        self._schedule_id = schedule_id

    def generate_schedule(self):
        """
        Delegates the schedule generation to the configured strategy and persists it.
        Expects strategies from App.models.strategy which work with Shift objects.
        """
        # Step 1: Generate the new shifts using the chosen strategy
        new_shifts = self._strategy.generate(
            self._schedule_id,
            self._staff_list, 
            self._schedule_templates
        )
        
        # Step 2: Save the generated shifts to the database (Persistence)
        self.save_schedule(new_shifts)
        
        # Step 3: Return the JSON representation of the new shifts
        return [s.get_json() for s in new_shifts]

    def save_schedule(self, shifts_to_save):
        """
        Persists the list of generated Shift objects to the database.
        """
        if shifts_to_save:
            db.session.add_all(shifts_to_save)
            db.session.commit()