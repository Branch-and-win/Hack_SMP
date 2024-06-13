import os

from src.smp_dash.main import ModelDash
from src.smp_model.input import ModelInput
from src.smp_model.model import Model
from src.smp_model.model_config import ModelConfig
from src.smp_scenario.scenario_config import ScenarioConfig
from src.smp_model.graph.length_velocity_calc import dump_velocity_length

def run_model(
        input_folder_path: str,
        output_folder_path: str,
        model_config: ModelConfig,
):
    input = ModelInput(
        input_folder_path=input_folder_path,
        output_folder_path=output_folder_path,
        model_config=model_config,
    )
    dump_velocity_length(input)
    model = Model(input)
    model.solve_model()
    model.output.create_output()


if __name__ == '__main__':
    input_folder_path = os.path.join('data', 'scenarios', 'base', 'input')
    output_folder_path = os.path.join('data', 'scenarios', 'base', 'output')

    config = ScenarioConfig.create_from_json(r'D:\PycharmProjects\SMP\data\scenarios\base\input\config.json')
    model_config = config.get_model_config()
    run_model(
        input_folder_path=r'D:/PycharmProjects//SMP/data/scenarios/base/input/',
        output_folder_path=output_folder_path,
        model_config=model_config,
    )

    dash = ModelDash(
        input_folder_path,
        output_folder_path,
        [config.start_date_dt]
    )
    dash.plot_results()
