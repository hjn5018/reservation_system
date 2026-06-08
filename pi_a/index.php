<?php
require_once 'api_client.php';

// =====================================================================
// 1. AJAX API Proxy Layer
// =====================================================================
if (isset($_GET['action'])) {
    header('Content-Type: application/json');
    
    $action = $_GET['action'];
    
    switch ($action) {
        case 'get_status':
            $res = ApiClient::getStatus();
            if ($res['result'] === 'success') {
                echo json_encode($res['data']);
            } else {
                echo json_encode($res);
            }
            break;
            
        case 'get_reservations':
            $res = ApiClient::getReservations();
            if ($res['result'] === 'success') {
                echo json_encode($res['data']);
            } else {
                echo json_encode(array());
            }
            break;
            
        case 'add_reservation':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                echo json_encode(array("result" => "error", "message" => "POST method required"));
                break;
            }
            
            $input = json_decode(file_get_contents('php://input'), true);
            $title = isset($input['title']) ? trim($input['title']) : '';
            $startTime = isset($input['start_time']) ? trim($input['start_time']) : '';
            $endTime = isset($input['end_time']) ? trim($input['end_time']) : '';
            
            if (empty($title) || empty($startTime) || empty($endTime)) {
                echo json_encode(array("result" => "error", "message" => "Missing required fields"));
                break;
            }
            
            $res = ApiClient::addReservation($title, $startTime, $endTime);
            if ($res['result'] === 'success') {
                echo json_encode($res['data']);
            } else {
                echo json_encode($res);
            }
            break;
            
        case 'delete_reservation':
            if ($_SERVER['REQUEST_METHOD'] !== 'DELETE') {
                echo json_encode(array("result" => "error", "message" => "DELETE method required"));
                break;
            }
            
            $id = isset($_GET['id']) ? intval($_GET['id']) : 0;
            if ($id <= 0) {
                echo json_encode(array("result" => "error", "message" => "Invalid ID"));
                break;
            }
            
            $res = ApiClient::deleteReservation($id);
            if ($res['result'] === 'success') {
                echo json_encode($res['data']);
            } else {
                echo json_encode($res);
            }
            break;
            
        case 'force_status':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                echo json_encode(array("result" => "error", "message" => "POST method required"));
                break;
            }
            
            $input = json_decode(file_get_contents('php://input'), true);
            $status = isset($input['status']) ? strtoupper(trim($input['status'])) : 'AUTO';
            
            // 핵심 기능: 긴급 제어 명령은 TCP 소켓(fsockopen)을 사용하여 Pi B에 전달합니다.
            $res = ApiClient::forceStatusSocket($status);
            echo json_encode($res);
            break;
            
        default:
            echo json_encode(array("result" => "error", "message" => "Unknown action"));
            break;
    }
    exit;
}
// =====================================================================
// 2. HTML/UI Rendering Layer (Action이 없을 시 진입)
// =====================================================================
?>
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>스마트 회의실 예약 시스템</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="container">
        <!-- 상단 헤더 -->
        <header>
            <h1>Smart Meeting Room Board</h1>
            <p>IoT 기반 실시간 예약 현황 및 회의실 제어 시스템</p>
        </header>

        <!-- 메인 대시보드 그리드 -->
        <div class="dashboard-grid">
            <!-- 1. 실시간 모니터링 카드 -->
            <div class="glass-card">
                <div class="section-title">회의실 실시간 상태</div>
                <div class="status-display">
                    <div id="status-badge" class="status-badge status-AVAILABLE">AVAILABLE</div>
                    
                    <div class="meeting-info">
                        <h3 id="meeting-title">현재 예약 또는 진행 중인 회의가 없습니다.</h3>
                        <p id="meeting-time">-</p>
                    </div>
                    
                    <div id="timer-display" class="time-counter">00:00:00</div>
                </div>
            </div>

            <!-- 2. 긴급 오버라이드 제어 패널 -->
            <div class="glass-card emergency-panel">
                <div class="section-title">긴급 상태 강제 전환</div>
                <div class="control-btn-group">
                    <button id="btn-force-avail" class="control-btn">강제 AVAILABLE</button>
                    <button id="btn-force-meeting" class="control-btn">강제 IN_MEETING</button>
                    <button id="btn-auto" class="control-btn control-btn-full active-auto">자동 (AUTO) 원복</button>
                </div>
            </div>
        </div>

        <!-- 하단 메인 기능 그리드 (예약 폼 & 목록) -->
        <div class="main-grid">
            <!-- 1. 예약 신청 폼 -->
            <div class="glass-card">
                <div class="section-title">신규 회의실 예약</div>
                
                <div id="error-message" style="color: var(--status-meeting); background: var(--status-meeting-bg); padding: 0.75rem; border-radius: 8px; font-size: 0.9rem; margin-bottom: 1.2rem; display: none; border: 1px solid var(--status-meeting);"></div>
                
                <form id="reservation-form">
                    <div class="form-group">
                        <label for="title">회의 주제</label>
                        <input type="text" id="title" class="form-control" placeholder="예: IoT 프로젝트 주간 회의" required autocomplete="off">
                    </div>
                    
                    <div class="form-group">
                        <label for="date">예약 일자</label>
                        <input type="date" id="date" class="form-control" required>
                    </div>
                    
                    <div class="form-group" style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                        <div>
                            <label for="start-time">시작 시간</label>
                            <input type="time" id="start-time" class="form-control" required>
                        </div>
                        <div>
                            <label for="end-time">종료 시간</label>
                            <input type="time" id="end-time" class="form-control" required>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn-primary" style="margin-top: 1rem;">예약 등록하기</button>
                </form>
            </div>

            <!-- 2. 예약 타임라인 / 목록 -->
            <div class="glass-card">
                <div class="section-title">예약 및 진행 현황 목록</div>
                <div id="reservation-list" class="reservation-list">
                    <!-- Javascript가 실시간으로 목록을 렌더링합니다. -->
                    <div class="no-data">예약 정보를 불러오고 있습니다...</div>
                </div>
            </div>
        </div>
    </div>

    <!-- 스크립트 연결 -->
    <script src="js/app.js"></script>
</body>
</html>
