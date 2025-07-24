# 테스트 시나리오 템플릿

## 프로젝트 정보

### 서버 환경
- **백엔드 서버**: https://api.example.local
- **백엔드 인증 서버**: https://auth.example.local
- **프론트엔드 서버**: https://example.local
- **프론트엔드 인증 서버**: https://auth.example.local/ui
- **개발 환경 (로컬)**: 
  - Backend: http://localhost:8000
  - Backend Auth: http://localhost:8090
  - Frontend: http://localhost:3000
  - Frontend Auth: http://localhost:5000

### API 문서
- **백엔드 서버 Swagger URL**: https://api.example.local/api/v1/docs
- **백엔드 인증 서버 Swagger URL**: https://auth.example.local/api/v1/docs
- **백엔드 서버 OpenAPI Spec**: https://api.example.local/api/v1/openapi.json
- **백엔드 인증 서버 OpenAPI Spec**: https://auth.example.local/api/v1/openapi.json
- **로컬 개발 환경**:
  - Backend Swagger: http://localhost:8000/docs
  - Backend Auth Swagger: http://localhost:8090/docs
  - OpenAPI JSON: http://localhost:8000/openapi.json
  - OpenAPI YAML: `./api-specs/openapi.yaml` (다운로드된 파일)

### 인증 정보
- **인증 방식**: JWT Bearer Token
- **토큰 위치**: Cookie (access_token, refresh_token)
- **토큰 만료**: Access Token 30분, Refresh Token 7일

## 테스트 환경 설정

### Frontend
```yaml
base_url: http://localhost:3000
test_user:
  email: test@example.com
  password: Test123!@#
admin_user:
  email: admin@example.com
  password: Admin123!@#
```

### Backend API
```yaml
base_url: http://localhost:8000
api_prefix: /api/v1
headers:
  Content-Type: application/json
  Accept: application/json
```

### Database
```yaml
test_db: postgresql://user:pass@localhost:5432/testdb
reset_before_test: true
```

## 시나리오 정보

### 시나리오 이름
[시나리오 이름을 입력하세요]

### 시나리오 설명
[시나리오의 목적과 테스트 범위를 설명하세요]

### 사전 조건
- [ ] 테스트 사용자 계정 생성
- [ ] 필요한 권한 설정
- [ ] 테스트 데이터 준비

### 테스트 데이터
```json
{
  "valid_user": {
    "email": "test@example.com",
    "password": "Test123!@#"
  },
  "invalid_user": {
    "email": "invalid@example.com",
    "password": "wrong_password"
  },
  "test_data": {
    // 추가 테스트 데이터
  }
}
```

## 시퀀스 다이어그램

```mermaid
sequenceDiagram
    participant Actor1
    participant Actor2
    participant Actor3
    
    Note over Actor1: 시나리오 시작
    Actor1->>Actor2: 액션 설명
    Actor2->>Actor3: API 호출 (메소드 경로)
    Actor3-->>Actor2: 응답
    Note over Actor1: 시나리오 종료
```

## API 엔드포인트 상세

### 1. 로그인 API
- **Endpoint**: POST /api/v1/users/login
- **Swagger**: http://localhost:8000/docs#/authentication/login
- **Request Body**:
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Response**:
  ```json
  {
    "user_info": {
      "id": "string",
      "email": "string",
      "name": "string"
    },
    "message": "로그인 성공"
  }
  ```
- **Cookies**: access_token, refresh_token

### 2. [다른 API 이름]
- **Endpoint**: [METHOD] /api/v1/[path]
- **Swagger**: [Swagger URL]
- **Request/Response**: [상세 내용]

## 테스트 케이스

### 정상 케이스
1. **TC001**: [테스트 케이스 이름]
   - 입력: [입력 데이터]
   - 기대 결과: [예상 결과]
   - 검증 항목: [체크 포인트]

### 예외 케이스
1. **TC002**: [예외 케이스 이름]
   - 입력: [잘못된 입력]
   - 기대 결과: [에러 응답]
   - 검증 항목: [에러 코드, 메시지]

## 모킹 설정

### 외부 서비스
```yaml
mock_services:
  - name: Payment Gateway
    url: https://payment.example.com
    mock_response: ./mocks/payment_success.json
  
  - name: Email Service
    url: https://email.example.com
    mock_response: ./mocks/email_sent.json
```

### 데이터베이스
```yaml
mock_data:
  users:
    - id: 1
      email: test@example.com
      encrypted_id: "encrypted_string"
  
  user_info:
    - user_id: 1
      name: "테스트 사용자"
```

## 테스트 실행 설정

### 환경 변수
```bash
TEST_ENV=local
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
TEST_TIMEOUT=30000
```

### 테스트 그룹
- `@smoke` - 기본 동작 확인
- `@regression` - 전체 회귀 테스트
- `@security` - 보안 관련 테스트
- `@performance` - 성능 테스트

## 검증 항목 체크리스트

### 기능 검증
- [ ] 정상 플로우 동작
- [ ] 에러 처리
- [ ] 데이터 검증
- [ ] 상태 변경 확인

### 보안 검증
- [ ] 인증/인가 처리
- [ ] 입력값 검증
- [ ] SQL Injection 방어
- [ ] XSS 방어

### 성능 검증
- [ ] 응답 시간 (< 1초)
- [ ] 동시 사용자 처리
- [ ] 메모리 사용량

## 참고 사항

### 알려진 이슈
- [이슈 설명 및 우회 방법]

### 관련 문서
- [API 설계 문서 링크]
- [테스트 전략 문서]
- [보안 가이드라인]

### 담당자
- **개발**: [개발자 이름]
- **QA**: [QA 담당자]
- **검토**: [검토자]