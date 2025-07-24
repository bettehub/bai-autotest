# bai.ai.kr AutoTest

MCP 기반의 다이어그램 주도 테스트 자동화 프레임워크입니다. Mermaid 시퀀스 다이어그램으로부터 다양한 언어와 프레임워크의 테스트 코드를 자동으로 생성합니다.

## 🚀 주요 기능

- **📊 다이어그램 파싱**: Mermaid 시퀀스 다이어그램에서 테스트 시나리오 자동 추출
- **🔧 다중 언어 지원**: 10개 이상의 프로그래밍 언어 지원
- **🧪 다양한 테스트 프레임워크**: 각 언어별 주요 테스트 프레임워크 지원
- **🎨 커스텀 템플릿**: YAML/JSON 기반 사용자 정의 템플릿
- **🤖 MCP 서버**: AI 도구와 통합 가능한 Model Context Protocol
- **🇰🇷 한글 지원**: 한국어 액션 자동 인식 및 처리

## 📦 설치

```bash
pip install bai-autotest
```

## 📦 지원 언어 및 프레임워크

### 🔹 Python
- **Pytest** - 가장 인기 있는 Python 테스트 프레임워크
- **unittest** - Python 표준 라이브러리

### 🔹 JavaScript/TypeScript
- **Playwright** - 크로스 브라우저 E2E 테스트 (Chrome, Firefox, Safari)
- **Cypress** - 모던 웹 애플리케이션 E2E 테스트 (실시간 디버깅)
- **Jest + React Testing Library** - React 컴포넌트 단위 테스트

### 🔹 Java
- **JUnit 5** - Java 표준 테스트 프레임워크
- **Spring Boot Test** - Spring 애플리케이션 통합 테스트

### 🔹 기타 언어 (템플릿 지원)
- **Ruby**: RSpec, Minitest
- **Go**: testing 패키지
- **PHP**: PHPUnit
- **C#**: NUnit, xUnit
- **Kotlin**: JUnit, Kotest
- **Swift**: XCTest

## 🚀 빠른 시작

### 1. Mermaid 다이어그램 파싱

```python
from bai_test_mcp.parsers import MermaidParser

diagram = """
sequenceDiagram
    participant User
    participant Frontend
    participant API
    
    User->>Frontend: 로그인 클릭
    Frontend->>API: POST /login
    API-->>Frontend: JWT 토큰
    Frontend->>Frontend: 대시보드로 리다이렉트
"""

parser = MermaidParser()
scenarios = parser.parse(diagram)
```

### 2. 테스트 코드 생성

```python
from bai_test_mcp.generators import PlaywrightGenerator, CypressGenerator

# Playwright 테스트 생성
playwright_gen = PlaywrightGenerator()
playwright_test = playwright_gen.generate(scenarios[0])

# Cypress 테스트 생성 (Next.js용)
cypress_gen = CypressGenerator()
cypress_test = cypress_gen.generate(scenarios[0])

print(cypress_test.code)
```

### 3. MCP 서버 사용

```bash
# MCP 서버 시작
bai-autotest serve

# 다른 터미널에서 MCP 클라이언트 사용
bai-autotest parse --file auth-flow.md
bai-autotest generate --scenario login --framework playwright
bai-autotest generate --scenario login --framework cypress  # Next.js E2E 테스트
bai-autotest generate --scenario login --framework jest-rtl  # React 컴포넌트 테스트
```

### 4. 다양한 언어로 테스트 생성

```bash
# Java JUnit 테스트
bai-autotest generate auth-flow.md -f custom -l java --template java_junit

# Spring Boot 테스트
bai-autotest generate auth-flow.md -f custom -l java --template java_spring

# Ruby RSpec 테스트
bai-autotest generate auth-flow.md -f custom -l ruby --template ruby_rspec

# 사용 가능한 템플릿 보기
bai-autotest templates

# 커스텀 템플릿 사용
bai-autotest generate auth-flow.md -f custom -l kotlin --template ./my-template.yaml
```

