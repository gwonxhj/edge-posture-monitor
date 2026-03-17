# Code Structure

이 문서는 Edge AI Posture Monitoring System의 코드 구조와 각 파일의 역할을 정리한 문서이다.

---

## 1. Entry Point

### `main_real.py`
실제 Raspberry Pi 런타임의 메인 진입점이다.

주요 역할:
- UART 핸드셰이크 수행
- 앱 서버 시작
- 프로필 선택 / 생성 흐름 제어
- 초기 캘리브레이션 수행 여부 결정
- 측정 시작 / 일시정지 / 재개 / 재캘리브레이션 / 종료 흐름 제어
- 세션 종료 후 리포트 및 DB 저장

---

## 2. Communication Layer

### `src/communication/uart_protocol.py`
STM32 <-> Raspberry Pi 간 UART 통신 규약을 정의한다.

주요 역할:
- baud rate 정의
- binary packet 크기 정의
- DAT / CAL header 정의
- ASCII control message 정의
- 센서 index mapping 정의
- checksum 계산 함수 제공

---

### `src/communication/command_sender.py`
RPi -> STM32 방향의 제어 명령 전송을 담당한다.

주요 역할:
- ACK 전송
- CHK_SIT 전송
- CAL 전송
- GO 전송
- STOP 전송
- QUIT 전송

---

### `src/communication/app_command_handler.py`
앱에서 들어온 command를 해석하고 stage 기준으로 유효성을 검사한다.

주요 역할:
- stage별 허용 command 검증
- profile 등록 / 선택 처리
- 측정 시작 / 일시정지 / 종료 처리
- 재캘리브레이션 요청 처리
- STAND 이후 resume / decline 처리

---

### `src/communication/session_state.py`
앱과 RPi가 공유하는 runtime stage 상수를 정의한다.

예:
- `boot_completed`
- `uart_link_ready`
- `profile_loaded`
- `wait_calibration_decision`
- `calibrating`
- `measuring`
- `paused`
- `session_saved`

---

### `src/communication/app_payload_builder.py`
앱에 전달할 JSON payload를 생성한다.

주요 역할:
- 실시간 자세 상태 payload 생성
- STAND event payload 생성
- overall summary payload 생성
- minute summary payload 생성

---

### `src/communication/wifi_server.py`
앱과 통신하기 위한 HTTP / WebSocket 서버를 제공한다.

주요 역할:
- health endpoint 제공
- meta 상태 제공
- command 수신
- realtime / report payload 브로드캐스트

---

## 3. Sensor Layer

### `src/sensor/sensor_receiver.py`
STM32에서 들어오는 UART 데이터를 수신하고 packet/event 단위로 복원한다.

주요 역할:
- DAT / CAL binary frame 수신
- STAND ASCII event 감지
- checksum 검증
- parse 실패 / checksum 실패 카운트 관리
- mock mode 지원

---

### `src/sensor/packet_parser.py`
128-byte binary payload를 구조화된 packet dict로 변환한다.

주요 역할:
- struct.unpack 수행
- header 검증
- loadcell / tof_1d / tof_3d / mpu 추출
- DAT / CAL frame type 구분

---

### `src/sensor/sensor_mapper.py`
raw packet을 의미 있는 semantic packet 구조로 변환한다.

주요 역할:
- 12개 loadcell을 등판 / 좌판 구조로 재배치
- 4개 1D ToF를 척추 구간 데이터로 매핑
- 32개 3D ToF를 좌/우 목 센서 summary로 축약
- 2개 MPU 값을 right / left / fused 형태로 정리

---

### `src/sensor/sensor_simulator.py`
Mock STM32 테스트용 가짜 센서 데이터를 생성한다.

주요 역할:
- normal / turtle_neck / forward_lean 등 posture별 mock data 생성
- loadcell / ToF / MPU 값 시뮬레이션

---

## 4. Core Logic

### `src/core/feature_extractor.py`
semantic packet에서 자세 판별용 feature를 계산한다.

주요 역할:
- 등판 좌우 하중 비율 계산
- 좌판 좌우 / 전후 하중 이동 계산
- 목 / 척추 ToF feature 계산
- MPU 평균 pitch 기반 feature 계산
- baseline 대비 delta feature 계산

---

### `src/core/posture_classifier.py`
학습된 ML 모델을 불러와 자세를 분류한다.

주요 역할:
- posture RF 모델 로드
- 입력 feature를 DataFrame으로 변환
- 자세 label 예측
- 예측 실패 시 fallback 처리

---

### `src/core/posture_flags.py`
규칙 기반 자세 이상 플래그를 계산한다.

주요 역할:
- turtle_neck 판정
- forward_lean 판정
- reclined 판정
- side_slouch 판정
- leg_cross_suspect 판정
- thinking_pose 판정
- perching 판정
- normal 판정

