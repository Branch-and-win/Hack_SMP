import os
import shutil
from datetime import timedelta, datetime

import pandas as pd

from src.smp_scenario.parent_scenario_config import ParentScenarioConfig
from src.smp_scenario.scenario import Scenario
from src.smp_scenario.scenario_config import ScenarioConfig


class ParentScenario(Scenario):
    """
    Родительский сценарий расчета СМП. Используется для последовательного расчета сценариев по интервалам
    """

    def __init__(
            self,
            name: str,
            scenario_folder_path: str,
            config: ParentScenarioConfig,
    ):
        # Название сценария
        self.name: str = name
        # Настройки сценария
        self.config: ParentScenarioConfig = config
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

        # Путь к папке с дочерними сценариями
        self.child_scenarios_folder_path: str = os.path.join(self.scenario_folder_path, 'child_scenarios')
        # Список последовательных дочерних сценариев
        self.child_scenario_chain = []
        self.create_child_scenarios()

    def create_child_scenarios(self):
        """
        Заполнение списка последовательных дочерних сценариев
        """
        self.clear_or_create_folder(self.child_scenarios_folder_path)
        for days_from_start in range(
                0, int((self.config.end_date_dt - self.config.start_date_dt).days),
                self.config.duration_days):

            child_scenario_name = f'{self.name}_{days_from_start}'
            child_scenario_folder_path = os.path.join(self.child_scenarios_folder_path, child_scenario_name)
            self.clear_or_create_folder(child_scenario_folder_path)

            child_config = ScenarioConfig(
                start_date=datetime.strftime(self.config.start_date_dt + timedelta(days=days_from_start), '%d-%m-%Y'),
                duration_days=self.config.duration_days,
                interval_hours=self.config.interval_hours,
                cross_days=self.config.cross_days,
            )
            scenario = Scenario(
                name=child_scenario_name,
                scenario_folder_path=child_scenario_folder_path,
                config=child_config,
            )
            self.child_scenario_chain.append(scenario)

    def run_chain_optimization(self):
        """
        Последовательных запуск дочерних сценариев
        """
        for i, child_scenario in enumerate(self.child_scenario_chain):
            if i == 0:
                child_scenario.copy_input_from_other_scenario(self)
            else:
                child_scenario.create_input_from_prev_scenario(self.child_scenario_chain[i - 1])
            child_scenario.run_optimization()

    def concatenate_chain_optimization_results(self):
        """
        Объединение результатов последовательных запусков дочерних сценариев
        """
        all_departures_list = []
        for child_scenario in self.child_scenario_chain:
            if not os.path.exists(os.path.join(child_scenario.output_folder_path, 'departures.xlsx')):
                raise FileNotFoundError(f'Не найден выходной файл departures.xlsx в сценарии {child_scenario.name}.')

            with pd.ExcelFile(os.path.join(child_scenario.output_folder_path, 'departures.xlsx')) as reader:
                child_scenario_departures_df = pd.read_excel(reader, sheet_name='Sheet1')
            all_departures_list.append(child_scenario_departures_df)
        all_departures_df = pd.concat(all_departures_list)
        with pd.ExcelWriter(os.path.join(self.output_folder_path, 'departures.xlsx')) as writer:
            all_departures_df.to_excel(writer)


if __name__ == '__main__':
    base_parent_scenario = ParentScenario.create_base_scenario(os.path.join('.', 'data', 'scenarios', 'base_parent'))
    base_parent_scenario.run_chain_optimization()
    base_parent_scenario.concatenate_chain_optimization_results()
    base_parent_scenario.create_dash()
