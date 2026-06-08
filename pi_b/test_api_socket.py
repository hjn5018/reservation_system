import json
import socket
import time
import urllib.request
from datetime import datetime, timedelta

def send_http_request(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
        json_data = json.dumps(data).encode('utf-8')
    else:
        json_data = None
        
    try:
        with urllib.request.urlopen(req, data=json_data, timeout=5) as response:
            res_data = response.read().decode('utf-8')
            return response.status, json.loads(res_data)
    except urllib.error.HTTPError as e:
        res_data = e.read().decode('utf-8')
        try:
            return e.code, json.loads(res_data)
        except Exception:
            return e.code, res_data
    except Exception as e:
        return 0, str(e)

def send_socket_command(host, port, command_dict):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))
        s.sendall(json.dumps(command_dict).encode('utf-8'))
        response = s.recv(1024).decode('utf-8')
        s.close()
        return json.loads(response)
    except Exception as e:
        return {"result": "error", "message": str(e)}

def run_tests():
    print("=== 스마트 회의실 통합 검증 테스트 시작 ===")
    
    api_url = "http://localhost:5000/api/reservations"
    status_url = "http://localhost:5000/api/status"
    socket_host = "localhost"
    socket_port = 9000
    
    # 0. 초기 상태 확인
    print("\n[테스트 0] 초기 예약 리스트 조회")
    status, res = send_http_request(api_url, "GET")
    print(f"Status: {status}, Data: {res}")
    
    # 기존 예약 다 지우기 (초기화)
    if status == 200 and isinstance(res, list):
        for item in res:
            del_status, del_res = send_http_request(f"{api_url}/{item['id']}", "DELETE")
            print(f"기존 예약 ID {item['id']} 삭제 결과: {del_status}")
            
    # 1. 예약 등록 (미래 시간)
    print("\n[테스트 1] 미래 시간 예약 등록 (10분 후 시작)")
    now = datetime.now()
    start_time = (now + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    end_time = (now + timedelta(minutes=70)).strftime("%Y-%m-%d %H:%M:%S")
    
    payload = {
        "title": "API Test Future Meeting",
        "start_time": start_time,
        "end_time": end_time
    }
    
    status, res = send_http_request(api_url, "POST", payload)
    print(f"Status: {status}, Data: {res}")
    assert status == 201, "예약 생성 실패"
    created_id = res["id"]
    
    # 2. 현재 상태 API 검사 (RESERVED여야 함)
    print("\n[테스트 2] 현재 회의실 상태 조회 (RESERVED 기대)")
    time.sleep(1.5) # 스케줄러 1초 주기 고려 대기
    status, res_status = send_http_request(status_url, "GET")
    print(f"Status: {status}, Data: {res_status}")
    assert res_status["actual_status"] == "RESERVED", "상태 불일치"
    
    # 3. 예약 중복 검사 테스트
    print("\n[테스트 3] 겹치는 시간대 예약 등록 시도 (실패 기대)")
    overlap_payload = {
        "title": "Overlap Meeting",
        "start_time": (now + timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": (now + timedelta(minutes=50)).strftime("%Y-%m-%d %H:%M:%S")
    }
    status, res = send_http_request(api_url, "POST", overlap_payload)
    print(f"Status: {status}, Data: {res}")
    assert status == 409, "중복 시간 예약 등록 방지 실패"
    
    # 4. TCP 소켓 강제 제어 테스트 (IN_MEETING으로 강제 오버라이드)
    print("\n[테스트 4] TCP 소켓을 이용한 긴급 상태 변경 (IN_MEETING 강제)")
    cmd = {"command": "force_status", "status": "IN_MEETING"}
    sock_res = send_socket_command(socket_host, socket_port, cmd)
    print(f"Socket Response: {sock_res}")
    assert sock_res["result"] == "success", "소켓 명령 실패"
    
    time.sleep(1.5)
    status, res_status = send_http_request(status_url, "GET")
    print(f"실시간 상태 (강제 적용 후): {res_status['actual_status']}")
    assert res_status["actual_status"] == "IN_MEETING", "강제 오버라이드 실패"
    
    # 5. TCP 소켓 강제 제어 복구 (AUTO로 전환)
    print("\n[테스트 5] TCP 소켓을 이용한 강제 모드 복구 (AUTO 복귀)")
    cmd = {"command": "force_status", "status": "AUTO"}
    sock_res = send_socket_command(socket_host, socket_port, cmd)
    print(f"Socket Response: {sock_res}")
    assert sock_res["result"] == "success", "소켓 명령 실패"
    
    time.sleep(1.5)
    status, res_status = send_http_request(status_url, "GET")
    print(f"실시간 상태 (원복 후): {res_status['actual_status']}")
    assert res_status["actual_status"] == "RESERVED", "자동 모드 원복 실패"
    
    # 6. 예약 삭제 테스트
    print("\n[테스트 6] 예약 삭제")
    status, res = send_http_request(f"{api_url}/{created_id}", "DELETE")
    print(f"Status: {status}, Data: {res}")
    assert status == 200, "예약 삭제 실패"
    
    # 7. 최종 상태 확인 (AVAILABLE 기대)
    print("\n[테스트 7] 예약 삭제 후 최종 회의실 상태 조회 (AVAILABLE 기대)")
    time.sleep(1.5)
    status, res_status = send_http_request(status_url, "GET")
    print(f"Status: {status}, Data: {res_status}")
    assert res_status["actual_status"] == "AVAILABLE", "상태 원복 실패"
    
    print("\n=== 모든 통합 검증 테스트 통과 완료! ===")

if __name__ == "__main__":
    run_tests()
