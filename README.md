# Claude Conversation Extractor - Claude Code 대화를 마크다운으로 추출

> 🚀 **Claude Code 대화를 추출할 수 있는 도구**. ~/.claude/projects에서 대화 기록을 검색하고, 로그를 추출하고, AI 프로그래밍 세션을 백업하세요.

> 🔀 이 프로젝트는 [ZeroSumQuant/claude-conversation-extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor)를 fork한 것입니다.

## 🇰🇷 패치 내용 (v1.1.2-ko)

원본 프로젝트에 다음 기능을 추가했습니다:

### 한글 UI

- 모든 사용자 대면 메시지를 한국어로 번역 (메뉴, 안내, 에러 메시지 등)
- 실시간 검색에서 한글 입력 지원 (멀티바이트 UTF-8 키보드 핸들러)
- UTF-8 인코딩 명시적 지정으로 한글 콘텐츠 추출/저장 보장

### 커스텀 경로 기억

- `~/.claude/conversation-extractor-config.json`에 최근 사용한 저장 경로 최대 3개 기억
- 폴더 선택 메뉴에 "최근 사용한 위치" 섹션 자동 표시
- MRU(Most Recently Used) 방식으로 가장 최근 경로가 맨 위에 표시

## 🎮 사용 방법

- **`claude-start`** - 인터랙티브 UI (ASCII 로고, 실시간 검색, 메뉴 방식 — 권장)
- **`claude-extract`** - CLI 모드 (명령줄 조작 및 스크립팅용)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 주요 기능

- **🔍 실시간 검색**: 입력하는 즉시 대화 검색 — 한글 검색 지원
- **📝 JSONL → 마크다운 변환**: 터미널 아티팩트 없이 깔끔한 추출
- **⚡ 빠른 검색**: 내용, 날짜, 대화명으로 검색
- **📦 일괄 추출**: 모든 Claude Code 대화를 한 번에 추출
- **🎯 설정 불필요**: `claude-extract` 실행만 하면 자동으로 찾아줌
- **🚀 외부 의존성 없음**: 순수 Python — 추가 패키지 불필요
- **🖥️ 크로스 플랫폼**: Windows, macOS, Linux 모두 지원

## 📦 설치

### 빠른 설치 (권장)

```bash
# pipx 사용 (Python 환경 문제 해결)
pipx install claude-conversation-extractor

# 또는 pip 사용
pip install claude-conversation-extractor
```

### 이 fork 버전 설치 (한글 UI)

```bash
git clone https://github.com/Epikoding/claude-conversation-extractor.git
cd claude-conversation-extractor
pip install -e .
```

### 플랫폼별 설정

<details>
<summary>macOS</summary>

```bash
brew install pipx
pipx ensurepath
pipx install claude-conversation-extractor
```

</details>

<details>
<summary>Windows</summary>

```bash
py -m pip install --user pipx
py -m pipx ensurepath
# 터미널 재시작 후:
pipx install claude-conversation-extractor
```

</details>

<details>
<summary>Linux</summary>

```bash
# Ubuntu/Debian
sudo apt install pipx
pipx ensurepath
pipx install claude-conversation-extractor
```

</details>

## 🚀 사용법

### 빠른 시작

```bash
# 인터랙티브 UI 실행 (ASCII 로고 + 실시간 검색)
claude-start

# 표준 CLI 인터페이스
claude-extract

# 특정 내용 검색
claude-search "API 연동"
```

실행하면:

1. `~/.claude/projects`에서 대화를 자동으로 찾고
2. 검색 또는 추출할 수 있는 인터랙티브 메뉴를 표시하고
3. JSONL 파일을 마크다운, JSON, 또는 HTML로 변환합니다

### CLI 명령어 모음

```bash
# 모든 대화 목록 보기
claude-extract --list

# 특정 대화 추출 (번호 지정)
claude-extract --extract 1,3,5

# 최근 N개 대화 추출
claude-extract --recent 5

# 모든 대화 일괄 추출
claude-extract --all

# 저장 위치 지정
claude-extract --output ~/my-claude-backups
```

### 📄 추출 형식

```bash
# JSON 형식으로 추출
claude-extract --format json --extract 1

# HTML 형식으로 추출 (보기 좋은 웹 포맷)
claude-extract --format html --all

# 도구 사용, MCP 응답, 시스템 메시지 포함
claude-extract --detailed --extract 1

# 옵션 조합
claude-extract --format html --detailed --recent 5
```

