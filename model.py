from pyomo.environ import *
import pandas as pd
from utils import constraints_from_dict

class Model:
	def __init__(self) -> None:
		self.model = ConcreteModel()

	def create_model(self, input):
		# Индикатор отправления судна v по ребру e в момент времени t
		self.model.departure = Var(input.departures, domain = Binary, initialize = 0)

		# Индикатор конца пути для судна v в порту p в момент времени t
		self.model.stop_place = Var(input.locations, domain = Binary)


		# Баланс прибытия и отправки судна в каждом порту
		consFlowBalance = {}
		for l in input.locations:
			consFlowBalance[l] = (
				(1 if (l.vessel.port_start == l.port and l.vessel.time_start == l.time) else 0) +
				sum(self.model.departure[d] 
					for d in l.input_departures_by_location)
				==
				sum(self.model.departure[d] 
					for d in l.output_departures_by_location) +
				self.model.stop_place[l]
			)			
		constraints_from_dict(consFlowBalance, self.model, 'consFlowBalance')

		# У каждого судна должна быть ровно одна конечная точка
		consOneStop = {}
		for v in input.vessels:
			consOneStop[v] = (
				sum(self.model.stop_place[l] for l in v.locations_by_vessel)
				==
				1
			)
		constraints_from_dict(consOneStop, self.model, 'consOneStop')

		consIcebreakerAssistance = {}
		for d in input.departures:
			if d.is_icebreaker_assistance:
				consIcebreakerAssistance[d] = (
					self.model.departure[d]
					<=
					sum(self.model.departure[d_i] for d_i in d.possible_icebreaker_departures)
				)
		constraints_from_dict(consIcebreakerAssistance, self.model, 'consIcebreakerAssistance')


		## Целевая функция 

		# Минимизация суммарного времени в пути и отклонения от конечного порта для каждого судна
		self.model.obj = Objective(expr = (
			sum((l.time - l.vessel.time_start) * self.model.stop_place[l] +
			(0 if l.vessel.is_icebreaker else (l.port.min_dist[l.vessel.port_end] * self.model.stop_place[l]) * 10) 
				for l in input.locations)
		), sense = minimize)

		return


	def solve_model(self):
		
		#Solver = SolverFactory('cbc')	

		#Solver.options['Threads' ] = 10
		#Solver.options['second' ] = 1800
		#Solver.options['allowableGap' ] = 0.02


		Solver = SolverFactory('appsi_highs')	
		Solver.options['time_limit'] = 900
		Solver.options['mip_rel_gap'] = 0.02


		SolverResults = Solver.solve(self.model, tee=True)

		return       
	

	def create_output(self, input):

		result_list_1 = [
			[
				d.vessel.name,
				d.edge.port_from.name,
				d.edge.port_to.name,
				d.time,
				d.duration,
				d.vessel.port_start.name,
				d.vessel.time_start,
				'-' if d.vessel.is_icebreaker else d.vessel.port_end.name,
				1 if d.is_icebreaker_assistance else 0,
				d.vessel.is_icebreaker
			]
			for d in input.departures
			if value(self.model.departure[d]) > 0.5
		]
		
		result_tmp_1 = pd.DataFrame(result_list_1, columns=[
			'vessel_name', 'port_from', 'port_to', 'time_from', 'duration', 'initial_port', 'initial_time', 'target_port', 'need_assistance', 'is_icebreaker'
		])

		result_tmp_1.to_excel('output/departures.xlsx')

		result_list_2 = [
			[
				l.vessel.name,
				l.port.name,
				l.time,
				l.vessel.port_start.name,
				l.vessel.time_start,
				'-' if l.vessel.is_icebreaker else l.vessel.port_end.name,
				l.vessel.is_icebreaker
			]
			for l in input.locations
			if value(self.model.stop_place[l]) > 0.5
		]
		
		result_tmp_2 = pd.DataFrame(result_list_2, columns=[
			'vessel_name', 'port', 'time', 'initial_port', 'initial_time', 'target_port', 'is_icebreaker'
		])

		result_tmp_2.to_excel('output/locations.xlsx')
		return