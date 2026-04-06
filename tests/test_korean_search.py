"""Tests for Korean character handling in search."""

import threading
from src.realtime_search import RealTimeSearch, SearchState


class TestKoreanInput:
    def test_handle_multibyte_korean_char(self):
        """Korean characters should be accepted as printable input."""
        rts = RealTimeSearch.__new__(RealTimeSearch)
        rts.state = SearchState()
        rts.search_lock = threading.Lock()
        rts.results_cache = {}
        rts.stop_event = threading.Event()

        # Simulate typing Korean character
        action = rts.handle_input("한")
        assert action == "redraw"
        assert rts.state.query == "한"
        assert rts.state.cursor_pos == 1

    def test_handle_multibyte_sequence(self):
        """Multiple Korean characters should build query correctly."""
        rts = RealTimeSearch.__new__(RealTimeSearch)
        rts.state = SearchState()
        rts.search_lock = threading.Lock()
        rts.results_cache = {}
        rts.stop_event = threading.Event()

        rts.handle_input("안")
        rts.handle_input("녕")
        assert rts.state.query == "안녕"
        assert rts.state.cursor_pos == 2
