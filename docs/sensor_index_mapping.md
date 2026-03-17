# Sensor Index Mapping Spec

## 문서 목적

이 문서는 STM32와 Raspberry Pi가 동일한 센서 인덱스 기준을 사용하도록 하기 위한 기준 문서이다.

본 문서의 인덱스 정의는 다음 영역에서 공통으로 사용된다.

- STM32 펌웨어 packet packing
- RPi packet parser
- RPi sensor mapper
- feature extraction
- posture analysis
- calibration logic
- debugging / logging

---

# 전체 센서 구성 요약

현재 시스템에서 Raspberry Pi가 받는 주요 센서 데이터는 다음과 같다.

1. Loadcell 12채널
2. Spine ToF 4채널
3. 3D ToF 32채널
4. MPU6050 2채널

---

# 1. Loadcell Index Mapping

Loadcell 데이터는 총 12개 채널로 구성된다.

자료형:
- `int32`

특징:
- STM32에서 tare 적용
- STM32에서 scaling 적용
- 좌판 3선식 pair는 STM32에서 정규화된 값으로 전달

## Index 정의

| Index | 이름 | 물리 위치 | 비고 |
|------|------|-----------|------|
| 0 | back_right_top | 등판 우측 상단 | 4선식 |
| 1 | back_right_upper_mid | 등판 우측 상부 중간 | 4선식 |
| 2 | back_right_lower_mid | 등판 우측 하부 중간 | 4선식 |
| 3 | back_right_bottom | 등판 우측 하단 | 4선식 |
| 4 | back_left_top | 등판 좌측 상단 | 4선식 |
| 5 | back_left_upper_mid | 등판 좌측 상부 중간 | 4선식 |
| 6 | back_left_lower_mid | 등판 좌측 하부 중간 | 4선식 |
| 7 | back_left_bottom | 등판 좌측 하단 | 4선식 |
| 8 | seat_rear_right | 좌판 후방 우측 | 3선식 pair normalized |
| 9 | seat_front_right | 좌판 전방 우측 | 3선식 pair normalized |
| 10 | seat_rear_left | 좌판 후방 좌측 | 3선식 pair normalized |
| 11 | seat_front_left | 좌판 전방 좌측 | 3선식 pair normalized |

---

## Loadcell 그룹 구조

### 등판(back)
- 0~3: 우측 등판
- 4~7: 좌측 등판

### 좌판(seat)
- 8: 우측 뒤
- 9: 우측 앞
- 10: 좌측 뒤
- 11: 좌측 앞

---

## Loadcell 해석 원칙

### 등판 4선식
등판 로드셀은 개별 채널 기준으로 해석한다.

### 좌판 3선식
좌판 로드셀은 물리적으로 2개 1세트 구조이나, RPi에는 이미 STM32에서 정규화된 채널값으로 전달된다.

즉 RPi는 다음과 같이 해석한다.

- 8 = seat_rear_right의 최종 채널값
- 9 = seat_front_right의 최종 채널값
- 10 = seat_rear_left의 최종 채널값
- 11 = seat_front_left의 최종 채널값

RPi는 좌판 채널에 대해 추가 pair 결합을 수행하지 않는다.

---

# 2. Spine ToF Index Mapping

Spine ToF 데이터는 총 4채널이다.

자료형:
- `uint16`

용도:
- 등판 거리 변화
- 척추 곡률 추정
- 등판 밀착도 분석

## Index 정의

| Index | 이름 | 물리 위치 |
|------|------|-----------|
| 0 | spine_upper | 등판 상단 |
| 1 | spine_upper_mid | 등판 상부 중간 |
| 2 | spine_lower_mid | 등판 하부 중간 |
| 3 | spine_lower | 등판 하단 |

---

# 3. 3D ToF Grid Mapping

3D ToF 데이터는 총 32채널이다.

자료형:
- `uint16`

센서:
- VL53L8CX 기반

용도:
- 머리/목 위치 요약
- 거북목 관련 feature
- 좌우 비대칭 분석

## 현재 사용 원칙

현재 RPi에서는 32개 raw grid 전체를 직접 classifier에 넣지 않고, 다음 두 단계로 처리한다.

1. raw grid 보존
2. summary feature 생성

예:
- mean
- min
- max
- left_mean
- right_mean
- lr_diff

## 3D ToF Sensors

헤드레스트 하단에는 **두 개의 ToF 센서**가 설치되어 있다.
각 센서는 **4x4 grid (16 pixel)** 데이터를 생성한다.
따라서 packet에 포함되는 총 ToF grid 값은 다음과 같다.

`2 esnsors x 16 valuse = 32 values`

즉 packet에는 **총 32개의 ToF grid 값**이 포함된다.

자료형:
`uint16 x 32`

---

## Sensor 구성

| Sensor | 위치 | Grid |
|------|------|------|
| ToF_A | 헤드레스트 우측 | 4×4 |
| ToF_B | 헤드레스트 좌측 | 4×4 |

