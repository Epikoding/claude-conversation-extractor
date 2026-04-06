#!/usr/bin/env python3
"""
Error handling and edge case tests for meaningful coverage
"""

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path before local imports
sys.path.append(str(Path(__file__).parent.parent))

# Local imports after sys.path modification
from extract_claude_logs import (ClaudeConversationExtractor,  # noqa: E402
                                 launch_interactive, main)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_fallback_all_dirs_fail(self):
        """Test init when all directory creation attempts fail"""
        call_count = 0

        def mkdir_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Let the last mkdir call succeed (the fallback cwd/claude-logs)
            if call_count <= 4:
                raise Exception("Permission denied")
            # Allow fallback mkdir to succeed (returns None like real mkdir)
            return None

        with patch("pathlib.Path.mkdir", side_effect=mkdir_side_effect):
            with patch("pathlib.Path.touch", side_effect=Exception("No write access")):
                with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                    with patch("builtins.print"):
                        # Should still create extractor, falling back to cwd
                        extractor = ClaudeConversationExtractor(None)
                        self.assertIn("claude-logs", str(extractor.output_dir))

    def test_extract_conversation_permission_error(self):
        """Test extract_conversation with permission error"""
        test_file = Path(self.temp_dir) / "test.jsonl"
        test_file.write_text('{"type": "test"}')

        extractor = ClaudeConversationExtractor(self.temp_dir)

        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with patch("builtins.print") as mock_print:
                result = extractor.extract_conversation(test_file)
                self.assertEqual(result, [])
                # Should print error message
                mock_print.assert_called()
                args = mock_print.call_args[0][0]
                self.assertIn("파일 읽기 오류", args)

    def test_save_as_markdown_write_error(self):
        """Test save_as_markdown with write error"""
        extractor = ClaudeConversationExtractor(self.temp_dir)
        conversation = [{"role": "user", "content": "Test", "timestamp": ""}]

        with patch("builtins.open", side_effect=IOError("Disk full")):
            # The current implementation does not catch IOError in save_as_markdown,
            # so it will propagate. Verify the error is raised.
            with self.assertRaises(IOError):
                extractor.save_as_markdown(conversation, "test")

    def test_list_recent_sessions_no_sessions_messages(self):
        """Test list_recent_sessions prints correct messages when no sessions"""
        extractor = ClaudeConversationExtractor(self.temp_dir)

        with patch.object(extractor, "find_sessions", return_value=[]):
            with patch("builtins.print") as mock_print:
                _ = extractor.list_recent_sessions()

                # Check all expected messages are printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                self.assertTrue(
                    any("세션을 찾을 수 없습니다" in str(call) for call in print_calls)
                )
                self.assertTrue(
                    any(
                        "Claude Code를 사용하고 대화가 저장되어 있는지 확인해 주세요"
                        in str(call)
                        for call in print_calls
                    )
                )

    def test_extract_multiple_skip_message(self):
        """Test extract_multiple prints skip message for empty conversations"""
        extractor = ClaudeConversationExtractor(self.temp_dir)
        sessions = [Path("test.jsonl")]

        with patch.object(extractor, "extract_conversation", return_value=[]):
            with patch("builtins.print") as mock_print:
                success, total = extractor.extract_multiple(sessions, [0])

                # Should print skip message
                print_calls = [str(call) for call in mock_print.call_args_list]
                self.assertTrue(
                    any("건너뜀" in str(call) for call in print_calls)
                )
                self.assertEqual(success, 0)
                self.assertEqual(total, 1)


class TestMainFunctionErrorCases(unittest.TestCase):
    """Test main() function error handling"""

    def test_main_invalid_extract_number_handling(self):
        """Test main handles invalid extract numbers gracefully"""
        with patch("sys.argv", ["prog", "--extract", "abc,1,xyz"]):
            with patch.object(
                ClaudeConversationExtractor,
                "find_sessions",
                return_value=[Path("test.jsonl")],
            ):
                with patch.object(
                    ClaudeConversationExtractor, "extract_multiple",
                    return_value=(1, 1),
                ) as mock_extract:
                    with patch("builtins.print") as mock_print:
                        main()

                        # Should skip invalid numbers but process valid ones
                        mock_extract.assert_called_once()
                        call_args = mock_extract.call_args
                        # main() passes format and detailed as kwargs
                        self.assertEqual(call_args[0][1], [0])  # Only valid index

                        # Should print error messages
                        print_calls = [str(call) for call in mock_print.call_args_list]
                        self.assertTrue(
                            any(
                                "Invalid session number: abc" in str(call)
                                for call in print_calls
                            )
                        )
                        self.assertTrue(
                            any(
                                "Invalid session number: xyz" in str(call)
                                for call in print_calls
                            )
                        )

    def test_main_all_with_no_sessions(self):
        """Test --all command with no sessions found"""
        with patch("sys.argv", ["prog", "--all"]):
            with patch.object(
                ClaudeConversationExtractor, "find_sessions", return_value=[]
            ):
                with patch.object(
                    ClaudeConversationExtractor, "extract_multiple", return_value=(0, 0)
                ) as mock_extract:
                    with patch("builtins.print"):
                        main()

                        # Should handle empty list gracefully
                        # main() passes format and detailed kwargs
                        mock_extract.assert_called_once_with(
                            [], [], format="markdown", detailed=False
                        )

    def test_main_search_import_error(self):
        """Test main handles search import error"""
        with patch("sys.argv", ["prog", "--search", "test"]):
            # Simulate import error
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                with patch("builtins.print"):
                    with patch("sys.exit"):
                        # Should handle import error gracefully
                        try:
                            main()
                        except ImportError:
                            pass  # Expected

    def test_launch_interactive_import_error(self):
        """Test launch_interactive handles import error"""
        with patch("builtins.__import__", side_effect=ImportError("No interactive_ui")):
            with patch("builtins.print"):
                with patch("sys.exit"):
                    # Should handle import error gracefully
                    try:
                        launch_interactive()
                    except ImportError:
                        pass  # Expected in current implementation


