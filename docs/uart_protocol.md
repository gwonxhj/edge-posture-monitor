# UART Protocol

## 개요 (Overview)

이 문서는 **STM32 ↔ Raspberry Pi 간 UART 통신 규약**을 정의한다.  
본 시스템은 하나의 UART 링크에서 **두 가지 통신 모드**를 사용한다.

1️⃣ **ASCII Control Mode**  
2️⃣ **Binary Sensor Stream Mode**

두 모드는 시스템 상태에 따라 명확히 분리되어 동작해야 한다.

---

# UART 연결 정보

- 연결: STM32 ↔ Raspberry Pi
- 통신 방식: UART Full Duplex
- Baud Rate: **921600**

---

# 통신 모드

## 1️⃣ ASCII Control Mode

ASCII 문자열 기반 제어 메시지를 사용하는 모드이다.

사용되는 상황:

- UART 초기 Handshake
- 착석 확인 (`CHK_SIT`)
- 측정 시작/중단
- 캘리브레이션 제어
- STAND 이벤트
- 기타 상태 제어

ASCII 메시지는 **newline (`\n`) 기준 한 줄 단위 메시지**로 전송한다.

예시:
```text
READY
ACK
LINK_OK
CHK_SIT
SIT
GO
STOP
CAL
STAND
```

⚠️ 중요

ASCII Control Mode 동안에는 **Binary Sensor Stream (`DAT:` / `CAL:`)** 이 동시에 전송되지 않아야 한다.

---

## 2️⃣ Binary Sensor Stream Mode

센서 데이터를 연속적으로 전송하는 모드이다.

두 가지 스트림이 존재한다.

| Stream | 설명 |
|------|------|
| `DAT:` | 실시간 측정 데이터 |
| `CAL:` | 캘리브레이션 데이터 |

Binary frame은 **고정 길이 프레임**으로 전송된다.

---

# ASCII Control Message 정의

## STM32 → Raspberry Pi

### READY

STM32 부팅 완료 후 UART 통신 준비 완료 상태
`READY`

---

### LINK_OK

RPi가 `ACK`를 보낸 후 링크가 정상적으로 연결되었음을 알림
`LINK_OK`

---

### SIT

RPi가 `CHK_SIT`을 보냈을 때 STM32가 사용자가 앉아있는 것을 확인하면 전송
`SIT`

---

### STAND

사용자가 의자에서 **일어났다고 STM32가 판단했을 때 전송**
`STAND`

특징

- Binary stream과 무관한 **독립 이벤트**
- ASCII 문자열 형태로 전송
- 보통 다음 상황에서 발생

예
```text
DAT: stream 중
       ↓
사용자가 5초 이상 일어남
       ↓
STM32 내부 판단
       ↓
STAND\n 전송
       ↓
STM32 측정 루프 종료
```

---

### CAL_DONE (Optional)

캘리브레이션 종료 알림 메시지
`CAL_DONE`

현재 설계 기준

- **필수 메시지는 아님**
- RPi가 캘리브레이션 시간을 직접 관리하기 때문에  
  STM32에서 반드시 보낼 필요는 없음
- 향후 펌웨어 설계에 따라 추가될 수 있음

---

## Raspberry Pi → STM32

### ACK

STM32 `READY`에 대한 응답
`ACK`

---

### CHK_SIT

STM32에게 **사용자 착석 여부 확인 요청**
`CHK_SIT`

STM32 동작
```text
CHK_SIT 수신
    ↓
로드셀 하중 확인
    ↓
착석 상태이면
    ↓
SIT 전송
```

---

### GO

측정 시작 요청
`GO`

STM32 동작
```text
GO 수신
   ↓
측정 루프 진입
   ↓
DAT: binary stream 시작
```

---

### STOP

측정 중단 요청
`STOP`

STM32 동작
```text
STOP 수신
↓
측정 루프 탈출
↓
Idle 상태 진입
↓
CHK_SIT 대기
```

