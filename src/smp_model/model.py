from pyomo.environ import Var, Binary, Objective, quicksum, minimize, SolverFactory, ConcreteModel
from pyomo.core import value

from src.smp_model.input import ModelInput
from src.smp_model.output import ModelOutput
from src.smp_model.utils import constraints_from_dict

from collections import defaultdict
import copy
import sys


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
		for l in self.input.locations:
			if l.time == l.vessel.time_start and l.vessel.port_start == l.port:
				self.model.stop_place[l] = 1
			else:
				self.model.stop_place[l] = 0

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
					self.model.departure[d] * d.duration 
					for d in self.input.departures 
					if not d.edge.is_fict
				) / 100
			)
			, sense=minimize
		)

		return

	def solve_model(self):
		print('Запуск оптимизации')
		print(self.input.config)
		
		# Solver = SolverFactory('cbc')

		# Solver.options['Threads' ] = 10
		# Solver.options['second' ] = 1800
		# Solver.options['allowableGap' ] = 0.02

		#solver = SolverFactory('appsi_highs')
		#solver.options['time_limit'] = 900
		#solver.options['mip_rel_gap'] = 0.02

		solver_name = 'appsi_highs'
		solver = SolverFactory(solver_name)
		# self.model.write('1.lp', io_options={'symbolic_solver_labels': True})
		if solver_name == 'appsi_highs':
			solver.options['time_limit'] = 3600
			solve_results = solver.solve(self.model, tee=True)
		else:
			solver.options['TimeLimit'] = 3600
			solver.options['Method'] = 3
			solve_results = solver.solve(self.model, tee=True, warmstart=True)

		return       
	
	def correct_results(self):
		print('Корректировка результатов')

		### Таблица Departures
		self.model.departure_result = defaultdict(int)
		self.model.departure_results = list()
		delay = defaultdict(int)
		corrected_time = dict()
		corrected_speed = dict()
		corrected_duration = dict()
		# vessel_port_example = dict()

		for d in self.input.departures:
			if value(self.model.departure[d]) > 0.5:
				self.model.departure_result[d] = 1
				corrected_time[d] = d.time
				corrected_speed[d] = d.speed
				corrected_duration[d] = d.duration
			
			# if d.edge.port_from.id == d.edge.port_to.id:
			# 	vessel_port_example[(d.vessel.id, d.edge.port_from.id)] = d

		# Связки
		linkage_departures = defaultdict(list)
		len_linkage = defaultdict(int)
		vessel_departures = defaultdict(list)
		for d in self.model.departure_result.keys():
			if d.edge.port_from.id != d.edge.port_to.id:
				linkage_departures[d.edge.port_from.id, d.edge.port_to.id, d.time].append(d)
				len_linkage[d.edge.port_from.id, d.edge.port_to.id, d.time] += 1
				vessel_departures[d.vessel.id].append(d)


		LINKAGES = sorted([linkage for linkage in linkage_departures.keys() 
					if len_linkage[linkage] > 1], key=lambda x: x[2])

		# Сортируем отправления по дате
		for vessel_id in vessel_departures.keys():
			vessel_departures[vessel_id] = sorted(vessel_departures[vessel_id],
											key=lambda x: x.time)



		# Итерируемся по связкам и сдвигаем время
		for linkage in LINKAGES:
			speed = min(d.speed for d in linkage_departures[linkage])
			duration = max(d.duration for d in linkage_departures[linkage])
			start_time = max(d.time + delay[d] for d in linkage_departures[linkage])
			for d in linkage_departures[linkage]:
				prev_delay = 0
				prev_time = start_time
				prev_duration = duration

				corrected_speed[d] = speed
				corrected_duration[d] = duration
				corrected_time[d] = start_time

				for d1 in vessel_departures[d.vessel.id]:
					if d1.time > d.time:
						delay[d1] = max(prev_time + prev_delay + prev_duration - d1.time, 0)
						corrected_time[d1] = d1.time + delay[d1]

						if delay[d1] == 0:
							break
						prev_delay = delay[d1]
						prev_time = d1.time
						prev_duration = d1.duration

		# Записываем результат для формирования отчета
		for vessel_id in vessel_departures.keys():
			prev_finish_time = 0
			for d in vessel_departures[vessel_id]:

				# Добавление ребра А-А
				interval = corrected_time[d] - max(d.vessel.time_start, prev_finish_time)
				if interval > 0:
					# d1 = vessel_port_example[vessel_id, d.edge.port_from.id]
					d1 = copy.deepcopy(d)
					d1.speed = 0
					d1.edge.avg_norm = 21
					d1.is_icebreaker_assistance = 0
					d1.edge.port_to = d1.edge.port_from

					d1.time = corrected_time[d] - interval
					d1.duration = interval
					self.model.departure_results.append(d1)

				 
				d.speed = corrected_speed[d]
				d.duration = corrected_duration[d]
				d.time = corrected_time[d]
				self.model.departure_results.append(d)

				prev_finish_time = d.time + d.duration

		# for d in self.model.departure_result.keys():
		# 	d.speed = corrected_speed[d]
		# 	d.duration = corrected_duration[d]
		# 	d.time = corrected_time[d]
		# 	self.model.departure_results.append(d)
			

		### Таблица Locations
		self.model.stop_place_result = dict()
		self.model.stop_place_results = list()
		for l in self.input.locations:
			self.model.stop_place_result[l] = value(self.model.stop_place[l])
			if value(self.model.stop_place[l]) > 0.5:
				try:
					l.time = max(corrected_time[d] + corrected_duration[d] for d in vessel_departures[l.vessel.id])
				except:
					# почему-то судно с vessel.id = 14 попадает сюда, хотя его нет в расчете
					pass
				self.model.stop_place_results.append(l)

		return


