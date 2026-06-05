#!/bin/bash

# =====================================================================
# Raspberry Pi A (Web Server) 자동 설정 및 배포 스크립트
# =====================================================================

# 1. 스크립트 실행 환경 확인 (Root 권한 확인)
if [ "$EUID" -ne 0 ]; then
  echo "[Error] 이 스크립트는 root 권한으로 실행해야 합니다. sudo ./setup_pi_a.sh 로 실행해주세요."
  exit 1
fi

echo "=================================================="
echo "Raspberry Pi A (Web Server) 환경 구성을 시작합니다..."
echo "=================================================="

# 2. 패키지 인덱스 업데이트 및 필요한 패키지 설치
echo "[1/4] 시스템 업데이트 및 Apache2/PHP 설치 중..."
apt-get update
apt-get install -y apache2 php php-curl php-json php-sqlite3

# 3. 기존의 기본 index.html 삭제 (PHP 화면을 메인으로 띄우기 위해)
if [ -f /var/www/html/index.html ]; then
  echo "[2/4] 기존 아파치 기본 index.html 제거 중..."
  mv /var/www/html/index.html /var/www/html/index.html.backup
fi

# 4. pi_a 폴더 내 소스코드를 Apache 웹 루트 디렉토리로 동기화
echo "[3/4] 웹 서버 소스 코드 복사 중..."
# 스크립트의 현재 위치 기준으로 상대 경로를 확인하여 복사
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -d "$PROJECT_DIR/pi_a" ]; then
  cp -r "$PROJECT_DIR/pi_a/"* /var/www/html/
  echo "=> 성공적으로 /var/www/html/ 경로로 파일을 복사했습니다."
else
  echo "[Warning] 프로젝트 디렉토리 내 pi_a 폴더를 찾을 수 없습니다."
  echo "현재 위치: $PROJECT_DIR"
fi

# 5. 웹 디렉토리 소유권 및 권한 부여
echo "[4/4] 권한 설정 및 아파치 서버 재기동 중..."
chown -R www-data:www-data /var/www/html/
chmod -R 755 /var/www/html/

# 6. 아파치 서비스 재시작
systemctl restart apache2

echo "=================================================="
echo "Raspberry Pi A 웹 서버 구축 완료!"
echo "웹 브라우저에서 http://localhost/ 또는 http://<Pi_A_IP_Address>/ 에 접속해보세요."
echo "=================================================="
