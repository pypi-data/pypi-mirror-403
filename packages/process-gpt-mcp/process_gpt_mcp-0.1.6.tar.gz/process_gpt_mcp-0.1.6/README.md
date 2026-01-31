# Process GPT MCP Server

업무 지원을 위한 MCP (Model Context Protocol) 도구 서버입니다.

## 개념

```
사용자 메시지 → Agent (LLM) → MCP 도구 호출 → 프로세스 실행/결과 반환
```

- **MCP** = 조회 + 실행 도구 모음
- **Agent** = 사용자 요청을 분석하고 적절한 도구를 순차적으로 호출

## 도구 목록 (7개)

| 도구명 | 설명 | 입력 |
|--------|------|------|
| `get_process_list` | 프로세스 정의 목록 조회 | `tenant_id` |
| `get_process_detail` | 프로세스 상세 정보 조회 | `tenant_id`, `process_id` |
| `get_form_fields` | 폼 필드 정보 조회 | `tenant_id`, `form_key` |
| `execute_process` | 프로세스 실행 | `tenant_id`, `user_uid`, `user_email`, `process_definition_id`, `activity_id`, `form_key`, `form_values`, `role_mappings`(선택) |
| `get_instance_list` | 진행 중인 인스턴스 조회 | `tenant_id`, `user_uid`, `process_id`(선택) |
| `get_todolist` | 할 일 목록 및 실행 결과 조회 | `tenant_id`, `instance_ids[]` |
| `get_organization` | 조직도 조회 | `tenant_id` |

## 도구 호출 흐름 가이드

### 프로세스 실행 요청 시
```
사용자: "12월 26일 휴가 1일 신청해줘"

1. get_process_list(tenant_id)
   → "휴가신청" 프로세스 ID 확인: "vacation_request"

2. get_process_detail(tenant_id, "vacation_request")
   → sequences에서 start_event 이후 첫 번째 액티비티 ID 확인
   → activities에서 해당 액티비티의 tool 필드에서 폼 키 확인
   → roles에서 역할 목록 확인

3. get_form_fields(tenant_id, "vacation_request_activity_001_form")
   → 폼 필드 정보: start_date, days, reason 등

4. execute_process(...)
   → form_values: {"start_date": "2024-12-26", "days": 1}
   → 프로세스 실행 완료
```

### 프로세스 실행 결과 조회 시
```
사용자: "나라장터 검색 결과 알려줘"

1. get_process_list(tenant_id)
   → "나라장터" 프로세스 ID 확인: "g2b_search"

2. get_instance_list(tenant_id, user_uid, "g2b_search")
   → 인스턴스 목록에서 proc_inst_id 확인

3. get_todolist(tenant_id, ["instance_id_1", "instance_id_2"])
   → 각 activity의 output 필드에서 실행 결과 확인
```

### 조직도/프로세스 상세 조회 시
```
사용자: "개발팀에 누가 있어?"
→ get_organization(tenant_id) 직접 호출

사용자: "휴가신청 프로세스 단계가 뭐야?"
→ get_process_list → get_process_detail 순서로 호출
```

## 설치

```bash
pip install process-gpt-mcp
```

## PyPI 배포

### 버전 업데이트
`pyproject.toml`에서 버전 수정:
```toml
version = "0.2.9"  # 새 버전으로 변경
```

### 빌드 및 배포 (PowerShell)
```powershell
# dist 폴더 정리 및 빌드
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
python -m build

# PyPI 업로드
$env:PYTHONIOENCODING = "utf-8"
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-xxx..."  # PyPI API 토큰
python -m twine upload dist/*
```

### 빌드 및 배포 (Bash/Linux/Mac)
```bash
# dist 폴더 정리 및 빌드
rm -rf dist/
python -m build

# PyPI 업로드
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-xxx..."  # PyPI API 토큰
python -m twine upload dist/*
```

### 필요 패키지
```bash
pip install build twine
```

