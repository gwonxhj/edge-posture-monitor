# POSTURE AI API Specification

## 1. Base URL

Raspberry Pi에서 서버가 실행되면 기본 주소는 아래와 같다.

```text
http://<raspberry_pi_ip>:8000
```

로컬 테스트에서는 보통 아래 주소를 사용한다.
```text
http://127.0.0.1:8000
```

참고
- 본 API는 실제 Raspberry Pi 환경뿐 아니라 Mock STM32 기반 테스트 환경에서도 동일하게 동작한다.

⸻

## 2. Health Check API

서버 상태를 확인하는 API이다.

Endpoint

`GET /health`

Example Request

`curl http://127.0.0.1:8000/health`

Example Response
```text
{
  "ok": true,
  "service": "posture_rpi",
  "backend": "wifi",
  "uart_link": true,
  "ws_clients": 1,
  "stage": "uart_link_ready"
}
```

Field Description
-	ok: 서버 동작 여부
-	service: 서비스 이름
-	backend: 현재 통신 방식
-	uart_link: STM32와 UART 연결 여부
-	ws_clients: 현재 WebSocket 연결 수
-	stage: 현재 시스템 상태

⸻

## 3. Meta API

현재 시스템 상태(meta 정보)를 조회하는 API이다.

Endpoint

`GET /meta`

Example Request

`curl http://127.0.0.1:8000/meta`

Example Response
```text
{
  "type": "meta",
  "connected": true,
  "backend": "wifi",
  "stage": "measuring",
  "ws_clients": 1,
  "timestamp": 1773226472,
  "user_id": "user_001",
  "user_name": "test"
}
```

Field Description
- type: payload 종류 (meta)
- connected: 서버 연결 상태
- backend: 현재 통신 방식
- stage: 현재 동작 단계
- ws_clients: 현재 WebSocket 연결 수
- timestamp: Unix timestamp
- user_id: 현재 사용자 ID
- user_name: 현재 사용자 이름

⸻

## 4. Command API

앱 또는 테스트 클라이언트가 Raspberry Pi에 명령을 전달하는 API이다.

Endpoint

`POST /command`

Content-Type

`application/json`

Example Success Response
```text
{
  "ok": true,
  "accepted": true,
  "message": "command_received",
  "stage": "profile_loaded"
}
```

Example Error Response
```text
{
  "ok": false,
  "accepted": false,
  "error": "missing_cmd",
  "stage": "uart_link_ready"
}
```

Example Invalid Stage Response
```text
{
  "ok": false,
  "accepted": false,
  "error": "invalid_stage",
  "stage": "uart_link_ready",
  "expected_stage": "wait_start_decision"
}
```

Field Description
- error: 에러 코드(ex. missing_cmd, invalid_stage)
- stage: 현재 시스템 stage
- expected_stage: 해당 command가 허용되는 stage

⸻

## 5. Command List

5-1. Submit Profile

새 사용자 프로필 등록
```text
{
  "cmd": "submit_profile",
  "user_id": "user_001",
  "name": "test",
  "height_cm": 175,
  "weight_kg": 70,
  "rest_work_min": 60,
  "rest_break_min": 10
}
```

Field Type
-	cmd: string
-	user_id: string
-	name: string
-	height_cm: int
-	weight_kg: int
-	rest_work_min: int
-	rest_break_min: int

설명
- 신규 사용자이거나 baseline이 없는 경우 이후 calibration 단계가 필요할 수 있다.

⸻

5-2. Select Profile

기존 사용자 선택
```json
{
  "cmd": "select_profile",
  "user_id": "user_001"
}
```

설명
- 기존 사용자를 선택한다.
- 선택된 사용자에 baseline이 없거나 재측정이 필요한 경우 이후 calibration 단계로 진행할 수 있다.

⸻

5-3. Start Calibration

캘리브레이션 시작 요청
```json
{
  "cmd": "start_calibration"
}
```

Valid Stage
- wait_calibration_decision

⸻

5-4. Skip Calibration

캘리브레이션 생략 요청
```json
{
  "cmd": "skip_calibration"
}
```

Valid Stage
- wait_calibration_decision

⸻

5-5. Start Measurement

