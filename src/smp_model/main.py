import os

from src.smp_dash.main import ModelDash
from src.smp_model.input import ModelInput
from src.smp_model.model import Model
from src.smp_model.model_config import ModelConfig
from src.smp_scenario.scenario_config import ScenarioConfig


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
    model = Model(input)
    model.solve_model()
    model.output.create_output()


if __name__ == '__main__':
    input_folder_path = os.path.join('data', 'scenarios', 'base', 'input')
    output_folder_path = os.path.join('data', 'scenarios', 'base', 'output')

    config = ScenarioConfig.create_from_json(os.path.join(input_folder_path, 'config.json'))
    model_config = config.get_model_config()
    run_model(
        input_folder_path=input_folder_path,
        output_folder_path=output_folder_path,
        model_config=model_config,
    )

    dash = ModelDash(
        input_folder_path,
        output_folder_path,
    )
    dash.plot_results()
