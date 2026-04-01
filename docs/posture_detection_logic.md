# Posture Detection Logic

이 문서는 Edge Posture Monitoring System에서 사용되는  
자세 판별 로직(Posture Classification Logic)을 설명한다.

본 시스템은 STM32에서 수집된 센서 데이터를 기반으로  
Raspberry Pi에서 자세를 분석하며, 현재 버전에서는  
Rule-based classification 방식을 사용한다.

---

# 1. Sensor Inputs

시스템은 다음 센서 데이터를 사용한다.

| Sensor | Description |
|------|-------------|
| Seat Pressure Sensors | 좌석 하중 분포 측정 |
| Back Pressure Sensors | 등받이 압력 측정 |
| ToF Distance Sensors | 목 / 척추 거리 측정 |
| IMU Sensors | 상체 기울기 측정 |

센서 데이터는 STM32에서 수집된 후 UART를 통해 Raspberry Pi로 전달된다.

---

# 2. Feature Extraction

본 시스템은 센서 raw 값을 직접 사용하지 않고,  
사용자별 baseline 대비 변화량(delta) 기반 feature를 생성한다.

## Feature Calculation Rule

각 feature는 다음과 같이 baseline 대비 변화량으로 계산된다.
```text
feature_delta = current_feature_value - baseline_feature_value
```

일부 feature는 비율 형태로 계산된다.
```text
ratio_feature = current_value / baseline_value
```

이러한 방식으로 사용자 체형 및 착석 습관에 따른 편차를 제거한다.

## 주요 feature 목록

센서 데이터로부터 다음과 같은 특징값을 계산한다.

- `back_lr_diff`: 등받이 좌우 하중 불균형 정도
- `back_upper_lower_ratio`: 등판 상부/하부 하중 비율
- `seat_lr_diff`: 좌판 좌우 하중 불균형 정도
- `seat_fb_shift`: 좌판 전후 하중 이동 정도
- `neck_mean`: 머리/목 영역 ToF 평균 거리
- `neck_forward_delta`: 목 평균 거리와 척추 중간 거리 차이
- `spine_curve`: 척추 상단과 하단 거리 차이
- `spine_variation`: 척추 구간별 거리 변화량
- `pitch_fused_deg`: 좌우 기울기 센서 평균값
- `pitch_lr_diff_deg`: 좌우 기울기 차이

---

# 3. Baseline-relative Interpretation

모든 feature는 절대값이 아닌,  
**사용자별 baseline 대비 변화량(delta)** 기준으로 해석된다.

예:

- neck_forward_delta ↑ → 거북목 증가
- seat_fb_shift ↑ → 상체 전방 이동
- back_total ↓ → 등받이 접촉 감소

이 구조는 사용자 체형 차이를 제거하기 위해 설계되었다.

---

# 4. Rule-based Posture Decision

자세 판별은 단일 threshold 기반이 아닌  
**feature 조합 기반 rule engine**으로 수행된다.

Rule-based posture decision은 시스템의 최종 판단 기준이며,
ML classifier 결과보다 우선적으로 적용된다.

## 주요 posture 판별 기준

### turtle_neck
- neck_forward_delta 증가
- neck_mean 증가

---

### forward_lean
- seat_fb_shift 증가
- spine_curve 증가
- pitch_fused_deg 증가

---

### reclined
- pitch_fused_deg 감소 (뒤로 기울기)
- back_total 증가

---

### side_slouch
- back_lr_diff 증가
- seat_lr_diff 증가

---

### leg_cross_suspect
- seat_lr_diff 증가
- back_lr_diff는 상대적으로 작음

---

### perching
- seat_front 집중 증가
- back_total 감소
- pitch 증가

---

### thinking_pose
- neck_forward_delta + 약한 forward_lean 조합

---

### normal
- 위 조건에 해당하지 않는 경우

---

# 5. Final Posture Selection

최종 자세는 다음 순서로 결정된다.

1. optional ML classifier (RandomForest 기반, 보조적 사용)
2. rule-based posture flags 생성
3. rule 기반 보정 적용
4. 최종 report posture 결정

---

# 6. Posture Score Calculation

점수는 고정 점수표가 아닌  
**시간 기반 penalty 시스템**으로 계산된다.

- posture 지속 시간 기반 감점
- 최초 threshold 도달 시 추가 감점
- 일정 시간 유지 시 누적 감점
- normal 자세 시 점수 회복

---

# 7. Summary

```text
sensor input
↓
feature extraction (baseline-relative)
↓
rule-based posture decision
↓
time-based scoring
↓
report generation
```