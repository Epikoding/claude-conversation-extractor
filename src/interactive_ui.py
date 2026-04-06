#!/usr/bin/env python3
"""Interactive terminal UI for Claude Conversation Extractor"""

import json
import os
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Handle both package and direct execution imports
try:
    from .extract_claude_logs import ClaudeConversationExtractor
    from .realtime_search import RealTimeSearch, create_smart_searcher
    from .search_conversations import ConversationSearcher
except ImportError:
    # Fallback for direct execution or when not installed as package
    from extract_claude_logs import ClaudeConversationExtractor
    from realtime_search import RealTimeSearch, create_smart_searcher
    from search_conversations import ConversationSearcher


class InteractiveUI:
    """Interactive terminal UI for easier conversation extraction"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir
        self.extractor = ClaudeConversationExtractor(output_dir)
        self.searcher = ConversationSearcher()
        self.sessions: List[Path] = []
        self.terminal_width = shutil.get_terminal_size().columns
        self.config_path = Path.home() / ".claude" / "conversation-extractor-config.json"

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

    def clear_screen(self):
        """Clear the terminal screen"""
        # Use ANSI escape codes for cross-platform compatibility
        print("\033[2J\033[H", end="")

    def print_banner(self):
        """Print a cool ASCII banner"""
        # Bright magenta color
        MAGENTA = "\033[95m"
        RESET = "\033[0m"
        BOLD = "\033[1m"

        banner = f"""{MAGENTA}{BOLD}

 ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗
██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝
██║     ██║     ███████║██║   ██║██║  ██║█████╗
██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝
╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗
 ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝
███████╗██╗  ██╗████████╗██████╗  █████╗  ██████╗████████╗
██╔════╝╚██╗██╔╝╚══██╔══╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝
█████╗   ╚███╔╝    ██║   ██████╔╝███████║██║        ██║
██╔══╝   ██╔██╗    ██║   ██╔══██╗██╔══██║██║        ██║
███████╗██╔╝ ██╗   ██║   ██║  ██║██║  ██║╚██████╗   ██║
╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝   ╚═╝

