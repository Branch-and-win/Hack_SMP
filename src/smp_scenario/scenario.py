import os
import shutil
from datetime import datetime
from typing import Union, List

import pandas as pd

from src.smp_dash.main_old import ModelDash
from src.smp_model.main import run_model
from src.smp_scenario.parent_scenario_config import ParentScenarioConfig
from src.smp_scenario.scenario_config import ScenarioConfig


class Scenario:
    """
    Сценарий расчета СМП
    """

    def __init__(
            self,
            name: str,
            scenario_folder_path: str,
            config: Union[ScenarioConfig, ParentScenarioConfig],
    ):
        # Название сценария
        self.name: str = name
        # Настройки сценария
        self.config: ScenarioConfig = config
        # Путь к папке сценария
        self.scenario_folder_path: str = scenario_folder_path
        # Путь к входным данным сценария
        self.input_folder_path: str = os.path.join(self.scenario_folder_path, 'input')
        # Путь к выходным данным сценария
        self.output_folder_path: str = os.path.join(self.scenario_folder_path, 'output')

        # Входные данные в формате DataFrame
        self.ports_df = pd.DataFrame
        self.edges_df = pd.DataFrame
        self.icebreakers_df = pd.DataFrame
        self.vessels_df = pd.DataFrame
        self.speed_decrease_df = pd.DataFrame

    @property
    def ports_dict(self):
        if not len(self.ports_df):
            return {}
        return self.ports_df.set_index('point_id').to_dict(orient='index')

    @classmethod
    def create_scenario(cls, scenario_folder_path: str, scenario_name: str):
        """
        Создание базового сценария на основе данных из папки
        """
        input_folder_path = os.path.join(scenario_folder_path, 'input')
        config = ScenarioConfig.create_from_json(os.path.join(input_folder_path, 'config.json'))

        return cls(
            name=scenario_name,
            scenario_folder_path=scenario_folder_path,
            config=config,
        )

    @staticmethod
    def clear_or_create_folder(folder_path: str):
        """
        Отчистка и создании папки по пути
        """
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        os.makedirs(folder_path)

    def clear_folders(self):
        """
        Отчистка входных и выходных данных
        """
        self.clear_or_create_folder(self.input_folder_path)
        self.clear_or_create_folder(self.output_folder_path)

    def fill_input_data_from_scenario_files(self, other_scenario: 'Scenario' = None):
        """
        Задание входных данных (DataFrame) с помощью данных из другого сценария
        """
        if other_scenario is None:
            other_scenario = self
        with pd.ExcelFile(os.path.join(other_scenario.input_folder_path, 'model_data.xlsx')) as reader:
            self.ports_df = pd.read_excel(reader, sheet_name='points')
            self.edges_df = pd.read_excel(reader, sheet_name='edges')
            self.icebreakers_df = pd.read_excel(reader, sheet_name='icebreakers')
            self.vessels_df = pd.read_excel(reader, sheet_name='vessels')
            self.speed_decrease_df = pd.read_excel(reader, sheet_name='speed_decrease')

    def save_input_objects_to_folder(self):
        """
        Сохранение данных в папку со входными данными с помощью данных DataFrame
        """
        self.clear_folders()
        with pd.ExcelWriter(os.path.join(self.input_folder_path, 'model_data.xlsx')) as writer:
            self.ports_df.to_excel(writer, sheet_name='points', index=False)
            self.edges_df.to_excel(writer, sheet_name='edges', index=False)
            self.icebreakers_df.to_excel(writer, sheet_name='icebreakers', index=False)
            self.vessels_df.to_excel(writer, sheet_name='vessels', index=False)
            self.speed_decrease_df.to_excel(writer, sheet_name='speed_decrease', index=False)
        self.config.to_json(self.input_folder_path)

    def copy_input_from_other_scenario(self, other_scenario: 'Scenario'):
        """
        Копия входных данных из другого сценария
        """
        self.fill_input_data_from_scenario_files(other_scenario)
        self.save_input_objects_to_folder()
        self.copy_velocity_env(other_scenario)

    def copy_velocity_env(self, other_scenario: 'Scenario') -> None:
        shutil.copyfile(
            os.path.join(other_scenario.input_folder_path, 'velocity_env.xlsx'),
            os.path.join(self.input_folder_path, 'velocity_env.xlsx')
        )

    def create_input_from_prev_scenario(self, prev_scenario: 'Scenario'):
        """
        Создание входных данных сценария на основе выходных данных другого сценария
        """
        self.fill_input_data_from_scenario_files(prev_scenario)
        self.update_input_from_output(prev_scenario)
        self.save_input_objects_to_folder()
        self.copy_velocity_env(prev_scenario)

    def update_input_from_output(self, prev_scenario: 'Scenario'):
        """
        Обновление входных данных на основе выходных данных другого сценария
        """
        if not os.path.exists(os.path.join(prev_scenario.output_folder_path, 'departures.xlsx')):
            raise FileNotFoundError('Не найден выходной файл departures.xlsx в предыдущем сценарии.')

        with pd.ExcelFile(os.path.join(prev_scenario.output_folder_path, 'departures.xlsx')) as reader:
            departures_df = pd.read_excel(reader, sheet_name='Sheet1')

        # Отправления, которые пересекают дату начала планирования текущего сценария
        cross_start_departures_df = departures_df[
            (departures_df['time_from_dt'] < self.config.start_date_dt)
            & (departures_df['time_to_dt'] > self.config.start_date_dt)
        ]
        update_start_points_dict = {}
        for row in cross_start_departures_df.itertuples():
            update_start_points_dict[row.vessel_id] = {
                'start_point_id': row.port_to_id,
                # Корректировка времени конца для ожиданий, пересекающих дату начала
                'start_date': row.time_to_dt if row.port_from_id != row.port_to_id else self.config.start_date_dt,
            }
        # Отправления, которые закончили перемещение до даты начала сценария
        ended_departures_df = departures_df[
            (departures_df['time_to_dt'] <= self.config.start_date_dt)
            & (~departures_df['vessel_id'].isin(update_start_points_dict))
        ]
        # Фильтрация только по последним перемещениям
        ended_departures_df = ended_departures_df.loc[ended_departures_df.groupby('vessel_id')['time_to_dt'].idxmax()]
        for row in ended_departures_df.itertuples():
            update_start_points_dict[row.vessel_id] = {
                'start_point_id': row.port_to_id,
                'start_date': self.config.start_date_dt,
            }
        ports_dict = self.ports_dict
        for row in self.vessels_df.itertuples():
            if row.vessel_id in update_start_points_dict:
                start_point_id = update_start_points_dict[row.vessel_id]['start_point_id']
                start_date = update_start_points_dict[row.vessel_id]['start_date']

                self.vessels_df.at[row.Index, 'start_point_id'] = start_point_id
                self.vessels_df.at[row.Index, 'start_point_name'] = ports_dict[start_point_id]['point_name']
                self.vessels_df.at[row.Index, 'date_start'] = start_date
            if self.vessels_df.at[row.Index, 'date_start'] < self.config.start_date_dt:
                self.vessels_df.at[row.Index, 'date_start'] = self.config.start_date_dt

        # Удаление выполненных заявок
        self.vessels_df = self.vessels_df[~(self.vessels_df['start_point_id'] == self.vessels_df['end_point_id'])]

        for row in self.icebreakers_df.itertuples():
            if row.vessel_id in update_start_points_dict:
                start_point_id = update_start_points_dict[row.vessel_id]['start_point_id']
                start_date = update_start_points_dict[row.vessel_id]['start_date']

                self.icebreakers_df.at[row.Index, 'start_point_id'] = start_point_id
                self.icebreakers_df.at[row.Index, 'start_point_name'] = ports_dict[start_point_id]['point_name']
                self.icebreakers_df.at[row.Index, 'date_start'] = start_date
            if self.icebreakers_df.at[row.Index, 'date_start'] < self.config.start_date_dt:
                self.icebreakers_df.at[row.Index, 'date_start'] = self.config.start_date_dt

    def run_optimization(self):
        """
        Запуск оптимизации СМП на данных сценария
        """
        model_config = self.config.get_model_config()
        run_model(
            self.input_folder_path,
            self.output_folder_path,
            model_config,
        )

    def optimize(self):
        self.run_optimization()

    def create_dash(self, scenario_start_dates: List[datetime]):
        """
        Создание отчета
        """
        dash = ModelDash(
            self.input_folder_path,
            self.output_folder_path,
            scenario_start_dates=scenario_start_dates
        )
        dash.plot_results()


if __name__ == '__main__':
    scenario_name = 'base'
    base_scenario = Scenario.create_scenario(os.path.join('.', 'data', 'scenarios', scenario_name), scenario_name)

    base_scenario.optimize()
    base_scenario.create_dash([base_scenario.config.start_date_dt])
