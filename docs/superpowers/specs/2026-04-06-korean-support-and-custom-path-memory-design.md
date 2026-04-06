# Korean Support & Custom Path Memory Design

## Overview

Claude Conversation Extractor에 두 가지 기능을 추가한다:

1. **커스텀 경로 기억**: "C. Custom location"으로 입력한 경로를 최근 3개까지 기억하여 다음 실행 시 Suggested locations에 표시
2. **한글 지원**: UI 텍스트 한글화, 한글 콘텐츠 추출 보장, 한글 검색 정상 동작

## 기능 1: 커스텀 경로 기억

### 설정 파일

- 위치: `~/.claude/conversation-extractor-config.json`
- 구조:
  ```json
  {
    "recent_custom_paths": [
      "/Users/example/Projects/logs",
      "/tmp/claude-export",
      "/Users/example/Backup/claude"
    ]
  }
  ```
- 최대 3개, MRU(Most Recently Used) 순서
- 이미 존재하는 경로를 다시 선택하면 리스트 맨 앞으로 이동 (중복 방지)

### UI 변경 (`interactive_ui.py` - `get_folder_selection()`)

변경 전:
```
📁 Where would you like to save your conversations?

Suggested locations:
  1. ~/Desktop/Claude Conversations
  2. ~/Documents/Claude Conversations
  3. ~/Downloads/Claude Conversations
  4. ./Claude Conversations

  C. Custom location
  Q. Quit
```

변경 후 (커스텀 경로 2개 저장된 경우):
```
📁 대화를 어디에 저장하시겠습니까?

추천 위치:
  1. ~/Desktop/Claude Conversations
  2. ~/Documents/Claude Conversations
  3. ~/Downloads/Claude Conversations
  4. ./Claude Conversations

최근 사용한 위치:
  5. /Users/example/Projects/logs
  6. /tmp/claude-export

  C. 직접 입력
  Q. 종료
```

- 기본 4개 추천 위치 아래에 "최근 사용한 위치" 섹션 추가
- 번호가 이어서 매겨짐 (5, 6, 7)
- 선택지 번호 범위 동적 조정

### 흐름

1. 앱 시작 시 설정 파일 로드 (파일 없으면 빈 상태로 시작)
2. `get_folder_selection()`에서 기본 추천 + 최근 커스텀 경로를 함께 표시
3. 사용자가 커스텀 경로 입력 또는 최근 경로 선택
4. 추출 완료 후 해당 경로를 설정 파일에 저장 (MRU 갱신, 최대 3개 유지)

### 구현 위치

- `interactive_ui.py`: 설정 로드/저장 메서드 추가, `get_folder_selection()` 수정
- 설정 파일 읽기/쓰기는 `InteractiveUI` 클래스 내 `_load_config()`, `_save_config()`, `_update_recent_paths(path)` 메서드로 구현

## 기능 2: 한글 지원

### UI 텍스트 한글화

변경 대상:

| 파일 | 변경 내용 |
|------|----------|
| `interactive_ui.py` | 모든 print/input 메시지 한글화 (메뉴, 안내, 에러) |
| `extract_claude_logs.py` | CLI 출력 메시지 한글화 (진행상황, 결과, 안내) |
| `search_cli.py` | 검색 안내/결과 메시지 한글화 |
| `realtime_search.py` | 검색 UI 안내 메시지 한글화 |
| `search_conversations.py` | 검색 결과 출력 메시지 한글화 |

예시 변환:
- `"🔍 Finding your Claude conversations..."` → `"🔍 대화를 검색하는 중..."`
- `"Enter search term: "` → `"검색어를 입력하세요: "`
- `"❌ No Claude conversations found!"` → `"❌ 대화를 찾을 수 없습니다!"`
- `"✅ Successfully extracted"` → `"✅ 추출 완료"`
- `"📁 Saving logs to:"` → `"📁 저장 위치:"`

### 한글 콘텐츠 추출

- JSONL 파싱 시 모든 `open()` 호출에 `encoding='utf-8'` 명시적 지정
- Markdown 저장 시에도 `encoding='utf-8'` 명시적 지정
- 현재 기본값 의존하는 부분을 전수 검사하여 수정

### 한글 검색

- `search_conversations.py`의 정규식 검색: 한글 패턴 정상 동작 확인
- 필요한 곳에 `re.UNICODE` 플래그 추가
- `realtime_search.py` 실시간 검색: 한글 멀티바이트 문자 입력 처리 확인 및 수정

## 변경 영향 범위

- 신규 파일: 없음
- 변경 파일: `interactive_ui.py`, `extract_claude_logs.py`, `search_cli.py`, `realtime_search.py`, `search_conversations.py`
- 외부 의존성 추가: 없음 (표준 라이브러리 `json`만 사용, 이미 프로젝트에서 사용 중)
- 설정 파일 신규 생성: `~/.claude/conversation-extractor-config.json`

## 테스트

- 커스텀 경로 기억: 설정 파일 로드/저장, MRU 순서, 최대 3개 제한, 중복 방지
- 한글 UI: 메시지 출력 확인
- 한글 추출: UTF-8 인코딩 JSONL 파싱 및 Markdown 저장
- 한글 검색: 정규식 한글 패턴 매칭, 실시간 검색 한글 입력
