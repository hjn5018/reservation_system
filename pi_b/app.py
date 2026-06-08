import os
import json
import time
import socket
import threading
from datetime import datetime
from flask import Flask, request, jsonify

# 로컬 모듈 임포트
from storage.json_store import JsonReservationRepository
from storage.sqlite_store import SqliteReservationRepository
from hardware.lcd import LcdController
from hardware.led import LedController
from hardware.buzzer import BuzzerController

app = Flask(__name__)

# 전역 설정 및 드라이버 객체 초기화용 변수
config = {}
db = None
lcd = None
led = None
buzzer = None

# 긴급 상태 오버라이드 관리
# force_mode가 활성화되어 있으면 스케줄러 자동 제어를 일시 중단하고 강제된 상태를 보여줌.
# force_mode가 "AUTO" 이면 자동 모드로 동작.
force_status = "AUTO" 

# 백그라운드 스케줄러 상태 추적용
last_active_status = None

def load_config():
    global config
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"[App] config.json 로드 실패: {e}")
        # 기본값 fallback
        config = {
            "server": {"host": "0.0.0.0", "port": 5000, "socket_port": 9000},
            "storage": {"type": "json", "json_path": "storage/reservations.json", "sqlite_path": "storage/reservations.db"},
            "lcd": {"mode": "I2C", "i2c_address": "0x27"},
            "rgb_led": {"red_pin": 17, "green_pin": 27, "blue_pin": 22},
            "buzzer": {"pin": 18},
            "mock": True
        }

def initialize_components():
    global db, lcd, led, buzzer
    load_config()
    
    # 1. DB 초기화
    storage_cfg = config.get("storage", {})
    storage_type = storage_cfg.get("type", "json").lower()
    
    if storage_type == "sqlite":
        db_path = storage_cfg.get("sqlite_path", "storage/reservations.db")
        db = SqliteReservationRepository(db_path)
        print(f"[App] SQLite 저장소 활성화: {db_path}")
    else:
        json_path = storage_cfg.get("json_path", "storage/reservations.json")
        db = JsonReservationRepository(json_path)
        print(f"[App] JSON 저장소 활성화: {json_path}")
        
    # 2. 하드웨어 드라이버 초기화
    lcd = LcdController(config)
    led = LedController(config)
    buzzer = BuzzerController(config)
    
    # 초기 하드웨어 상태 설정
    lcd.display_status("INITIALIZING", "Please wait...")
    led.set_status("OFF")

def check_time_overlap(start1_str, end1_str, start2_str, end2_str):
    fmt = "%Y-%m-%d %H:%M:%S"
    s1 = datetime.strptime(start1_str, fmt)
    e1 = datetime.strptime(end1_str, fmt)
    s2 = datetime.strptime(start2_str, fmt)
    e2 = datetime.strptime(end2_str, fmt)
    # 두 구간이 겹치려면: s1 < e2 이고 s2 < e1
    return s1 < e2 and s2 < e1

# CORS 처리를 위한 미들웨어 (PHP 프런트가 다른 도메인/포트에서 접속할 수 있으므로 간단한 헤더 추가)
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    return response

@app.route("/api/reservations", methods=["GET"])
def get_reservations():
    try:
        reservations = db.get_all()
        return jsonify(reservations), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500

@app.route("/api/reservations", methods=["POST"])
def add_reservation():
    try:
        data = request.json
        if not data:
            return jsonify({"result": "error", "message": "No JSON payload provided"}), 400
            
        title = data.get("title")
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        
        if not all([title, start_time, end_time]):
            return jsonify({"result": "error", "message": "Missing required fields: title, start_time, end_time"}), 400
            
        # 1. 시간 형식 유효성 체크
        fmt = "%Y-%m-%d %H:%M:%S"
        try:
            s_dt = datetime.strptime(start_time, fmt)
            e_dt = datetime.strptime(end_time, fmt)
        except ValueError:
            return jsonify({"result": "error", "message": "Invalid time format. Use YYYY-MM-DD HH:MM:SS"}), 400
            
        if s_dt >= e_dt:
            return jsonify({"result": "error", "message": "Start time must be before end_time"}), 400
            
        # 2. 예약 시간 중복 검사
        existing = db.get_all()
        for res in existing:
            if check_time_overlap(start_time, end_time, res["start_time"], res["end_time"]):
                return jsonify({
                    "result": "error", 
                    "message": f"Time overlap with existing meeting '{res['title']}' ({res['start_time']} ~ {res['end_time']})"
                }), 409
                
        # 3. 예약 생성
        new_res = db.add(title, start_time, end_time)
        
        # 만약 신규 예약이 현재 시간에 즉시 걸쳐있다면 백그라운드 스레드에서 다음 루프 시 감지하지만, 즉시 제어 반응을 주도록 트리거 가능.
        return jsonify({
            "result": "success", 
            "message": "Reservation created successfully",
            "id": new_res["id"]
        }), 201
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500

