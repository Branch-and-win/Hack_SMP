import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.smp_scenario.scenario import Scenario


if __name__ == '__main__':
    base_scenario = Scenario.create_base_scenario(os.path.join('data', 'scenarios', 'base'))
    base_scenario.run_optimization()
