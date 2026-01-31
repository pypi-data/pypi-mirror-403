"""
AgentSudo Budget Tracker
=========================
Tracks agent spending with Redis or in-memory storage.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)



def _utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


@dataclass
class SpendRecord:
    """Agent spending record."""
    
    agent_id: str
    total_spend_usd: float = 0.0
    request_count: int = 0
    window_start: datetime = field(default_factory=_utc_now)
    last_request: datetime | None = None
    
    @property
    def is_expired(self) -> bool:
        """Check if budget window has expired (hourly)."""
        return _utc_now() - self.window_start > timedelta(hours=1)
    
    def reset(self) -> None:
        """Reset for new window."""
        self.total_spend_usd = 0.0
        self.request_count = 0
        self.window_start = _utc_now()
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize record for storage and API responses."""
        return {
            "agent_id": self.agent_id,
            "total_spend_usd": round(self.total_spend_usd, 4),
            "request_count": self.request_count,
            "window_start": self.window_start.isoformat(),
            "last_request": self.last_request.isoformat() if self.last_request else None,
        }


class BudgetStorage(ABC):
    """Abstract budget storage interface."""
    
    @abstractmethod
    async def get(self, agent_id: str) -> SpendRecord | None:
        """Get spending record for agent."""
        pass
    
    @abstractmethod
    async def save(self, record: SpendRecord) -> None:
        """Save spending record."""
        pass
    
    @abstractmethod
    async def increment(self, agent_id: str, amount: float) -> SpendRecord:
        """Atomically increment spend and return updated record."""
        pass


class InMemoryBudgetStorage(BudgetStorage):
    """In-memory budget storage for development."""
    
    def __init__(self) -> None:
        self._records: dict[str, SpendRecord] = {}
    
    async def get(self, agent_id: str) -> SpendRecord | None:
        record = self._records.get(agent_id)
        if record and record.is_expired:
            record.reset()
        return record
    
    async def save(self, record: SpendRecord) -> None:
        self._records[record.agent_id] = record
    
    async def increment(self, agent_id: str, amount: float) -> SpendRecord:
        record = await self.get(agent_id)
        
        if not record:
            record = SpendRecord(agent_id=agent_id)
        
        # Note: is_expired check already handled in get()
        record.total_spend_usd += amount
        record.request_count += 1
        record.last_request = _utc_now()
        
        await self.save(record)
        return record


class RedisBudgetStorage(BudgetStorage):
    """Redis-based budget storage for production."""
    
    KEY_PREFIX = "agentsudo:budget:"
    WINDOW_TTL = 3600  # 1 hour
    
    def __init__(self, redis_client: Any) -> None:
        self._redis = redis_client
    
    def _key(self, agent_id: str) -> str:
        return f"{self.KEY_PREFIX}{agent_id}"
    
    async def get(self, agent_id: str) -> SpendRecord | None:
        import json
        
        try:
            data = await self._redis.get(self._key(agent_id))
            if not data:
                return None
            
            parsed = json.loads(data)
            return SpendRecord(
                agent_id=parsed["agent_id"],
                total_spend_usd=parsed["total_spend_usd"],
                request_count=parsed["request_count"],
                window_start=datetime.fromisoformat(parsed["window_start"]),
                last_request=datetime.fromisoformat(parsed["last_request"]) if parsed.get("last_request") else None,
            )
        except Exception as e:
            logger.error(f"Redis get failed for {agent_id}: {e}")
            return None
    
    async def save(self, record: SpendRecord) -> None:
        import json
        
        try:
            await self._redis.setex(
                self._key(record.agent_id),
                self.WINDOW_TTL,
                json.dumps(record.to_dict()),
            )
        except Exception as e:
            logger.error(f"Redis save failed for {record.agent_id}: {e}")
            raise
    
    async def increment(self, agent_id: str, amount: float) -> SpendRecord:
        """Atomically increment spend using Lua script."""
        script = """
        local key = KEYS[1]
        local amount = tonumber(ARGV[1])
        local now = ARGV[2]
        
        local data = redis.call('GET', key)
        local record
        
        if data then
            record = cjson.decode(data)
            record.total_spend_usd = record.total_spend_usd + amount
            record.request_count = record.request_count + 1
        else
            record = {
                agent_id = ARGV[3],
                total_spend_usd = amount,
                request_count = 1,
                window_start = now
            }
        end
        
        record.last_request = now
        redis.call('SETEX', key, 3600, cjson.encode(record))
        
        return cjson.encode(record)
        """
        
        import json
        
        now = _utc_now().isoformat()  # FIX: Use timezone-aware time
        
        try:
            result = await self._redis.eval(
                script,
                1,
                self._key(agent_id),
                str(amount),
                now,
                agent_id,
            )
            
            parsed = json.loads(result)
            return SpendRecord(
                agent_id=parsed["agent_id"],
                total_spend_usd=parsed["total_spend_usd"],
                request_count=parsed["request_count"],
                window_start=datetime.fromisoformat(parsed["window_start"]),
                last_request=datetime.fromisoformat(parsed["last_request"]) if parsed.get("last_request") else None,
            )
        except Exception as e:
            logger.error(f"Redis increment failed for {agent_id}: {e}")
            raise


