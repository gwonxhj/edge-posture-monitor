import json
import sqlite3
from collections import defaultdict
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path="posture_system.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _table_exists(self, conn, table_name: str) -> bool:
        cur = conn.cursor()
        cur.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table_name,))
        return cur.fetchone() is not None

    def _column_exists(self, conn, table_name: str, column_name: str) -> bool:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        cols = cur.fetchall()
        for col in cols:
            if col["name"] == column_name:
                return True
        return False

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()

        # -------------------------------------------------
        # users
        # -------------------------------------------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            height_cm REAL NOT NULL,
            weight_kg REAL NOT NULL,
            rest_work_min INTEGER NOT NULL,
            rest_break_min INTEGER NOT NULL,
            mode TEXT DEFAULT 'pc',
            sensitivity TEXT DEFAULT 'normal',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        # -------------------------------------------------
        # baselines
        # 히스토리 유지 구조
        # -------------------------------------------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS baselines (
            baseline_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            baseline_json TEXT NOT NULL,
            calibrated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        """)

        # -------------------------------------------------
        # sessions
        # end_reason 추가 고려
        # -------------------------------------------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            total_sitting_sec REAL DEFAULT 0,
            avg_score REAL DEFAULT 0,
            dominant_posture TEXT,
            created_at TEXT NOT NULL,
            end_reason TEXT DEFAULT 'normal_stop',
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        """)

        # 기존 DB에 end_reason 컬럼이 없으면 migration
        if not self._column_exists(conn, "sessions", "end_reason"):
            cur.execute("""
            ALTER TABLE sessions
            ADD COLUMN end_reason TEXT DEFAULT 'normal_stop'
            """)

        # -------------------------------------------------
        # minute_reports
        # session_id + minute_index 중복 방지
        # -------------------------------------------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS minute_reports (
            minute_report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            minute_index INTEGER NOT NULL,
            avg_score REAL NOT NULL,
            dominant_posture TEXT,
            dominant_ratio REAL,
            report_json TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
        """)

        # -------------------------------------------------
        # daily_reports
        # user_id + report_date 당 1행 유지하도록 재구성
        # -------------------------------------------------
        if self._table_exists(conn, "daily_reports"):
            self._rebuild_daily_reports_table(conn)
        else:
            cur.execute("""
            CREATE TABLE daily_reports (
                daily_report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                report_date TEXT NOT NULL,
                avg_score REAL NOT NULL,
                total_sitting_sec REAL NOT NULL,
                dominant_posture TEXT,
                dominant_ratio REAL,
                summary_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                UNIQUE(user_id, report_date)
            )
            """)

        # -------------------------------------------------
        # indexes
        # -------------------------------------------------
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_baselines_user_time
        ON baselines(user_id, calibrated_at DESC)
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_user_date
        ON sessions(user_id, session_date)
        """)

        cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_minute_reports_session_minute
        ON minute_reports(session_id, minute_index)
        """)

        cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_reports_user_date
        ON daily_reports(user_id, report_date)
        """)

        conn.commit()
        conn.close()

    def _rebuild_daily_reports_table(self, conn):
        """
        기존 daily_reports가
        - UNIQUE(user_id, report_date)가 없거나
        - 같은 날짜에 여러 줄이 들어가 있더라도

        앱/보고서용으로 user_id + report_date 당 1행만 유지되게 재구성
        """
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_reports'")
        if cur.fetchone() is None:
            return

        # 기존 데이터 읽기
        cur.execute("""
        SELECT *
        FROM daily_reports
        ORDER BY user_id, report_date, created_at
        """)
        rows = cur.fetchall()

        merged = {}
        for row in rows:
            key = (row["user_id"], row["report_date"])

            summary_json = row["summary_json"]
            summary = {}
            if summary_json:
                try:
                    summary = json.loads(summary_json)
                except Exception:
                    summary = {}

            posture_duration_sec = summary.get("posture_duration_sec", {})

            if key not in merged:
                merged[key] = {
                    "user_id": row["user_id"],
                    "report_date": row["report_date"],
                    "weighted_score_sum": row["avg_score"] * row["total_sitting_sec"],
                    "total_sitting_sec": row["total_sitting_sec"],
                    "posture_duration_sec": defaultdict(float),
                    "created_at": row["created_at"],
                }

            item = merged[key]
            item["weighted_score_sum"] += 0 if key not in merged else 0  # 구조 명확화용

            for posture, sec in posture_duration_sec.items():
                item["posture_duration_sec"][posture] += float(sec)

            # total / score 누적
            if item["created_at"] < row["created_at"]:
                item["created_at"] = row["created_at"]

        # merged 재계산
        rebuilt_rows = []
        for key, item in merged.items():
            user_id, report_date = key

            # 같은 날짜에 여러 개 있던 기존 rows 다시 조회해서 정확히 재집계
            same_rows = [r for r in rows if r["user_id"] == user_id and r["report_date"] == report_date]

            total_sec = 0.0
            weighted_score_sum = 0.0
            posture_sum = defaultdict(float)
            latest_created_at = same_rows[0]["created_at"]

            for r in same_rows:
                total_sec += float(r["total_sitting_sec"])
                weighted_score_sum += float(r["avg_score"]) * float(r["total_sitting_sec"])

                if r["created_at"] > latest_created_at:
                    latest_created_at = r["created_at"]

                try:
                    s = json.loads(r["summary_json"]) if r["summary_json"] else {}
                except Exception:
                    s = {}

                for posture, sec in s.get("posture_duration_sec", {}).items():
                    posture_sum[posture] += float(sec)

            avg_score = round(weighted_score_sum / total_sec, 2) if total_sec > 0 else 0.0

            if posture_sum:
                dominant_posture = max(posture_sum, key=posture_sum.get)
                dominant_ratio = round((posture_sum[dominant_posture] / total_sec) * 100, 2) if total_sec > 0 else 0.0
            else:
                dominant_posture = None
                dominant_ratio = 0.0

            normal_sec = float(posture_sum.get("normal", 0.0) or 0.0)

            if total_sec > 0:
                good_posture_ratio = round((normal_sec / total_sec) * 100, 2)
                bad_posture_ratio = round(100.0 - good_posture_ratio, 2)
            else:
                good_posture_ratio = 0.0
                bad_posture_ratio = 0.0

            summary_json = {
                "avg_score": avg_score,
                "total_sitting_sec": round(total_sec, 2),
                "dominant_posture": dominant_posture,
                "dominant_posture_ratio": dominant_ratio,
                "good_posture_ratio": good_posture_ratio,
                "bad_posture_ratio": bad_posture_ratio,
                "posture_duration_sec": dict(posture_sum),
            }

            rebuilt_rows.append((
                user_id,
                report_date,
                avg_score,
                round(total_sec, 2),
                dominant_posture,
                dominant_ratio,
                json.dumps(summary_json, ensure_ascii=False),
                latest_created_at,
            ))

        # 기존 테이블 교체
        cur.execute("DROP TABLE IF EXISTS daily_reports_new")
        cur.execute("""
        CREATE TABLE daily_reports_new (
            daily_report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            report_date TEXT NOT NULL,
            avg_score REAL NOT NULL,
            total_sitting_sec REAL NOT NULL,
            dominant_posture TEXT,
            dominant_ratio REAL,
            summary_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            UNIQUE(user_id, report_date)
        )
        """)

        for row in rebuilt_rows:
            cur.execute("""
            INSERT INTO daily_reports_new (
                user_id, report_date, avg_score,
                total_sitting_sec, dominant_posture,
                dominant_ratio, summary_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, row)

        cur.execute("DROP TABLE daily_reports")
        cur.execute("ALTER TABLE daily_reports_new RENAME TO daily_reports")

    # -------------------------------------------------
    # user
    # -------------------------------------------------
    def upsert_user(
        self,
        user_id,
        name,
        height_cm,
        weight_kg,
        rest_work_min,
        rest_break_min,
        mode="pc",
        sensitivity="normal",
    ):
        now = datetime.now().isoformat()
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO users (
            user_id, name, height_cm, weight_kg,
            rest_work_min, rest_break_min, mode, sensitivity,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            height_cm=excluded.height_cm,
            weight_kg=excluded.weight_kg,
            rest_work_min=excluded.rest_work_min,
            rest_break_min=excluded.rest_break_min,
            mode=excluded.mode,
            sensitivity=excluded.sensitivity,
            updated_at=excluded.updated_at
        """, (
            user_id, name, height_cm, weight_kg,
            rest_work_min, rest_break_min, mode, sensitivity,
            now, now
        ))

        conn.commit()
        conn.close()

    def get_user(self, user_id):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        SELECT *
        FROM users
        WHERE user_id=?
        """, (user_id,))

        row = cur.fetchone()
        conn.close()

        if row is None:
            return None

        return dict(row)

    # -------------------------------------------------
    # baseline
    # -------------------------------------------------
    def save_baseline(self, user_id, baseline: dict):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO baselines (
            user_id, baseline_json, calibrated_at
        ) VALUES (?, ?, ?)
        """, (
            user_id,
            json.dumps(baseline, ensure_ascii=False),
            datetime.now().isoformat(),
        ))

        conn.commit()
        conn.close()

    def get_latest_baseline(self, user_id):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        SELECT baseline_json
        FROM baselines
        WHERE user_id=?
        ORDER BY calibrated_at DESC, baseline_id DESC
        LIMIT 1
        """, (user_id,))

        row = cur.fetchone()
        conn.close()

        if row is None:
            return None

        try:
            return json.loads(row["baseline_json"])
        except Exception:
            return None

    # -------------------------------------------------
    # sessions
    # -------------------------------------------------
    def create_session(self, user_id):
        now = datetime.now()
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO sessions (
            user_id, session_date, start_time, created_at, end_reason
        ) VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            now.date().isoformat(),
            now.isoformat(),
            now.isoformat(),
            "normal_stop",
        ))

        session_id = cur.lastrowid
        conn.commit()
        conn.close()
        return session_id

    def end_session(
        self,
        session_id,
        total_sitting_sec,
        avg_score,
        dominant_posture,
        end_reason="normal_stop",
    ):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        UPDATE sessions
        SET end_time=?, total_sitting_sec=?, avg_score=?, dominant_posture=?, end_reason=?
        WHERE session_id=?
        """, (
            datetime.now().isoformat(),
            total_sitting_sec,
            avg_score,
            dominant_posture,
            end_reason,
            session_id,
        ))

        conn.commit()
        conn.close()

    def get_session(self, session_id):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        SELECT *
        FROM sessions
        WHERE session_id=?
        """, (session_id,))

        row = cur.fetchone()
        conn.close()

        if row is None:
            return None

        return dict(row)

    # -------------------------------------------------
    # minute reports
    # -------------------------------------------------
    def save_minute_reports(self, session_id, minute_summary_list):
        conn = self._connect()
        cur = conn.cursor()

        for item in minute_summary_list:
            cur.execute("""
            INSERT INTO minute_reports (
                session_id, minute_index, avg_score,
                dominant_posture, dominant_ratio, report_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id, minute_index) DO UPDATE SET
                avg_score=excluded.avg_score,
                dominant_posture=excluded.dominant_posture,
                dominant_ratio=excluded.dominant_ratio,
                report_json=excluded.report_json
            """, (
                session_id,
                item["minute_index"],
                item["avg_score"],
                item["dominant_posture"],
                item["dominant_posture_ratio"],
                json.dumps(item, ensure_ascii=False),
            ))

        conn.commit()
        conn.close()

    # -------------------------------------------------
    # daily reports
    # 하루에 사용자당 1행 유지
    # -------------------------------------------------
    def save_daily_report(self, user_id, overall_summary):
        report_date = datetime.now().date().isoformat()
        now_iso = datetime.now().isoformat()

        new_avg_score = float(overall_summary.get("avg_score", 0))
        new_total_sec = float(overall_summary.get("total_sitting_sec", 0))
        new_posture_duration = overall_summary.get("posture_duration_sec", {}) or {}

        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        SELECT *
        FROM daily_reports
        WHERE user_id=? AND report_date=?
        """, (user_id, report_date))

        existing = cur.fetchone()

        if existing is None:
            posture_sum = defaultdict(float)
            for posture, sec in new_posture_duration.items():
                posture_sum[posture] += float(sec)

            if posture_sum and new_total_sec > 0:
                dominant_posture = max(posture_sum, key=posture_sum.get)
                dominant_ratio = round((posture_sum[dominant_posture] / new_total_sec) * 100, 2)
            else:
                dominant_posture = overall_summary.get("dominant_posture")
                dominant_ratio = float(overall_summary.get("dominant_posture_ratio", 0))

            normal_sec = float(posture_sum.get("normal", 0.0) or 0.0)

            if new_total_sec > 0:
                good_posture_ratio = round((normal_sec / new_total_sec) * 100, 2)
                bad_posture_ratio = round(100.0 - good_posture_ratio, 2)
            else:
                good_posture_ratio = 0.0
                bad_posture_ratio = 0.0

            summary_json = {
                "avg_score": round(new_avg_score, 2),
                "total_sitting_sec": round(new_total_sec, 2),
                "dominant_posture": dominant_posture,
                "dominant_posture_ratio": dominant_ratio,
                "good_posture_ratio": good_posture_ratio,
                "bad_posture_ratio": bad_posture_ratio,
                "posture_duration_sec": dict(posture_sum),
            }

            cur.execute("""
            INSERT INTO daily_reports (
                user_id, report_date, avg_score,
                total_sitting_sec, dominant_posture,
                dominant_ratio, summary_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                report_date,
                round(new_avg_score, 2),
                round(new_total_sec, 2),
                dominant_posture,
                dominant_ratio,
                json.dumps(summary_json, ensure_ascii=False),
                now_iso,
            ))

        else:
            existing_total_sec = float(existing["total_sitting_sec"])
            existing_avg_score = float(existing["avg_score"])

            try:
                existing_summary = json.loads(existing["summary_json"]) if existing["summary_json"] else {}
            except Exception:
                existing_summary = {}

            existing_posture_duration = existing_summary.get("posture_duration_sec", {}) or {}

            merged_total_sec = existing_total_sec + new_total_sec

            if merged_total_sec > 0:
                merged_avg_score = round(
                    ((existing_avg_score * existing_total_sec) + (new_avg_score * new_total_sec)) / merged_total_sec,
                    2,
                )
            else:
                merged_avg_score = 0.0

            posture_sum = defaultdict(float)

            for posture, sec in existing_posture_duration.items():
                posture_sum[posture] += float(sec)

            for posture, sec in new_posture_duration.items():
                posture_sum[posture] += float(sec)

            if posture_sum and merged_total_sec > 0:
                dominant_posture = max(posture_sum, key=posture_sum.get)
                dominant_ratio = round((posture_sum[dominant_posture] / merged_total_sec) * 100, 2)
            else:
                dominant_posture = overall_summary.get("dominant_posture")
                dominant_ratio = float(overall_summary.get("dominant_posture_ratio", 0))

            normal_sec = float(posture_sum.get("normal", 0.0) or 0.0)

            if merged_total_sec > 0:
                good_posture_ratio = round((normal_sec / merged_total_sec) * 100, 2)
                bad_posture_ratio = round(100.0 - good_posture_ratio, 2)
            else:
                good_posture_ratio = 0.0
                bad_posture_ratio = 0.0

            merged_summary = {
                "avg_score": merged_avg_score,
                "total_sitting_sec": round(merged_total_sec, 2),
                "dominant_posture": dominant_posture,
                "dominant_posture_ratio": dominant_ratio,
                "good_posture_ratio": good_posture_ratio,
                "bad_posture_ratio": bad_posture_ratio,
                "posture_duration_sec": dict(posture_sum),
            }

            cur.execute("""
            UPDATE daily_reports
            SET avg_score=?,
                total_sitting_sec=?,
                dominant_posture=?,
                dominant_ratio=?,
                summary_json=?,
                created_at=?
            WHERE user_id=? AND report_date=?
            """, (
                merged_avg_score,
                round(merged_total_sec, 2),
                dominant_posture,
                dominant_ratio,
                json.dumps(merged_summary, ensure_ascii=False),
                now_iso,
                user_id,
                report_date,
            ))

        conn.commit()
        conn.close()