from Port import Port


class Edge:
    def __init__(self, port_from: Port, port_to: Port, distance: float) -> None:
        self.port_from = port_from
        self.port_to = port_to
        self.distance = distance
        # Признак: является ли ребро фиктивным
        self.is_fict = self.port_from == self.port_to

    def __str__(self) -> str:
        return f"E({self.port_from, self.port_to})"

    def __repr__(self):
        return f"E({self.port_from}, {self.port_to})"
