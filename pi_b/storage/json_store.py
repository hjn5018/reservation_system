import os
import json
import threading
from .base import ReservationRepository

class JsonReservationRepository(ReservationRepository):
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.lock = threading.Lock()
        
        # 파일이 존재하지 않는 경우 초기화
        dir_name = os.path.dirname(self.json_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            
        if not os.path.exists(self.json_path):
            self._write_file([])

    def _read_file(self) -> list:
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_file(self, data: list):
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_all(self) -> list:
        with self.lock:
            return self._read_file()

    def get_by_id(self, reservation_id: int) -> dict:
        with self.lock:
            data = self._read_file()
            for item in data:
                if item.get("id") == reservation_id:
                    return item
            return None

    def add(self, title: str, start_time: str, end_time: str) -> dict:
        with self.lock:
            data = self._read_file()
            
            # 새 ID 생성 (최대 ID + 1)
            next_id = 1
            if data:
                next_id = max(item.get("id", 0) for item in data) + 1
            
            new_reservation = {
                "id": next_id,
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "status": "RESERVED"  # 기본 상태는 RESERVED
            }
            
            data.append(new_reservation)
            self._write_file(data)
            return new_reservation

    def delete(self, reservation_id: int) -> bool:
        with self.lock:
            data = self._read_file()
            original_len = len(data)
            data = [item for item in data if item.get("id") != reservation_id]
            
            if len(data) < original_len:
                self._write_file(data)
                return True
            return False

    def update_status(self, reservation_id: int, status: str) -> bool:
        with self.lock:
            data = self._read_file()
            updated = False
            for item in data:
                if item.get("id") == reservation_id:
                    item["status"] = status
                    updated = True
                    break
            
            if updated:
                self._write_file(data)
                return True
            return False
