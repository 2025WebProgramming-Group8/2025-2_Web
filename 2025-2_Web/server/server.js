const express = require('express');
const http = require('http');
const { Server } = require("socket.io");
const axios = require('axios'); 

const app = express();
const PORT = 3000; 
const server = http.createServer(app);

const io = new Server(server, {
    cors: {
        origin: "http://127.0.0.1:8000",
        methods: ["GET", "POST"]
    }
});

// 방 상태 저장소
const studyRoomsStatus = {}; 
// 연결 끊김 감지 타이머 저장소 (새로고침 처리용)
const disconnectTimers = {};

// 헬퍼 함수: 현재 흐른 시간 계산해서 반환
function getRealTimeStatus(room) {
    if (!studyRoomsStatus[room]) return {};
    
    const realTimeData = {};
    for (const [userId, status] of Object.entries(studyRoomsStatus[room])) {
        let displayTime = status.totalTimeOnDB;
        if (status.isStudying) {
            // 공부 중이라면: (기존 DB 시간) + (현재 시간 - 시작 시간)
            const elapsed = Math.floor((Date.now() - status.startTime) / 1000);
            displayTime += elapsed;
        }
        
        realTimeData[userId] = {
            ...status,
            time: displayTime // 클라이언트에게 보낼 계산된 시간
        };
    }
    return realTimeData;
}

io.on(  'connection', (socket) => {
    
    // 1. 방 입장 (새로고침 후 재접속 포함)
    socket.on('join_room', (data) => {
        const { roomId, userId } = data;
        const sRoomId = String(roomId);
        const sUserId = String(userId);

        socket.join(sRoomId);
        socket.currentRoomId = sRoomId;
        socket.currentUserId = sUserId;

        // ★ 핵심: 만약 퇴실 타이머가 돌아가고 있었다면 취소 (재접속 성공!)
        if (disconnectTimers[sUserId]) {
            console.log(`[재접속] 유저 ${sUserId} 복귀 완료. 퇴실 처리 취소.`);
            clearTimeout(disconnectTimers[sUserId]);
            delete disconnectTimers[sUserId];
        }

        // 방 데이터 초기화
        studyRoomsStatus[sRoomId] = studyRoomsStatus[sRoomId] || {};
        
        // 기존 상태가 없다면 초기화 (처음 들어온 경우)
        if (!studyRoomsStatus[sRoomId][sUserId]) {
            studyRoomsStatus[sRoomId][sUserId] = {
                totalTimeOnDB: 0, // DB에서 불러온 초기값은 클라이언트가 timer_action으로 보내줄 때 업데이트됨
                isStudying: false,
                startTime: null,
                time: 0
            };
        }

        // 현재 상태 전송
        io.to(sRoomId).emit('status_update', getRealTimeStatus(sRoomId));
    });

    // 2. 타이머 시작/중지 액션
    socket.on('timer_action', (data) => {
        const { room, userId, action, currentTime } = data;
        const sRoomId = String(room);
        const sUserId = String(userId);

        studyRoomsStatus[sRoomId] = studyRoomsStatus[sRoomId] || {};
        
        // 상태 객체 가져오기 (없으면 생성)
        let status = studyRoomsStatus[sRoomId][sUserId];
        if (!status) {
            status = { totalTimeOnDB: currentTime, isStudying: false, startTime: null };
            studyRoomsStatus[sRoomId][sUserId] = status;
        }

        if (action === 'start') {
            // 시작: 현재 클라이언트 시간을 기준으로 시작점 설정
            status.isStudying = true;
            status.totalTimeOnDB = currentTime; // 기준점 갱신
            status.startTime = Date.now();
            
            // 타이머가 돌고 있었다면 제거 (중복 방지)
            if (disconnectTimers[sUserId]) {
                clearTimeout(disconnectTimers[sUserId]);
                delete disconnectTimers[sUserId];
            }

        } else if (action === 'stop') {
            // 중지: 시간 정산 및 DB 저장
            if (status.isStudying) {
                const elapsedSeconds = Math.floor((Date.now() - status.startTime) / 1000);
                status.totalTimeOnDB += elapsedSeconds;
                status.isStudying = false;
                status.startTime = null;

                // DB 저장 요청
                saveToDjango(sUserId, status.totalTimeOnDB, sRoomId);
            }
        }

        // 방 전체에 업데이트
        io.to(sRoomId).emit('status_update', getRealTimeStatus(sRoomId));
    });
    // 실시간 채팅 메시지 처리 (추가)
    socket.on('chat_message', (data) => {
        // data 구조: { room, nickname, message }
        // 같은 방에 있는 모든 사람(나 포함)에게 메시지를 그대로 전달
        io.to(data.room).emit('new_chat', data);
    });

    // 3. 연결 끊김 (새로고침 시 발생)
    socket.on('disconnect', () => {
        const roomId = socket.currentRoomId;
        const userId = socket.currentUserId;

        if (roomId && userId && studyRoomsStatus[roomId] && studyRoomsStatus[roomId][userId]) {
            const status = studyRoomsStatus[roomId][userId];

            if (status.isStudying) {
                console.log(`[연결 끊김] 유저 ${userId} - 5초 대기...`);

                // ★ 핵심: 바로 끄지 않고 5초 대기 (새로고침 대응)
                disconnectTimers[userId] = setTimeout(() => {
                    console.log(`[시간 초과] 유저 ${userId} 완전 퇴실 처리.`);
                    
                    // 5초 뒤에도 안 돌아오면 진짜 퇴실 처리
                    const elapsedSeconds = Math.floor((Date.now() - status.startTime) / 1000);
                    status.totalTimeOnDB += elapsedSeconds;
                    status.isStudying = false;
                    
                    // DB 저장
                    saveToDjango(userId, status.totalTimeOnDB, roomId);

                    // 방 사람들에게 알림
                    io.to(roomId).emit('status_update', getRealTimeStatus(roomId));
                    
                    delete disconnectTimers[userId];
                }, 5000); // 5초 대기
            }
        }
    });
});

// DB 저장 함수 분리
function saveToDjango(userId, time, roomId) {
    axios.post('http://127.0.0.1:8000/api/save-time/', { 
        userId: userId,
        currentTime: time, 
        room: roomId, 
    })
    .then(response => {
        console.log(`[DB 저장] User ${userId}: ${time}초`);
    })
    .catch(error => {
        console.error(`[DB 에러] User ${userId}:`, error.message);
    });
}

server.listen(PORT, () => {
    console.log(`Socket.IO 서버 가동: 포트 ${PORT}`);
});