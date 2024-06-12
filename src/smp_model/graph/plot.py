import os
import pandas as pd
import plotly.express as px

input_folder = 'data'

def read_ports_xlsx(input_folder) -> None:
    port_data = pd.read_excel(os.path.join(input_folder, 'model_data.xlsx'), sheet_name='points')
    return port_data

def read_edges_xlsx(input_folder) -> None:
    edge_data = pd.read_excel(os.path.join(input_folder, 'model_data.xlsx'), sheet_name='edges')
    return edge_data

port_df = read_ports_xlsx(input_folder)
port_df['longitude'] = port_df['longitude'].apply(lambda x: 360 + x if x < 0 else x)
edges_df = read_edges_xlsx(input_folder)

# # px.line_mapbox(us_cities, lat="lat", lon="lon", color="State", zoom=3, height=300)

visible_titles = ['ports']
fig = px.scatter_mapbox(port_df,
                        lat="latitude",
                        lon="longitude",
                        zoom=2,
                        height=1080,
                        width=1920)
for row in edges_df.itertuples():
    fig.add_traces(px.line_mapbox(port_df[port_df['point_id'].isin([row.start_point_id, row.end_point_id])], lat="latitude", lon="longitude").data)
    visible_titles.append(f'{row.start_point_id} - {row.end_point_id}')
    # port_df[port_df['point_id'].isin([row.start_point_id, row.end_point_id])]
    # fig.add_trace()


fig.update_layout(mapbox_style="open-street-map")

# fig.update_layout(
#     updatemenus=[
#         dict(
#             active=0,
#             buttons=list([
#                 dict(label="None",
#                      method="update",
#                      args=[{"visible": [True, False, True, False]},
#                            {"title": "Yahoo",
#                             "annotations": []}]),
#                 dict(label="High",
#                      method="update",
#                      args=[{"visible": [True, True, False, False]},
#                            {"title": "Yahoo High",
#                             "annotations": []}]),
#                 dict(label="Low",
#                      method="update",
#                      args=[{"visible": [False, False, True, True]},
#                            {"title": "Yahoo Low",
#                             "annotations": []}]),
#                 dict(label="Both",
#                      method="update",
#                      args=[{"visible": [True, True, True, True]},
#                            {"title": "Yahoo",
#                             "annotations": []}]),
#             ]),
#         )
#     ])

fig.update_layout(
    updatemenus=[
        dict(
            active=0,
            buttons=list([
                dict(
                    label=visible_title,
                    method="update",
                    args=[{"visible": [True] + [False] * (i - 1) + [True] + (len(visible_titles) - (i - 1) - 1) * [False]},
                          {
                              "title": visible_title,
                              "annotations": []
                          }
                          ]
                )
                for i, visible_title in enumerate(visible_titles)
            ]),
        )
    ])

# visible_titles

#
# BBox = ((df.longitude.min(),   df.longitude.max(),
#          df.latitude.min(), df.latitude.max()))
# fig, ax = plt.subplots(figsize = (30,20))
# ax.set_xlim(BBox[0],BBox[1])
# ax.set_ylim(BBox[2],BBox[3])
# ax.imshow(ruh_m, zorder=0, extent = BBox, aspect= 'equal')
# # ax.imshow(ruh_m)
# plt.show()



# import numpy as np
# import pandas as pd
#
# import requests
# import xml.etree.ElementTree as ET
# from tqdm import tqdm
#
# # Plotting
# import plotly.express as px
#
# # Specify the coordinates (longitude, latitude) of origin and destination
# # first parameter is longitude, second parameter is latitude
#
# source = (-83.920699, 35.96061) # Knoxville
# dest  = (-73.973846, 40.71742)  # New York City
#
# start = "{},{}".format(source[0], source[1])
# end = "{},{}".format(dest[0], dest[1])
# # Service - 'route', mode of transportation - 'driving', without alternatives
# url = 'http://router.project-osrm.org/route/v1/driving/{};{}?alternatives=false&annotations=nodes'.format(start, end)
#
#
# headers = { 'Content-type': 'application/json'}
# r = requests.get(url, headers = headers)
# print("Calling API ...:", r.status_code) # Status Code 200 is success
#
#
# routejson = r.json()
# route_nodes = routejson['routes'][0]['legs'][0]['annotation']['nodes']
#
# ### keeping every third element in the node list to optimise time
# route_list = []
# for i in range(0, len(route_nodes)):
#     if i % 100==1:
#         route_list.append(route_nodes[i])
#
# coordinates = []
#
# for node in tqdm(route_list):
#     try:
#         url = 'https://api.openstreetmap.org/api/0.6/node/' + str(node)
#         r = requests.get(url, headers = headers)
#         myroot = ET.fromstring(r.text)
#         for child in myroot:
#             lat, long = child.attrib['lat'], child.attrib['lon']
#         coordinates.append((lat, long))
#     except:
#         continue
# print(coordinates[:10])
#
# df_out = pd.DataFrame({'Node': np.arange(len(coordinates))})
# df_out['coordinates'] = coordinates
# df_out[['lat', 'long']] = pd.DataFrame(df_out['coordinates'].tolist())
#
# # Converting Latitude and Longitude into float
# df_out['lat'] = df_out['lat'].astype(float)
# df_out['long'] = df_out['long'].astype(float)
#
# # Plotting the coordinates on map
# color_scale = [(0, 'red'), (1,'green')]
# fig = px.scatter_mapbox(df_out,
#                         lat="lat",
#                         lon="long",
#                         zoom=8,
#                         height=600,
#                         width=900)
#
#
# fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()