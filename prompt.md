# Project Prompt (v2.0)

## 프로젝트명
**Web-based Smart Meeting Room Reservation System (JSON & Dual-LCD Mode Support)**

## 프로젝트 개요
본 프로젝트는 두 대의 Raspberry Pi를 이용하여 회의실 예약 및 상태 관리 시스템을 구현합니다.
깃허브 리포지토리를 하나로 통합하되, Pi A와 Pi B의 역할에 따라 디렉토리를 분리하여 배포를 용이하게 합니다.

* **Pi A (Apache + PHP)**: 사용자에게 예약 관리 및 조회 웹 페이지를 제공합니다. 데이터 동기화 이슈를 방지하기 위해 자체 DB를 가지지 않고, Pi B의 Flask REST API를 호출하여 예약 데이터를 생성, 조회 및 삭제합니다.
* **Pi B (Flask Control Server + GPIO)**: LCD1602, RGB LED, Passive Buzzer를 제어합니다. 로컬 JSON 파일(`reservations.json`)을 임시 데이터베이스로 사용하여 예약 목록을 보관 및 갱신하고, 백그라운드 스레드를 통해 예약 시간에 맞추어 하드웨어 상태를 실시간으로 업데이트합니다.
* **통신 구조**:
  - 사용자는 웹 브라우저를 통해 Pi A(Apache/PHP)에 접속합니다.
  - Pi A는 백엔드에서 Pi B의 Flask API(HTTP JSON REST)를 호출하여 데이터를 조작합니다.
  - 실시간 제어 명령 또는 긴급 상태 변경 알림은 TCP Socket 통신을 통해서도 가능하도록 하이브리드로 구성합니다.

---

# Directory Structure
GitHub 리포지토리는 다음과 같이 분할되어 각 Raspberry Pi 기기에서 필요한 부분만 쉽게 설정할 수 있도록 합니다.

```text
reservation_system/ (Git Root)
├── README.md               # 프로젝트 전체 가이드 및 퀵스타트
├── scripts/                # 라즈베리파이별 자동 설정 쉘 스크립트
│   ├── setup_pi_a.sh       # Pi A 환경 구축 (Apache, PHP 설치 및 웹 루트 설정)
│   └── setup_pi_b.sh       # Pi B 환경 구축 (Python venv, GPIO 및 Flask 라이브러리 설치)
├── pi_a/                   # Raspberry Pi A - Web Server 소스 코드
│   ├── index.php           # 예약 등록 & 현황판 통합 UI
│   ├── api_client.php      # Pi B Flask API와 통신을 담당하는 Helper 클래스
│   ├── css/
│   │   └── style.css       # 미려하고 프리미엄한 웹 UI 디자인 스타일시트
│   └── js/
│       └── app.js          # 실시간 비동기(AJAX) 예약 갱신 및 상태 모니터링
└── pi_b/                   # Raspberry Pi B - Control Server 소스 코드
    ├── app.py              # Flask 메인 서버 (REST API 및 백그라운드 스케줄러 실행)
    ├── config.json         # 하드웨어 및 저장소 설정 파일 (LCD 모드, 핀 맵 등)
    ├── requirements.txt    # Python 의존 패키지 목록
    ├── storage/            # 데이터 저장 레이어
    │   ├── __init__.py
    │   ├── base.py         # ReservationRepository (추상 기본 클래스)
    │   ├── json_store.py   # JsonReservationRepository (JSON 파일 기반 저장소 구현)
    │   ├── sqlite_store.py # SqliteReservationRepository (추후 마이그레이션용 Stub)
    │   └── reservations.json # JSON 데이터 파일
    └── hardware/           # 하드웨어 제어 추상화 모듈
        ├── __init__.py
        ├── lcd.py          # LCD1602 제어 드라이버 (I2C 모드 & Direct GPIO 모드 동시 지원)
        ├── led.py          # RGB LED 제어 (AVAILABLE-Green, RESERVED-Blue, IN_MEETING-Red)
        └── buzzer.py       # Passive Buzzer 제어 (회의 시작/종료 멜로디 재생)
```

---

# Hardware Design & GPIO Assignment

## 1. LCD1602 Dual-Mode Support
설정 파일(`config.json`)의 `lcd_mode` 값(`"I2C"` 또는 `"GPIO"`)에 따라 하드웨어 드라이버가 다르게 동작하도록 추상화합니다.

### A. I2C 모듈이 장착된 경우 (`"lcd_mode": "I2C"`)
* SDA, SCL 단 2개의 데이터 선만 사용하여 연결합니다.
* 라이브러리: `RPLCD.i2c` 또는 `smbus` 계열 사용.
* **I2C 기본 주소**: 주로 `0x27` 또는 `0x3F`.

