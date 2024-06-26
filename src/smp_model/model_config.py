import json
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ModelConfig:
    hours_in_interval: int
    hours_in_horizon: int
    hours_in_cross: int
    start_date: datetime
    timelimit: int
    k_bests: int

    @property
    def end_date(self):
        return self.start_date + timedelta(hours=self.hours_in_horizon)

    @property
    def planning_hours(self):
        return self.hours_in_horizon + self.hours_in_cross

    # @classmethod
    # def create_from_json(cls, json_file_path: str) -> 'ScenarioConfig':
    #     """
    #     Создание конфига из json файла
    #     """
    #     with open(json_file_path) as f:
    #         config = cls.create_from_dict(json.load(f))
    #     return config

    def __str__(self):
        return (
            f'Конфиг запуска: Дата начала - {self.start_date};'
            f' Количество часов в одном интервале - {self.hours_in_interval};'
            f' Количество часов планирования - {self.hours_in_horizon};'
            f' Количество часов сверх планирования (cross) - {self.hours_in_cross};'
            f' Timelimit - {self.timelimit};'
            f' k_bests - {self.k_bests};'
        )
