class SpeedDecrease:
    def __init__(
        self, 
        class_type: str, 
        integer_velocity: int, 
        is_icebreaker_assistance: bool,
        is_possible: bool,
        speed_decrease_pct: float,
        base_speed: str
    ) -> None:
        self.class_type = class_type
        self.integer_velocity = integer_velocity
        self.is_icebreaker_assistance = is_icebreaker_assistance
        self.is_possible = is_possible
        self.speed_decrease_pct = speed_decrease_pct
        self.base_speed = base_speed



