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

센서 데이터로부터 다음 특징(feature)을 계산한다.

### 2.1 Pressure Balance

좌석 하중 분포를 이용하여 좌우 균형을 계산한다.
`pressure_balance = left_pressure / right_pressure`
이 값이 일정 범위를 벗어나면 자세가 한쪽으로 기울어진 것으로 판단한다.

---

### 2.2 Neck Distance

ToF 센서를 이용하여 목과 센서 사이의 거리를 측정한다.

거리가 증가하면 사용자가 고개를 앞으로 내민 것으로 판단한다.
`neck_distance > threshold → turtle_neck`

---

### 2.3 Spine Distance

척추 방향 ToF 센서를 이용하여 상체 기울기를 판단한다.
`spine_distance > threshold → forward_lean`

---

### 2.4 Upper Body Tilt

IMU 센서를 이용하여 상체 기울기를 계산한다.
`tilt_angle > threshold → reclined`

---

# 3. Posture Classification

자세 분류는 rule-based classifier로 수행된다.

각 센서 feature를 기준으로 posture label을 결정한다.

예시 로직
```text
if neck_distance > neck_threshold:
posture = “turtle_neck”

elif spine_distance > spine_threshold:
posture = “forward_lean”

elif pressure_balance outside normal range:
posture = “side_slouch”

elif tilt_angle > tilt_threshold:
posture = “reclined”

else:
posture = “normal”
```

---

# 4. Supported Posture Labels

시스템은 다음 자세 유형을 분류한다.

| Posture | Description |
|------|-------------|
| normal | 정상 자세 |
| turtle_neck | 거북목 |
| forward_lean | 상체 굽힘 |
| reclined | 기대앉기 |
| side_slouch | 측면 기울어짐 |
| leg_cross_suspect | 다리 꼬기 의심 |
| thinking_pose | 턱 괴기 |
| perching | 걸터앉기 |

---

# 5. Posture Score Calculation

각 자세는 점수 시스템으로 평가된다.

예시 기준

| Posture | Score |
|------|------|
| normal | 100 |
| turtle_neck | 60 |
| forward_lean | 50 |
| reclined | 40 |
| side_slouch | 40 |

세션 동안 평균 점수를 계산하여 자세 리포트를 생성한다.

---

# 6. Future Extension

현재 시스템은 rule-based classification을 사용하지만  
향후 다음과 같은 방식으로 확장할 수 있다.

### Machine Learning Based Classification
```text
sensor data
↓
feature extraction
↓
ML model (RandomForest / CNN)
↓
posture classification
```

### LLM-based Feedback System

LLM을 활용하여 사용자 자세 패턴을 분석하고  
맞춤형 자세 교정 피드백을 제공할 수 있다.

예
```text
posture history
↓
LLM analysis
↓
personalized posture recommendation
```

---

# 7. Summary

현재 posture classification은 다음 방식으로 수행된다.
```text
sensor input
↓
feature extraction
↓
rule-based classification
↓
posture score calculation
↓
report generation
```
이 구조는 Edge 환경에서의 낮은 지연시간과  
안정적인 동작을 목표로 설계되었다.