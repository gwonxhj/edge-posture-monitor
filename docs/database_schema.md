# POSTURE AI Database Schema

## Database Engine

SQLite

---

# 1. users

| Column | Type | Description |
|------|------|-------------|
| user_id | TEXT | 사용자 ID |
| name | TEXT | 사용자 이름 |
| height_cm | INTEGER | 키 |
| weight_kg | INTEGER | 체중 |
| rest_work_min | INTEGER | 작업 시간 |
| rest_break_min | INTEGER | 휴식 시간 |
| mode | TEXT | 사용 모드 |
| sensitivity | INTEGER | 민감도 설정 |
| created_at | TEXT | 생성 시간 |
| updated_at | TEXT | 수정 시간 |

---

# 2. baselines

| Column | Type | Description |
|------|------|-------------|
| baseline_id | INTEGER | baseline ID |
| user_id | TEXT | 사용자 ID |
| baseline_json | TEXT | feature baseline 저장 |
| calibrated_at | TEXT | 캘리브레이션 시간 |

---

# 3. sessions

| Column | Type | Description |
|------|------|-------------|
| session_id | INTEGER | 세션 ID |
| user_id | TEXT | 사용자 ID |
| start_time | TEXT | 시작 시간 |
| end_time | TEXT | 종료 시간 |
| total_sitting_sec | REAL | 총 착석 시간 |
| avg_score | REAL | 평균 점수 |
| dominant_posture | TEXT | 대표 자세 |
| end_reason | TEXT | 종료 이유 |
| created_at | TEXT | 생성 시간 |
| posture_duration_json | TEXT | posture별 누적 시간(JSON) |

---

# 4. minute_reports

| Column | Type | Description |
|------|------|-------------|
| minute_report_id | INTEGER | ID |
| session_id | INTEGER | 세션 ID |
| minute_index | INTEGER | 분 index |
| avg_score | REAL | 평균 점수 |
| dominant_posture | TEXT | 대표 자세 |
| dominant_ratio | REAL | 자세 비율 |
| report_json | TEXT | 상세 데이터(JSON) |

---

# 5. enhanced_reports

| Column | Type | Description |
|------|------|-------------|
| enhanced_report_id | INTEGER | ID |
| session_id | INTEGER | 세션 ID |
| report_json | TEXT | summary_text / trend_text / exercise_recommendations / summary 포함 |
| created_at | TEXT | 생성 시간 |

---

# 6. daily_reports

| Column | Type | Description |
|------|------|-------------|
| daily_report_id | INTEGER | ID |
| user_id | TEXT | 사용자 ID |
| report_date | TEXT | 날짜 |
| avg_score | REAL | 평균 점수 |
| total_sitting_sec | REAL | 총 시간 |
| dominant_posture | TEXT | 대표 자세 |
| dominant_ratio | REAL | 비율 |
| summary_json | TEXT | 요약 데이터(JSON) |
| created_at | TEXT | 생성 시간 |