## 🎯 Playwright vs Cypress

### Playwright
- **개발사**: Microsoft
- **특징**: 
  - ✅ 여러 브라우저 지원 (Chrome, Firefox, Safari, Edge)
  - ✅ 여러 언어 지원 (JS, TS, Python, C#, Java)
  - ✅ 빠른 실행 속도, CI/CD에 최적화
- **사용 시기**: 여러 브라우저 테스트, 다양한 언어 프로젝트

### Cypress
- **개발사**: Cypress.io
- **특징**:
  - ✅ 실시간 리로드와 시각적 디버깅
  - ✅ 타임 트래블 (각 단계별 스냅샷)
  - ✅ 자동 대기 및 재시도
  - ✅ 개발자 친화적 API
- **사용 시기**: JS/TS 프로젝트, 개발 중 테스트, Next.js/React 앱

## 🛠️ 커스텀 템플릿 예시

```yaml
# custom-template.yaml
name: "My Custom Test"
language: kotlin
framework: kotest
file_extension: ".kt"

imports: |
  import io.kotest.core.spec.style.DescribeSpec
  import io.kotest.matchers.shouldBe

test_start: |
  describe("${description}") {
    it("${method_name}") {

api_call: |
      val response = client.${method_lower}("${endpoint}")
      response.status shouldBe 200

test_end: |
    }
  }
```

## 📚 아키텍처

```
bai-autotest/
├── parsers/          # 다이어그램 파싱 모듈
│   ├── base.py      # 추상 파서 인터페이스
│   └── mermaid.py   # Mermaid 다이어그램 파서
├── generators/       # 테스트 코드 생성기
│   ├── base.py      # 추상 생성기 인터페이스
│   ├── playwright.py # Playwright 테스트 생성기
│   ├── pytest.py    # Pytest 생성기
│   ├── cypress.py   # Cypress 테스트 생성기 (Next.js E2E)
│   ├── jest_rtl.py  # Jest + RTL 생성기 (React 컴포넌트)
│   ├── custom.py    # 커스텀 템플릿 기반 생성기
│   └── templates/   # 빌트인 템플릿
│       ├── java_junit.yaml
│       ├── java_spring.yaml
│       └── react_testing_library.yaml
├── executors/        # 테스트 실행 엔진
│   └── runner.py    # 테스트 러너 인터페이스
└── mcp/             # MCP 서버 구현
    └── server.py    # MCP 프로토콜 핸들러
```

## 🔍 사용 예시

### 기본 제공 생성기
```bash
# Python Pytest
bai-autotest generate auth.md -f pytest

# JavaScript Playwright  
bai-autotest generate auth.md -f playwright

# React Testing Library
bai-autotest generate auth.md -f jest-rtl

# Cypress E2E
bai-autotest generate auth.md -f cypress
```

### 템플릿 기반 생성기
```bash
# Java JUnit
bai-autotest generate auth.md -f custom -l java --template java_junit

# Spring Boot
bai-autotest generate auth.md -f custom -l java --template java_spring

# 사용 가능한 템플릿 확인
bai-autotest templates
```

## 💡 특별 기능

- **한글 지원**: "로그인", "클릭", "입력" 등 한국어 액션 자동 인식
- **API 모킹**: 각 프레임워크에 맞는 API 모킹 코드 자동 생성
- **호환성**: 언어별 네이밍 컨벤션 자동 적용 (camelCase, snake_case)

## 💻 개발

```bash
# 저장소 클론
git clone https://github.com/bettehub/bai-autotest
cd bai-autotest

# 개발 모드로 설치
pip install -e .[dev]

# 테스트 실행
pytest

# 코드 포맷팅
black src tests
```

## 📄 라이선스

MIT 라이선스 - 자세한 내용은 LICENSE 파일을 참조하세요

## 🤝 기여

새로운 언어나 프레임워크 지원을 추가하고 싶으신가요? 템플릿을 만들어 PR을 보내주세요!