
from .states import AVAILABLE, LOCKED, BOOKED


class Seat:
    def __init__(self, seat_id):
        self.seat_id = seat_id
        self.status = AVAILABLE
        self.locked_by = None
        self.lock_time = None

    def is_locked(self):
        return self.status == LOCKED
    
    def is_available(self):
        return self.status == AVAILABLE

    def is_booked(self):
        return self.status == BOOKED    

