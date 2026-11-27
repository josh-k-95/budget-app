from app.auth.ratelimit import SlidingWindowLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_up_to_limit_then_blocks_until_window_passes() -> None:
    clock = FakeClock()
    limiter = SlidingWindowLimiter(3, 60, clock=clock)
    for _ in range(3):
        assert limiter.retry_after("k") is None
        limiter.hit("k")
    assert limiter.retry_after("k") == 60
    clock.now += 59.5
    assert limiter.retry_after("k") == 1
    clock.now += 0.5
    assert limiter.retry_after("k") is None


def test_keys_are_independent_and_reset_clears() -> None:
    limiter = SlidingWindowLimiter(1, 60, clock=FakeClock())
    limiter.hit("a")
    assert limiter.retry_after("a") is not None
    assert limiter.retry_after("b") is None
    limiter.reset("a")
    assert limiter.retry_after("a") is None
