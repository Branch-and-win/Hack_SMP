class Port:
    def __init__(self, id, name, longitude, latitude) -> None:
        self.id = id
        self.name = name
        self.longitude = longitude
        self.latitude = latitude
        self.min_dist = {}

    def calculate_min_time(self, edges_dict, ports):
        for p in ports:
            if p.id == self.id:
                self.min_dist[p.id] = 0
            elif (self.id, p.id) in edges_dict.keys():
                self.min_dist[p.id] = round(edges_dict[self.id, p.id].distance / 15, 0) * 2
            else:
                self.min_dist[p.id] = 300

    def add_min_dist(self, key, value):
        self.min_dist[key] = value
        return
        