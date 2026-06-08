document.addEventListener('DOMContentLoaded', () => {
    // DOM 요소 캐싱
    const statusBadge = document.getElementById('status-badge');
    const meetingTitle = document.getElementById('meeting-title');
    const meetingTime = document.getElementById('meeting-time');
    const timerDisplay = document.getElementById('timer-display');
    const reservationList = document.getElementById('reservation-list');
    const reservationForm = document.getElementById('reservation-form');
    const errorMessage = document.getElementById('error-message');
    
    // 긴급 제어 버튼
    const btnForceAvail = document.getElementById('btn-force-avail');
    const btnForceUse = document.getElementById('btn-force-use');
    const btnAuto = document.getElementById('btn-auto');

    let timerInterval = null;
    let targetTime = null;

    // 초기 실행
    refreshData();
    // 3초마다 상태 및 예약 목록 폴링
    setInterval(refreshData, 3000);

    // 예약 등록 폼 서브밋
    reservationForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        const title = document.getElementById('title').value.trim();
        const date = document.getElementById('date').value;
        const startTime = document.getElementById('start-time').value;
        const endTime = document.getElementById('end-time').value;

        if (!title || !date || !startTime || !endTime) {
            showError('모든 필드를 채워주세요.');
            return;
        }

        // YYYY-MM-DD HH:MM:SS 규격으로 병합
        const start_time = `${date} ${startTime}:00`;
        const end_time = `${date} ${endTime}:00`;

        if (new Date(start_time) >= new Date(end_time)) {
            showError('시작 시간은 종료 시간보다 빨라야 합니다.');
            return;
        }

        try {
            const response = await fetch('index.php?action=add_reservation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, start_time, end_time })
            });
            const result = await response.json();

            if (result.result === 'success') {
                reservationForm.reset();
                // 오늘 날짜로 자동 복원
                setDefaultDates();
                refreshData();
            } else {
                showError(result.message || '예약 등록에 실패했습니다.');
            }
        } catch (err) {
            showError('서버 통신 오류가 발생했습니다.');
        }
    });

    // 긴급 강제 제어 이벤트 바인딩
    btnForceAvail.addEventListener('click', () => sendForceStatus('AVAILABLE'));
    btnForceUse.addEventListener('click', () => sendForceStatus('IN_USE'));
    btnAuto.addEventListener('click', () => sendForceStatus('AUTO'));

    // 오늘 날짜 기본값 설정
    setDefaultDates();

    function setDefaultDates() {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const dd = String(today.getDate()).padStart(2, '0');
        document.getElementById('date').value = `${yyyy}-${mm}-${dd}`;
    }

    // 서버 데이터 가져오기 (현재 상태 및 전체 리스트)
    async function refreshData() {
        try {
            // 1. 상태 정보 갱신
            const statusRes = await fetch('index.php?action=get_status');
            const statusData = await statusRes.json();
            updateStatusUI(statusData);

            // 2. 예약 목록 리스트 갱신
            const listRes = await fetch('index.php?action=get_reservations');
            const listData = await listRes.json();
            updateListUI(listData);
        } catch (err) {
            console.error('Data refresh error:', err);
        }
    }

    // 상태 UI 업데이트
    function updateStatusUI(data) {
        if (!data || data.result === 'error') return;

        const actualStatus = data.actual_status;
        const forceStatus = data.force_status;

        // 상태 배지 업데이트
        statusBadge.className = `status-badge status-${actualStatus}`;
        statusBadge.textContent = actualStatus;

        // 긴급 제어 활성화 버튼 스타일 토글
        btnForceAvail.classList.toggle('active-force-avail', forceStatus === 'AVAILABLE');
        btnForceUse.classList.toggle('active-force-use', forceStatus === 'IN_USE');
        btnAuto.classList.toggle('active-auto', forceStatus === 'AUTO');

        // 진행/예정 행사 정보 바인딩
        if (actualStatus === 'IN_USE' && data.active_meeting) {
            meetingTitle.textContent = data.active_meeting.title;
            meetingTime.textContent = `${data.active_meeting.start_time} ~ ${data.active_meeting.end_time}`;
            targetTime = new Date(data.active_meeting.end_time.replace(/-/g, '/')).getTime();
            startCountdown();
        } else if (actualStatus === 'RESERVED' && data.next_meeting) {
            meetingTitle.textContent = `대기 행사: ${data.next_meeting.title}`;
            meetingTime.textContent = `시작 예정: ${data.next_meeting.start_time}`;
            targetTime = new Date(data.next_meeting.start_time.replace(/-/g, '/')).getTime();
            startCountdown();
        } else {
            meetingTitle.textContent = '현재 예약 또는 진행 중인 행사가 없습니다.';
            meetingTime.textContent = '-';
            stopCountdown();
            timerDisplay.textContent = '00:00:00';
        }
    }

    // 예약 목록 리스트 UI 그리기
    function updateListUI(data) {
        if (!data || !Array.isArray(data)) {
            reservationList.innerHTML = '<div class="no-data">예약 정보를 불러올 수 없습니다.</div>';
            return;
        }

        if (data.length === 0) {
            reservationList.innerHTML = '<div class="no-data">예약된 행사 목록이 비어 있습니다.</div>';
            return;
        }

        // 시작 시간 기준으로 정렬되어 온 목록 표시
        reservationList.innerHTML = '';
        data.forEach(item => {
            const itemEl = document.createElement('div');
            itemEl.className = 'reservation-item';
            
            // 상태 배지 한글 매핑 또는 스타일
            let badgeText = item.status;
            let badgeClass = `badge-${item.status}`;

            itemEl.innerHTML = `
                <div class="reservation-info">
                    <div class="reservation-title">${escapeHtml(item.title)}</div>
                    <div class="reservation-time">
                        <span class="badge ${badgeClass}">${badgeText}</span>
                        ${item.start_time.substring(5, 16)} ~ ${item.end_time.substring(11, 16)}
                    </div>
                </div>
                <button class="btn-delete" data-id="${item.id}">삭제</button>
            `;
            
            // 삭제 버튼 바인딩
            itemEl.querySelector('.btn-delete').addEventListener('click', () => deleteReservation(item.id, item.title));
            reservationList.appendChild(itemEl);
        });
    }

    // 예약 삭제 요청
    async function deleteReservation(id, title) {
        if (!confirm(`'${title}' 예약을 삭제하시겠습니까?`)) return;

        try {
            const response = await fetch(`index.php?action=delete_reservation&id=${id}`, {
                method: 'DELETE'
            });
            const result = await response.json();

            if (result.result === 'success') {
                refreshData();
            } else {
                alert(result.message || '예약 삭제에 실패했습니다.');
            }
        } catch (err) {
            alert('통신 중 오류가 발생했습니다.');
        }
    }

    // 긴급 제어 명령 송신
    async function sendForceStatus(status) {
        try {
            const response = await fetch('index.php?action=force_status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });
            const result = await response.json();

            if (result.result === 'success') {
                refreshData();
            } else {
                alert(result.message || '상태 변경에 실패했습니다.');
            }
        } catch (err) {
            alert('통신 중 오류가 발생했습니다.');
        }
    }

    // 카운트다운 시작
    function startCountdown() {
        if (timerInterval) clearInterval(timerInterval);
        
        updateTimer();
        timerInterval = setInterval(updateTimer, 1000);
    }

    function updateTimer() {
        if (!targetTime) return;

        const now = new Date().getTime();
        let diff = targetTime - now;

        if (diff <= 0) {
            timerDisplay.textContent = '00:00:00';
            clearInterval(timerInterval);
            refreshData(); // 시간 종료 시 상태 즉시 갱신
            return;
        }

        const hrs = String(Math.floor(diff / (1000 * 60 * 60))).padStart(2, '0');
        diff %= (1000 * 60 * 60);
        const mins = String(Math.floor(diff / (1000 * 60))).padStart(2, '0');
        diff %= (1000 * 60);
        const secs = String(Math.floor(diff / 1000)).padStart(2, '0');

        timerDisplay.textContent = `${hrs}:${mins}:${secs}`;
    }

    function stopCountdown() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        targetTime = null;
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.style.display = 'block';
    }

    function hideError() {
        errorMessage.style.display = 'none';
        errorMessage.textContent = '';
    }

    function escapeHtml(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