@app.route("/api/reservations/<int:res_id>", methods=["DELETE"])
def delete_reservation(res_id):
    try:
        # 삭제 대상 확인
        res = db.get_by_id(res_id)
        if not res:
            return jsonify({"result": "error", "message": "Reservation not found"}), 404
            
        success = db.delete(res_id)
        if success:
            return jsonify({"result": "success", "message": "Reservation deleted successfully"}), 200
        else:
            return jsonify({"result": "error", "message": "Failed to delete reservation"}), 500
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500

@app.route("/api/force_status", methods=["POST"])
def api_force_status():
    global force_status
    try:
        data = request.json or {}
        status = data.get("status", "AUTO").upper()
        
        valid_statuses = ["AUTO", "AVAILABLE", "RESERVED", "IN_USE"]
        if status not in valid_statuses:
            return jsonify({"result": "error", "message": f"Invalid status. Choose from {valid_statuses}"}), 400
            
        force_status = status
        print(f"[App] HTTP API 강제 제어 수신: {force_status}")
        
        # 소켓 수신 시와 동일하게 스케줄러가 즉시 상태 변화를 감지하도록 last_active_status를 None으로 해서 하드웨어 강제 동기화
        update_hardware_immediately()
        
        return jsonify({"result": "success", "message": f"Status forced to {force_status}"}), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500

@app.route("/api/status", methods=["GET"])
def get_current_status():
    """현재 활성화된 실제 상태와 진행 중이거나 대기 중인 예약 정보를 제공하는 모니터링 API"""
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reservations = db.get_all()
        
        computed_status = "AVAILABLE"
        active_meeting = None
        next_meeting = None
        
        # 현재 시간에 해당하는 예약 찾기
        for res in reservations:
            if res["start_time"] <= now_str < res["end_time"]:
                computed_status = "IN_USE"
                active_meeting = res
                break
                
        # 현재 진행 중인 예약이 없을 시, 가장 가까운 미래 예약 찾기
        if computed_status != "IN_USE":
            future_meetings = [r for r in reservations if r["start_time"] > now_str]
            if future_meetings:
                # 시작 시간순 정렬
                future_meetings.sort(key=lambda x: x["start_time"])
                computed_status = "RESERVED"
                next_meeting = future_meetings[0]
                
        # 긴급 강제 상태 오버라이드 반영
        actual_status = computed_status if force_status == "AUTO" else force_status
        
        return jsonify({
            "current_time": now_str,
            "computed_status": computed_status,
            "force_status": force_status,
            "actual_status": actual_status,
            "active_meeting": active_meeting,
            "next_meeting": next_meeting
        }), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 500

def update_hardware_immediately():
    """스케줄러 대기 없이 즉시 하드웨어 상태를 강제 동기화시키기 위해 스케줄러 상태를 리셋"""
    global last_active_status
    last_active_status = None

