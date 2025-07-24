# BAI 로그인 테스트 시나리오

## 프로젝트 정보

### 서버 환경

- **백엔드 서버**: https://api.bai.ai.local (Backend)
- **백엔드 인증 서버**: https://auth.bai.ai.local (Backend Auth)
- **프론트엔드 서버**: https://bai.ai.local (Frontend)
- **프론트엔드 인증 서버**: https://auth.bai.ai.local/ui (Frontend Auth)

### API 문서

- **백엔드 서버 Swagger URL**: https://api.bai.ai.local/api/v1/docs
- **백엔드 인증 서버 Swagger URL**: https://auth.bai.ai.local/api/v1/docs
- **백엔드 서버 OpenAPI Spec**: https://api.bai.ai.local/api/v1/openapi.json

### 인증 정보

- **인증 방식**: JWT Bearer Token (Cookie 기반)
- **토큰 위치**: HttpOnly Cookie (access_token, refresh_token)
- **토큰 만료**: Access Token 30분, Refresh Token 30일
- **보안**: AES-256-CBC 암호화, bcrypt 해싱

## 테스트 환경 설정

### Frontend (Next.js)

```yaml
base_url: http://localhost:3000
auth_url: http://localhost:5000
test_user:
  email: test@bai.ai.kr
  password: Test123!@#
  user_nick: 테스트사용자
```

### Backend API (FastAPI)

```yaml
base_url: http://localhost:8000
api_prefix: /api/v1
headers:
  Content-Type: application/json
  Accept: application/json
```

## 시나리오: 사용자 로그인 플로우

### 시나리오 설명

사용자가 이메일과 비밀번호로 로그인하고, JWT 토큰을 발급받아 인증된 상태로 메인 페이지에 접근하는 전체 플로우를 테스트

### 사전 조건

- [X] 테스트 사용자 계정이 DB에 존재
- [X] Frontend/Backend 서버 실행 중
- [X] 데이터베이스 연결 정상

### 테스트 데이터

```json
{
  "valid_user": {
    "user_id": "test@bai.ai.kr",
    "password": "Test123!@#"
  },
  "invalid_credentials": {
    "user_id": "test@bai.ai.kr",
    "password": "wrong_password"
  },
  "non_existent_user": {
    "user_id": "notexist@bai.ai.kr",
    "password": "Test123!@#"
  }
}
```

## 시퀀스 다이어그램

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API as Users API
    participant Security as Security Module
    participant DB

    User->>Frontend: 접속 (로그인 페이지)
    User->>Frontend: 이메일/비밀번호 입력
    Frontend->>API: POST /api/v1/users/login
    API->>Security: 사용자 ID 암호화 (AES-256)
    API->>DB: UserInfo 조회 (암호화된 ID)
    DB-->>API: 사용자 정보
    API->>Security: 비밀번호 검증 (bcrypt)
    API->>DB: UserLoginInfo 업데이트
    Note over API: 로그인 성공인 경우
    API->>Security: JWT 토큰 생성
    API->>DB: Refresh Token 저장
    API-->>Frontend: JWT 토큰 (쿠키) + 사용자 정보
    Frontend->>Frontend: 메인 페이지로 이동
    Note over API: 로그인 실패인 경우
    API-->>Frontend: 에러 메시지
    Frontend->>Frontend: 에러 표시
