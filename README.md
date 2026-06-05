# Smart Meeting Room Reservation System

두 대의 Raspberry Pi(Pi A: Apache 웹서버, Pi B: Flask 제어 및 하드웨어 제어 서버)를 활용한 IoT 스마트 회의실 예약 및 상태 관리 시스템입니다.

## 주요 특징
- **Pi A / Pi B 다중 구조**: 하나의 깃 리포지토리 안에서 Pi A(웹 인터페이스)와 Pi B(하드웨어 제어 및 DB)를 디렉토리 단위로 깔끔하게 격리하여 각각 독립적인 배포가 가능합니다.
- **I2C & Direct GPIO LCD 듀얼 모드**: LCD1602 모듈에 I2C 모듈(PCF8574 등)이 결합된 경우와 결합되지 않은 일반 GPIO 핀 직결 방식 모두 설정 파일(`config.json`) 수정을 통해 지원합니다.
- **JSON 파일 데이터베이스 및 SQLite 확장성**: 최초 프로토타이핑 시 데이터베이스 서버 없이도 단순하게 파일로 저장되는 JSON 데이터 저장 방식을 제공하며, Repository Pattern(인터페이스 추상화)을 구현하여 차후 SQLite 등 SQL DB로 설정 변경만으로 즉시 마이그레이션이 가능합니다.

---

## 디렉토리 구조 (Directory Structure)

```text
reservation_system/ (Git Root)
├── README.md               # 프로젝트 전체 가이드 및 퀵스타트
├── scripts/                # 라즈베리파이별 자동 설정 쉘 스크립트
│   ├── setup_pi_a.sh       # Pi A용 패키지(Apache, PHP) 설치 및 소스 동기화 스크립트
│   └── setup_pi_b.sh       # Pi B용 가상환경(venv) 및 파이썬 라이브러리 자동 구축 스크립트
├── pi_a/                   # Raspberry Pi A - Web Server PHP 소스 코드
│   ├── index.php           # 사용자 통합 예약 관리 및 모니터링 UI
│   ├── api_client.php      # Pi B Flask API 통신 담당 PHP Helper
│   ├── css/
│   │   └── style.css       # 미려한 모던 스타일시트
│   └── js/
│       └── app.js          # 실시간 비동기(AJAX) 예약 갱신 및 상태 모니터링 JS
└── pi_b/                   # Raspberry Pi B - Control Server Python 소스 코드
    ├── app.py              # Flask 메인 서버 (REST API & 백그라운드 시간 분석 스레드)
    ├── config.json         # 하드웨어 핀 및 저장소 설정 파일 (LCD 모드, 핀 맵 등)
    ├── requirements.txt    # Python 의존 패키지 목록
    ├── storage/            # 데이터 저장 레이어 (JSON & SQLite 추상화)
    │   ├── __init__.py
    │   ├── base.py         # ReservationRepository (추상 기본 클래스 인터페이스)
    │   ├── json_store.py   # JsonReservationRepository (JSON 파일 기반 저장 구현)
    │   ├── sqlite_store.py # SqliteReservationRepository (추후 마이그레이션용 구현 Stub)
    │   └── reservations.json # JSON 데이터 파일
    └── hardware/           # 하드웨어 제어 추상화 모듈
        ├── __init__.py
        ├── lcd.py          # LCD1602 제어 드라이버 (I2C 모드 & Direct GPIO 모드)
        ├── led.py          # RGB LED 제어 (Green/Blue/Red)
        └── buzzer.py       # Passive Buzzer 제어 (시작/종료 알림음)
```

---

## 하드웨어 연결 및 설정 (GPIO Pin Mapping)

라즈베리파이와 센서 간의 물리 핀 맵 구성 정보입니다. `pi_b/config.json` 파일을 수정하여 핀 구성을 커스텀할 수 있습니다.

### 1. LCD1602 설정 (`lcd_mode` 옵션)
- **I2C 모드 (`"I2C"`)**: LCD 뒤에 I2C 백팩 모듈이 납땜되어 있을 때 사용합니다.
  - SDA (GPIO2), SCL (GPIO3) 단 2개의 신호선만 사용하여 연결합니다.
- **GPIO Direct 모드 (`"GPIO"`)**: LCD 모듈 단독으로 존재하여 6개의 데이터/제어 핀을 라즈베리 파이에 직접 매핑하여 사용합니다.
  - RS, E, D4, D5, D6, D7을 지정된 GPIO 핀에 1:1로 매핑합니다.

### 2. RGB LED 및 부저 연결
- **RGB LED**: Green (GPIO27), Blue (GPIO22), Red (GPIO17)
- **Passive Buzzer**: PWM 신호 출력 (GPIO18)

---

## 빠른 시작 가이드 (Quick Start Guide)

깃허브(GitHub)에 코드를 업로드한 후, 각 라즈베리 파이에서 아래의 과정을 통해 쉽게 코드를 배포 및 실행할 수 있습니다.

### 1. 공통 준비 단계 (각 라즈베리 파이에서)
```bash
# 코드 클론
git clone <your-github-repo-url>
cd reservation_system
```

### 2. Raspberry Pi A (Web Server) 설정 및 실행
Pi A에서는 제공되는 쉘 스크립트를 통해 Apache 웹 서버와 PHP를 자동 설치하고 소스 코드를 웹 경로(`/var/www/html`)로 배포합니다.
```bash
# 배포 스크립트 실행 권한 부여 및 실행
chmod +x scripts/setup_pi_a.sh
./scripts/setup_pi_a.sh
```
설치 완료 후 웹 브라우저에서 `http://<Pi_A_IP_Address>/`로 접속하면 예약 관리 웹 UI가 나타납니다.

### 3. Raspberry Pi B (Control & GPIO Server) 설정 및 실행
Pi B에서는 하드웨어 제어용 패키지(파이썬 가상환경 설치 포함)와 Flask 구동 라이브러리를 구성합니다.
```bash
# 배포 스크립트 실행 권한 부여 및 실행
chmod +x scripts/setup_pi_b.sh
./scripts/setup_pi_b.sh

# 가상 환경 활성화 후 Flask 서버 기동
source pi_b/venv/bin/activate
cd pi_b
python app.py
```

---

## 설정 파일 구성 예시 (`pi_b/config.json`)

Pi B의 서버 포트 및 사용 저장소(JSON vs SQLite), LCD1602 하드웨어 모드를 구성합니다.

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "socket_port": 9000
  },
  "storage": {
    "type": "json",
    "json_path": "storage/reservations.json",
    "sqlite_path": "storage/reservations.db"
  },
  "lcd": {
    "mode": "I2C",
    "i2c_address": "0x27",
    "pins": {
      "rs": 26,
      "e": 19,
      "d4": 13,
      "d5": 6,
      "d6": 5,
      "d7": 11
    }
  },
  "rgb_led": {
    "red_pin": 17,
    "green_pin": 27,
    "blue_pin": 22
  },
  "buzzer": {
    "pin": 18
  }
}
```
> **Tip:** LCD를 직접 GPIO 핀으로 연결할 때는 `"mode": "GPIO"`로 수정하고 하단의 `pins` 설정을 회로 배선에 맞게 변경하십시오. SQLite DB를 적용하고 싶을 때는 `"type": "sqlite"`로만 변경하면 저장 시스템이 즉시 전환됩니다.
