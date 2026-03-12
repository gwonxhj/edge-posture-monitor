# POSTURE AI Test Checklist

## 1. UART Communication

| Test | Result |
|-----|-------|
| UART READY handshake | ✔ |
| LINK_OK response | ✔ |
| command transmission | ✔ |

---

# 2. Calibration Flow

| Test | Result |
|-----|-------|
| calibration start command | ✔ |
| baseline calculation | ✔ |
| baseline DB save | ✔ |

---

# 3. Measurement Flow

| Test | Result |
|-----|-------|
| start measurement | ✔ |
| sensor stream reception | ✔ |
| posture classification | ✔ |
| pause measurement | ✔ |
| resume measurement | ✔ |

---

# 4. Stand Detection

| Test | Result |
|-----|-------|
| stand event detection | ✔ |
| resume request | ✔ |
| decline resume | ✔ |
| quit measurement | ✔ |

---

# 5. Report Generation

| Test | Result |
|-----|-------|
| minute report generation | ✔ |
| session summary generation | ✔ |
| daily report aggregation | ✔ |

---

# 6. Database Validation

| Table | Check |
|------|------|
| users | user creation |
| baselines | calibration history |
| sessions | session start / end |
| minute_reports | minute aggregation |
| daily_reports | daily aggregation |

---

# 7. Mock Testing

Mock STM32 환경에서 전체 시스템을 검증하였다.

테스트 항목

- fake sensor stream
- stand event simulation
- measurement resume
- report generation
- DB persistence