---

### CAL

캘리브레이션 시작 요청
`CAL`

STM32 동작
```text
CAL 수신
↓
캘리브레이션 루프 진입
↓
CAL: binary stream 시작
```

---

# Binary Sensor Packet

Binary sensor packet은 **고정 길이 프레임**으로 구성된다.

Frame 구조
```text
[128 bytes data] + [1 byte checksum]
```

총 프레임 크기
`129 bytes`

---

# Binary Frame Header

Binary frame은 항상 **4 byte ASCII header**로 시작한다.

| Header | 의미 |
|------|------|
| `DAT:` | 실시간 측정 데이터 |
| `CAL:` | 캘리브레이션 데이터 |

예
```text
DAT:
CAL:
```

---

# Sensor Packet Data Layout

현재 STM32 펌웨어에서 사용하는 payload 구조

Python struct format
`<4s 12i 4H 32H 2h`

구성 요소

| Field | 설명 |
|------|------|
| header | `DAT:` 또는 `CAL:` |
| loadcells | 로드셀 값 |
| spine ToF | 등판 ToF 센서 |
| 3D ToF | 헤드레스트 ToF 센서 |
| IMU | MPU6050 |

⚠️ 주의

- STM32에서 **이미 tare / scale 처리된 값**을 전송
- RPi에서는 추가 보정 없이 feature extraction에 사용

---

# Checksum

Checksum은 **128 byte data 전체 XOR 방식**을 사용한다.

계산 방식
`checksum = XOR(all 128 data bytes)`

RPi 동작
```text
if received_checksum != calc_checksum(data):
packet discard
```

---

# Packet Loss Handling

현재 구현 기준

- sequence number 없음
- timestamp 없음

따라서 RPi는 다음 방식으로 처리

- checksum mismatch → packet discard
- parser sync 깨질 경우 → header 재탐색

---

# STAND 이벤트 처리

STM32 내부 로직
```text
seat_weight_sum 계산
↓
5kg 이하 상태 지속
↓
5초 지속
↓
STAND\n 전송
↓
측정 루프 탈출
```

RPi 동작
```text
STAND 수신
↓
측정 종료 처리
↓
앱에게 이벤트 전달
↓
재시작 여부 결정
```

---

# Measurement Flow

## 측정 시작
```text
RPi -> CHK_SIT
STM32 -> SIT
RPi -> GO
STM32 -> DAT: stream 시작
```

---

# Recalibration Flow
```text
RPi -> STOP
STM32 측정 루프 탈출

RPi -> CHK_SIT
STM32 -> SIT

RPi -> CAL
STM32 -> CAL: stream 시작

RPi baseline 계산

RPi -> GO
STM32 -> DAT: stream 재개
```

CAL_DONE 메시지는 **옵션이며 현재 설계에서는 필수 아님**

---

# 핵심 설계 원칙

1️⃣ ASCII Control과 Binary Stream은 **동시에 사용하지 않는다**

2️⃣ `DAT:` / `CAL:` stream은 **측정 또는 캘리브레이션 상태에서만 전송**

3️⃣ STAND 이벤트는 **Binary stream과 독립적인 ASCII 이벤트**

4️⃣ `CHK_SIT` 구간에서는 **binary packet 전송 금지**

---

# 참고

센서 구성

- Loadcell
- VL53L8CX ToF
- MPU6050

RPi 처리

- Feature extraction
- Posture classification
- Score calculation
- Realtime monitoring

---

# Binary Sensor Packet Payload Layout

이 섹션은 STM32가 RPi로 전송하는 Binary Sensor Packet 내부 데이터 구조를 정의한다.

Binary packet은 다음 구조를 가진다.
`[128 bytes data] + [1 byte checksum]`

총 frame 크기
`129 bytes`
RPi에서는 이 128 byte data를 Python struct.unpack을 사용하여 파싱한다.