{RESET}"""
        print(banner)

    def print_centered(self, text: str, char: str = "="):
        """Print text centered with decorative characters"""
        padding = (self.terminal_width - len(text) - 2) // 2
        print(f"{char * padding} {text} {char * padding}")

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

    def show_sessions_menu(self) -> List[int]:
        """Display sessions and let user select which to extract"""
        self.clear_screen()
        self.print_banner()

        # Get all sessions
        print("\n🔍 대화를 검색하는 중...")
        self.sessions = self.extractor.find_sessions()

        if not self.sessions:
            print("\n❌ 대화를 찾을 수 없습니다!")
            print("Claude Code를 한 번 이상 사용했는지 확인해 주세요.")
            input("\n계속하려면 Enter를 누르세요...")
            return []

        print(f"\n✅ {len(self.sessions)}개의 대화를 찾았습니다!\n")

        # Display sessions
        for i, session_path in enumerate(self.sessions[:20], 1):  # Show max 20
            project = session_path.parent.name
            modified = datetime.fromtimestamp(session_path.stat().st_mtime)
            size_kb = session_path.stat().st_size / 1024

            date_str = modified.strftime("%Y-%m-%d %H:%M")
            print(f"  {i:2d}. [{date_str}] {project[:30]:<30} ({size_kb:.1f} KB)")

        if len(self.sessions) > 20:
            print(f"\n  ... 외 {len(self.sessions) - 20}개의 대화")

        print("\n" + "=" * 60)
        print("\nOptions:")
        print("  A. 모든 대화 추출")
        print("  R. 최근 5개 추출")
        print("  S. 특정 대화 선택 (예: 1,3,5)")
        print("  F. 대화 검색 (실시간 검색)")
        print("  Q. 종료")

        while True:
            choice = input("\n선택: ").strip().upper()

            if choice == "Q":
                return []
            elif choice == "A":
                return list(range(len(self.sessions)))
            elif choice == "R":
                return list(range(min(5, len(self.sessions))))
            elif choice == "S":
                selection = input("대화 번호를 입력하세요 (예: 1,3,5): ").strip()
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(",")]
                    # Validate indices
                    if all(0 <= i < len(self.sessions) for i in indices):
                        return indices
                    else:
                        print("❌ 잘못된 선택입니다. 올바른 번호를 입력해 주세요.")
                except ValueError:
                    print("❌ 잘못된 형식입니다. 쉼표로 구분된 번호를 입력해 주세요.")
            elif choice == "F":
                # Search functionality
                search_results = self.search_conversations()
                if search_results:
                    return search_results
            else:
                print("❌ 잘못된 선택입니다. 다시 시도해 주세요.")

    def show_progress(self, current: int, total: int, message: str = ""):
        """Display a simple progress bar"""
        bar_width = 40
        progress = current / total if total > 0 else 0
        filled = int(bar_width * progress)
        bar = "█" * filled + "░" * (bar_width - filled)

        print(f"\r[{bar}] {current}/{total} {message}", end="", flush=True)

    def search_conversations(self) -> List[int]:
        """Launch real-time search interface"""
        # Enhance searcher with smart search
        smart_searcher = create_smart_searcher(self.searcher)

        # Create and run real-time search
        rts = RealTimeSearch(smart_searcher, self.extractor)
        selected_file = rts.run()

        if selected_file:
            # View the selected conversation
            self.extractor.display_conversation(Path(selected_file))
            
            # Ask if user wants to extract it
            extract_choice = input("\n📤 이 대화를 추출하시겠습니까? (y/N): ").strip().lower()
            if extract_choice == 'y':
                try:
                    index = self.sessions.index(Path(selected_file))
                    return [index]
                except ValueError:
                    print("\n❌ 오류: 선택한 파일을 세션 목록에서 찾을 수 없습니다")
                    input("\n계속하려면 Enter를 누르세요...")
            
            # Return empty to go back to menu
            return []

        return []

    def extract_conversations(self, indices: List[int], output_dir: Path) -> int:
        """Extract selected conversations with progress display"""
        print(f"\n📤 {len(indices)}개의 대화를 추출하는 중...\n")

        # Update the extractor's output directory
        self.extractor.output_dir = output_dir

        # Use the extractor's method
        success_count, total_count = self.extractor.extract_multiple(
            self.sessions, indices
        )

        print(
            f"\n\n✅ {success_count}/{total_count}개의 대화를 추출했습니다!"
        )
        return success_count

    def open_folder(self, path: Path):
        """Open the output folder in the system file explorer"""
        try:
            if platform.system() == "Windows":
                os.startfile(str(path))
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(path)])
        except Exception:
            pass  # Silently fail if we can't open the folder

    def run(self):
        """Main interactive UI flow"""
        try:
            # Get output folder
            output_dir = self.get_folder_selection()
            if not output_dir:
                print("\n👋 안녕히 가세요!")
                return

            # Get session selection
            selected_indices = self.show_sessions_menu()
            if not selected_indices:
                print("\n👋 안녕히 가세요!")
                return

            # Create output directory if needed
            output_dir.mkdir(parents=True, exist_ok=True)

            # Extract conversations
            success_count = self.extract_conversations(selected_indices, output_dir)

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

            if success_count > 0:
                print(f"\n📁 저장 위치: {output_dir}")

                # Offer to open the folder
                open_choice = input("\n🗂️  저장 폴더를 여시겠습니까? (Y/n): ").strip().lower()
                if open_choice != "n":
                    self.open_folder(output_dir)

            else:
                print("\n❌ 추출된 대화가 없습니다.")

            input("\n✨ 종료하려면 Enter를 누르세요...")

        except KeyboardInterrupt:
            print("\n\n👋 안녕히 가세요!")
        except Exception as e:
            print(f"\n❌ 오류: {e}")
            input("\n종료하려면 Enter를 누르세요...")


def main():
    """Entry point for interactive UI"""
    ui = InteractiveUI()
    ui.run()


if __name__ == "__main__":
    main()
