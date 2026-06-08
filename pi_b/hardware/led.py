try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False

class LedController:
    def __init__(self, config: dict):
        self.config = config.get("rgb_led", {})
        self.mock_mode = config.get("mock", False) or not GPIO_AVAILABLE
        
        self.red_pin = self.config.get("red_pin", 17)
        self.green_pin = self.config.get("green_pin", 27)
        self.blue_pin = self.config.get("blue_pin", 22)
        
        if self.mock_mode:
            print(f"[LED] Mock LED 모드로 작동합니다. (핀 R:{self.red_pin}, G:{self.green_pin}, B:{self.blue_pin})")
            return
            
        try:
            # GPIO 경고 제거 및 모드 설정
            GPIO.setwarnings(False)
            if GPIO.getmode() is None:
                GPIO.setmode(GPIO.BCM)
                
            GPIO.setup(self.red_pin, GPIO.OUT)
            GPIO.setup(self.green_pin, GPIO.OUT)
            GPIO.setup(self.blue_pin, GPIO.OUT)
            
            # 초기값 Off
            self._write_pins(False, False, False)
            print(f"[LED] RGB LED 초기화 완료 (R:{self.red_pin}, G:{self.green_pin}, B:{self.blue_pin})")
        except Exception as e:
            print(f"[LED] RGB LED 초기화 실패: {e}. Mock 모드로 전환합니다.")
            self.mock_mode = True

    def _write_pins(self, red: bool, green: bool, blue: bool):
        if self.mock_mode:
            return
        # Common Cathode 기준 (True = HIGH = LED ON)
        GPIO.output(self.red_pin, GPIO.HIGH if red else GPIO.LOW)
        GPIO.output(self.green_pin, GPIO.HIGH if green else GPIO.LOW)
        GPIO.output(self.blue_pin, GPIO.HIGH if blue else GPIO.LOW)

    def set_status(self, status: str):
        status = status.upper()
        if status == "AVAILABLE":
            # 녹색(Green) ON
            if self.mock_mode:
                print("[MOCK LED] Color: GREEN (Auditorium is Available)")
            else:
                self._write_pins(False, True, False)
        elif status == "RESERVED":
            # 청색(Blue) ON
            if self.mock_mode:
                print("[MOCK LED] Color: BLUE (Auditorium is Reserved)")
            else:
                self._write_pins(False, False, True)
        elif status == "IN_USE":
            # 적색(Red) ON
            if self.mock_mode:
                print("[MOCK LED] Color: RED (Auditorium is In Use)")
            else:
                self._write_pins(True, False, False)
        else:
            # 알 수 없는 상태일 경우 모두 끔
            if self.mock_mode:
                print("[MOCK LED] Color: OFF (Unknown state)")
            else:
                self._write_pins(False, False, False)

    def close(self):
        if self.mock_mode:
            return
        try:
            self._write_pins(False, False, False)
            # 개별 핀 리소스 정리
            GPIO.cleanup([self.red_pin, self.green_pin, self.blue_pin])
            print("[LED] RGB LED 리소스가 해제되었습니다.")
        except Exception as e:
            print(f"[LED] RGB LED 해제 오류: {e}")