class TestSearchFunctionality(unittest.TestCase):
    """Test search functionality in main()"""

    def test_main_search_basic(self):
        """Test basic search functionality"""
        with patch("sys.argv", ["prog", "--search", "test query"]):
            # Mock the entire search flow
            mock_searcher = Mock()
            mock_result = Mock(
                file_path=Path("test.jsonl"),
                conversation_id="123",
                matched_content="test match",
                speaker="human",
                relevance_score=0.9,
            )
            mock_searcher.search.return_value = [mock_result]

            # Patch the lazy import of search_conversations inside main()
            mock_search_module = Mock()
            mock_search_module.ConversationSearcher.return_value = mock_searcher
            with patch.dict(
                "sys.modules",
                {"search_conversations": mock_search_module},
            ):
                with patch("builtins.print") as mock_print:
                    with patch("builtins.input", return_value=""):
                        main()

                        # Should call search
                        mock_searcher.search.assert_called()

                        # Should print results
                        print_calls = [str(call) for call in mock_print.call_args_list]
                        self.assertTrue(
                            any("1개의 결과를 찾았습니다" in str(call) for call in print_calls)
                        )

    def test_main_search_with_filters(self):
        """Test search with all filter options"""
        with patch(
            "sys.argv",
            [
                "prog",
                "--search-regex",
                "test",
                "--search-speaker",
                "human",
                "--search-date-from",
                "2024-01-01",
                "--search-date-to",
                "2024-12-31",
                "--case-sensitive",
            ],
        ):
            mock_searcher = Mock()
            mock_searcher.search.return_value = []

            mock_search_module = Mock()
            mock_search_module.ConversationSearcher.return_value = mock_searcher
            with patch.dict(
                "sys.modules",
                {"search_conversations": mock_search_module},
            ):
                with patch("builtins.print"):
                    main()

                    # Verify search was called with correct parameters
                    mock_searcher.search.assert_called_once()
                    call_kwargs = mock_searcher.search.call_args[1]
                    self.assertEqual(call_kwargs["mode"], "regex")
                    self.assertEqual(call_kwargs["speaker_filter"], "human")
                    self.assertTrue(call_kwargs["case_sensitive"])


class TestInteractiveMode(unittest.TestCase):
    """Test interactive mode functionality"""

    def test_main_interactive_flag_calls_launch(self):
        """Test --interactive flag calls interactive_main via lazy import"""
        mock_interactive_main = Mock()
        mock_module = Mock()
        mock_module.main = mock_interactive_main
        with patch("sys.argv", ["prog", "--interactive"]):
            with patch.dict("sys.modules", {"interactive_ui": mock_module}):
                main()
                mock_interactive_main.assert_called_once()

    def test_main_export_flag_calls_interactive(self):
        """Test --export flag launches interactive mode via lazy import"""
        mock_interactive_main = Mock()
        mock_module = Mock()
        mock_module.main = mock_interactive_main
        with patch("sys.argv", ["prog", "--export", "logs"]):
            with patch.dict("sys.modules", {"interactive_ui": mock_module}):
                main()
                mock_interactive_main.assert_called_once()

    def test_main_no_args_calls_list_sessions(self):
        """Test no arguments calls list_recent_sessions (default action)"""
        with patch("sys.argv", ["prog"]):
            with patch.object(
                ClaudeConversationExtractor, "list_recent_sessions", return_value=[]
            ) as mock_list:
                with patch("builtins.print"):
                    main()
                    mock_list.assert_called_once()


if __name__ == "__main__":
    unittest.main()