측정 시작 요청
```json
{
  "cmd": "start_measurement"
}
```

Valid Stage
- wait_start_decision

동작 설명
- 사용자가 측정 시작을 선택했을 때 사용한다.
- RPi는 STM32에 착석 확인을 위해 CHK_SIT을 반복 전송한다.
- STM32가 SIT을 응답하면 RPi는 GO를 전송한다.
- 이후 실시간 측정이 시작된다.

⸻

5-6. Pause Measurement

측정 일시정지 요청
```json
{
  "cmd": "pause_measurement"
}
```

Valid Stage
- measuring

동작 설명
- 측정이 진행 중일 때 사용자가 잠시 측정을 멈추고 싶을 때 사용한다.
- RPi는 STM32에 STOP 명령을 전송한다.
- STM32는 즉시 측정을 중단하고 idle 상태로 전환한다.
- RPi는 현재까지의 측정 데이터를 메모리에 유지한다.
- 이 시점에는 세션을 DB에 저장하지 않는다.
- 이후 앱은 resume_measurement 또는 quit_measurement를 보낼 수 있다.

⸻

5-7. Resume Measurement

일시정지 후 측정 재개 요청
```json
{
  "cmd": "resume_measurement"
}
```

Valid Stage
- paused

동작 설명
- 일시정지 상태(paused)에서 측정을 다시 이어서 진행할 때 사용한다.
- RPi는 STM32에 CHK_SIT을 반복 전송한다.
- STM32가 SIT을 응답하면 RPi는 GO를 전송한다.
- 이후 기존 세션에 이어서 측정을 계속 진행한다.
- pause 이전에 누적된 측정 데이터는 유지된다.

⸻

5-8. Quit Measurement

측정 종료 요청
```json
{
  "cmd": "quit_measurement"
}
```

Valid Stage
- measuring
- paused
- wait_restart_decision

동작 설명
- 측정 중이거나 일시정지 상태일 때 사용자가 세션을 완전히 종료하고 싶을 때 사용한다.
- 측정 중(measuring)인 경우 RPi는 STM32에 STOP 명령을 전송한 뒤 세션을 종료한다.
- 일시정지 상태(paused) 또는 STAND 이후 상태처럼 STM32가 이미 idle 상태인 경우에는 추가 명령 없이 세션 종료가 가능하다.
- RPi는 현재까지 누적된 데이터를 기준으로 세션을 종료하고 리포트를 저장한다.

⸻

5-9. Resume After Stand

사용자가 자리에서 다시 앉아 측정을 재개할 때 사용한다.
```json
{
  "cmd": "resume_after_stand"
}
```

Valid Stage
- wait_restart_decision

동작 설명
- STM32가 STAND를 보낸 이후 사용자가 다시 측정을 이어가고 싶을 때 사용한다.
- RPi는 STM32에 CHK_SIT을 전송한다.
- STM32가 SIT을 응답하면 RPi는 GO를 전송한다.
- 이후 측정을 재개한다.

⸻

5-10. Decline Resume After Stand

자리 이탈 후 측정을 종료할 때 사용한다.
```json
{
  "cmd": "decline_resume_after_stand"
}
```

Valid Stage
- wait_restart_decision

동작 설명
- STM32가 STAND 이벤트를 RPi로 전송하면 이미 측정이 중단된 상태로 간주한다.
- 사용자가 재측정을 원하지 않을 때 이 명령을 사용한다.
- 이 경우 RPi는 STM32에 추가 명령을 보내지 않는다.
- RPi는 현재까지 누적된 데이터를 기준으로 세션을 종료하고 리포트를 저장한다.

⸻

5-11. Request Recalibration

재캘리브레이션 요청
```json
{
  "cmd": "request_recalibration"
}
```

Valid Stage
- wait_calibration_decision
- paused

동작 설명
- 기존 baseline을 다시 측정하기 위해 사용된다.
- 상황에 따라 RPi는 STOP -> CHK_SIT -> CAL 흐름을 수행한다.

⸻

## 6. WebSocket API

실시간 상태를 앱으로 push 전송하는 API이다.

Endpoint

`ws://<raspberry_pi_ip>:8000/ws`

로컬 테스트에서는 아래 주소를 사용한다.

