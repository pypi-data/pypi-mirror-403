# Seat Allocation Engine – Working Cycle

This document explains **how the Seat Allocation Engine works internally**, step by step. It focuses on the **lifecycle of a seat**, **locking rules**, **bulk operations**, and **cleanup mechanics**. No UI, API, or framework concepts are involved here—this is purely the domain engine.

---

## 1. Core Purpose

The engine is designed to solve one problem **correctly**:

> Allocate seats to users in a safe, fair, and deterministic way.

It guarantees:
- No double booking
- No permanent locks
- No partial group bookings
- No lock stealing

---

## 2. Core Concepts

### 2.1 Seat as a Resource
Each seat is treated as an **independent resource**.

A seat has exactly one of three states:
- `AVAILABLE`
- `LOCKED`
- `BOOKED`

Once a seat is `BOOKED`, it is **terminal** and cannot change state.

---

### 2.2 Seat Ownership

When a seat is locked:
- It is owned by exactly **one user**
- Only that user can book it
- Other users are rejected

Ownership is enforced strictly at all times.

---

## 3. Seat Lifecycle

The lifecycle of a seat follows this strict state machine:

```
AVAILABLE → LOCKED → BOOKED
     ↑        |
     └────────┘  (lock expiry)
```

Invalid transitions are never allowed.

---

## 4. Locking Mechanism

### 4.1 Single Seat Locking

When a user requests to lock a seat:

1. The engine checks if the seat exists
2. If the seat is `BOOKED` → reject
3. If the seat is `LOCKED` → reject
4. If the seat is `AVAILABLE` → lock it

A successful lock records:
- `locked_by` (user id)
- `lock_time` (timestamp)

---

### 4.2 Bulk Seat Locking (Group Selection)

Bulk locking is **atomic**.

This means:
> Either all seats are locked, or none are.

#### Working cycle:

**Phase 1 – Validation (read-only)**
- All seats must exist
- All seats must be `AVAILABLE`
- If any seat fails → abort immediately

**Phase 2 – Commit (write)**
- All seats are locked together
- Same user
- Same lock timestamp

No partial locking is ever possible.

---

## 5. Booking Mechanism

### 5.1 Single Seat Booking

To book a seat:

1. Seat must exist
2. Seat must be `LOCKED`
3. Seat must be locked by the same user

If all checks pass:
- Seat transitions to `BOOKED`
- Lock metadata is cleared

---

### 5.2 Bulk Seat Booking

Bulk booking follows the same atomic principle as bulk locking.

**Validation phase:**
- All seats must exist
- All seats must be `LOCKED`
- All seats must be locked by the same user

**Commit phase:**
- All seats transition to `BOOKED`

If any seat fails validation → **no seat is booked**.

---

## 6. Lock Expiry (Auto Release)

Locks are **temporary by design**.

### 6.1 Timeout Rule

- Each lock has a maximum lifetime (`LOCK_TIMEOUT`)
- Default: 10 seconds

---

### 6.2 Cleanup Mechanism

Lock expiry is handled by a **system-level cleanup function**:

```
cleanup_expired_locks()
```

This function:
- Iterates over all seats
- Releases locks that exceeded the timeout
- Never depends on user actions

Important rule:

> A lock may expire, but it is never stolen by another user.

---

## 7. Concurrency Safety

All operations run inside a **global lock**.

This guarantees:
- Atomic operations
- No race conditions
- Deterministic behavior

The engine prioritizes **correctness over performance**.

---

## 8. Separation of Responsibilities

| Layer | Responsibility |
|-----|--------------|
| Seat | State + truth checks |
| SeatManager | Transitions + rules |
| Cleanup | Time-based expiry |
| UI / API | Input & presentation only |

The engine does **not** know about:
- Clicks
- HTTP
- UI state
- Databases

---

## 9. What This Engine Guarantees

✔ No double booking
✔ No permanent locks
✔ No partial group bookings
✔ Strong ownership enforcement
✔ Deterministic outcomes

---

## 10. What This Engine Intentionally Does NOT Do

- No UI rendering
- No HTTP / REST handling
- No persistence
- No background threads

These are integration concerns and belong outside the engine.

---

## 11. Intended Usage

This engine is designed to be:
- Packaged as a reusable library
- Called from event-driven systems
- Used under web, desktop, or CLI interfaces

The engine remains unchanged while integrations evolve.

---

## 12. Final Note

This is a **domain-correct seat allocation engine**.

All future work (UI, APIs, persistence, scaling) should be built **on top of this logic**, not mixed into it.

This separation is intentional and fundamental.



---

# Public API Reference

This section lists **all public methods exposed by the SeatLock engine**, with a one-line explanation of what each does. These are the only methods consumers should rely on.

---

## Importing the Engine

```python
from seatlock import Seat, SeatManager
```

---

## Core Classes

### `Seat`
Represents a single seat as an independent resource.

- `Seat(seat_id)` → Create a new seat with a unique identifier
- `is_available()` → Returns `True` if the seat is free
- `is_locked()` → Returns `True` if the seat is temporarily reserved
- `is_booked()` → Returns `True` if the seat is permanently booked

---

### `SeatManager`
Central engine that enforces all locking, booking, cancellation, and cleanup rules.

---

## Locking Methods

- `lock_seat(seat_id, user_id)`  
  Locks a single available seat for a user

- `lock_seats_bulk(seat_ids, user_id)`  
  Atomically locks multiple seats for a user (all-or-nothing)

---

## Booking Methods

- `book_a_seat(seat_id, user_id)`  
  Permanently books a single seat previously locked by the same user

- `book_seats_bulk(seat_ids, user_id)`  
  Atomically books multiple seats previously locked by the same user

---

## Cancellation Methods

- `cancel_lock(seat_id, user_id)`  
  Releases a lock held by the user on a single seat

- `cancel_locks_bulk(seat_ids, user_id)`  
  Atomically releases locks held by the user on multiple seats

---

## Cleanup / System Methods

- `cleanup_expired_locks()`  
  System-level method that releases all locks exceeding the configured timeout

---

## Notes on Usage

- All methods are **thread-safe**
- All bulk operations are **atomic**
- Only the lock owner may book or cancel seats
- Booked seats are **final and immutable**
- Time-based lock expiry is handled **only** by `cleanup_expired_locks`

---

This API is intentionally minimal and stable. All UI, event handling, persistence, and networking should be built **on top of these methods**, not mixe