## 환경 변수 설정

`env.example.txt`를 참고하여 `.env` 파일을 생성하세요:

```bash
# Supabase 설정
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# 백엔드 API 설정 (프로세스 실행용)
API_BASE_URL=https://your-api-server.com
```

## 테스트

### MCP Inspector로 테스트
```bash
npx @modelcontextprotocol/inspector python -m process_gpt_mcp.server
```

### FastMCP dev 모드
```bash
fastmcp dev src/process_gpt_mcp/server.py
```

## Cursor에서 사용

`.cursor/mcp.json` 파일에 추가:

```json
{
  "mcpServers": {
    "work-assistant": {
      "command": "process-gpt-mcp",
      "args": [],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_ANON_KEY": "your-anon-key"
      }
    }
  }
}
```

## 사용 시나리오 예시

### 시나리오 1: 프로세스 실행 (휴가 신청)
```
사용자: "12월 26일 휴가 1일 신청해줘"

Agent:
1. get_process_list(tenant_id="uengine")
   → [{"id": "vacation_request", "name": "휴가신청"}, ...]
   
2. get_process_detail(tenant_id="uengine", process_id="vacation_request")
   → sequences: [{source: "start_event", target: "activity_001"}]
   → activities: [{id: "activity_001", tool: "formHandler:vacation_request_activity_001_form", role: "requester"}]
   → roles: [{name: "requester", ...}]
   
3. get_form_fields(tenant_id="uengine", form_key="vacation_request_activity_001_form")
   → fields_json: [{name: "start_date", type: "date"}, {name: "days", type: "number"}, ...]
   
4. execute_process(
     tenant_id="uengine",
     user_uid="user-uuid",
     user_email="user@example.com",
     process_definition_id="vacation_request",
     activity_id="activity_001",
     form_key="vacation_request_activity_001_form",
     form_values={"start_date": "2024-12-26", "days": 1},
     role_mappings=[{"name": "requester", "endpoint": ["user-uuid"]}]
   )
   → {"process_instance_id": "vacation_request.xxx-xxx", "message": "프로세스가 성공적으로 실행되었습니다."}
```

### 시나리오 2: 업무 현황 조회
```
사용자: "내 진행 중인 업무 뭐가 있어?"

Agent:
1. get_instance_list(tenant_id="uengine", user_uid="user-uuid")
   → [{"proc_inst_id": "inst1", "proc_def_id": "vacation_request", "status": "IN_PROGRESS"}, ...]
   
2. get_todolist(tenant_id="uengine", instance_ids=["inst1", "inst2"])
   → 각 인스턴스의 activity 목록과 output(실행 결과) 반환
   
Agent: "현재 2개의 업무가 진행 중입니다. 휴가신청 건은 승인 대기 중이며..."
```

### 시나리오 3: 검색 프로세스 실행 및 결과 조회
```
사용자: "서울 날씨 검색해줘"

Agent:
1. get_process_list → "날씨검색" 프로세스 ID: "weather_search"
2. get_process_detail → 첫 번째 액티비티, 폼 키 확인
3. get_form_fields → location 필드 확인
4. execute_process(form_values={"location": "서울"})
   → 프로세스 실행 (에이전트가 자동으로 날씨 API 호출)

잠시 후...

사용자: "날씨 검색 결과 알려줘"

Agent:
1. get_process_list → "weather_search"
2. get_instance_list(process_id="weather_search") → 최근 인스턴스 ID
3. get_todolist(instance_ids=[...]) → output에서 날씨 정보 확인

Agent: "서울의 현재 날씨는 맑음, 기온 5도입니다..."
```

### 시나리오 4: 조직도 조회
```
사용자: "우리 회사 조직도 보여줘"

Agent:
1. get_organization(tenant_id="uengine")
   → 조직도 정보 반환
   
Agent: "우리 회사는 개발팀, 기획팀, 디자인팀으로 구성되어 있습니다..."
```