현재 사용되는 struct format
`<4s 12i 4H 32H 2h`
각 필드 의미는 다음과 같다.

## Packet Field Layout
| Index | Type | Count | Description |
| ------ | ------ | ------ | ------ |
| 0 | char[4] | 1 | Header (DAT: 또는 CAL:) |
| 1 | int32 | 12 | Loadcell / Force related values |
| 2 | uint16 | 4 | Spine ToF distance summary |
| 3 | uint16 | 32 | 3D ToF grid values |
| 4 | int16 | 2 | IMU tilt / orientation values |

## Detatiled Field Description

### Header

4 bytes ASCII header

가능한 값
```text
DAT:
CAL:
```

설명
| Header | 의미 |
| ------ | ------ |
| DAT: | 실시간 측정 데이터 |
| CAL: | 캘리브레이션 데이터 |

### Loadcell Data(12 x int32)

STM32에서 tare 및 scaling 처리된 로드셀 값

RPi에서는 다음 용도로 사용한다.
- 좌우 체중 분포 분석
- 전후 체중 분포 분석
- 착석 여부 판단
- posture feature extraction

로드셀 인덱스 매핑은 다음과 같다.
| Sensor Index | 위치 |
| ------ | ------ |
| 0 | 등판 우측 상단 |
| 1 | 등판 우측 하단 |
| 2 | 등판 좌측 상단 |
| 3 | 등판 좌측 하단 |
| 4 | 좌판 상단 좌 |
| 5 | 좌판 상단 우 |
| 6 | 좌판 중앙 좌 |
| 7 | 좌판 중앙 우 |
| 8 | 좌판 후방 우 |
| 9 | 좌판 전방 우 |
| 10 | 좌판 후방 좌 |
| 11 | 좌판 전방 좌 |

### Spine ToF(4 x uint16)

등판에 설치된 ToF 센서 요약 값

센서 위치
| Index | 위치 |
| ------ | ------ |
| 14 | 등판 상단 |
| 15 | 등판 중단 |
| 16 | 등판 하단 |
| 17 | 등판 추가 센서 |

용도
- 척추 곡률 변화 감지
- 등판 밀착 여부 분석

### 3D ToF Grid(32 x uint16)

헤드레스트 하단에 위치한 VL53L8CX 8x8 센서
전체 64 pixel 중 일부 요약 또는 downsample된 값 사용
현재 packet에는 32개 grid 값이 포함된다.

용도
- 머리 위치
- 목 기울기
- 거북목 감지

센서 위치
| Indel | 위치 |
| ------ | ------ |
| 12 | 헤드레스트 우측 |
| 13 | 헤드레스트 좌측 |

### IMU Data(2 x int16)

MPU6050 기반 기울기 값
| Field | 설명 |
| ------ | ------ |
| tilt_x | 좌우 기울기 |
| tilt_y | 전후 기울기 |

RPi에서는 다음 용도로 사용
- 상체 기울기 분석
- posture classifier feature

### Checksum

마지막 byte는 XOR checksum

계산 방법
`checksum = XOR(all 128 data bytes)`

RPi에서는 다음 방식으로 검증한다.
```text
if received_checksum != calc_checksum(data):
    packet discard
```

### Packet Example(Conceptual)

```text
DAT:
[loadcell data]
[spine tof]
[3d tof grid]
[imu tilt]
[checksum]
```

### Parsing Rule(RPi)

RPi는 다음 순서를 따른다.

1. Header 탐색(DAT: / CAL:)
2. 128 byte payload 확보
3. checksum 검증
4. struc unpack
5. semantic mapping

### Important Notes

1. Binary Packet 구조는 고정 길이이다.
2. ASCII control message와 binary stream은 동시에 전송하지 않는다.
3. STAND 이벤트는 binary packet 내부가 아닌 별도 ASCII 메시지로 전송된다.
4. CAL: packet은 캘리브레이션 중에만 발생한다.