---

### `src/core/posture_mapper.py`
내부 자세 label을 사용자 표시용 문자열로 반환한다.

예:
- `normal` -> `정자세`

---

### `src/core/posture_score.py`
자세 상태를 바탕으로 자세 점수와 알림 단계를 관리한다.

주요 역할:
- posture별 경고 임계시간 관리
- posture 유지 시간 계산
- 점수 감소 로직 수행
- 반복 경고 단계 계산
- 전체 착석 시간 / 자세별 누적 시간 계산

---

### `src/core/monitoring_metrics.py`
baseline 대비 현재 자세 안정도를 계산한다.

주요 역할:
- loadcell balance score 계산
- spine ToF score 계산
- neck ToF score 계산
- score -> level(good / warning / danger) 변환

---

## 5. Runtime / App Flow

### `src/runtime/measurement_runtime.py`
실시간 측정 루프의 핵심 실행부이다.

주요 역할:
- DAT packet 처리
- STAND event 처리
- 앱 command 처리
- feature 추출 / 분류 / 점수 계산
- realtime payload 생성
- sample log 저장
- 재캘리블이션 중단/재개 처리

---

### `src/app_flow/calibration_flow.py`
캘리브레이션 흐름을 실행한다.

주요 역할:
- 착석 확인
- CAL 명령 전송
- CAL packet 수집
- baseline 계산
- CAL_DONE 확인
- baseline 저장

---

### `src/app_flow/sit_detector.py`
착석 확인 흐름을 담당한다.

주요 역할:
- CHK_SIT 전송
- STM32의 SIT 응답 대기

---

### `src/app_flow/app_flow_controller.py`
앱 command를 기다리는 상위 단계 흐름 제어 함수들을 제공한다.

주요 역할:
- profile command 대기
- calibration decision 대기
- measurement start 대기
- restart decision 대기
- paused 상태 resume / quit / recalibration 결정 대기

---

## 6. Session / Profile

### `src/session/session_manager.py`
현재 런타임 세션 상태를 관리한다.

주요 역할:
- 현재 사용자 프로필 관리
- current baseline 관리
- session active 여부 관리
- measurement started 여부 관리

---

### `src/session/profile_manager.py`
사용자 프로필 파일(JSON)을 관리한다.

주요 역할:
- 프로필 생성
- 프로필 로드 / 저장
- baseline 업데이트
- 사용자 설정 업데이트
- 프로필 목록 조회

---

### `src/session/calibration.py`
캘리브레이션 데이터 수집 및 baseline 계산을 담당한다.

주요 역할:
- feature 누적 합 계산
- 일정 시간 샘플 수집
- 평균 baseline 생성

---

## 7. Storage Layer

### `src/storage/database_manager.py`
SQLite 데이터베이스 접근을 담당한다.

주요 역할:
- users / baselines / sessions / minute_reports / daily_reports 테이블 초기화
- 사용자 정보 저장
- baseline 저장
- session 생성 / 종료
- minute report 저장
- daily report 저장 / 병합

---

### `src/storage/sample_logger.py`
실시간 샘플 로그를 CSV 형태로 저장한다.

주요 역할:
- 세션별 CSV 로그 파일 생성
- raw / semantic / feature / delta / predicted / flags 저장
- 후속 모델 재학습용 데이터셋 기록

---

## 8. Report Layer

### `src/report/report_generator.py`
측정 중 수집된 데이터를 바탕으로 리포트를 생성한다.

주요 역할:
- 전체 세션 요약 생성
- 분 단위 요약 생성
- good / bad posture ratio 계산

---

## 9. Feedback Layer

### `src/feedback/audio_feedback.py`
자세 이상 감지 시 오디오 피드백을 재생한다.

주요 역할:
- posture alert 음성 / 경고 출력

---

## 10. Tools

### `tools/fake_stm32.py`
STM32 없이 전체 시스템을 테스트하기 위한 가상 송신기이다.

주요 역할:
- READY / LINK_OK / SIT / STAND / CAL_DONE 이벤트 시뮬레이션
- CAL / DAT 흐름 시뮬레이션
- posture scenario 기반 mock sensor 데이터 송신

---

### `tools/uart_packet_snifeer.py`
UART raw packet을 직접 확인하기 위한 디버깅 도구이다.

주요 역할:
- raw DAT / CAL frame 수신
- checksum 검증
- 센서값 출력

---

## 11. 문서

### `docs/api_spec.md`
앱 <-> RPi API 인터페이스 명세

### `docs/system_architecture.md`
시스템 구조 및 모듈 구성 설명

### `docs/runtime_sequence.md`
런타임 sequence 및 측정 / 재캘리브레이션 / STAND 흐름 설명

### `docs/test_checklist.md`
Mock 테스트 및 실연동 전 체크리스트