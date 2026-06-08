import time

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False

# 주요 음계 주파수 정의
NOTE_C4 = 261.63 # 도
NOTE_E4 = 329.63 # 미
NOTE_G4 = 392.00 # 솔

class BuzzerController:
    def __init__(self, config: dict):
        self.config = config.get("buzzer", {})
        self.mock_mode = config.get("mock", False) or not GPIO_AVAILABLE
        self.pin = self.config.get("pin", 18)
        
        if self.mock_mode:
            print(f"[BUZZER] Mock Buzzer 모드로 작동합니다. (핀: {self.pin})")
            return
            
        try:
            GPIO.setwarnings(False)
            if GPIO.getmode() is None:
                GPIO.setmode(GPIO.BCM)
                
            GPIO.setup(self.pin, GPIO.OUT)
            print(f"[BUZZER] Passive Buzzer 초기화 완료 (핀: {self.pin})")
        except Exception as e:
            print(f"[BUZZER] Passive Buzzer 초기화 실패: {e}. Mock 모드로 전환합니다.")
            self.mock_mode = True

    def _play_tone(self, frequency: float, duration: float):
        if self.mock_mode:
            return
            
        try:
            # PWM 생성 (주파수 설정)
            pwm = GPIO.PWM(self.pin, frequency)
            pwm.start(50.0) # 듀티 사이클 50%
            time.sleep(duration)
            pwm.stop()
            # 음 간의 구분을 위해 아주 잠깐 대기
            time.sleep(0.05)
        except Exception as e:
            print(f"[BUZZER] 톤 출력 중 오류 발생: {e}")

    def play_start_melody(self):
        """도 -> 미 -> 솔 멜로디 재생 (회의 시작 알림)"""
        if self.mock_mode:
            print("[MOCK BUZZER] ♪ 멜로디 재생: 도(C4) -> 미(E4) -> 솔(G4) [회의 시작!]")
            return
            
        self._play_tone(NOTE_C4, 0.2)
        self._play_tone(NOTE_E4, 0.2)
        self._play_tone(NOTE_G4, 0.2)

    def play_end_melody(self):
        """솔 -> 미 -> 도 멜로디 재생 (회의 종료 알림)"""
        if self.mock_mode:
            print("[MOCK BUZZER] ♪ 멜로디 재생: 솔(G4) -> 미(E4) -> 도(C4) [회의 종료!]")
            return
            
        self._play_tone(NOTE_G4, 0.2)
        self._play_tone(NOTE_E4, 0.2)
        self._play_tone(NOTE_C4, 0.2)

    def close(self):
        if self.mock_mode:
            return
        try:
            GPIO.cleanup(self.pin)
            print("[BUZZER] Passive Buzzer 리소스가 해제되었습니다.")
        except Exception as e:
            print(f"[BUZZER] Passive Buzzer 해제 오류: {e}")
