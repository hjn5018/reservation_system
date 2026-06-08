# Walkthrough - Smart Meeting Room Reservation System (v1.0)

스마트 회의실 예약 및 상태 제어 시스템 구축이 성황리에 완료되었습니다. 본 문서는 구현된 컴포넌트 목록, 동작 방식, 그리고 통합 테스트 결과를 상세하게 보여줍니다.

---

## 1. 구현된 컴포넌트 및 파일 목록

### Raspberry Pi B (Control Server)
- [config.json](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/config.json): 하드웨어 핀 및 저장소 타입(JSON/SQLite), 포트 바인딩 등의 정보를 담고 있는 핵심 설정 파일입니다.
- [requirements.txt](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/requirements.txt): Raspberry Pi 환경용 패키지 목록을 담고 있습니다.
- **저장소 레이어 (storage)**:
  - [base.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/storage/base.py): Repository Pattern을 구현하기 위한 추상 기본 인터페이스 클래스입니다.
  - [json_store.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/storage/json_store.py): 스레드 락(`threading.Lock`)을 활용해 파일 입출력 충돌을 방지한 JSON 저장소 파일입니다.
  - [sqlite_store.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/storage/sqlite_store.py): 데이터 유실 및 성능 최적화를 위한 SQLite DB 저장소 모듈입니다.
  - [__init__.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/storage/__init__.py): 저장소 패키지 엔트리포인트입니다.
- **하드웨어 제어 레이어 (hardware)**:
  - [lcd.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/hardware/lcd.py): LCD1602 드라이버입니다. I2C 및 Direct BCM 핀 매핑을 듀얼 지원하며, PC 테스팅을 위해 Mock 모드를 내장합니다.
  - [led.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/hardware/led.py): RGB LED를 제어하여 AVAILABLE(Green), RESERVED(Blue), IN_MEETING(Red) 상태를 표시합니다.
  - [buzzer.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/hardware/buzzer.py): Passive Buzzer PWM 제어로 회의 시작 및 종료 알림음(도-미-솔 / 솔-미-도)을 재생합니다.
  - [__init__.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/hardware/__init__.py): 하드웨어 패키지 엔트리포인트입니다.
- **메인 및 테스트 스크립트**:
  - [app.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/app.py): Flask Web API, 실시간 상태 검사 스케줄러 루프 및 TCP Socket Server(9000 포트 긴급 명령 대기)를 멀티스레딩으로 구동하는 종합 메인 스크립트입니다.
  - [test_storage.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/test_storage.py): 저장소 단독 CRUD 테스트를 실행합니다.
  - [test_api_socket.py](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_b/test_api_socket.py): 전체 REST API 및 TCP 소켓 긴급 제어 명령의 유효성 검증을 담당합니다.

