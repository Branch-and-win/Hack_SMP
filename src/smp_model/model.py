from pyomo.environ import Var, Binary, Objective, quicksum, minimize, SolverFactory, ConcreteModel

from src.smp_model.input import ModelInput
from src.smp_model.output import ModelOutput
from src.smp_model.utils import constraints_from_dict


class Model:
	def __init__(self, input: ModelInput) -> None:
		self.model = ConcreteModel()
		self.input = input

		self.output = ModelOutput(
			self.model,
			self.input,
		)

		self.create_model()

	def create_model(self):
		print('Подготовка модели')

		## Переменные
		# Индикатор отправления судна v по ребру e в момент времени t
		self.model.departure = Var(self.input.departures, domain=Binary, initialize=0)

		# Индикатор конца пути для судна v в порту p в момент времени t
		self.model.stop_place = Var(self.input.locations, domain=Binary)

		## Ограничения

		# Баланс прибытия и отправки судна в каждом порту
		cons_flow_balance = {}
		for l in self.input.locations:
			cons_flow_balance[l] = (
				(1 if (l.vessel.port_start == l.port and l.vessel.time_start == l.time) else 0)
				+ quicksum(
					self.model.departure[d]
					for d in l.input_departures_by_location
				)
				==
				quicksum(
					self.model.departure[d]
					for d in l.output_departures_by_location
				)
				+ self.model.stop_place[l]
			)			
		constraints_from_dict(cons_flow_balance, self.model, 'cons_flow_balance')

		# У каждого судна должна быть ровно одна конечная точка
		cons_one_stop = {}
		for v in self.input.vessels:
			cons_one_stop[v] = (
				sum(self.model.stop_place[l] for l in v.locations_by_vessel)
				==
				1
			)
		constraints_from_dict(cons_one_stop, self.model, 'cons_one_stop')

		'''
		# Ограничение: запрет движения без ледокола
		cons_icebreaker_assistance = {}
		for d in self.input.departures:
			if d.is_icebreaker_assistance:
				cons_icebreaker_assistance[d] = (
					self.model.departure[d]
					<=
					sum(self.model.departure[d_i] for d_i in d.possible_icebreaker_departures)
				)
		constraints_from_dict(cons_icebreaker_assistance, self.model, 'cons_icebreaker_assistance')
		'''

		# Ограничение: максимальное количество судов в караване
		cons_max_vessels_assistance = {}
		for (e, t) in self.input.edge_t_connections:
			cons_max_vessels_assistance[e, t] = (
				quicksum(
					self.model.departure[self.input.departures_dict[v, e, t, True]]
					for v in self.input.edge_t_connections[e, t].allowed_vessels
					if  (v, e, t, True) in self.input.departures_dict.keys()
				)
				<=
				# TODO: сделать параметром?
				3 * quicksum(
					self.model.departure[self.input.departures_dict[v, e, t, False]]
					for v in self.input.edge_t_connections[e, t].allowed_vessels
					if v.is_icebreaker
				)
			)
		constraints_from_dict(cons_max_vessels_assistance, self.model, 'cons_max_vessels_assistance')


		## Целевая функция 

		# Минимизация суммарного времени в пути и отклонения от конечного порта для каждого судна
		self.model.obj = Objective(
			expr=(
				quicksum(
					(0 if l.vessel.is_icebreaker else ((l.time - l.vessel.time_start) * self.model.stop_place[l]))
					+ (0 if l.vessel.is_icebreaker else (l.min_time_to_end_port * self.model.stop_place[l]) * 5)
					- self.model.stop_place[l] * int(l.port == l.vessel.port_end) * 300
					for l in self.input.locations
				)
				+ quicksum(
					d * 0 for d in self.model.departure.values()
				) / 10
			)
			, sense=minimize
		)

		return

	def solve_model(self):
		print('Запуск оптимизации')
		
		# Solver = SolverFactory('cbc')

		# Solver.options['Threads' ] = 10
		# Solver.options['second' ] = 1800
		# Solver.options['allowableGap' ] = 0.02

		#solver = SolverFactory('appsi_highs')
		#solver.options['time_limit'] = 900
		#solver.options['mip_rel_gap'] = 0.02

		solver = SolverFactory('appsi_highs')
		solver.options['TimeLimit'] = 900

		# self.model.write('1.lp', io_options={'symbolic_solver_labels': True})
		solve_results = solver.solve(self.model, tee=True)

		return       

