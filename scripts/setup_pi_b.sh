#!/bin/bash

# =====================================================================
# Raspberry Pi B (Control Server) 자동 설정 및 라이브러리 설치 스크립트
# =====================================================================

# 1. 스크립트 실행 환경 확인 (Root 권한 확인)
if [ "$EUID" -ne 0 ]; then
  echo "[Error] 이 스크립트는 root 권한으로 실행해야 합니다. sudo ./setup_pi_b.sh 로 실행해주세요."
  exit 1
fi

echo "=================================================="
echo "Raspberry Pi B (Control Server) 구성을 시작합니다..."
echo "=================================================="

# 2. 시스템 패키지 설치
echo "[1/4] 시스템 패키지 설치 중 (Python3, pip, venv, I2C 관련 도구)..."
apt-get update
apt-get install -y python3 python3-pip python3-venv python3-dev i2c-tools

# 3. Raspberry Pi I2C 인터페이스 활성화 (I2C 모듈 LCD 사용 시 필요)
echo "[2/4] Raspberry Pi I2C 인터페이스 활성화 시도 중..."
if command -v raspi-config >/dev/null 2>&1; then
  raspi-config nonint do_i2c 0
  echo "=> raspi-config를 통해 I2C 인터페이스를 활성화했습니다."
else
  echo "=> [Info] raspi-config 명령어를 찾을 수 없어 I2C 활성화 단계를 건너뜁니다. (라즈베리파이 기기 외 환경)"
fi

# 4. 가상환경 구성
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PI_B_DIR="$PROJECT_DIR/pi_b"

if [ -d "$PI_B_DIR" ]; then
  echo "[3/4] 파이썬 가상환경(venv) 생성 중..."
  cd "$PI_B_DIR" || exit 1
  python3 -m venv venv
  
  # 소유권을 일반 유저로 돌려주거나 현재 로그인된 사용자(보통 pi 또는 외부 유저)가 쓸 수 있도록 설정
  # sudo로 실행했으므로 원래 유저명을 확인하여 소유권 이전
  if [ -n "$SUDO_USER" ]; then
    chown -R "$SUDO_USER":"$SUDO_USER" venv
  fi

  echo "[4/4] 가상환경 내 의존성 패키지 설치 중..."
  # 원래 유저 권한으로 pip 패키지 설치
  if [ -n "$SUDO_USER" ]; then
    sudo -u "$SUDO_USER" ./venv/bin/pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
      sudo -u "$SUDO_USER" ./venv/bin/pip install -r requirements.txt
    else
      # requirements.txt가 없을 경우 기본 하드웨어 및 백엔드 라이브러리 직접 설치
      echo "=> requirements.txt가 없어 기본 패키지(Flask, RPi.GPIO, RPLCD, smbus2)를 직접 설치합니다."
      sudo -u "$SUDO_USER" ./venv/bin/pip install Flask RPi.GPIO RPLCD smbus2
    fi
  else
    ./venv/bin/pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
      ./venv/bin/pip install -r requirements.txt
    else
      ./venv/bin/pip install Flask RPi.GPIO RPLCD smbus2
    fi
  fi
  
  echo "=================================================="
  echo "Raspberry Pi B 제어 서버 환경 구성 완료!"
  echo "실행 방법:"
  echo "  cd pi_b"
  echo "  source venv/bin/activate"
  echo "  python app.py"
  echo "=================================================="
else
  echo "[Error] 프로젝트 내 pi_b 디렉토리를 찾을 수 없습니다."
  exit 1
fi
