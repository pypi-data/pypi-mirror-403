import threading, time
from .states import AVAILABLE, BOOKED, LOCKED


class SeatManager:
    LOCK_TIMEOUT = 10  # seconds

    def __init__(self, seats):
        self.seats = {seat.seat_id: seat for seat in seats}
        self.global_lock = threading.Lock()


    def cleanup_expired_locks(self):
        with self.global_lock:
            now = time.time()

            for seat in self.seats.values():
                if seat.is_locked():
                    if now - seat.lock_time > self.LOCK_TIMEOUT:
                        self._release_lock(seat)


    def lock_seat(self, seat_id, user_id):
        with self.global_lock:
            seat = self.seats.get(seat_id)

            if not seat:
                return f"Seat {seat_id} does not exist"

            # Expire old lock if timeout passed
            if seat.is_locked():
                if time.time() - seat.lock_time > self.LOCK_TIMEOUT:
                    self._release_lock(seat)

            if seat.is_booked():
                return f"Seat {seat_id} is already booked"

            if seat.is_locked():
                return f"Seat {seat_id} is currently locked by {seat.locked_by}"

            seat.status = LOCKED
            seat.locked_by = user_id
            seat.lock_time = time.time()

            return f"Seat {seat_id} is locked by {user_id}"


    def lock_seats_bulk(self, seat_ids, user_id):
        with self.global_lock:
            seats_to_lock = []

            # Phase 1: validation (READ-ONLY)
            for seat_id in seat_ids:
                seat = self.seats.get(seat_id)

                if not seat:
                    return f"Seat {seat_id} does not exist"

                if seat.is_booked():
                    return f"Seat {seat_id} is already booked"

                if seat.is_locked():
                    # If locked by someone else, reject
                    return f"Seat {seat_id} is locked by {seat.locked_by}"

                seats_to_lock.append(seat)

            # Phase 2: commit (WRITE)
            lock_time = time.time()
            for seat in seats_to_lock:
                seat.status = LOCKED
                seat.locked_by = user_id
                seat.lock_time = lock_time

            return f"Seats {seat_ids} locked by {user_id}"
        

    def book_a_seat(self, seat_id, user_id):
        with self.global_lock:
            seat = self.seats.get(seat_id)

            if not seat:
                return f"Seat {seat_id} does not exist"

            if not seat.is_locked():
                return f"Seat {seat_id} is not locked"

            if seat.locked_by != user_id:
                return f"Seat {seat_id} is locked by another user"

            seat.status = BOOKED
            seat.locked_by = None
            seat.lock_time = None

            return f"Seat {seat_id} is now booked by {user_id}"
        

    def book_seats_bulk(self, seat_ids, user_id):
          with self.global_lock:
            seats_to_book = []

            # Validation
            for seat_id in seat_ids:
                seat = self.seats.get(seat_id)

                if not seat:
                    return f"Seat {seat_id} does not exist"

                if not seat.is_locked():
                    return f"Seat {seat_id} is not locked"

                if seat.locked_by != user_id:
                    return f"Seat {seat_id} is locked by another user"

                seats_to_book.append(seat)

            # Commit booking
            for seat in seats_to_book:
                seat.status = BOOKED
                seat.locked_by = None
                seat.lock_time = None

            return f"Seats {seat_ids} successfully booked by {user_id}"
    def cancel_lock(self, seat_id, user_id):
        with self.global_lock:
            seat = self.seats.get(seat_id)

            if not seat:
                return f"Seat {seat_id} does not exist"

            if seat.is_booked():
                return f"Seat {seat_id} is already booked and cannot be cancelled"

            if not seat.is_locked():
                return f"Seat {seat_id} is not locked"

            if seat.locked_by != user_id:
                return f"Seat {seat_id} is locked by another user"

            self._release_lock(seat)
            return f"Seat {seat_id} lock cancelled by {user_id}"
    
    def cancel_locks_bulk(self, seat_ids, user_id):
        with self.global_lock:
            seats_to_cancel = []

            # Validation phase
            for seat_id in seat_ids:
                seat = self.seats.get(seat_id)

                if not seat:
                    return f"Seat {seat_id} does not exist"

                if seat.is_booked():
                    return f"Seat {seat_id} is already booked and cannot be cancelled"

                if not seat.is_locked():
                    return f"Seat {seat_id} is not locked"

                if seat.locked_by != user_id:
                    return f"Seat {seat_id} is locked by another user"

                seats_to_cancel.append(seat)

            # Commit phase
            for seat in seats_to_cancel:
                self._release_lock(seat)

            return f"Locks for seats {seat_ids} cancelled by {user_id}"




    def _release_lock(self, seat):
        seat.status = AVAILABLE
        seat.locked_by = None
        seat.lock_time = None