```

## API 엔드포인트 상세

### 1. 로그인 API

- **Endpoint**: POST /api/v1/users/login
- **Swagger**: http://localhost:8000/docs#/users/login_api_v1_users_login_post
- **Request Body**:
  ```json
  {
    "user_id": "test@bai.ai.kr",
    "password": "Test123!@#"
  }
  ```
- **Success Response (200)**:
  ```json
  {
    "success": true,
    "status": 200,
    "data": {
      "user_info": {
        "user_sys_id": "encrypted_id_string",
        "user_id": "test@bai.ai.kr",
        "user_nick": "테스트사용자"
      }
    },
    "message": "로그인 성공"
  }
  ```
- **Error Response (401)**:
  ```json
  {
    "success": false,
    "status": 401,
    "error": "비밀번호가 일치하지 않습니다",
    "message": "로그인 실패"
  }
  ```
- **Cookies Set**:
  - `access_token`: JWT 액세스 토큰
  - `refresh_token`: 리프레시 토큰

### 2. 토큰 갱신 API

- **Endpoint**: POST /api/v1/users/refresh
- **Swagger**: http://localhost:8000/docs#/users/refresh_token_api_v1_users_refresh_post
- **Headers**: Cookie with refresh_token
- **Response**: New access_token in cookie

## 테스트 케이스

### 정상 케이스

1. **TC001**: 유효한 자격증명으로 로그인 성공
   - 입력: 올바른 이메일/비밀번호
   - 기대 결과:
     - HTTP 200
     - access_token, refresh_token 쿠키 설정
     - 사용자 정보 반환
   - 검증 항목:
     - [X] 응답 상태 코드
     - [X] 쿠키 존재 여부
     - [X] 사용자 정보 정확성
     - [X] 메인 페이지 리다이렉션

### 예외 케이스

1. **TC002**: 잘못된 비밀번호

   - 입력: 올바른 이메일, 잘못된 비밀번호
   - 기대 결과: HTTP 401, 에러 메시지
   - 검증: 에러 메시지 "비밀번호가 일치하지 않습니다"
2. **TC003**: 존재하지 않는 사용자

   - 입력: 존재하지 않는 이메일
   - 기대 결과: HTTP 401, 에러 메시지
   - 검증: 에러 메시지 "사용자를 찾을 수 없습니다"
3. **TC004**: 이메일 형식 오류

   - 입력: 잘못된 이메일 형식
   - 기대 결과: HTTP 422, 유효성 검증 오류
   - 검증: 프론트엔드 유효성 검사

## 모킹 설정

### 보안 모듈 (개발 환경)

```python
# Security 모듈 모킹
mock_security = {
    "encrypt_user_id": lambda x: f"encrypted_{x}",
    "verify_password": lambda x, y: True,
    "create_jwt_token": lambda x: "mock_jwt_token"
}
```

## 테스트 실행 설정

### 환경 변수

```bash
# .env.test
TEST_ENV=test
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
AUTH_FRONTEND_URL=http://localhost:5000
DB_CONNECTION=postgresql://test:test@localhost:5432/bai_test
REDIS_URL=redis://localhost:6379/1
SECRET_KEY=test_secret_key_for_testing_only
```

### 테스트 그룹

- `@smoke` - 로그인 기본 동작
- `@security` - 암호화, 토큰 검증
- `@integration` - DB 연동 테스트
- `@e2e` - 전체 플로우 테스트

## MCP 테스트 생성 명령

```bash
# 다이어그램 파싱
@bai-autotest parse_diagram으로 file_path: "examples/login-scenario-filled.md" 파일을 파싱해줘

# E2E 테스트 생성 (Playwright)
@bai-autotest generate_test로 다음 설정으로 테스트를 생성해줘:
- scenario_name: "사용자 로그인 플로우"
- framework: "playwright"
- config: {
    "base_url": "http://localhost:3000",
    "api_url": "http://localhost:8000"
  }

# API 테스트 생성 (Pytest)
@bai-autotest generate_test로 백엔드 API 테스트를 생성해줘:
- scenario_name: "사용자 로그인 플로우"
- framework: "pytest"
- config: {
    "base_url": "http://localhost:8000",
    "use_async": true
  }
```

## 참고 사항

### 보안 고려사항

- 모든 비밀번호는 bcrypt로 해싱
- 사용자 ID는 AES-256-CBC로 암호화
- JWT 토큰은 HttpOnly 쿠키로 전송
- CORS 설정 확인 필요

### 관련 문서

- [BAI 인증 시스템 설계서](../docs/auth-design.md)
- [API 명세서](http://localhost:8000/docs)
- [보안 가이드라인](../docs/security-guide.md)
