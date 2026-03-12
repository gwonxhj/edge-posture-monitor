# POSTURE AI System Architecture

## 1. Overview

POSTURE AI는 사용자의 앉은 자세를 실시간으로 분석하고 장시간의 자세 패턴을 기록하여 리포트를 생성하는 시스템이다.

본 시스템은 다음 구성요소로 이루어진다.

- Mobile App / Client
- Raspberry Pi Controller
- STM32 Sensor Node
- Database
- Report Engine

센서 데이터는 STM32에서 수집되어 UART를 통해 Raspberry Pi로 전달되며,  
Raspberry Pi에서 자세 분류 및 리포트 생성이 수행된다.

---

# 2. System Architecture
```text
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
            │ Sensor Input
            ▼
      Pressure / ToF / IMU
```
---

# 3. Raspberry Pi Software Architecture
```text
src/
 ├ communication
 │   ├ wifi_server.py
 │   ├ command_sender.py
 │   └ uart_protocol.py
 │
 ├ sensor
 │   └ sensor_receiver.py
 │
 ├ core
 │   ├ posture_classifier.py
 │   └ posture_score.py
 │
 ├ session
 │   ├ session_manager.py
 │   └ calibration.py
 │
 ├ runtime
 │   └ measurement_runtime.py
 │
 ├ report
 │   └ report_generator.py
 │
 └ storage
     └ database_manager.py
```
---

# 4. Runtime Flow

시스템 동작 순서는 다음과 같다.

1. Raspberry Pi 부팅
2. STM32 UART handshake 수행
3. 앱에서 사용자 프로필 선택
4. 캘리브레이션 수행 (필요 시)
5. 측정 시작
6. 실시간 자세 분석
7. STM32가 STAND 이벤트 전송
8. RPi가 앱에 stand_event 전달
9. 사용자가 재측정 여부 선택
10. 측정 재개 또는 세션 종료
11. 리포트 생성 및 DB 저장

---

# 5. Posture Analysis Pipeline
```text
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
DatabaseManager
```
---

# 6. Report Metrics

시스템은 다음 지표를 계산한다.

| Metric | Description |
|------|-------------|
| avg_score | 평균 자세 점수 |
| total_sitting_sec | 총 착석 시간 |
| dominant_posture | 가장 많이 나타난 자세 |
| dominant_posture_ratio | 해당 자세 비율 |
| good_posture_ratio | 정상 자세 비율 |
| bad_posture_ratio | 비정상 자세 비율 |

---

# 7. Data Storage

SQLite 기반으로 다음 데이터를 저장한다.

- 사용자 정보
- 캘리브레이션 데이터
- 세션 기록
- 분 단위 리포트
- 일일 누적 리포트

---

# 8. Hardware Integration

STM32는 다음 센서 데이터를 RPi로 전송한다.

- Seat pressure sensors (좌석 하중 분포)
- Back pressure sensors (등받이 압력)
- ToF distance sensors (목 / 척추 거리 측정)
- IMU gyro data (상체 기울기)

센서 데이터는 STM32에서 전처리된 후 UART 프로토콜로 RPi에 전달된다.

---

# 9. Mock Testing

실제 하드웨어 없이 시스템을 검증하기 위해  
`fake_stm32.py` 기반 mock 테스트 환경을 구축하였다.

이 mock 노드는 STM32의 UART 프로토콜을 시뮬레이션하며
센서 데이터 스트림과 STAND 이벤트를 발생시킨다.

이를 통해 다음 기능을 사전 검증하였다.

- UART handshake
- posture data stream
- stand detection
- resume / stop flow
- report generation

# 10. Measurement Stop Policy

### Pause Measurement

측정 중 사용자가 일시정지를 요청하면 RPi는 STM32에 STOP 명령을 전송한다.  
STM32는 측정을 중단하고 idle 상태로 전환한다.

이 경우 세션은 종료되지 않으며 pause 상태로 유지된다.  
사용자는 이후 resume_measurement 또는 quit_measurement 명령을 선택할 수 있다.


### Quit Measurement

측정 중 사용자가 세션 종료를 요청하면 RPi는 STM32에 STOP 명령을 전송한다.  
STM32는 측정을 중단하고 idle 상태로 전환한다.

RPi는 현재까지 누적된 데이터를 기반으로 세션 리포트를 생성하고  
SQLite 데이터베이스에 저장한다.


### STAND Event Handling

STM32가 STAND 이벤트를 전송하면 이미 측정이 중단된 상태로 간주한다.

RPi는 앱에 stand_event를 전달하며 사용자는 다음 중 하나를 선택할 수 있다.

- resume_after_stand (재측정)
- decline_resume_after_stand (세션 종료)
- quit_measurement (즉시 종료)