class Vessel:
    def __init__(self, id, name, is_icebreaker, port_start, port_end, time_start, max_speed, class_type) -> None:
        self.id = id
        self.name = name
        self.is_icebreaker = is_icebreaker
        self.port_start = port_start
        self.port_end = port_end
        self.time_start = time_start
        self.max_speed = max_speed
        self.class_type = class_type
        self.locations_by_vessel = []

    def add_location(self, location):
        self.locations_by_vessel.append(location)
        return

    def __str__(self):
        return f"V({self.id}, {self.name})"

    def __repr__(self):
        return f"V({self.id}, {self.name})"
