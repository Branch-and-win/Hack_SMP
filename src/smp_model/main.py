from src.smp_model.input import ModelInput
from src.smp_model.model import Model


if __name__ == '__main__':
    print('Preparing data')
    input = ModelInput(input_folder='data')
    model = Model()

    print('Preparing model')
    model.create_model(input)
    model.solve_model()
    print('Preparing output')
    model.create_output(input)
