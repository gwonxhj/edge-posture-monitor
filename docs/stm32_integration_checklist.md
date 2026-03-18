# STM32 Integration Checklist

## 1. UART Communication
- [ ] Correct port configured (e.g., /dev/ttyUSB0 or /dev/ttyACM0)
- [ ] Baud rate matches STM32 firmware (115200)
- [ ] No packet loss or buffer overflow

## 2. Handshake Protocol
- [ ] READY → ACK → LINK_OK 정상 동작
- [ ] SIT 이벤트 정상 수신
- [ ] CAL → CAL_DONE 정상 흐름 확인
- [ ] GO → 측정 시작 확인
- [ ] STAND 이벤트 정상 감지

## 3. Sensor Data Validation
- [ ] loadcell 값 정상 범위 확인
- [ ] tof_1d / tof_3d 값 분포 확인
- [ ] mpu pitch 값 정상 변화 확인
- [ ] 값이 0 또는 고정값으로 들어오지 않는지 확인

## 4. Baseline Calibration
- [ ] baseline 값 정상 저장
- [ ] delta_map 계산 정상 동작
- [ ] calibration 이후 posture 변화 반영 확인

## 5. Posture Classification
- [ ] normal 자세 정상 판별
- [ ] forward_lean / turtle_neck 실제 분리 확인
- [ ] thinking_pose 실제 분포 확인 (중요)

## 6. Logging & Storage
- [ ] sample_logs 저장 확인
- [ ] posture_duration 누적 확인
- [ ] enhanced_report DB 저장 확인
- [ ] session_id 정상 증가

## 7. Failure Handling
- [ ] checksum 실패 시 로그 출력
- [ ] UART disconnect 대응 확인
- [ ] 이상 데이터 필터링 여부 확인

## 8. Performance
- [ ] 50Hz 입력에서 지연 없는지
- [ ] CPU 사용량 확인
- [ ] 메모리 누수 여부 확인