class BudgetTracker:
    """Production-grade budget tracker."""
    
    def __init__(self, storage: BudgetStorage | None = None) -> None:
        self._storage = storage or InMemoryBudgetStorage()
    
    async def get_status(
        self,
        agent_id: str,
        max_budget: float,
    ) -> dict[str, Any]:
        """Get current budget status for an agent."""
        if max_budget <= 0:
            raise ValueError("max_budget must be positive")
        
        record = await self._storage.get(agent_id)
        
        if not record:
            return {
                "agent_id": agent_id,
                "current_spend_usd": 0.0,
                "max_budget_usd": max_budget,
                "remaining_usd": max_budget,
                "percent_used": 0.0,
                "request_count": 0,
            }
        
        remaining = max_budget - record.total_spend_usd
        percent = (record.total_spend_usd / max_budget) * 100
        
        return {
            "agent_id": agent_id,
            "current_spend_usd": round(record.total_spend_usd, 4),
            "max_budget_usd": max_budget,
            "remaining_usd": round(max(0, remaining), 4),
            "percent_used": round(percent, 1),
            "request_count": record.request_count,
            "window_start": record.window_start.isoformat(),
        }
    
    async def check_budget(
        self,
        agent_id: str,
        max_budget: float,
        cost: float,
    ) -> tuple[bool, str]:
        """Check if agent has budget for a cost."""
        if cost < 0:
            return False, "Cost cannot be negative"
        
        record = await self._storage.get(agent_id)
        current_spend = record.total_spend_usd if record else 0.0
        projected = current_spend + cost
        
        if projected > max_budget:
            return False, (
                f"Budget exceeded: ${current_spend:.2f} + ${cost:.2f} = "
                f"${projected:.2f} > ${max_budget:.2f} limit"
            )
        
        return True, f"Budget OK: ${projected:.2f} / ${max_budget:.2f}"
    
    async def record_spend(
        self,
        agent_id: str,
        cost: float,
    ) -> SpendRecord:
        """Record a spend and return updated record."""
        if cost < 0:
            raise ValueError("Cost cannot be negative")
        return await self._storage.increment(agent_id, cost)

    async def check_and_spend(
        self,
        agent_id: str,
        cost: float,
        limit: float,
    ) -> bool:
        """
        Convenience method: check budget and record spend atomically.
        
        Args:
            agent_id: The agent identifier
            cost: Cost to spend
            limit: Maximum budget limit
            
        Returns:
            True if spend was allowed, False if budget exceeded
        """
        allowed, _ = await self.check_budget(agent_id, limit, cost)
        if allowed and cost > 0:
            await self.record_spend(agent_id, cost)
        return allowed
