# Korean Support & Custom Path Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add custom path memory (MRU, max 3) and full Korean UI/search support to Claude Conversation Extractor.

**Architecture:** Config file at `~/.claude/conversation-extractor-config.json` stores recent custom paths. All user-facing strings in 5 source files are replaced with Korean. Realtime search keyboard handler is extended to accept multibyte (Korean) input.

**Tech Stack:** Python 3.8+ standard library only (`json`, `pathlib`, `re`). No new dependencies.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/interactive_ui.py` | Modify | Config load/save, custom path UI, Korean UI strings |
| `src/extract_claude_logs.py` | Modify | Korean CLI strings |
| `src/search_cli.py` | Modify | Korean search CLI strings |
| `src/realtime_search.py` | Modify | Korean search UI strings, multibyte keyboard input |
| `src/search_conversations.py` | Modify | Korean error/status strings, encoding fix |
| `tests/test_config.py` | Create | Config load/save/MRU tests |
| `tests/test_korean_search.py` | Create | Korean search pattern tests |

---

### Task 1: Config Load/Save

**Files:**
- Create: `tests/test_config.py`
- Modify: `src/interactive_ui.py:1-33`

- [ ] **Step 1: Write failing tests for config management**

```python
# tests/test_config.py
"""Tests for config load/save and MRU path management."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def _make_ui(config_dir, output_dir):
    """Create InteractiveUI with custom config path and suppressed output."""
    from src.interactive_ui import InteractiveUI

    with patch.object(InteractiveUI, '__init__', lambda self, *a, **kw: None):
        ui = InteractiveUI.__new__(InteractiveUI)
        ui.config_path = config_dir / "conversation-extractor-config.json"
        ui.output_dir = output_dir
        ui.sessions = []
        ui.terminal_width = 80
        return ui


class TestConfigLoadSave:
    def test_load_config_no_file(self, tmp_path):
        ui = _make_ui(tmp_path, tmp_path / "out")
        config = ui._load_config()
        assert config == {"recent_custom_paths": []}

    def test_save_and_load_config(self, tmp_path):
        ui = _make_ui(tmp_path, tmp_path / "out")
        ui._save_config({"recent_custom_paths": ["/foo", "/bar"]})
        config = ui._load_config()
        assert config["recent_custom_paths"] == ["/foo", "/bar"]

    def test_load_config_corrupt_json(self, tmp_path):
        config_path = tmp_path / "conversation-extractor-config.json"
        config_path.write_text("not json!!!")
        ui = _make_ui(tmp_path, tmp_path / "out")
        config = ui._load_config()
        assert config == {"recent_custom_paths": []}


class TestUpdateRecentPaths:
    def test_add_new_path(self, tmp_path):
        ui = _make_ui(tmp_path, tmp_path / "out")
        ui._save_config({"recent_custom_paths": []})
        ui._update_recent_paths(Path("/new/path"))
        config = ui._load_config()
        assert config["recent_custom_paths"] == ["/new/path"]

    def test_mru_order(self, tmp_path):
        ui = _make_ui(tmp_path, tmp_path / "out")
        ui._save_config({"recent_custom_paths": ["/old"]})
        ui._update_recent_paths(Path("/new"))
        config = ui._load_config()
        assert config["recent_custom_paths"] == ["/new", "/old"]

    def test_max_three(self, tmp_path):
        ui = _make_ui(tmp_path, tmp_path / "out")
        ui._save_config({"recent_custom_paths": ["/a", "/b", "/c"]})
        ui._update_recent_paths(Path("/d"))
        config = ui._load_config()
        assert config["recent_custom_paths"] == ["/d", "/a", "/b"]

    def test_duplicate_moves_to_front(self, tmp_path):
        ui = _make_ui(tmp_path, tmp_path / "out")
        ui._save_config({"recent_custom_paths": ["/a", "/b", "/c"]})
        ui._update_recent_paths(Path("/b"))
        config = ui._load_config()
        assert config["recent_custom_paths"] == ["/b", "/a", "/c"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mini_bot/Downloads/claude-conversation-extractor-main && python -m pytest tests/test_config.py -v`
Expected: FAIL - `_load_config`, `_save_config`, `_update_recent_paths` not found

- [ ] **Step 3: Implement config methods in InteractiveUI**

Add `import json` to the imports at the top of `src/interactive_ui.py` (line 4 area), then add three methods to the `InteractiveUI` class after `__init__`:

```python
# Add to imports at top of file:
import json

# In InteractiveUI.__init__, add after self.terminal_width = ...:
        self.config_path = Path.home() / ".claude" / "conversation-extractor-config.json"

# Add these methods after __init__:
    def _load_config(self) -> dict:
        """Load config from JSON file. Returns default if missing/corrupt."""
        try:
            if self.config_path.exists():
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "recent_custom_paths" in data:
                    return data
        except (json.JSONDecodeError, OSError):
            pass
        return {"recent_custom_paths": []}

    def _save_config(self, config: dict):
        """Save config to JSON file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps(config, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _update_recent_paths(self, path: Path):
        """Add path to MRU list (max 3, dedup, most recent first)."""
        config = self._load_config()
        paths = config["recent_custom_paths"]
        path_str = str(path)
        if path_str in paths:
            paths.remove(path_str)
        paths.insert(0, path_str)
        config["recent_custom_paths"] = paths[:3]
        self._save_config(config)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/mini_bot/Downloads/claude-conversation-extractor-main && python -m pytest tests/test_config.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/mini_bot/Downloads/claude-conversation-extractor-main
git add tests/test_config.py src/interactive_ui.py
git commit -m "feat: add config load/save with MRU path management"
```

---

### Task 2: Custom Path Memory UI

**Files:**
- Modify: `src/interactive_ui.py:69-103` (`get_folder_selection`)
- Modify: `src/interactive_ui.py:236-268` (`run` method)

- [ ] **Step 1: Write failing test for get_folder_selection showing recent paths**

Append to `tests/test_config.py`:

```python
class TestFolderSelectionWithRecentPaths:
    def test_recent_paths_shown_in_menu(self, tmp_path, capsys):
        """Recent custom paths should appear after default suggestions."""
        ui = _make_ui(tmp_path, tmp_path / "out")
        ui._save_config({"recent_custom_paths": ["/my/custom/path"]})

        # Simulate selecting '5' (first recent path)
        with patch("builtins.input", return_value="5"):
            result = ui.get_folder_selection()

        assert result == Path("/my/custom/path")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/mini_bot/Downloads/claude-conversation-extractor-main && python -m pytest tests/test_config.py::TestFolderSelectionWithRecentPaths -v`
Expected: FAIL - `get_folder_selection` doesn't use config

- [ ] **Step 3: Rewrite get_folder_selection to include recent paths**

Replace `get_folder_selection` in `src/interactive_ui.py` (lines 69-103):

```python
    def get_folder_selection(self) -> Optional[Path]:
        """Simple folder selection dialog with recent custom paths."""
        self.clear_screen()
        self.print_banner()
        print("\n📁 대화를 어디에 저장하시겠습니까?\n")

        # Default suggestions
        home = Path.home()
        suggestions = [
            home / "Desktop" / "Claude Conversations",
            home / "Documents" / "Claude Conversations",
            home / "Downloads" / "Claude Conversations",
            Path.cwd() / "Claude Conversations",
        ]

        print("추천 위치:")
        for i, path in enumerate(suggestions, 1):
            print(f"  {i}. {path}")

        # Load recent custom paths
        config = self._load_config()
        recent_paths = config.get("recent_custom_paths", [])
        if recent_paths:
            print("\n최근 사용한 위치:")
            for i, path_str in enumerate(recent_paths, len(suggestions) + 1):
                print(f"  {i}. {path_str}")

        all_choices = suggestions + [Path(p) for p in recent_paths]
        total = len(all_choices)

        print(f"\n  C. 직접 입력")
        print("  Q. 종료")

        while True:
            choice = input(f"\n옵션을 선택하세요 (1-{total}, C, 또는 Q): ").strip().upper()

            if choice == "Q":
                return None
            elif choice == "C":
                custom_path = input("\n경로를 입력하세요: ").strip()
                if custom_path:
                    return Path(custom_path).expanduser()
            elif choice.isdigit() and 1 <= int(choice) <= total:
                return all_choices[int(choice) - 1]
            else:
                print("❌ 잘못된 선택입니다. 다시 시도해 주세요.")
```

- [ ] **Step 4: Update the `run` method to save custom path after extraction**

In `src/interactive_ui.py`, in the `run` method (around line 255, after `success_count = self.extract_conversations(...)`), add:

```python
            # Save custom path to recent list if not a default suggestion
            home = Path.home()
            default_suggestions = [
                home / "Desktop" / "Claude Conversations",
                home / "Documents" / "Claude Conversations",
                home / "Downloads" / "Claude Conversations",
                Path.cwd() / "Claude Conversations",
            ]
            if output_dir not in default_suggestions:
                self._update_recent_paths(output_dir)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/mini_bot/Downloads/claude-conversation-extractor-main && python -m pytest tests/test_config.py -v`
Expected: All 8 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/mini_bot/Downloads/claude-conversation-extractor-main
git add src/interactive_ui.py tests/test_config.py
git commit -m "feat: show recent custom paths in folder selection menu"
```

---

### Task 3: Korean UI - interactive_ui.py

**Files:**
- Modify: `src/interactive_ui.py`

- [ ] **Step 1: Translate all remaining English strings in interactive_ui.py**

The `get_folder_selection` method was already translated in Task 2. Now translate the rest of `interactive_ui.py`:

| Line | English | Korean |
|------|---------|--------|
| 110 | `"🔍 Finding your Claude conversations..."` | `"🔍 대화를 검색하는 중..."` |
| 114-115 | `"❌ No Claude conversations found!"` / `"Make sure you've used Claude Code at least once."` | `"❌ 대화를 찾을 수 없습니다!"` / `"Claude Code를 한 번 이상 사용했는지 확인해 주세요."` |
| 117 | `"Press Enter to exit..."` | `"계속하려면 Enter를 누르세요..."` |
| 120 | `f"✅ Found {len(self.sessions)} conversations!\n"` | `f"✅ {len(self.sessions)}개의 대화를 찾았습니다!\n"` |
| 131 | `f"  ... and {len(self.sessions) - 20} more conversations"` | `f"  ... 외 {len(self.sessions) - 20}개의 대화"` |
| 136 | `"  A. Extract ALL conversations"` | `"  A. 모든 대화 추출"` |
| 137 | `"  R. Extract 5 most RECENT"` | `"  R. 최근 5개 추출"` |
| 138 | `"  S. SELECT specific conversations (e.g., 1,3,5)"` | `"  S. 특정 대화 선택 (예: 1,3,5)"` |
| 139 | `"  F. SEARCH conversations (real-time search)"` | `"  F. 대화 검색 (실시간 검색)"` |
| 140 | `"  Q. QUIT"` | `"  Q. 종료"` |
| 142 | `"Your choice: "` | `"선택: "` |
| 152 | `"Enter conversation numbers (e.g., 1,3,5): "` | `"대화 번호를 입력하세요 (예: 1,3,5): "` |
| 155 | `"❌ Invalid selection. Please use valid numbers."` | `"❌ 잘못된 선택입니다. 올바른 번호를 입력해 주세요."` |
| 157 | `"❌ Invalid format. Use comma-separated numbers."` | `"❌ 잘못된 형식입니다. 쉼표로 구분된 번호를 입력해 주세요."` |
| 168 | `"❌ Invalid choice. Please try again."` | `"❌ 잘못된 선택입니다. 다시 시도해 주세요."` |
| 193 | `"📤 Extract this conversation? (y/N): "` | `"📤 이 대화를 추출하시겠습니까? (y/N): "` |
| 199 | `"❌ Error: Selected file not found in sessions list"` | `"❌ 오류: 선택한 파일을 세션 목록에서 찾을 수 없습니다"` |
| 200 | `"Press Enter to continue..."` | `"계속하려면 Enter를 누르세요..."` |
| 209 | `f"📤 Extracting {len(indices)} conversations...\n"` | `f"📤 {len(indices)}개의 대화를 추출하는 중...\n"` |
| 221 | `f"✅ Successfully extracted {success_count}/{total_count} conversations!"` | `f"✅ {success_count}/{total_count}개의 대화를 추출했습니다!"` |
| 248-249 | `"👋 Goodbye!"` | `"👋 안녕히 가세요!"` |
| 258 | `f"📁 Files saved to: {output_dir}"` | `f"📁 저장 위치: {output_dir}"` |
| 261 | `"🗂️  Open output folder? (Y/n): "` | `"🗂️  저장 폴더를 여시겠습니까? (Y/n): "` |
| 265 | `"❌ No conversations were extracted."` | `"❌ 추출된 대화가 없습니다."` |
| 268 | `"✨ Press Enter to exit..."` | `"✨ 종료하려면 Enter를 누르세요..."` |
| 271 | `"👋 Goodbye!"` | `"👋 안녕히 가세요!"` |
| 273 | `f"❌ Error: {e}"` | `f"❌ 오류: {e}"` |
| 274 | `"Press Enter to exit..."` | `"종료하려면 Enter를 누르세요..."` |

- [ ] **Step 2: Apply all string replacements**

Apply the replacements listed above to `src/interactive_ui.py` using Edit tool.

- [ ] **Step 3: Verify the file still has valid Python syntax**

Run: `cd /Users/mini_bot/Downloads/claude-conversation-extractor-main && python -c "import ast; ast.parse(open('src/interactive_ui.py').read()); print('OK')"` 
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd /Users/mini_bot/Downloads/claude-conversation-extractor-main
git add src/interactive_ui.py
git commit -m "feat: translate interactive_ui.py to Korean"
```

---

### Task 4: Korean UI - extract_claude_logs.py

**Files:**
- Modify: `src/extract_claude_logs.py`

- [ ] **Step 1: Translate all English strings in extract_claude_logs.py**

| Line | English | Korean |
|------|---------|--------|
| 53 | `f"📁 Saving logs to: {self.output_dir}"` | `f"📁 저장 위치: {self.output_dir}"` |
| 161 | `f"❌ Error reading file {jsonl_path}: {e}"` | `f"❌ 파일 읽기 오류 {jsonl_path}: {e}"` |
| 203 | `"❌ No messages found in conversation"` | `"❌ 대화에서 메시지를 찾을 수 없습니다"` |
| 225 | `"↑↓ to scroll • Q to quit • Enter to continue\n"` | `"↑↓ 스크롤 • Q 종료 • Enter 계속\n"` |
| 266 | `"[Enter] Continue • [Q] Quit: "` | `"[Enter] 계속 • [Q] 종료: "` |
| 268 | `"👋 Stopped viewing"` | `"👋 보기를 종료했습니다"` |
| 279 | `"📄 End of conversation"` | `"📄 대화 끝"` |
| 281 | `"Press Enter to continue..."` | `"계속하려면 Enter를 누르세요..."` |
| 284 | `f"❌ Error displaying conversation: {e}"` | `f"❌ 대화 표시 오류: {e}"` |
| 285 | `"Press Enter to continue..."` | `"계속하려면 Enter를 누르세요..."` |
| 542 | `f"❌ Unsupported format: {format}"` | `f"❌ 지원하지 않는 형식: {format}"` |
| 623 | `"No preview available"` | `"미리보기 없음"` |
| 632 | `"❌ No Claude sessions found in ~/.claude/projects/"` | `"❌ ~/.claude/projects/에서 세션을 찾을 수 없습니다"` |
| 633 | `"💡 Make sure you've used Claude Code and have conversations saved."` | `"💡 Claude Code를 사용하고 대화가 저장되어 있는지 확인해 주세요."` |
| 636 | `f"📚 Found {len(sessions)} Claude sessions:\n"` | `f"📚 {len(sessions)}개의 세션을 찾았습니다:\n"` |
| 692-694 | `f"✅ {success}/{total}: ..."` | `f"✅ {success}/{total}: ..."` (keep as-is, format string is language-neutral) |
| 696 | `f"⏭️  Skipped session {idx + 1} (no conversation)"` | `f"⏭️  세션 {idx + 1} 건너뜀 (대화 없음)"` |
| 698 | `f"❌ Invalid session number: {idx + 1}"` | `f"❌ 잘못된 세션 번호: {idx + 1}"` |
| 825 | `f"❌ Invalid date format: {args.search_date_from}"` | `f"❌ 잘못된 날짜 형식: {args.search_date_from}"` |
| 831 | same for `search_date_to` | same pattern |
| 839 | `f"🔍 Searching for: {query}"` | `f"🔍 검색 중: {query}"` |
| 851 | `"❌ No matches found."` | `"❌ 일치하는 결과가 없습니다."` |
| 854 | `f"✅ Found {len(results)} matches across conversations:"` | `f"✅ {len(results)}개의 결과를 찾았습니다:"` |
| 876 | `"View a conversation? Enter number (1-{}) or press Enter to skip: "` | `"대화를 보시겠습니까? 번호를 입력하세요 (1-{}) 또는 Enter로 건너뛰기: "` |
| 886 | `"📤 Extract this conversation? (y/N): "` | `"📤 이 대화를 추출하시겠습니까? (y/N): "` |
| 898-899 | `"👋 Cancelled"` | `"👋 취소됨"` |
| 914-916 | CLI help strings | Korean equivalents |
| 933 | `f"📤 Extracting {len(indices)} session(s) as {args.format.upper()}..."` | `f"📤 {len(indices)}개의 세션을 {args.format.upper()} 형식으로 추출하는 중..."` |
| 935 | `"📋 Including detailed tool use and system messages"` | `"📋 도구 사용 및 시스템 메시지 포함"` |
| 939 | `f"✅ Successfully extracted {success}/{total} sessions"` | `f"✅ {success}/{total}개의 세션을 추출했습니다"` |
| 944 | similar to 933 | similar pattern |
| 956 | similar to 933 | similar pattern |

- [ ] **Step 2: Apply all string replacements**

Apply the replacements listed above to `src/extract_claude_logs.py` using Edit tool.

- [ ] **Step 3: Verify valid Python syntax**

Run: `cd /Users/mini_bot/Downloads/claude-conversation-extractor-main && python -c "import ast; ast.parse(open('src/extract_claude_logs.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd /Users/mini_bot/Downloads/claude-conversation-extractor-main
git add src/extract_claude_logs.py
git commit -m "feat: translate extract_claude_logs.py to Korean"
```

---

### Task 5: Korean UI - search_cli.py and search_conversations.py

**Files:**
- Modify: `src/search_cli.py`
- Modify: `src/search_conversations.py`

- [ ] **Step 1: Translate search_cli.py strings**

| Line | English | Korean |
|------|---------|--------|
| 30 | `"🔍 Enter search term: "` | `"🔍 검색어를 입력하세요: "` |
| 32 | `"👋 Search cancelled"` | `"👋 검색이 취소되었습니다"` |
| 35 | `"❌ No search term provided"` | `"❌ 검색어가 입력되지 않았습니다"` |
| 39 | `f"🔍 Searching for: '{search_term}'"` | `f"🔍 검색 중: '{search_term}'"` |
| 50 | `f"✅ Found {len(results)} results across conversations:\n"` | `f"✅ {len(results)}개의 결과를 찾았습니다:\n"` |
| 88 | `"  V. VIEW a conversation"` | `"  V. 대화 보기"` |
| 89 | `"  E. EXTRACT all conversations"` | `"  E. 모든 대화 추출"` |
| 90 | `"  Q. QUIT"` | `"  Q. 종료"` |
| 93 | `"Your choice: "` | `"선택: "` |
| 102 | `"📤 Extract this conversation? (y/N): "` | `"📤 이 대화를 추출하시겠습니까? (y/N): "` |
| 110 | `"Select conversation to view:"` | `"볼 대화를 선택하세요:"` |
| 115 | `"Enter number (1-{}): "` | `"번호를 입력하세요 (1-{}): "` |
| 127 | `"❌ Invalid selection"` | `"❌ 잘못된 선택입니다"` |
| 132 | `f"📤 Extracting session {i}..."` | `f"📤 세션 {i} 추출 중..."` |
| 139 | `"👋 Goodbye!"` | `"👋 안녕히 가세요!"` |
| 142 | `"👋 Search cancelled"` | `"👋 검색이 취소되었습니다"` |
| 144 | `f"❌ No matches found for '{search_term}'"` | `f"❌ '{search_term}'에 대한 결과가 없습니다"` |
| 145-148 | Tips section | Korean equivalents |

- [ ] **Step 2: Translate search_conversations.py strings**

| Line | English | Korean |
|------|---------|--------|
| 29 | `"Note: Install spacy..."` | `"참고: 향상된 시맨틱 검색을 위해 spacy를 설치하세요"` |
| 30 | `"      pip install spacy..."` | `"      pip install spacy && python -m spacy download en_core_web_sm"` |
| 83 | `"Warning: spaCy model not found. Using basic search."` | `"경고: spaCy 모델을 찾을 수 없습니다. 기본 검색을 사용합니다."` |
| 308 | `f"Error searching {jsonl_file}: {e}"` | `f"검색 오류 {jsonl_file}: {e}"` |
| 385 | same | same pattern |
| 405 | `f"Invalid regex pattern: {e}"` | `f"잘못된 정규식 패턴: {e}"` |
| 467 | same as 308 | same pattern |
| 549 | same as 308 | same pattern |
| 815 | `f"Created search index with {len(...)} conversations"` | `f"{len(...)}개의 대화로 검색 인덱스를 생성했습니다"` |

Also fix `search_conversations.py:812` - add `encoding="utf-8"`:
```python
# Line 812: missing encoding
with open(output_file, "w", encoding="utf-8") as f:
```

- [ ] **Step 3: Apply all replacements and verify syntax**

Run:
```bash
cd /Users/mini_bot/Downloads/claude-conversation-extractor-main
python -c "import ast; ast.parse(open('src/search_cli.py').read()); print('search_cli OK')"
python -c "import ast; ast.parse(open('src/search_conversations.py').read()); print('search_conversations OK')"
```
Expected: Both `OK`

- [ ] **Step 4: Commit**

```bash
cd /Users/mini_bot/Downloads/claude-conversation-extractor-main
git add src/search_cli.py src/search_conversations.py
git commit -m "feat: translate search_cli.py and search_conversations.py to Korean"
```

---

### Task 6: Korean UI - realtime_search.py and Multibyte Input

**Files:**
- Modify: `src/realtime_search.py:136, 176-178, 191-193, 234, 362`
- Create: `tests/test_korean_search.py`

- [ ] **Step 1: Write failing test for Korean character input**

```python
# tests/test_korean_search.py
"""Tests for Korean character handling in search."""

from src.realtime_search import RealTimeSearch, SearchState


class TestKoreanInput:
    def test_handle_multibyte_korean_char(self):
        """Korean characters should be accepted as printable input."""
        rts = RealTimeSearch.__new__(RealTimeSearch)
        rts.state = SearchState()
        rts.search_lock = __import__("threading").Lock()
        rts.results_cache = {}
        rts.stop_event = __import__("threading").Event()

        # Simulate typing Korean character '한'
        action = rts.handle_input("한")
        assert action == "redraw"
        assert rts.state.query == "한"
        assert rts.state.cursor_pos == 1

    def test_handle_multibyte_sequence(self):
        """Multiple Korean characters should build query correctly."""
        rts = RealTimeSearch.__new__(RealTimeSearch)
        rts.state = SearchState()
        rts.search_lock = __import__("threading").Lock()
        rts.results_cache = {}
        rts.stop_event = __import__("threading").Event()

        rts.handle_input("안")
        rts.handle_input("녕")
        assert rts.state.query == "안녕"
        assert rts.state.cursor_pos == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/mini_bot/Downloads/claude-conversation-extractor-main && python -m pytest tests/test_korean_search.py -v`
Expected: FAIL - `handle_input` rejects non-ASCII characters (line 362: `ord(key) >= 32 and ord(key) < 127`)

- [ ] **Step 3: Fix handle_input to accept multibyte characters**

In `src/realtime_search.py`, replace line 362:

```python
# OLD (line 362):
        elif key and len(key) == 1 and ord(key) >= 32 and ord(key) < 127:  # Printable character

# NEW:
        elif key and len(key) >= 1 and key.isprintable():  # Printable character (including Korean)
```

- [ ] **Step 4: Fix KeyboardHandler.get_key to read multibyte UTF-8 characters**

In `src/realtime_search.py`, replace lines 136-139 in the Unix `get_key` method:

```python
# OLD (lines 136-139):
                elif ord(char) >= 32 and ord(char) < 127:  # Printable characters
                    return char
                else:
                    return None

# NEW:
                elif ord(char) >= 32:  # Printable characters (including multibyte start)
                    # Handle multibyte UTF-8 (Korean, etc.)
                    if ord(char) > 127:
                        byte = char.encode('utf-8')
                        # Read remaining bytes for multibyte character
                        result = byte
                        while True:
                            try:
                                result.decode('utf-8')
                                break
                            except UnicodeDecodeError:
                                if select.select([sys.stdin], [], [], 0.05)[0]:
                                    next_char = sys.stdin.read(1)
                                    result += next_char.encode('latin-1')
                                else:
                                    return None
                        return result.decode('utf-8')
                    return char
                else:
                    return None
```

- [ ] **Step 5: Translate realtime_search.py UI strings**

| Line | English | Korean |
|------|---------|--------|
| 176 | `"🔍 REAL-TIME SEARCH"` | `"🔍 실시간 검색"` |
| 178 | `"Type to search • ↑↓ to select • Enter to open • ESC to exit"` | `"검색어 입력 • ↑↓ 선택 • Enter 열기 • ESC 종료"` |
| 191 | `f"No results found for '{query}'"` | `f"'{query}'에 대한 결과가 없습니다"` |
| 193 | `"Start typing to search..."` | `"검색어를 입력하세요..."` |
| 234 | `"Search: {query}"` | `"검색: {query}"` |
| 536 | `f"✅ Selected: {selected_file}"` | `f"✅ 선택됨: {selected_file}"` |
| 539 | `"👋 Search cancelled"` | `"👋 검색이 취소되었습니다"` |

- [ ] **Step 6: Run tests**

Run: `cd /Users/mini_bot/Downloads/claude-conversation-extractor-main && python -m pytest tests/test_korean_search.py -v`
Expected: All 2 tests PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/mini_bot/Downloads/claude-conversation-extractor-main
git add src/realtime_search.py tests/test_korean_search.py
git commit -m "feat: add Korean input support and translate realtime_search.py"
```

---

### Task 7: Final Verification

**Files:** All modified files

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/mini_bot/Downloads/claude-conversation-extractor-main && python -m pytest tests/ -v --tb=short`
Expected: All tests pass (existing + new)

- [ ] **Step 2: Verify Python syntax of all modified files**

Run:
```bash
cd /Users/mini_bot/Downloads/claude-conversation-extractor-main
for f in src/interactive_ui.py src/extract_claude_logs.py src/search_cli.py src/realtime_search.py src/search_conversations.py; do
  python -c "import ast; ast.parse(open('$f').read()); print('$f OK')"
done
```
Expected: All 5 files `OK`

- [ ] **Step 3: Fix any test failures and commit**

If failures exist, fix and commit. Otherwise skip.

- [ ] **Step 4: Final commit if needed**

```bash
cd /Users/mini_bot/Downloads/claude-conversation-extractor-main
git add -A
git commit -m "chore: final verification pass"
```
