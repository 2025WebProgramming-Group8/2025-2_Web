const express = require('express');
const http = require('http');
const { Server } = require("socket.io");

const app = express();
// 📌 Django 서버와 포트 충돌을 피하기 위해 3000번 포트 사용 (cors 설정 필수)
const PORT = 3000; 
const server = http.createServer(app);

// 📌 CORS 설정: Django 서버 주소(127.0.0.1:8000)를 허용합니다.
const io = new Server(server, {
    cors: {
        origin: "http://127.0.0.1:8000",
        methods: ["GET", "POST"]
    }
});

// 📌 스터디 그룹별 실시간 상태를 저장하는 객체
// { 'studyRoomId': { 'userId1': { time: 300, isStudying: true }, 'userId2': { time: 0, isStudying: false }, ... } }
const studyRoomsStatus = {}; 

io.on('connection', (socket) => {
    console.log('새로운 사용자 연결됨:', socket.id);

    let currentRoomId = null;

    // 1. 클라이언트가 방에 입장할 때 호출됨
    socket.on('join_room', (roomId) => {
        socket.join(roomId); // Socket.IO의 'Room' 기능으로 그룹 통신 환경 조성
        currentRoomId = roomId;
        console.log(`[${socket.id}] 룸에 입장: ${roomId}`);

        // 초기 상태 전송: 새로 접속한 사용자에게 현재 방의 상태를 보냄
        if (studyRoomsStatus[roomId]) {
            socket.emit('status_update', studyRoomsStatus[roomId]);
        }
    });

    // 2. 타이머 시작/정지 이벤트 처리
    socket.on('timer_action', (data) => {
        const { room, userId, action, currentTime } = data;
        
        studyRoomsStatus[room] = studyRoomsStatus[room] || {};

        if (action === 'start') {
            studyRoomsStatus[room][userId] = { 
                time: currentTime, 
                isStudying: true,
                // 서버에서 시작 시간을 기록하면 정확도가 높아집니다.
                startTime: Date.now() 
            };
        } else if (action === 'stop') {
            studyRoomsStatus[room][userId].isStudying = false;
            // 📌 여기서는 DB 저장 로직이 필요합니다. (3단계 참고)
        }

        // 3. 해당 룸의 모든 사용자에게 변경된 상태를 브로드캐스트
        io.to(room).emit('status_update', studyRoomsStatus[room]);
    });

    // 4. 연결 해제 처리 (페이지 닫거나 나갈 때)
    socket.on('disconnect', () => {
        console.log('사용자 연결 해제됨:', socket.id);
        // 필요에 따라 studyRoomsStatus에서 해당 사용자 상태를 'offline'으로 변경하고 브로드캐스트할 수 있습니다.
    });
});

server.listen(PORT, () => {
    console.log(`Socket.IO 서버가 ${PORT}번 포트에서 실행 중입니다.`);
});