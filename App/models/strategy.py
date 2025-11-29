import abc
from datetime import datetime
from App.database import db
from App.models.staff import Staff
from App.models.shift import Shift 

def calculate_duration_hours(start_time_str, end_time_str):
    try:
        start = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        duration = end - start
        return duration.total_seconds() / 3600
    except Exception:
        return 0.0

class ScheduleStrategy(abc.ABC):
    @abc.abstractmethod
    def generate(self, staff_list: list[Staff], schedule_templates: list[dict], schedule_id: int) -> list[Shift]:
        pass

class EvenDistribution(ScheduleStrategy):
    def generate(self, staff_list: list[Staff], schedule_templates: list[dict], schedule_id: int) -> list[Shift]:
        new_shifts = []
        if not staff_list or not schedule_templates:
            return new_shifts

        num_staff = len(staff_list)
        
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

class MinimalDays(ScheduleStrategy):
    def generate(self, staff_list: list[Staff], schedule_templates: list[dict], schedule_id: int) -> list[Shift]:
        new_shifts = []
        if not staff_list or not schedule_templates:
            return new_shifts

        staff_shift_counts = {staff.id: 0 for staff in staff_list}

        for template in schedule_templates:
            staff_id_to_assign = min(staff_shift_counts, key=staff_shift_counts.get)
            
            new_shifts.append(Shift(
                staff_id=staff_id_to_assign,
                schedule_id=schedule_id,
                start_time=template['start_time'],
                end_time=template['end_time']
            ))
            
            staff_shift_counts[staff_id_to_assign] += 1
            
        return new_shifts

class BalancedShift(ScheduleStrategy):
    def generate(self, staff_list: list[Staff], schedule_templates: list[dict], schedule_id: int) -> list[Shift]:
        new_shifts = []
        if not staff_list or not schedule_templates:
            if not staff_list:
                print("no staff")
            if not schedule_templates:
                print("no templates")
                
            return new_shifts

        staff_hour_totals = {staff.id: 0.0 for staff in staff_list}

        for template in schedule_templates:
            duration = calculate_duration_hours(template['start_time'], template['end_time']) 
            
            staff_id_to_assign = min(staff_hour_totals, key=staff_hour_totals.get)
            
            new_shifts.append(Shift(
                staff_id=staff_id_to_assign,
                schedule_id=schedule_id,
                start_time=template['start_time'],
                end_time=template['end_time']
            ))
            
            staff_hour_totals[staff_id_to_assign] += duration
            
        return new_shifts
class ScheduleStrategyFactory:
    STRATEGY_MAP = {
        'even': EvenDistribution,
        'minimal': MinimalDays,
        'balanced': BalancedShift
    }

    @staticmethod
    def create_strategy(method_type: str) -> ScheduleStrategy:
        method_type = method_type.lower().strip()
        strategy_class = ScheduleStrategyFactory.STRATEGY_MAP.get(method_type)
        
        if not strategy_class:
            raise ValueError(f"Invalid scheduling method type: {method_type}. Must be one of {list(ScheduleStrategyFactory.STRATEGY_MAP.keys())}")
        
        return strategy_class()