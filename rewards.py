"""Configuration for partner rewards."""
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class PartnerrewardsConfig:
    """Configuration for partner rewards feature."""
    enabled: bool = True
    timeout_ms: int = int(os.getenv("LOYALTY_POINTS_API_TIMEOUT", "5000"))
    max_retries: int = 3
    batch_size: int = 100
    cache_ttl_seconds: int = 300
    allowed_regions: List[str] = field(default_factory=lambda: ["us-east-1", "us-west-2", "eu-west-1"])

    def validate(self) -> bool:
        """Validate configuration values."""
        if self.timeout_ms < 100:
            raise ValueError("Timeout must be >= 100ms")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.batch_size > 10000:
            raise ValueError("Batch size too large")
        return True


# Default configuration
DEFAULT_CONFIG = PartnerrewardsConfig()


# --- refactor: simplify scheduler logic ---
"""Configuration for referral bonus."""
import os
from dataclasses import dataclass, field
from typing import List


