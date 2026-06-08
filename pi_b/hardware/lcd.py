import sys

# RPi.GPIO 및 RPLCD 임포트 시도
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False

try:
    from RPLCD.i2c import CharLCD as I2cCharLCD
    from RPLCD.gpio import CharLCD as GpioCharLCD
    RPLCD_AVAILABLE = True
except (ImportError, RuntimeError):
    RPLCD_AVAILABLE = False

class LcdController:
    def __init__(self, config: dict):
        self.config = config.get("lcd", {})
        # config 전체에서 mock 활성화 여부 또는 라이브러리 미지원 시 mock_mode 작동
        self.mock_mode = config.get("mock", False) or not (GPIO_AVAILABLE and RPLCD_AVAILABLE)
        self.lcd = None
        
        if self.mock_mode:
            print("[LCD] Mock LCD 모드로 작동합니다. (물리 LCD 연결 없음)")
            return
            
        try:
            mode = self.config.get("mode", "I2C").upper()
            if mode == "I2C":
                addr_str = self.config.get("i2c_address", "0x27")
                i2c_address = int(addr_str, 16)
                # PCF8574 백팩 LCD 초기화
                self.lcd = I2cCharLCD(
                    i2c_expander='PCF8574',
                    address=i2c_address,
                    port=1,
                    cols=16,
                    rows=2,
                    dotsize=8
                )
                print(f"[LCD] I2C 모드로 초기화 완료 (주소: {addr_str})")
            elif mode == "GPIO":
                pins = self.config.get("pins", {})
                # BCM 핀 매핑
                pin_rs = pins.get("rs", 26)
                pin_e = pins.get("e", 19)
                pin_d4 = pins.get("d4", 13)
                pin_d5 = pins.get("d5", 6)
                pin_d6 = pins.get("d6", 5)
                pin_d7 = pins.get("d7", 11)
                
                self.lcd = GpioCharLCD(
                    pin_rs=pin_rs,
                    pin_rw=None,
                    pin_e=pin_e,
                    pins_data=[pin_d4, pin_d5, pin_d6, pin_d7],
                    numbering_mode=GPIO.BCM,
                    cols=16,
                    rows=2,
                    dotsize=8
                )
                print("[LCD] GPIO Direct 모드로 초기화 완료")
        except Exception as e:
            print(f"[LCD] LCD 초기화 실패: {e}. Mock 모드로 강제 전환합니다.")
            self.mock_mode = True

    def display_status(self, status: str, title: str = ""):
        # LCD 한 줄당 16글자 제한
        line1 = f"STATUS: {status}"[:16]
        # 회의실 상태가 AVAILABLE일 때는 제목이 빈 문자열일 수 있음
        line2 = f"{title}"[:16] if title else ""
        
        # 글자 뒤 남는 부분을 공백으로 채워 이전 텍스트 잔여물을 지움
        line1 = line1.ljust(16)
        line2 = line2.ljust(16)
        
        if self.mock_mode:
            print(f"[MOCK LCD] ┌────────────────┐")
            print(f"[MOCK LCD] │{line1}│")
            print(f"[MOCK LCD] │{line2}│")
            print(f"[MOCK LCD] └────────────────┘")
            return
            
        try:
            self.lcd.clear()
            self.lcd.cursor_pos = (0, 0)
            self.lcd.write_string(line1)
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string(line2)
        except Exception as e:
            print(f"[LCD] LCD 쓰기 오류: {e}")

    def close(self):
        if self.mock_mode or not self.lcd:
            return
        try:
            self.lcd.close()
            print("[LCD] LCD 리소스가 해제되었습니다.")
        except Exception as e:
            print(f"[LCD] LCD 해제 오류: {e}")
