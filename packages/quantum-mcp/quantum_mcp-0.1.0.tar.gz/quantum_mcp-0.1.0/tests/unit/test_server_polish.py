# Description: Test server polish features.
# Description: Validates session management, caching, budget tracking, and logging.
"""Test server polish features."""

import pytest

from quantum_mcp.server import (
    BudgetTracker,
    ResultCache,
    SessionManager,
)


class TestSessionManager:
    """Test session management."""

    def test_create_session(self):
        """Test creating a new session."""
        manager = SessionManager()
        session_id = manager.create_session()

        assert session_id is not None
        assert len(session_id) > 0

    def test_track_job(self):
        """Test tracking a job in a session."""
        manager = SessionManager()
        session_id = manager.create_session()

        manager.track_job(session_id, "job-123", "submitted")
        jobs = manager.get_session_jobs(session_id)

        assert "job-123" in jobs
        assert jobs["job-123"] == "submitted"

    def test_update_job_status(self):
        """Test updating job status."""
        manager = SessionManager()
        session_id = manager.create_session()

        manager.track_job(session_id, "job-123", "submitted")
        manager.update_job_status(session_id, "job-123", "completed")

        jobs = manager.get_session_jobs(session_id)
        assert jobs["job-123"] == "completed"

    def test_invalid_session(self):
        """Test accessing invalid session returns empty."""
        manager = SessionManager()
        jobs = manager.get_session_jobs("invalid-session")

        assert jobs == {}

    def test_session_expiry(self):
        """Test session can be expired."""
        manager = SessionManager()
        session_id = manager.create_session()
        manager.track_job(session_id, "job-123", "submitted")

        manager.expire_session(session_id)
        jobs = manager.get_session_jobs(session_id)

        assert jobs == {}


class TestResultCache:
    """Test result caching."""

    def test_cache_result(self):
        """Test caching a result."""
        cache = ResultCache()
        cache.set("job-123", {"counts": {"00": 50, "11": 50}})

        result = cache.get("job-123")
        assert result is not None
        assert result["counts"]["00"] == 50

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = ResultCache()
        result = cache.get("nonexistent")

        assert result is None

    def test_cache_invalidation(self):
        """Test invalidating cached result."""
        cache = ResultCache()
        cache.set("job-123", {"counts": {}})
        cache.invalidate("job-123")

        result = cache.get("job-123")
        assert result is None

    def test_cache_clear(self):
        """Test clearing entire cache."""
        cache = ResultCache()
        cache.set("job-1", {})
        cache.set("job-2", {})

        cache.clear()

        assert cache.get("job-1") is None
        assert cache.get("job-2") is None


class TestBudgetTracker:
    """Test budget tracking."""

    def test_initial_budget(self):
        """Test initial budget is set."""
        tracker = BudgetTracker(budget_limit=10.0)

        assert tracker.budget_limit == 10.0
        assert tracker.spent == 0.0
        assert tracker.remaining == 10.0

    def test_record_cost(self):
        """Test recording a cost."""
        tracker = BudgetTracker(budget_limit=10.0)
        tracker.record_cost(2.5, "job-123")

        assert tracker.spent == 2.5
        assert tracker.remaining == 7.5

    def test_can_afford(self):
        """Test checking if can afford a cost."""
        tracker = BudgetTracker(budget_limit=10.0)
        tracker.record_cost(7.0, "job-1")

        assert tracker.can_afford(2.0) is True
        assert tracker.can_afford(5.0) is False

    def test_budget_exceeded_raises(self):
        """Test that recording over budget raises error."""
        tracker = BudgetTracker(budget_limit=10.0)
        tracker.record_cost(8.0, "job-1")

        with pytest.raises(ValueError, match="Budget exceeded"):
            tracker.record_cost(5.0, "job-2", strict=True)

    def test_cost_history(self):
        """Test cost history tracking."""
        tracker = BudgetTracker(budget_limit=10.0)
        tracker.record_cost(2.0, "job-1")
        tracker.record_cost(3.0, "job-2")

        history = tracker.get_history()
        assert len(history) == 2
        assert history[0]["job_id"] == "job-1"
        assert history[0]["cost"] == 2.0
