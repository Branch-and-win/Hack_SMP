import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.smp_scenario.scenario import Scenario
from src.smp_scenario.parent_scenario import ParentScenario


if __name__ == '__main__':
    scenario_name = 'base'
    base_scenario = Scenario.create_scenario(os.path.join('data', 'scenarios', scenario_name), scenario_name)
    base_scenario.run_optimization()

    # base_parent_scenario = ParentScenario.create_base_scenario(os.path.join('.', 'data', 'scenarios', 'base_parent_test'))
    # base_parent_scenario.run_chain_optimization()
    # base_parent_scenario.concatenate_chain_optimization_results()
    # start_scenarios_dates = [child_scenario.config.start_date_dt for child_scenario in base_parent_scenario.child_scenario_chain]
    # base_parent_scenario.create_dash(start_scenarios_dates)