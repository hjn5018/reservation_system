import os
import sqlite3
import threading
from .base import ReservationRepository

class SqliteReservationRepository(ReservationRepository):
    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path
        self.lock = threading.Lock()
        
        # 상위 폴더 생성
        dir_name = os.path.dirname(self.sqlite_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            
        # 테이블 생성 초기화
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()

    def _get_connection(self):
        # sqlite3.connect에서 timeout을 주어 lock 충돌을 완화
        return sqlite3.connect(self.sqlite_path, timeout=10.0)

    def get_all(self) -> list:
        with self.lock:
            conn = self._get_connection()
            # row를 딕셔너리로 읽어오기 위해 factory 설정
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, start_time, end_time, status FROM reservations ORDER BY start_time ASC")
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]

    def get_by_id(self, reservation_id: int) -> dict:
        with self.lock:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, start_time, end_time, status FROM reservations WHERE id = ?", (reservation_id,))
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None

    def add(self, title: str, start_time: str, end_time: str) -> dict:
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reservations (title, start_time, end_time, status) VALUES (?, ?, ?, ?)",
                (title, start_time, end_time, "RESERVED")
            )
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            
            return {
                "id": new_id,
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "status": "RESERVED"
            }

    def delete(self, reservation_id: int) -> bool:
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            return affected_rows > 0

    def update_status(self, reservation_id: int, status: str) -> bool:
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE reservations SET status = ? WHERE id = ?", (status, reservation_id))
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            return affected_rows > 0
