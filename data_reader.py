import pandas as pd

lat = pd.read_excel("data/IntegrVelocity.xlsx", sheet_name='lat', header=None)
lon = pd.read_excel("data/IntegrVelocity.xlsx", sheet_name='lon', header=None)
integer_vel = pd.read_excel("data/IntegrVelocity.xlsx", sheet_name='03-Mar-2020', header=None)


points_info = pd.read_excel('data/graph.xlsx', sheet_name='points')
edges_info = pd.read_excel('data/graph.xlsx', sheet_name='edges')

points_info['start_point_id'] = points_info['point_id']
points_info['end_point_id'] = points_info['point_id']

edges_info = edges_info.merge(points_info[['end_point_id', 'point_name']], on=['end_point_id'], how='left')
edges_info.rename(columns={'point_name':'end_point_name'}, inplace=True)

edges_info = edges_info.merge(points_info[['start_point_id', 'point_name']], on=['start_point_id'], how='left')
edges_info.rename(columns={'point_name':'start_point_name'}, inplace=True)

edges_info = edges_info[['start_point_name', 'end_point_name']]




