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
    )

    def __init__(self, start_date, duration_days, interval_hours, cross_days):
        # Дата начала построения графика движения
        self.start_date: str = start_date
        # Количество дней планирования
        self.duration_days: int = duration_days
        # Уровень дискретизации времени в оптимизации
        self.interval_hours: int = interval_hours
        # Количество доп. дней планирования
        self.cross_days: int = cross_days

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
        )

    @property
    def start_date_dt(self):
        return datetime.strptime(self.start_date, '%d-%m-%Y')

    @property
    def end_date_dt(self) -> datetime:
        return self.start_date_dt + timedelta(days=self.duration_days)

    @classmethod
    def create_from_json(cls, json_file_path: str) -> 'ScenarioConfig':
        """
        Создание конфига из json файла
        """
        with open(json_file_path) as f:
            config = cls.create_from_dict(json.load(f))
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
        )