# =====================================================================
# Background Scheduler Thread
# =====================================================================
def scheduler_loop():
    global last_active_status, force_status
    print("[Scheduler] 백그라운드 스케줄러 루프가 시작되었습니다.")
    
    while True:
        try:
            now_dt = datetime.now()
            now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # DB 예약 목록 확인
            reservations = db.get_all()
            
            computed_status = "AVAILABLE"
            active_meeting = None
            next_meeting = None
            
            # 1. 진행 중 예약 검사
            for res in reservations:
                if res["start_time"] <= now_str < res["end_time"]:
                    computed_status = "IN_USE"
                    active_meeting = res
                    break
                    
            # 2. 예정 예약 검사 (진행 중 예약이 없을 시)
            if computed_status != "IN_USE":
                future_meetings = [r for r in reservations if r["start_time"] > now_str]
                if future_meetings:
                    future_meetings.sort(key=lambda x: x["start_time"])
                    computed_status = "RESERVED"
                    next_meeting = future_meetings[0]
            
            # 3. 강제 오버라이드 유무 반영
            target_status = computed_status if force_status == "AUTO" else force_status
            
            # 4. DB 상태 필드 갱신 (예약 항목이 있는 경우 상태 동기화)
            # - IN_USE 상태일 때, 해당 예약의 DB status를 "IN_USE"으로 변경
            # - RESERVED 상태일 때, 해당 예약의 DB status를 "RESERVED"로 변경
            for res in reservations:
                # 현재 해당 예약의 DB에 기록된 상태가 다른 경우만 갱신
                if res["start_time"] <= now_str < res["end_time"]:
                    if res["status"] != "IN_USE":
                        db.update_status(res["id"], "IN_USE")
                elif res["start_time"] > now_str:
                    if res["status"] != "RESERVED":
                        db.update_status(res["id"], "RESERVED")
                else:
                    # 지난 예약
                    if res["status"] != "AVAILABLE":
                        db.update_status(res["id"], "AVAILABLE")
            
            # 5. 상태 전환 시 하드웨어 작동 (LED, LCD, 부저)
            if target_status != last_active_status:
                print(f"[Scheduler] 상태 전환 감지: {last_active_status} -> {target_status}")
                
                # LCD 내용 결정
                lcd_title = ""
                if target_status == "IN_USE" and active_meeting:
                    lcd_title = active_meeting["title"]
                elif target_status == "RESERVED" and next_meeting:
                    lcd_title = next_meeting["title"]
                elif target_status == "AVAILABLE":
                    lcd_title = "Empty Aud."
                elif force_status != "AUTO":
                    lcd_title = "FORCE MODE ACTIVE"
                
                # 하드웨어 업데이트
                lcd.display_status(target_status, lcd_title)
                led.set_status(target_status)
                
                # 알림음 재생 트리거
                # AVAILABLE -> IN_USE (또는 RESERVED -> IN_USE) : 시작 멜로디
                if target_status == "IN_USE" and last_active_status in ["AVAILABLE", "RESERVED"]:
                    buzzer.play_start_melody()
                # IN_USE -> AVAILABLE (또는 IN_USE -> RESERVED) : 종료 멜로디
                elif last_active_status == "IN_USE" and target_status in ["AVAILABLE", "RESERVED"]:
                    buzzer.play_end_melody()
                
                last_active_status = target_status
                
        except Exception as e:
            print(f"[Scheduler] 오류 발생: {e}")
            
        time.sleep(1)

# =====================================================================
# TCP Socket Server Thread (긴급 제어 명령 처리)
# =====================================================================
def socket_server_loop():
    global force_status
    socket_cfg = config.get("server", {})
    host = socket_cfg.get("host", "0.0.0.0")
    port = socket_cfg.get("socket_port", 9000)
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 포트 재사용 옵션 설정
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"[Socket Server] TCP 긴급 제어 포트 {port} 대기 시작...")
    except Exception as e:
        print(f"[Socket Server] 바인딩 실패: {e}")
        return

    while True:
        try:
            client_socket, addr = server_socket.accept()
            print(f"[Socket Server] 연결 수신: {addr}")
            
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data:
                client_socket.close()
                continue
                
            print(f"[Socket Server] 수신 데이터: {data}")
            
            try:
                cmd_json = json.loads(data)
                command = cmd_json.get("command")
                
                if command == "force_status":
                    status = cmd_json.get("status", "AUTO").upper()
                    valid_statuses = ["AUTO", "AVAILABLE", "RESERVED", "IN_USE"]
                    
                    if status in valid_statuses:
                        force_status = status
                        print(f"[Socket Server] 강제 상태 변경 적용: {force_status}")
                        update_hardware_immediately()
                        
                        response = {"result": "success", "message": f"Forced status set to {force_status}"}
                    else:
                        response = {"result": "error", "message": f"Invalid status '{status}'"}
                else:
                    response = {"result": "error", "message": f"Unknown command '{command}'"}
            except json.JSONDecodeError:
                response = {"result": "error", "message": "Invalid JSON format"}
                
            client_socket.sendall(json.dumps(response).encode('utf-8'))
            client_socket.close()
            
        except Exception as e:
            print(f"[Socket Server] 루프 내 오류 발생: {e}")
            time.sleep(1)

# =====================================================================
# Main 구동부
# =====================================================================
if __name__ == "__main__":
    initialize_components()
    
    # 스케줄러 스레드 구동
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()
    
    # TCP 소켓 스레드 구동
    socket_thread = threading.Thread(target=socket_server_loop, daemon=True)
    socket_thread.start()
    
    # Flask 앱 구동
    server_cfg = config.get("server", {})
    host = server_cfg.get("host", "0.0.0.0")
    port = server_cfg.get("port", 5000)
    
    print(f"[App] Flask REST API 서버 시작: {host}:{port}")
    try:
        # debug=False로 설정해야 백그라운드 스레드들이 2번 중복 기동되는 것을 막을 수 있음
        app.run(host=host, port=port, debug=False)
    finally:
        # 종료 시 자원 해제
        if lcd: lcd.close()
        if led: led.close()
        if buzzer: buzzer.close()