### Raspberry Pi A (Web Server)
- [config.php](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_a/config.php): Pi B의 REST API 호스트 경로 및 소켓 주소를 동적 관리하는 설정 파일입니다.
- [api_client.php](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_a/api_client.php): PHP cURL 모듈을 사용해 REST API 요청을 보내고, `fsockopen`을 통해 Pi B 소켓 포트로 직접 긴급 상태 강제 전환 명령을 발송하는 PHP API Wrapper입니다.
- [style.css](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_a/css/style.css): 프리미엄 HSL 다크 테마 디자인과 Glassmorphism 효과, 그리고 반응형 Grid가 결합된 모던 스타일시트입니다.
- [app.js](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_a/js/app.js): AJAX 비동기 예약 신청 및 삭제를 처리하며, 3초 주기로 상태를 실시간 폴링하고, 남은 시간에 대한 카운트다운 타이머를 화면에 노출합니다.
- [index.php](file:///c:/Users/USER/Desktop/2502110649_jinyong/수업/2학년_1학기/IoT제어실습/reservation_system/pi_a/index.php): 브라우저 CORS 회피를 위해 AJAX 백엔드 프록시 역할과 HTML 템플릿 렌더링 역할을 동시에 제공하는 메인 엔트리 웹 파일입니다.

---

## 2. 통합 검증 및 테스트 통과 로그

시스템이 요구사항 정의서(`prompt.md`)대로 안전하게 연동되는지 검증하기 위해 로컬 호스트 PC에서 Flask 및 소켓 포트를 가동하고, **JSON 저장소 모드**와 **SQLite DB 저장소 모드** 각각에 대하여 전체 통합 검증 시나리오(`test_api_socket.py`)를 돌려 검증하였습니다.

### 시나리오 상세 동작 흐름
1. `GET /api/reservations`: 초기 예약 리스트가 빈 상태(`[]`)임을 확인.
2. `POST /api/reservations`: 미래 시간 대의 예약을 등록하고 ID(1번)가 생성됨을 확인.
3. `GET /api/status`: 실시간 상태 조회를 통해, 예약이 대기 상태인 `RESERVED`로 연동됨을 확인.
4. `POST /api/reservations`: 기존 예약 시간 범위와 겹치는 임의 예약을 재신청했을 때, 중복 예약 검출 기능에 의해 **409 Conflict** 에러가 정상적으로 반환됨을 확인.
5. **TCP Socket Command**: 포트 `9000`으로 긴급 강제 제어 명령(`force_status: IN_MEETING`)을 쏘았을 때, Mock LCD/LED에 상태 오버라이드가 즉각 반영되고 `GET /api/status`에서 실제 상태가 `IN_MEETING`으로 출력됨을 확인.
6. **TCP Socket Command**: 강제 모드를 해제(`force_status: AUTO`)했을 때, 실시간 스케줄러 자동 감지 모드로 다시 복귀하여 본래 예약 대기 상태인 `RESERVED`로 복원됨을 확인.
7. `DELETE /api/reservations/<id>`: 테스트로 등록했던 1번 예약을 삭제.
8. `GET /api/status`: 예약 목록 소거 후 최종 회의실 상태가 초기 상태인 `AVAILABLE`로 잘 복원됨을 최종 확인.

### SQLite DB 저장소 모드 검증 로그 (task-101)
```text
=== 스마트 회의실 통합 검증 테스트 시작 ===

[테스트 0] 초기 예약 리스트 조회
Status: 200, Data: []

[테스트 1] 미래 시간 예약 등록 (10분 후 시작)
Status: 201, Data: {'id': 1, 'message': 'Reservation created successfully', 'result': 'success'}

[테스트 2] 현재 회의실 상태 조회 (RESERVED 기대)
Status: 200, Data: {'active_meeting': None, 'actual_status': 'RESERVED', 'computed_status': 'RESERVED', 'current_time': '2026-06-08 16:12:11', 'force_status': 'AUTO', 'next_meeting': {'end_time': '2026-06-08 17:22:05', 'id': 1, 'start_time': '2026-06-08 16:22:05', 'status': 'RESERVED', 'title': 'API Test Future Meeting'}}

[테스트 3] 겹치는 시간대 예약 등록 시도 (실패 기대)
Status: 409, Data: {'message': "Time overlap with existing meeting 'API Test Future Meeting' (2026-06-08 16:22:05 ~ 2026-06-08 17:22:05)", 'result': 'error'}

[테스트 4] TCP 소켓을 이용한 긴급 상태 변경 (IN_MEETING 강제)
Socket Response: {'result': 'success', 'message': 'Forced status set to IN_MEETING'}
실시간 상태 (강제 적용 후): IN_MEETING

[테스트 5] TCP 소켓을 이용한 강제 모드 복구 (AUTO 복귀)
Socket Response: {'result': 'success', 'message': 'Forced status set to AUTO'}
실시간 상태 (원복 후): RESERVED

[테스트 6] 예약 삭제
Status: 200, Data: {'message': 'Reservation deleted successfully', 'result': 'success'}

[테스트 7] 예약 삭제 후 최종 회의실 상태 조회 (AVAILABLE 기대)
Status: 200, Data: {'active_meeting': None, 'actual_status': 'AVAILABLE', 'computed_status': 'AVAILABLE', 'current_time': '2026-06-08 16:12:26', 'force_status': 'AUTO', 'next_meeting': None}

=== 모든 통합 검증 테스트 통과 완료! ===
```

---

## 3. 종합 요약
- **하드웨어 듀얼 모드 지원**: I2C 모드(Address 16진수 자동 형변환 적용)와 BCM GPIO Direct 연결 방식을 설정 변경으로 모두 지원합니다.
- **플랫폼 추상화**: 라즈베리 파이 라이브러리 미탑재 환경(Windows, macOS)에서도 `ImportError` 예외 처리를 통해 터미널 가상 디스플레이 로그로 하드웨어 흐름을 에뮬레이션합니다.
- **저장소 독립성 확보**: 추상 기본 클래스를 통한 인터페이스 제공으로 `storage.type`을 `"json"`에서 `"sqlite"`로 스위칭하는 것만으로 완벽한 저장소 데이터 엔진 이전을 완료했습니다.
- **프리미엄 Web UI**: 다크모드, Glassmorphism, 3초 주기 실시간 비동기 폴링, 그리고 카운트다운 타이머 연동이 적용되어 뛰어난 미적 품질을 제공합니다.
