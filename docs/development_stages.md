# Development Stages

## 1. Overview

본 프로젝트는 STM32 센서 노드와 Raspberry Pi 엣지 런타임을 분리한 구조에서,
실시간 자세 분석 시스템을 단계적으로 검증하고 확장하는 방식으로 개발되었다.

전체 개발은 크게 두 단계로 나뉜다.

1. Mock-based Validation  
   - 실제 STM32 하드웨어 없이 Fake STM32를 이용해 전체 파이프라인을 사전 검증하는 단계

2. Real Hardware Integration  
   - 실제 STM32 센서 입력을 Raspberry Pi에 연결하여, 실측 데이터 기반으로 센서 해석 및 자세 판별 로직을 보정하는 단계

이 문서는 각 개발 단계에서 무엇을 검증했고,
실제 하드웨어 연동 시 어떤 부분이 변경되는지를 정리한다.

---

## 2. Stage 1 - Mock-based Validation

### 2-1. Purpose

실제 센서 연동 이전에 시스템 전체 구조가 정상적으로 동작하는지 검증하기 위해
Mock 기반 테스트 환경을 먼저 구축하였다.

이 단계의 목적은 다음과 같다.

- UART 통신 파이프라인이 정상 동작하는지 검증
- Raspberry Pi 런타임의 상태 전이 로직을 검증
- 자세 feature 추출 및 posture flag 로직이 의도대로 동작하는지 검증
- session / minute / daily report 생성 및 저장 흐름을 검증
- 실제 하드웨어 연동 전에 backend/app/report 구조를 안정화

### 2-2. What was validated

Mock STM32 기반으로 다음 항목들을 검증하였다.

- UART handshake (READY / ACK / LINK_OK)
- calibration flow
- measurement flow
- STAND event 처리
- pause / resume / recalibration / quit command flow
- real-time posture analysis pipeline
- report generation pipeline
- SQLite storage pipeline
- WebSocket / HTTP API 기반 앱 연동 구조

### 2-3. Key outputs

이 단계에서 다음 결과를 확보하였다.

- Fake STM32 기반 hardware-independent test environment 구축
- posture별 단일 시나리오 검증 완료
- dominant posture / duration 집계 로직 검증 완료
- enhanced report(rule-based) 생성 구조 구축
- 디버깅용 sensor / feature / flag 관측 로직 추가
- 실연동 전 Raspberry Pi 서버 환경 구성 완료

### 2-4. Limitations

Mock 단계는 전체 파이프라인을 검증하는 데 매우 유효했지만,
실제 하드웨어 데이터의 물리적 특성을 완전히 반영하지는 못한다.

대표적인 한계는 다음과 같다.

- 실제 Loadcell 값 분포와 Mock 값 분포가 다를 수 있음
- 실제 ToF 센서의 거리 노이즈 및 좌우 편차가 반영되지 않음
- 실제 MPU6050의 축 방향 / drift / scale 이슈가 반영되지 않음
- thinking_pose처럼 posture 경계가 모호한 경우, 실측 데이터 기반 추가 보정이 필요함
- STAND threshold 및 calibration baseline이 실제 착석 환경과 다를 수 있음

---

## 3. Stage 2 - Real Hardware Integration

### 3-1. Purpose

이 단계에서는 실제 STM32 센서 데이터를 Raspberry Pi에 연결하여,
Mock 환경에서 검증한 파이프라인이 실제 하드웨어에서도 안정적으로 동작하는지 검증한다.

핵심 목적은 다음과 같다.

- 실제 UART packet이 정상적으로 수신되는지 검증
- 센서 raw 값이 기대 범위로 들어오는지 확인
- sensor mapping / feature extraction / delta 계산이 실제 데이터에서도 유효한지 검증
- posture flag threshold를 실측 데이터 기준으로 보정
- calibration / STAND / posture transition 로직을 실제 환경에 맞게 조정

### 3-2. Expected changes

실제 하드웨어 연동 단계에서는 다음 부분의 코드 또는 파라미터가 변경될 수 있다.

- UART packet parsing 세부 처리
- sensor_mapper의 채널 순서 / 좌우 매핑 / 단위 변환
- feature_extractor의 feature 계산 방식
- posture_flags의 threshold
- calibration baseline 처리 방식
- STAND 감지 조건
- monitoring metric 해석 범위
- report wording 또는 enhanced report 기준

### 3-3. Why these changes are needed

Mock 단계의 값은 의도적으로 설계된 synthetic sensor value이기 때문에,
실제 하드웨어 입력과는 분포와 노이즈 특성이 다를 수 있다.

따라서 실제 센서 연동 단계에서는 다음 이유로 코드 보정이 필요할 수 있다.

- 실제 센서 raw 값의 scale 차이
- 채널 배치 또는 방향성 차이
- baseline 대비 delta 크기 차이
- posture 간 경계가 Mock보다 덜 명확함
- 특정 posture에서 복합 flag가 동시에 발생할 가능성이 높음
- STAND / SIT 이벤트 기준이 실제 하중 변화와 다를 수 있음

즉, Stage 2의 목표는 구조를 새로 만드는 것이 아니라,
Stage 1에서 검증한 구조를 실제 센서 특성에 맞게 보정하는 것이다.

### 3-4. Validation plan

실연동 단계에서는 아래 순서로 검증을 수행한다.

1. UART handshake 확인
2. 실제 센서 raw 값 확인
3. sensor mapping 결과 확인
4. feature / delta 값 확인
5. posture flag 및 report posture 확인
6. calibration 결과 확인
7. STAND / resume 흐름 확인
8. session / report / DB 저장 확인

이 과정에서 debug_sensor payload, DEBUG FEATURE, DEBUG FLAGS,
SNAPSHOT[POSTURE_CHANGED] 로그를 활용해 원인 레이어를 분리한다.

---

## 4. Design Principle

본 프로젝트는 처음부터 실제 하드웨어에만 의존하지 않고,
Mock 기반 검증을 통해 전체 시스템 구조를 먼저 안정화한 뒤
실제 하드웨어 연동으로 확장하는 방식을 채택하였다.

이 방식의 장점은 다음과 같다.

- 센서 미연동 상태에서도 backend/app/report를 먼저 개발 가능
- 실제 하드웨어 문제와 소프트웨어 구조 문제를 분리 가능
- 테스트 재현성이 높아짐
- 실연동 이후에도 regression test 용도로 Mock 환경을 계속 활용 가능

즉, Mock 코드는 임시 코드가 아니라,
실제 하드웨어 통합 이후에도 유지할 가치가 있는 테스트 인프라이다.

---

## 5. Summary

본 프로젝트는 다음 순서로 진화한다.

- Stage 1: Mock STM32 기반 전체 파이프라인 검증 완료
- Stage 2: 실제 STM32 센서 데이터 연동 및 threshold / mapping 보정 진행
- Stage 3: 실측 데이터 기반 모델/리포트 고도화 예정

현재 저장소의 main 라인은 최종 시스템 방향으로 계속 발전시키되,
Mock validation 단계는 별도 문서와 git tag를 통해 보존한다.