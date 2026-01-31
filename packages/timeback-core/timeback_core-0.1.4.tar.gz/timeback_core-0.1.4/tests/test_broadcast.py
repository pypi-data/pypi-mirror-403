"""Tests for BroadcastResults."""

import pytest

from timeback_core.broadcast import BroadcastResults


class TestAllSuccesses:
    """Tests with all successes."""

    @pytest.fixture
    def results(self) -> BroadcastResults[int]:
        """Create results with all successes."""
        return BroadcastResults(
            _results={
                "alpha": {"ok": True, "value": 1},
                "beta": {"ok": True, "value": 2},
                "gamma": {"ok": True, "value": 3},
            }
        )

    def test_succeeded_returns_all_results(self, results: BroadcastResults[int]):
        """succeeded returns all results."""
        assert results.succeeded == [("alpha", 1), ("beta", 2), ("gamma", 3)]

    def test_failed_returns_empty_list(self, results: BroadcastResults[int]):
        """failed returns empty list."""
        assert results.failed == []

    def test_all_succeeded_is_true(self, results: BroadcastResults[int]):
        """allSucceeded is true."""
        assert results.all_succeeded is True

    def test_any_failed_is_false(self, results: BroadcastResults[int]):
        """anyFailed is false."""
        assert results.any_failed is False

    def test_values_returns_all_values(self, results: BroadcastResults[int]):
        """values() returns all values."""
        assert results.values() == [1, 2, 3]


class TestAllFailures:
    """Tests with all failures."""

    @pytest.fixture
    def results(self) -> BroadcastResults[int]:
        """Create results with all failures."""
        return BroadcastResults(
            _results={
                "alpha": {"ok": False, "error": RuntimeError("Alpha failed")},
                "beta": {"ok": False, "error": RuntimeError("Beta failed")},
            }
        )

    def test_succeeded_returns_empty_list(self, results: BroadcastResults[int]):
        """succeeded returns empty list."""
        assert results.succeeded == []

    def test_failed_returns_all_errors(self, results: BroadcastResults[int]):
        """failed returns all errors."""
        failed = results.failed
        assert len(failed) == 2
        assert failed[0][0] == "alpha"
        assert str(failed[0][1]) == "Alpha failed"
        assert failed[1][0] == "beta"
        assert str(failed[1][1]) == "Beta failed"

    def test_all_succeeded_is_false(self, results: BroadcastResults[int]):
        """allSucceeded is false."""
        assert results.all_succeeded is False

    def test_any_failed_is_true(self, results: BroadcastResults[int]):
        """anyFailed is true."""
        assert results.any_failed is True

    def test_values_throws_with_failed_names(self, results: BroadcastResults[int]):
        """values() throws with failed names."""
        with pytest.raises(RuntimeError, match="operations failed for: alpha, beta"):
            results.values()


class TestMixedResults:
    """Tests with mixed results."""

    @pytest.fixture
    def results(self) -> BroadcastResults[str]:
        """Create results with mixed success/failure."""
        return BroadcastResults(
            _results={
                "alpha": {"ok": True, "value": "success"},
                "beta": {"ok": False, "error": RuntimeError("Beta error")},
                "gamma": {"ok": True, "value": "also success"},
            }
        )

    def test_succeeded_returns_only_successful_results(self, results: BroadcastResults[str]):
        """succeeded returns only successful results."""
        assert results.succeeded == [("alpha", "success"), ("gamma", "also success")]

    def test_failed_returns_only_failed_results(self, results: BroadcastResults[str]):
        """failed returns only failed results."""
        failed = results.failed
        assert len(failed) == 1
        assert failed[0][0] == "beta"
        assert str(failed[0][1]) == "Beta error"

    def test_all_succeeded_is_false(self, results: BroadcastResults[str]):
        """allSucceeded is false."""
        assert results.all_succeeded is False

    def test_any_failed_is_true(self, results: BroadcastResults[str]):
        """anyFailed is true."""
        assert results.any_failed is True

    def test_values_throws_listing_failed_names(self, results: BroadcastResults[str]):
        """values() throws listing failed names."""
        with pytest.raises(RuntimeError, match="operations failed for: beta"):
            results.values()


class TestEmptyResults:
    """Tests with empty results."""

    @pytest.fixture
    def results(self) -> BroadcastResults[int]:
        """Create empty results."""
        return BroadcastResults(_results={})

    def test_succeeded_returns_empty_list(self, results: BroadcastResults[int]):
        """succeeded returns empty list."""
        assert results.succeeded == []

    def test_failed_returns_empty_list(self, results: BroadcastResults[int]):
        """failed returns empty list."""
        assert results.failed == []

    def test_all_succeeded_is_true_vacuous_truth(self, results: BroadcastResults[int]):
        """allSucceeded is true (vacuous truth)."""
        assert results.all_succeeded is True

    def test_any_failed_is_false(self, results: BroadcastResults[int]):
        """anyFailed is false."""
        assert results.any_failed is False

    def test_values_returns_empty_list(self, results: BroadcastResults[int]):
        """values() returns empty list."""
        assert results.values() == []


class TestDirectPropertyAccess:
    """Tests for direct property access."""

    @pytest.fixture
    def results(self) -> BroadcastResults[int]:
        """Create results with mixed success/failure."""
        return BroadcastResults(
            _results={
                "alpha": {"ok": True, "value": 42},
                "beta": {"ok": False, "error": RuntimeError("Failed")},
            }
        )

    def test_can_access_results_by_name(self, results: BroadcastResults[int]):
        """Can access results by name."""
        assert results["alpha"] == {"ok": True, "value": 42}

    def test_can_check_ok_status_directly(self, results: BroadcastResults[int]):
        """Can check ok status directly."""
        assert results["alpha"]["ok"] is True
        assert results["beta"]["ok"] is False

    def test_can_iterate_over_client_names(self, results: BroadcastResults[int]):
        """Can iterate over client names."""
        names = list(results)
        assert names == ["alpha", "beta"]

    def test_len_returns_number_of_results(self, results: BroadcastResults[int]):
        """len() returns number of results."""
        assert len(results) == 2

    def test_contains_checks_for_name(self, results: BroadcastResults[int]):
        """in operator checks for name."""
        assert "alpha" in results
        assert "gamma" not in results

    def test_keys_returns_all_client_names(self, results: BroadcastResults[int]):
        """keys() returns all client names."""
        assert results.keys() == ["alpha", "beta"]

    def test_items_returns_all_tuples(self, results: BroadcastResults[int]):
        """items() returns all (name, result) tuples."""
        items = results.items()
        assert len(items) == 2
        assert items[0][0] == "alpha"
        assert items[1][0] == "beta"
