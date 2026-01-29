from dataclasses import dataclass, field


@dataclass
class RetrySettings:
    """Configuration for retry behavior when making API requests.

    Attributes:
        initial_delay: Initial delay in seconds before retrying failed API requests. Defaults to 1.
        maximum_wait_time: Maximum total time in seconds to wait for retries. Set to 0 to disable retries. Defaults to 65.
        status_codes: HTTP status codes that should trigger a retry. Defaults to [429, 502, 503, 504].
        backoff_multiplier: Multiplier for exponential backoff. Defaults to 2.
    """

    initial_delay: float = 1
    # Set maximum_wait_time to 65 as this is greater than the MDS rate limiter window of 1 minute
    maximum_wait_time: float = 65
    status_codes: list[int] = field(default_factory=lambda: [429, 502, 503, 504])
    backoff_multiplier: float = 2