**지원 형식:**

- **Markdown** (기본값) - 깔끔하고 읽기 쉬운 텍스트
- **JSON** - 분석 및 처리용 구조화 데이터
- **HTML** - 구문 강조가 있는 웹 뷰어블 포맷

**상세 모드 (`--detailed`):**

- 도구 호출 및 파라미터
- MCP 서버 응답
- 시스템 메시지 및 에러
- 터미널 명령 출력
- 대화의 모든 메타데이터 포함

### 🔍 대화 검색

```bash
# 직접 검색
claude-search                    # 검색어 입력 프롬프트
claude-search "zig build"        # 특정 용어 검색
claude-search "에러 처리"         # 한글 검색 지원

# 인터랙티브 메뉴에서 검색
claude-extract
# "F. 대화 검색" 선택하면 실시간 검색
```

**검색 기능:**

- 모든 대화에 대한 빠른 전문 검색
- 기본적으로 대소문자 구분 없음
- 정확한 일치, 부분 일치, 패턴 매칭
- 일치 미리보기 및 대화 컨텍스트 표시
- 검색 결과에서 바로 추출 가능

## 📁 Claude Code 로그 저장 위치

### 기본 위치:

- **macOS/Linux**: `~/.claude/projects/*/chat_*.jsonl`
- **Windows**: `%USERPROFILE%\.claude\projects\*\chat_*.jsonl`

### 추출된 대화 형식:

```text
~/Desktop/Claude logs/claude-conversation-2025-06-09-abc123.md
├── 메타데이터 (세션 ID, 타임스탬프)
├── 👤 사용자 메시지
├── 🤖 Claude 응답
└── 깔끔한 마크다운 포맷
```

## ❓ 자주 묻는 질문

### Claude Code 대화를 어떻게 추출하나요?

`pip install claude-conversation-extractor`로 설치한 후 `claude-extract`를 실행하세요. 도구가 `~/.claude/projects`에서 모든 대화를 자동으로 찾습니다.

### 도구 사용을 포함한 상세 내역은 어떻게 추출하나요?

`--detailed` 플래그를 사용하세요:

```bash
claude-extract --detailed --format html --extract 1
```

### Claude Code는 대화를 어디에 저장하나요?

`~/.claude/projects/`에 JSONL 파일로 저장합니다. 내장 추출 기능이 없어서 이 도구가 필요합니다.

### Claude Code 기록을 검색할 수 있나요?

네! `claude-search`를 실행하거나 메뉴에서 "대화 검색"을 선택하세요.

### 모든 세션을 어떻게 백업하나요?

`claude-extract --all`로 모든 대화를 한 번에 추출하세요.

### Claude.ai (웹 버전)에서도 작동하나요?

아니요, 이 도구는 Claude Code (데스크톱 앱) 전용입니다. Claude.ai는 설정에서 자체 내보내기 기능이 있습니다.

### 이 도구는 공식 도구인가요?

아니요, 독립적인 오픈소스 도구입니다. 로컬 Claude Code 파일을 읽을 뿐 — API나 인터넷 연결이 필요 없습니다.

## 🔧 기술 세부사항

### 작동 원리

1. `~/.claude/projects`에서 JSONL 파일 탐색
2. Claude의 내부 데이터 구조 파싱
3. 사용자 입력과 Claude 응답 추출
4. 마크다운/JSON/HTML로 변환
5. 즉시 검색을 위한 콘텐츠 인덱싱

### 요구사항

- Python 3.8+ (3.9, 3.10, 3.11, 3.12, 3.14 호환)
- Claude Code 설치 및 기존 대화 존재
- 핵심 기능에 외부 의존성 없음

### 선택사항: spaCy를 이용한 고급 검색

```bash
pip install spacy
python -m spacy download en_core_web_sm
```

## 🔒 개인정보 및 보안

- ✅ **100% 로컬**: 대화 데이터를 외부로 전송하지 않음
- ✅ **오프라인**: 인터넷 없이 완전히 동작
- ✅ **추적 없음**: 원격 측정이나 분석 없음
- ✅ **오픈소스**: 직접 코드를 검토 가능
- ✅ **읽기 전용**: Claude Code 파일을 수정하지 않음

## 📜 라이선스

MIT License - [LICENSE](LICENSE) 참조.

---

**참고**: Claude Code 대화 추출을 위한 독립 도구입니다. Anthropic과 제휴 관계가 없습니다.