---

## Packet 배열 구조

`[ToF_A grid 16 values] + [ToF_B grid 16 values]`

즉 packet 내부 배열은 다음과 같다
```text
0~15: ToF_A
16~31: ToF B
```

---

## 3D ToF 배열 해석 주의

현재 32개 grid의 정확한 물리 배열 순서(row-major / column-major / 좌우 반전 여부)는 STM32 펌웨어 문서와 반드시 일치해야 한다.

즉 아래 항목은 별도 확정 필요:

- grid index 0의 물리 위치
- 좌/우 절반을 어떤 기준으로 나누는지
- 상/하 방향이 뒤집히지 않았는지

현재 RPi 요약 로직은 다음의 단순 가정을 사용한다.

- 앞 16개 = left half
- 뒤 16개 = right half

이 가정은 추후 실제 센서 배열 문서 기준으로 수정될 수 있다.

---

# 4. MPU6050 Index Mapping

MPU6050 관련 데이터는 총 2채널이다.

자료형:
- `int16`

단위:
- degree(도)

특징:
- 가속도 기반 pitch 각도
- STM32에서 degree 정수로 변환 후 전송
- 자이로/칼만필터/상보필터는 현재 미적용
- 내부 DLPF 적용

## Index 정의

| Index | 이름 | 설명 |
|------|------|------|
| 0 | right_pitch_deg | 우측 센서 기준 pitch |
| 1 | left_pitch_deg | 좌측 센서 기준 pitch |

RPi에서는 추가로 아래 값을 생성한다.

- `pitch_fused_deg = (right + left) / 2`
- `pitch_lr_diff_deg = abs(right - left)`

---

# 5. RPi Semantic Mapping 규칙

RPi `sensor_mapper.py`는 packet parser 결과를 다음 semantic structure로 변환한다.

## Loadcell

```python
{
  "back_right": {
    "top": ...,
    "upper_mid": ...,
    "lower_mid": ...,
    "bottom": ...,
  },
  "back_left": {
    "top": ...,
    "upper_mid": ...,
    "lower_mid": ...,
    "bottom": ...,
  },
  "seat_right": {
    "rear": ...,
    "front": ...,
  },
  "seat_left": {
    "rear": ...,
    "front": ...,
  }
}
```

## ToF

```python
{
  "spine": {
    "upper": ...,
    "upper_mid": ...,
    "lower_mid": ...,
    "lower": ...,
  },
  "head_raw": [...32 values...],
  "head_summary": {
    "mean": ...,
    "min": ...,
    "max": ...,
    "left_mean": ...,
    "right_mean": ...,
    "lr_diff": ...,
  }
}
```

## IMU

```python
{
  "right_pitch_deg": ...,
  "left_pitch_deg": ...,
  "pitch_fused_deg": ...,
  "pitch_lr_diff_deg": ...,
}
```

---

# 6. Feature Extraction 연계 규칙

RPi feature extractor는 숫자 index를 직접 사용하지 않는다.
반드시 semantic mapping 이후의 field만 사용한다.

예:
- loadcell["seat_right"]["front"]
- tof["spine"]["upper"]
- imu["pitch_fused_deg"]

즉 feature extractor / monitoring / posture flags / classifier는 sensor index를 몰라야 한다.

---

# 7. 변경 관리 원칙

센서 순서, 위치, wiring, scaling 방식이 변경되면 가장 먼저 아래 두 파일을 수정해야 한다.
1.	docs/sensor_index_mapping.md
2.	src/sensor/sensor_mapper.py

그 이후에 필요한 경우만 다음을 수정한다.
- feature_extractor.py
- monitoring_metrics.py
- posture_flags.py
- posture_classifier.py

즉 sensor physical change는 mapper 계층에서 먼저 흡수하는 것을 원칙으로 한다.

---

# 8. 검증 체크리스트

센서 인덱스 변경 또는 실보드 연동 시 아래를 확인한다.
- 등판 좌/우가 뒤바뀌지 않았는가
- 좌판 전/후가 뒤바뀌지 않았는가
- spine ToF 상/하가 뒤바뀌지 않았는가
- 3D ToF 좌/우 해석이 실제 물리 배치와 일치하는가
- MPU pitch 부호가 기대 방향과 일치하는가
- 좌판 하중 변화가 seat_front/seat_rear에 올바르게 반영되는가
- 기대기 동작 시 back_total이 증가하는가

---

# 9. 현재 기준 요약

현재 기준에서 RPi는 다음을 전제로 한다.
- Loadcell 12개는 STM32에서 이미 유의미한 채널값으로 정리됨
- Spine ToF 4개는 상/중상/중하/하 순서
- 3D ToF 32개는 raw grid + summary 방식 사용
- MPU6050 2개는 degree 단위 pitch 값
- Sensor index 자체는 mapper 아래 계층에서만 직접 사용
