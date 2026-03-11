# Edge Posture Monitor

센서 기반 자세 분석 시스템 (Edge AI 기반 자세 모니터링 시스템)

이 프로젝트는 사용자의 앉은 자세를 실시간으로 분석하고,
자세 점수 및 자세 리포트를 생성하는 스마트 자세 모니터링 시스템이다.

센서 데이터는 STM32에서 수집되며 Raspberry Pi에서 분석을 수행한다.

---

# 1. 프로젝트 개요

Edge Posture Monitor는 장시간 앉아서 작업하는 환경에서
사용자의 자세를 분석하고 잘못된 자세를 감지하기 위해 설계된 시스템이다.

이 시스템은 센서 데이터를 기반으로 사용자의 자세를 분류하고
자세 점수를 계산하여 리포트를 생성한다.

주요 기능

- 실시간 자세 감지
- 자세 점수 계산
- 자세 패턴 분석
- 분 단위 자세 리포트 생성
- 하루 단위 자세 리포트 생성

---

# 2. 시스템 구조

전체 시스템은 다음과 같은 구조로 구성된다.

Mobile App
     │
     │ WiFi (HTTP / WebSocket)
     ▼
Raspberry Pi Controller
     │
     │ UART
     ▼
STM32 Sensor Node
     │
     ▼
압력 센서 / ToF 센서 / 기타 센서

---

# 3. 데이터 처리 파이프라인

Sensor Data
     │
     ▼
SensorReceiver
     │
     ▼
PostureClassifier
     │
     ▼
PostureScoreEngine
     │
     ▼
ReportGenerator
     │
     ▼
SQLite Database

---

# 4. 주요 기능

## 실시간 자세 감지

센서 데이터를 기반으로 사용자의 자세를 실시간으로 분류한다.

지원되는 자세 유형

- normal
- turtle_neck
- forward_lean
- reclined
- side_slouch
- leg_cross_suspect
- thinking_pose
- perching

---

## 자세 점수 계산

각 자세 상태를 기반으로 자세 점수를 계산한다.

평가 요소

- 목 각도
- 허리 기울기
- 상체 중심

---

## STAND 감지

사용자가 자리에서 일어나는 경우를 감지한다.

STAND 감지 시

- 측정 자동 중지
- 재측정 여부 선택 가능

---

## 자세 리포트 생성

시스템은 다음 3단계의 리포트를 생성한다.

1. 실시간 자세 상태
2. 분 단위 자세 리포트
3. 하루 단위 자세 리포트

예시 데이터

- avg_score
- total_sitting_sec
- dominant_posture
- good_posture_ratio
- bad_posture_ratio

---

# 5. 데이터베이스 구조

시스템은 SQLite 데이터베이스를 사용한다.

사용되는 테이블

- users
- baselines
- sessions
- minute_reports
- daily_reports

각 테이블의 역할

users  
사용자 프로필 정보 저장

baselines  
사용자 자세 기준값 저장

sessions  
측정 세션 기록

minute_reports  
분 단위 자세 분석 결과

daily_reports  
하루 단위 자세 분석 결과

---

# 6. Mock 테스트 환경

실제 STM32 하드웨어 없이 테스트할 수 있도록
Fake STM32 환경이 제공된다.

사용 파일
tools/fake_stm32.py

이를 통해 다음 기능을 테스트할 수 있다.
	•	UART 통신
	•	자세 분석 로직
	•	리포트 생성
	•	데이터베이스 저장

---

# 7. API 인터페이스

Raspberry Pi는 모바일 앱과 통신하기 위한 HTTP API를 제공한다.

주요 엔드포인트
  • GET  /health
  • GET  /meta
  • POST /command
  • WS   /ws

세부 명세는 아래 문서에 정리되어 있다.
docs/api_spec.md

---

# 8. 문서

프로젝트 관련 상세 문서는 docs 폴더에 정리되어 있다.
  • docs/system_architecture.md
  • docs/api_spec.md
  • docs/test_checklist.md

---

# 9. 기술 스택

하드웨어

- STM32
- Raspberry Pi

소프트웨어

- Python
- SQLite
- UART 통신
- WebSocket
- HTTP API

---

# 10. 향후 개발 계획

- 실제 센서 하드웨어 연동
- 모바일 앱 UI 개발
- 자세 교정 피드백 기능
- 장기 자세 분석 기능

---

# 11. 개발자

권혁준

AI / Embedded Systems

