from abc import ABC, abstractmethod

class ReservationRepository(ABC):
    """
    ReservationRepository는 예약 데이터 저장소의 인터페이스를 정의하는 추상 베이스 클래스입니다.
    """

    @abstractmethod
    def get_all(self) -> list:
        """
        모든 예약 정보를 리스트로 반환합니다.
        각 예약은 딕셔너리 형태입니다:
        [
            {
                "id": 1,
                "title": "회의 제목",
                "start_time": "YYYY-MM-DD HH:MM:SS",
                "end_time": "YYYY-MM-DD HH:MM:SS",
                "status": "RESERVED"
            }
        ]
        """
        pass

    @abstractmethod
    def get_by_id(self, reservation_id: int) -> dict:
        """
        특정 ID에 해당하는 예약 정보를 반환합니다. 존재하지 않으면 None을 반환합니다.
        """
        pass

    @abstractmethod
    def add(self, title: str, start_time: str, end_time: str) -> dict:
        """
        새로운 예약을 등록합니다. 등록된 예약 정보를 딕셔너리로 반환합니다.
        """
        pass

    @abstractmethod
    def delete(self, reservation_id: int) -> bool:
        """
        특정 ID의 예약을 삭제합니다. 성공 여부를 bool로 반환합니다.
        """
        pass

    @abstractmethod
    def update_status(self, reservation_id: int, status: str) -> bool:
        """
        특정 ID의 예약 상태를 변경합니다. 성공 여부를 bool로 반환합니다.
        """
        pass