### B. I2C 모듈이 없는 경우 (Direct GPIO 연결) (`"lcd_mode": "GPIO"`)
* LCD1602의 GPIO 핀들을 직접 라즈베리 파이에 매핑합니다 (4비트 모드 기준 최소 6개 핀 필요).
* 라이브러리: `RPLCD.gpio` (Rpi.GPIO 기반) 사용.

### GPIO Pin Map List (Default)

| Device | Type/Pin | GPIO (BCM) | Description |
| :--- | :--- | :--- | :--- |
| **LCD1602 (I2C Mode)** | SDA | GPIO2 (Pin 3) | I2C Data (I2C 모드 시 필수) |
| | SCL | GPIO3 (Pin 5) | I2C Clock (I2C 모드 시 필수) |
| **LCD1602 (GPIO Mode)**| RS | GPIO26 | Register Select (Direct 모드) |
| | E | GPIO19 | Enable (Direct 모드) |
| | D4 | GPIO13 | Data Bit 4 (Direct 모드) |
| | D5 | GPIO6 | Data Bit 5 (Direct 모드) |
| | D6 | GPIO5 | Data Bit 6 (Direct 모드) |
| | D7 | GPIO11 | Data Bit 7 (Direct 모드) |
| **RGB LED** | Red | GPIO17 | RGB LED 적색 제어 |
| | Green | GPIO27 | RGB LED 녹색 제어 |
| | Blue | GPIO22 | RGB LED 청색 제어 |
| **Passive Buzzer** | PWM | GPIO18 | 피에조 부저 주파수 음계 제어 |

---

# Storage Strategy (JSON to SQL)

데이터베이스 교체의 용이성을 확보하기 위해 **Repository Pattern**을 적용합니다. 
`pi_b/storage/base.py`에 추상 클래스 `ReservationRepository`를 정의하고, 모든 비즈니스 로직(Flask API, Background Thread)은 이 추상 인터페이스를 통해서만 데이터에 접근하게 만듭니다.

### 1. JSON 기반 저장소 우선 적용 (`json_store.py`)
* `reservations.json` 파일에 JSON 포맷으로 예약 정보를 저장합니다.
* 읽기/쓰기 시 파일 입출력(File I/O) 락(Lock)을 걸어 동시성 이슈를 예방합니다.

### 2. SQL 기반 저장소로 확장 가능 구조 (`sqlite_store.py`)
* 프로젝트 배포 및 기본 검증이 끝난 후, `sqlite_store.py`를 구현하여 SQLite DB로 교체가 가능하게 만듭니다.
* 인터페이스가 완전히 동일하기 때문에, `config.json`의 `"storage_type"`을 `"json"`에서 `"sqlite"`로 수정하는 것만으로 데이터베이스 엔진 마이그레이션이 완료됩니다.

#### Reservations JSON Schema Example
```json
[
  {
    "id": 1,
    "title": "IoT Project Review",
    "start_time": "2026-06-05 18:00:00",
    "end_time": "2026-06-05 19:00:00",
    "status": "RESERVED"
  }
]
```

---

# State & Scenario Design

## 1. 회의실 상태 정의
* **AVAILABLE**: 회의실 비어 있음. (LCD: `AVAILABLE`, RGB LED: `GREEN`)
* **RESERVED**: 예약 완료, 시작 전 대기. (LCD: `RESERVED`, RGB LED: `BLUE`)
* **IN_MEETING**: 회의 진행 중. (LCD: `IN MEETING`, RGB LED: `RED`)

## 2. 상태 전환 트리거
* **AVAILABLE -> RESERVED**: 사용자가 웹페이지(Pi A)에서 미래 시간대의 예약을 등록했을 때.
* **RESERVED -> IN_MEETING**: 현재 시간이 예약 시작 시간에 도달했을 때.
  - *부저 알림음*: 도(C4) -> 미(E4) -> 솔(G4) 3음 재생.
* **IN_MEETING -> AVAILABLE**: 현재 시간이 예약 종료 시간에 도달했을 때.
  - *부저 알림음*: 솔(G4) -> 미(E4) -> 도(C4) 3음 재생.
* **예약 즉시 시작**: 현재 시간 범위 내로 예약이 등록되면 즉시 `IN_MEETING` 상태로 진입하고 LED 및 부저 피드백이 발생합니다.

---

# API & Communication Protocol

Pi A(Apache/PHP)와 Pi B(Flask) 간에는 JSON HTTP API를 기본으로 사용합니다.

