import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.smp_model.model_config import ModelConfig


class ScenarioConfig:
    """
    Конфиг сценария СМП
    """
    __slots__ = (
        'start_date',
        'duration_days',
        'interval_hours',
        'cross_days',
        'timelimit',
        'k_bests',
    )

    def __init__(self, start_date, duration_days, interval_hours, cross_days, timelimit, k_bests):
        # Дата начала построения графика движения
        self.start_date: str = start_date
        # Количество дней планирования
        self.duration_days: int = duration_days
        # Уровень дискретизации времени в оптимизации
        self.interval_hours: int = interval_hours
        # Количество доп. дней планирования
        self.cross_days: int = cross_days

        self.timelimit: int = timelimit
        self.k_bests: int = k_bests

    @classmethod
    def create_from_dict(cls, config_dict: dict) -> 'ScenarioConfig':
        """
        Создание конфига из словаря
        """
        return cls(
            config_dict['start_date'],
            config_dict['duration_days'],
            config_dict['interval_hours'],
            config_dict['cross_days'],
            config_dict['timelimit'],
            config_dict['k_bests'],
        )

    @property
    def start_date_dt(self):
        return datetime.strptime(self.start_date, '%d-%m-%Y')

    @property
    def end_date_dt(self) -> datetime:
        return self.start_date_dt + timedelta(days=self.duration_days)

    @staticmethod
    def json_to_dict(json_file_path: str) -> dict:
        with open(json_file_path) as f:
            return json.load(f)

    @classmethod
    def create_from_json(cls, json_file_path: str) -> 'ScenarioConfig':
        """
        Создание конфига из json файла
        """
        config = cls.create_from_dict(cls.json_to_dict(json_file_path))
        return config

    def to_json(self, output_folder_path: str) -> None:
        """
        Сохранение конфига в json файл
        """
        with open(os.path.join(output_folder_path, 'config.json'), 'w') as out_json:
            json.dump({
                attr_name: getattr(self, attr_name) for attr_name in self.__slots__
            }, out_json, indent=4)

    def get_model_config(self) -> ModelConfig:
        """
        Создание конфига для оптимизационной модели
        """
        return ModelConfig(
            hours_in_interval=self.interval_hours,
            hours_in_horizon=self.interval_hours * self.duration_days * 24,
            hours_in_cross=self.interval_hours * self.cross_days * 24,
            start_date=self.start_date_dt,
            timelimit=self.timelimit,
            k_bests=self.k_bests,
        )


if __name__ == '__main__':
    ScenarioConfig.create_from_json(os.path.join('.', 'data', 'scenarios', 'base', 'input', 'config.json'))