`ws://127.0.0.1:8000/ws`

전달되는 payload 종류
-	meta
-	realtime_status
-	stand_event
-	minute_summary
-	overall_summary
- enhanced_report

특징
-	새 WebSocket 클라이언트가 연결되면 현재 snapshot을 즉시 받는다.
-	전송 순서는 보통 meta → latest realtime_status → latest report 이다.
-	앱 재실행 또는 재연결 시 상태 복구에 사용한다.

⸻

## 7. Realtime Status Payload

실시간 자세 상태 데이터

Example
```text
{
  "type": "realtime_status",
  "user_id": "user_001",
  "timestamp": 1773211239,
  "posture": {
    "dominant": "thinking_pose",
    "flags": {
      "turtle_neck": true,
      "forward_lean": true,
      "reclined": false,
      "side_slouch": false,
      "leg_cross_suspect": false,
      "thinking_pose": true,
      "perching": false,
      "normal": false
    }
  },
  "score": {
    "current": 100.0,
    "alert": false,
    "alert_stage": 0
  },
  "monitoring": {
    "loadcell": {
      "balance_score": 97.2,
      "balance_level": "good"
    },
    "spine_tof": {
      "score": 8.7,
      "level": "danger"
    },
    "neck_tof": {
      "score": 29.0,
      "level": "danger"
    }
  }
}
```

주의
- posture.dominant는 실시간 classifier 출력 기준 자세이다.
- 최종 리포트에서 사용하는 대표 자세는 rule-based flag 보정 결과와 다를 수 있다.
- 앱에서는 posture.dominant와 posture.flags를 함께 사용하는 것을 권장한다.

⸻

## 8. Stand Event Payload

사용자가 자리에서 일어났을 때 앱에 보내는 이벤트

설명
- STM32가 사용자의 자리 이탈을 감지하면 'STAND' 이벤트를 RPi로 전송한다.
- 이 시점에서 STM32는 이미 측정을 중단하고 idle 상태로 전환된 상태이다.
- 앱은 재측정 여부를 사용자에게 물어본다.
- 이 상태에서는 resume_after_stand, decline_resume_after_stand, quit_measurement 중 하나를 보낼 수 있다.

Example
```text
{
  "type": "stand_event",
  "user_id": "user_001",
  "timestamp": 1773218563,
  "message": "사용자가 자리에서 일어났습니다. 측정을 재시작 하시겠습니까?",
  "actions": {
    "resume": "resume_after_stand",
    "stop": "decline_resume_after_stand"
  }
}
```

⸻

## 9. Minute Summary Payload

분 단위 요약 데이터

Example
```text
{
  "type": "minute_summary",
  "user_id": "user_001",
  "session_id": 1,
  "minute_index": 0,
  "avg_score": 100.0,
  "dominant_posture": "turtle_neck",
  "dominant_posture_ratio": 25.0,
  "good_posture_ratio": 17.33,
  "bad_posture_ratio": 82.67
}
```

⸻

## 10. Overall Summary Payload

세션 종료 후 전체 요약 데이터

Example
```text
{
  "type": "overall_summary",
  "user_id": "user_001",
  "session_id": 1,
  "avg_score": 100.0,
  "total_sitting_sec": 24.0,
  "dominant_posture": "turtle_neck",
  "dominant_posture_ratio": 37.5,
  "good_posture_ratio": 25.25,
  "bad_posture_ratio": 74.75,
  "posture_duration_sec": {
    "normal": 6.06,
    "turtle_neck": 9.0,
    "forward_lean": 4.96,
    "reclined": 0.0,
    "side_slouch": 2.4,
    "leg_cross_suspect": 1.54,
    "thinking_pose": 0.04,
    "perching": 0.0
  }
}
```

⸻

## 10-A. Enhanced Report Payload

세션 종료 후 rule-based 또는 향후 LLM 기반으로 생성되는 해석형 리포트 데이터

Example
```text
{
  "type": "enhanced_report",
  "user_id": "user_001",
  "session_id": 1,
  "data": {
    "summary_text": "전체 평균 점수는 100.0점으로 우수 수준입니다. 주요 자세는 forward_lean이며, 나쁜 자세 비율은 100.0%입니다.",
    "trend_text": "측정 전반에서 forward_lean 자세가 지속되었습니다.",
    "exercise_recommendations": [
      "허리 신전 스트레칭",
      "플랭크",
      "고관절 스트레칭"
    ]
  }
}
```

