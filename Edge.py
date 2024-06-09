class Edge:
    def __init__(self, port_from, port_to, distance) -> None:
        self.port_from = port_from
        self.port_to = port_to
        self.distance = distance