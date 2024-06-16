from dataclasses import dataclass
from datetime import datetime, timedelta

from src.smp_model.model_config import ModelConfig
from src.smp_scenario.scenario_config import ScenarioConfig


@dataclass
class ParentScenarioConfig(ScenarioConfig):
    __slots__ = (
        'start_date',
        'end_date',
        'duration_days',
        'interval_hours',
        'cross_days',
    )

    def __init__(
            self,
            start_date: str,
            end_date: str,
            duration_days: int,
            interval_hours: int,
            cross_days: int,
    ):
        super().__init__(start_date, duration_days, interval_hours, cross_days)
        # Дата окончания планирования родительского сценария
        self.end_date = end_date

    @property
    def end_date_dt(self):
        return datetime.strptime(self.end_date, '%d-%m-%Y')

    @classmethod
    def create_from_dict(cls, config_dict: dict) -> 'ParentScenarioConfig':
        return cls(
            config_dict['start_date'],
            config_dict['end_date'],
            config_dict['duration_days'],
            config_dict['interval_hours'],
            config_dict['cross_days'],
        )

    def get_child_model_config(self, model_start_date_dt: datetime) -> ModelConfig:
        return ModelConfig(
            hours_in_interval=self.interval_hours,
            hours_in_horizon=self.interval_hours * self.duration_days * 24,
            hours_in_cross=self.interval_hours * self.cross_days * 24,
            start_date=model_start_date_dt,
        )