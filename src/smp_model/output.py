import os
from datetime import datetime, timedelta

import pandas as pd
from pyomo.core import value, ConcreteModel
import plotly.express as px

from src.smp_model.input import ModelInput


class ModelOutput:
    def __init__(self, model: ConcreteModel, input: ModelInput):
        self.model = model
        self.input = input

        self.result_departures_df = pd.DataFrame(
            columns=[
                'vessel_name',
                'vessel_id',
                'port_from',
                'port_from_id',
                'port_to',
                'port_to_id',
                'time_from',
                'duration',
                'initial_port',
                'initial_time',
                'target_port',
                'need_assistance',
                'is_icebreaker',
                'time_from_dt',
                'time_to_dt',
                'class_type',
                'integer_ice',
                'speed',
                'max_speed'
            ]
        )
        self.result_locations_df = pd.DataFrame(
            columns=[
                'vessel_name',
                'port',
                'time',
                'initial_port',
                'initial_time',
                'target_port',
                'is_icebreaker',
            ]
        )
        self.start_planning_dates_df = pd.DataFrame(
            columns=[
                'date',
            ]
        )

    def create_output(self):
        print('Подготовка выходных данных')

        result_departures = [
            [
                d.vessel.name,
                d.vessel.id,
                d.edge.port_from.name,
                d.edge.port_from.id,
                d.edge.port_to.name,
                d.edge.port_to.id,
                d.time,
                d.duration,
                d.vessel.port_start.name,
                d.vessel.time_start,
                '-' if d.vessel.is_icebreaker else d.vessel.port_end.name,
                1 if d.is_icebreaker_assistance else 0,
                d.vessel.is_icebreaker,
                self.input.config.start_date + timedelta(hours=d.time),
                self.input.config.start_date + timedelta(hours=d.time + d.duration),
                 d.vessel.class_type,
                round(d.edge.avg_norm, 0),
                d.speed,
                d.vessel.max_speed
            ]
            for d in self.model.departure_results
        ]
        self.result_departures_df = pd.DataFrame(result_departures, columns=self.result_departures_df.columns)

        result_locations = [
            [
                l.vessel.name,
                l.port.name,
                l.time,
                l.vessel.port_start.name,
                l.vessel.time_start,
                '-' if l.vessel.is_icebreaker else l.vessel.port_end.name,
                l.vessel.is_icebreaker
            ]
            for l in self.model.stop_place_results
        ]

        self.result_locations_df = pd.DataFrame(result_locations, columns=self.result_locations_df.columns)

        self.start_planning_dates_df = pd.DataFrame([self.input.config.start_date], columns=self.start_planning_dates_df.columns)

        with pd.ExcelWriter(os.path.join(self.input.output_folder_path, 'departures.xlsx')) as writer:
            self.result_departures_df.to_excel(writer)
        with pd.ExcelWriter(os.path.join(self.input.output_folder_path, 'locations.xlsx')) as writer:
            self.result_locations_df.to_excel(writer)
        with pd.ExcelWriter(os.path.join(self.input.output_folder_path, 'start_planning_dates.xlsx')) as writer:
            self.start_planning_dates_df.to_excel(writer)
        with pd.ExcelWriter(os.path.join(self.input.output_folder_path, 'vessel_best_routes.xlsx')) as writer:
            self.input.vessel_best_routes_df.to_excel(writer)
        return
