# Runtime Sequence

이 문서는 Edge Posture Monitoring System의 실제 런타임 동작 흐름을 정의한다.

시스템은 다음 3가지 주요 흐름으로 구성된다.

1. Measurement Flow (기본 측정 흐름)
2. Recalibration Flow (재캘리브레이션)
3. STAND Flow (착석 해제 이벤트 처리)

---

# 1. Measurement Flow

사용자가 측정을 시작했을 때의 기본 동작 흐름

```mermaid
sequenceDiagram
    participant App
    participant RPi
    participant STM32

    App ->> RPi: start_measurement
    RPi ->> STM32: CHK_SIT
    STM32 -->> RPi: SIT

    RPi ->> STM32: GO
    STM32 -->> RPi: DAT stream start

    loop Realtime Processing
        STM32 -->> RPi: DAT packet

        RPi ->> RPi: parse_sensor_packet
        RPi ->> RPi: map_raw_packet
        RPi ->> RPi: extract_features
        RPi ->> RPi: classifier.predict
        RPi ->> RPi: detect_posture_flags
        RPi ->> RPi: score_engine.update
        RPi ->> RPi: report_generator.add_sample

        RPi -->> App: realtime status (WebSocket)
    end
```

---

# 2. Recalibration Flow

측정 중 재캘리브레이션 요청 시 동작 흐름

```mermaid
sequenceDiagram
    participant App
    participant RPi
    participant STM32

    App ->> RPi: start_calibration

    RPi ->> STM32: STOP
    STM32 -->> RPi: (measurement loop exit)

    RPi ->> STM32: CHK_SIT
    STM32 -->> RPi: SIT

    RPi ->> STM32: CAL
    STM32 -->> RPi: CAL stream start

    loop Calibration Data Collection
        STM32 -->> RPi: CAL packet
    end

    STM32 -->> RPi: CAL_DONE

    RPi ->> RPi: baseline 계산
    RPi ->> RPi: baseline 저장

    RPi ->> STM32: GO
    STM32 -->> RPi: DAT stream 재개
```

---

# 3. STAND Flow

사용자가 자리에서 일어났을 때 처리 흐름

```mermaid
sequenceDiagram
    participant STM32
    participant RPi
    participant App

    STM32 -->> RPi: STAND event

    RPi ->> App: stand event 전달
    RPi ->> RPi: measurement pause 상태 전환

    App ->> RPi: user decision

    alt resume
        RPi ->> STM32: CHK_SIT
        STM32 -->> RPi: SIT
        RPi ->> STM32: GO
        RPi ->> RPi: measurement resume
    else quit
        RPi ->> RPi: session 종료
        RPi ->> RPi: report 저장
    end
```

---

# 4. Data Processing Pipeline(Runtime 내부 처리)

센서 데이터는 다음과 같은 파이프라인으로 처리된다.

```mermaid
flowchart TD
    A[DAT Packet] --> B[parse_sensor_packet]
    B --> C[map_raw_packet]
    C --> D[extract_features]
    D --> E[classifier.predict]
    E --> F[detect_posture_flags]
    F --> G[score_engine.update]
    G --> H[report_generator.add_sample]
    H --> I[app_server.update_status]
```

---

# 5. 주요 설계 포인트

## 상태 기반 제어

시스템은 다음 상태를 기반으로 동작한다.

- WAIT_SIT
- CALIBRATING
- MEASURING
- PAUSED
- WAIT_RESTART_DECISION

## 통신 구조

- STM32 <-> RPi: UART(Binary + Control Message)
- RPi <-> App: HTTP / WebSocket

## 이벤트 기반 처리

- STAND 이벤트 -> 측정 중단 및 사용자 선택
- CAL_DONE 이벤트 -> 캘리브레이션 종료 신호

## 재캘리브레이션 특징

- 측정 중에도 수행 가능
- 기존 baseline을 새로운 baseline으로 교체
- 이후 측정은 새로운 기준으로 진행

---

# 6. 요약

이 시스템은 다음 특징을 가진다.

- 실시간 센서 데이터 처리 기반 자세 분석 시스템
- 상태 기반 제어 흐름
- 이벤트 기반 측정 제어(STAND / CAL_DONE)
- 재캘리브레이션 지원
- Edge 환경에서 독립적으로 동작 가능한 구조