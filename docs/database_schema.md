# POSTURE AI Database Schema

## Database Engine

SQLite

---

# 1. users

사용자 프로필 정보 저장

| Column | Type | Description |
|------|------|-------------|
| user_id | TEXT | 사용자 ID |
| name | TEXT | 사용자 이름 |
| height_cm | INTEGER | 키 |
| weight_kg | INTEGER | 체중 |
| rest_work_min | INTEGER | 작업 시간 |
| rest_break_min | INTEGER | 휴식 시간 |

---

# 2. baselines

사용자 캘리브레이션 기준값 저장

| Column | Type | Description |
|------|------|-------------|
| baseline_id | INTEGER | baseline ID |
| user_id | TEXT | 사용자 ID |
| created_at | TEXT | 생성 시간 |

---

# 3. sessions

측정 세션 기록

| Column | Type | Description |
|------|------|-------------|
| session_id | INTEGER | 세션 ID |
| user_id | TEXT | 사용자 ID |
| start_time | TEXT | 시작 시간 |
| end_time | TEXT | 종료 시간 |
| total_sitting_sec | REAL | 총 착석 시간 |
| avg_score | REAL | 평균 자세 점수 |
| dominant_posture | TEXT | 대표 자세 |
| end_reason | TEXT | 종료 이유 |

---

# 4. minute_reports

분 단위 자세 리포트

| Column | Type | Description |
|------|------|-------------|
| minute_report_id | INTEGER | ID |
| session_id | INTEGER | 세션 ID |
| minute_index | INTEGER | 분 index |
| avg_score | REAL | 평균 점수 |
| dominant_posture | TEXT | 대표 자세 |

---

# 5. daily_reports

일일 자세 리포트

| Column | Type | Description |
|------|------|-------------|
| daily_report_id | INTEGER | ID |
| user_id | TEXT | 사용자 ID |
| report_date | TEXT | 날짜 |
| avg_score | REAL | 평균 점수 |
| total_sitting_sec | REAL | 총 착석 시간 |
| dominant_posture | TEXT | 대표 자세 |