Field Description
- type: payload 종류 (enhanced_report)
- user_id: 사용자 ID
- session_id: 세션 ID
- data.summary_text: 전체 요약 문장
- data.trend_text: 자세 추이 설명
- data.exercise_recommendations: 추천 운동 리스트

⸻

## 11. Posture Label List

서버에서 사용하는 대표 자세 문자열 목록
-	normal
-	turtle_neck
-	forward_lean
-	reclined
-	side_slouch
-	leg_cross_suspect
-	thinking_pose
-	perching

앱에서는 아래처럼 한글 매핑해서 사용할 수 있다.
-	normal → 정자세
-	turtle_neck → 거북목
-	forward_lean → 상체 굽힘
-	reclined → 기대앉기
-	side_slouch → 측면 기울어짐
-	leg_cross_suspect → 다리 꼬기 의심
-	thinking_pose → 턱 괴기 / 생각 자세
-	perching → 걸터앉기

⸻

## 12. Stage List

현재 시스템에서 사용하는 주요 stage 문자열
-	boot_completed
-	uart_link_ready
-	profile_loaded
-	wait_calibration_decision
-	wait_sit_for_calibration
-	calibrating
-	calibration_completed
-	wait_start_decision
-	wait_sit_for_measure
-	measuring
- paused
-	wait_restart_decision
-	measurement_stop_requested
-	session_saved

추가 설명
- `measurement_stop_requested`: 종료 또는 중단 요청이 수신되어 세션 종료 절차로 진입한 상태

앱은 meta.stage를 기준으로 화면 상태를 전환한다.

⸻

## 13. Measurement Control Flow

13-1. 측정 시작

1. App -> RPi: start_measurement
2. RPi -> STM32: CHK_SIT 반복 전송
3. STM32 -> RPi: SIT
4. RPi -> STM32: GO
5. 측정 시작

⸻

13-2. 측정 중 사용자 직접 일시정지

App -> RPi
```json
{
  "cmd": "pause_measurement"
}
```

동작
- RPi -> STM32: STOP
- STM32 -> idle 상태 전환
- RPi -> 앱 상태: paused
- 세션은 유지되며 DB 저장은 하지 않음

⸻

13-3. 일시정지 후 측정 재개

App -> RPi
```json
{
  "cmd": "resume_measurement"
}
```

동작
- RPi -> STM32: CHK_SIT
- STM32 -> RPi: SIT
- RPi -> STM32: GO
- 기존 세션에 이어서 측정 재개

⸻

13-4. 일시정지 후 측정 종료

App -> RPi
```json
{
  "cmd": "quit_measurement"
}
```

동작
- paused 상태에서는 STM32가 이미 idle 상태이므로 추가 제어 없이 종료 가능
- measuring 상태에서 직접 종료 요청이 들어온 경우에는 RPi -> STM32: STOP
- 세션 종료 및 리포트 저장

⸻

13-5. 측정 중 사용자 자리 이탈

1. STM32 -> RPi: STAND
2. RPi -> App: stand_event 전송
3. App -> RPi: resume_after_stand, decline_resume_after_stand 또는 quit_measurement

⸻

13-6. STAND 이후 재측정 선택

App -> RPi
```json
{
  "cmd": "resume_after_stand"
}
```

동작
- RPi -> STM32: CHK_SIT
- STM32 -> RPi: SIT
- RPi -> STM32: GO
- 측정 재개

⸻

13-7. STAND 이후 재측정 거부

App -> RPi
```json
{
  "cmd": "decline_resume_after_stand"
}
```

동작
- STM32는 이미 idle 상태
- RPi는 STM32에 별도 명령을 보내지 않음
- 세션 종료 및 리포트 저장

⸻

13-8. STAND 이후 즉시 종료

App -> RPi
```json
{
  "cmd": "quit_measurement"
}
```

동작
- STM32는 이미 idle 상태
- RPi는 STM32에 추가 명령을 보내지 않음
- 세션 종료 및 리포트 저장

⸻