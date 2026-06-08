import os
import unittest
from storage.json_store import JsonReservationRepository
from storage.sqlite_store import SqliteReservationRepository

class TestStorage(unittest.TestCase):
    def setUp(self):
        self.json_test_path = "storage/test_reservations.json"
        self.sqlite_test_path = "storage/test_reservations.db"
        
        # 이전 테스트 잔여물 제거
        if os.path.exists(self.json_test_path):
            os.remove(self.json_test_path)
        if os.path.exists(self.sqlite_test_path):
            os.remove(self.sqlite_test_path)
            
        self.json_repo = JsonReservationRepository(self.json_test_path)
        self.sqlite_repo = SqliteReservationRepository(self.sqlite_test_path)

    def tearDown(self):
        # 테스트 파일 정리
        if os.path.exists(self.json_test_path):
            os.remove(self.json_test_path)
        if os.path.exists(self.sqlite_test_path):
            os.remove(self.sqlite_test_path)

    def test_json_repo_operations(self):
        # 1. 초기 상태 확인
        all_res = self.json_repo.get_all()
        self.assertEqual(len(all_res), 0)
        
        # 2. 예약 추가
        res = self.json_repo.add("Test Event", "2026-06-08 10:00:00", "2026-06-08 11:00:00")
        self.assertEqual(res["id"], 1)
        self.assertEqual(res["title"], "Test Event")
        self.assertEqual(res["status"], "RESERVED")
        
        # 3. 전체 조회 확인
        all_res = self.json_repo.get_all()
        self.assertEqual(len(all_res), 1)
        self.assertEqual(all_res[0]["id"], 1)
        
        # 4. ID 개별 조회 확인
        res_by_id = self.json_repo.get_by_id(1)
        self.assertIsNotNone(res_by_id)
        self.assertEqual(res_by_id["title"], "Test Event")
        
        # 없는 ID 조회
        self.assertIsNone(self.json_repo.get_by_id(999))
        
        # 5. 상태 변경
        update_result = self.json_repo.update_status(1, "IN_USE")
        self.assertTrue(update_result)
        
        res_by_id = self.json_repo.get_by_id(1)
        self.assertEqual(res_by_id["status"], "IN_USE")
        
        # 6. 예약 삭제
        delete_result = self.json_repo.delete(1)
        self.assertTrue(delete_result)
        
        all_res = self.json_repo.get_all()
        self.assertEqual(len(all_res), 0)

    def test_sqlite_repo_operations(self):
        # 1. 초기 상태 확인
        all_res = self.sqlite_repo.get_all()
        self.assertEqual(len(all_res), 0)
        
        # 2. 예약 추가
        res = self.sqlite_repo.add("SQLite Event", "2026-06-08 14:00:00", "2026-06-08 15:00:00")
        self.assertIsNotNone(res["id"])
        self.assertEqual(res["title"], "SQLite Event")
        self.assertEqual(res["status"], "RESERVED")
        
        # 3. 전체 조회 확인
        all_res = self.sqlite_repo.get_all()
        self.assertEqual(len(all_res), 1)
        self.assertEqual(all_res[0]["title"], "SQLite Event")
        
        # 4. ID 개별 조회 확인
        res_by_id = self.sqlite_repo.get_by_id(res["id"])
        self.assertIsNotNone(res_by_id)
        self.assertEqual(res_by_id["title"], "SQLite Event")
        
        # 없는 ID 조회
        self.assertIsNone(self.sqlite_repo.get_by_id(999))
        
        # 5. 상태 변경
        update_result = self.sqlite_repo.update_status(res["id"], "IN_USE")
        self.assertTrue(update_result)
        
        res_by_id = self.sqlite_repo.get_by_id(res["id"])
        self.assertEqual(res_by_id["status"], "IN_USE")
        
        # 6. 예약 삭제
        delete_result = self.sqlite_repo.delete(res["id"])
        self.assertTrue(delete_result)
        
        all_res = self.sqlite_repo.get_all()
        self.assertEqual(len(all_res), 0)

if __name__ == "__main__":
    unittest.main()