### 1. 예약 목록 조회
* **GET** `/api/reservations`
* **Response**:
  ```json
  [
    {
      "id": 1,
      "title": "Design Meeting",
      "start_time": "2026-06-05 18:00:00",
      "end_time": "2026-06-05 19:00:00",
      "status": "RESERVED"
    }
  ]
  ```

### 2. 예약 신규 등록
* **POST** `/api/reservations`
* **Payload**:
  ```json
  {
    "title": "Design Meeting",
    "start_time": "2026-06-05 18:00:00",
    "end_time": "2026-06-05 19:00:00"
  }
  ```
* **Response**:
  ```json
  {
    "result": "success",
    "message": "Reservation created successfully",
    "id": 2
  }
  ```

### 3. 예약 삭제
* **DELETE** `/api/reservations/<int:id>`
* **Response**:
  ```json
  {
    "result": "success",
    "message": "Reservation deleted successfully"
  }
  ```

### 4. 실시간 긴급 상태 강제 제어 (TCP Socket - 선택 사양)
* Pi B는 TCP `Port 9000`에서 백그라운드 소켓 서버를 열어두어, 긴급 강제 명령 수신이 가능하게 구성합니다.
* **Payload**: `{"command": "force_status", "status": "AVAILABLE"}`

---

# Project Task List

## Phase 1. 환경 구축 및 구조 설계 (Setup)
* [ ] GitHub 리포지토리 폴더 구조 생성 (`pi_a`, `pi_b`, `scripts`)
* [ ] Pi A 설정 자동화 스크립트 작성 (`setup_pi_a.sh`)
* [ ] Pi B 설정 자동화 스크립트 작성 (`setup_pi_b.sh`)
* [ ] Pi B 설정 파일(`config.json`) 설계 및 구조 구축

## Phase 2. 데이터 저장소 추상화 및 JSON DB 구축 (Storage)
* [ ] `pi_b/storage/base.py`에 `ReservationRepository` 추상화 클래스 설계
* [ ] `pi_b/storage/json_store.py` 구현 (`reservations.json` 파일 읽기/쓰기 구현)
* [ ] 저장소 유닛 테스트 코드 작성 (JSON 데이터 생성, 조회, 삭제 기능 확인)

## Phase 3. 하드웨어 드라이버 추상화 (Hardware GPIO)
* [ ] `pi_b/hardware/lcd.py` 구현
  - `config.json`의 `lcd_mode`를 동적으로 읽어 `RPLCD.i2c` 혹은 `RPLCD.gpio` 초기화 구현
* [ ] `pi_b/hardware/led.py` 구현 (RGB LED 제어 및 상태별 색상 출력 매핑)
* [ ] `pi_b/hardware/buzzer.py` 구현 (Passive Buzzer PWM 기반 멜로디 재생 함수)
* [ ] Mock(가상) 하드웨어 드라이버 구성 (라즈베리파이가 없는 PC 테스트 환경 지원을 위해 GPIO 에러 예외처리 및 터미널 출력 대체 코드 포함)

## Phase 4. Pi B 제어 서버 & API 구축 (Control Server)
* [ ] Flask 기반 REST API 구현 (예약 조회, 등록, 삭제 API)
* [ ] 백그라운드 스케줄러 스레드 구현
  - 1초 간격으로 JSON DB의 예약을 조회하여 현재 시간과 예약 시간을 비교
  - 상태 전환 조건 만족 시 하드웨어(LCD, LED, Buzzer) 드라이버 호출 및 예약 상태 변경 저장
* [ ] TCP Socket 서버 구현 (Port 9000에서 긴급 명령 수신용 백그라운드 스레드 가동)

## Phase 5. Pi A 웹 인터페이스 구현 (Web UI)
* [ ] `pi_a/index.php` 구현
  - 예약 현황 타임라인 뷰 및 신규 예약 폼 디자인
  - HSL 컬러, 부드러운 그라데이션, 반응형 그리드를 적용한 프리미엄 CSS 테마
* [ ] `pi_a/api_client.php` 구현 (cURL을 사용해 Pi B의 Flask API를 호출하는 PHP 헬퍼)
* [ ] `pi_a/js/app.js` 작성 (비동기 AJAX 예약 추가/삭제 및 주기적 상태 모니터링 폴링)

## Phase 6. 통합 테스트 및 DB 마이그레이션 (Test & SQL Expansion)
* [ ] 가상 환경(Mock)을 이용한 PC에서의 시뮬레이션 및 API 연동 테스트
* [ ] 실제 Raspberry Pi A, B에 각각 배포 스크립트를 통한 설치 및 테스트
* [ ] `pi_b/storage/sqlite_store.py`를 완성하여 SQLite DB 전환 가능 여부 최종 검증
