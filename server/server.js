const express = require('express');
const http = require('http');
const { Server } = require("socket.io");
const axios = require('axios'); 

const app = express();
const PORT = 3000; 
const server = http.createServer(app);

// CORS 설정: Django 서버 주소(Nginx 포트)를 허용해야 합니다.
const io = new Server(server, {
    cors: {
        origin: "http://127.0.0.1:8000", // Nginx 포트를 바라봄
        methods: ["GET", "POST"]
    }
});

const studyRoomsStatus = {}; 

io.on('connection', (socket) => {
    socket.on('join_room', (data) => {
        const { roomId, userId } = data; // 클라이언트에서 {roomId, userId}를 보내야 합니다.
        socket.join(roomId);
        // 소켓 객체에 사용자 정보 저장
        socket.currentRoomId = String(roomId);
        socket.currentUserId = String(userId); 
        
        if (studyRoomsStatus[roomId]) {
            socket.emit('status_update', studyRoomsStatus[roomId]);
        }
    });

    socket.on('timer_action', (data) => {
        const { room, userId: rawUserId, action, currentTime } = data;
        const userId = String(rawUserId);
    
    // 현재 사용자의 상태를 참조
    studyRoomsStatus[room] = studyRoomsStatus[room] || {};
    const status = studyRoomsStatus[room][userId];

    if (action === 'start') {
        // 시작 시 클라이언트가 보낸 누적 시간을 DB 누적 시간으로 저장
        studyRoomsStatus[room][userId] = { 
            totalTimeOnDB: currentTime,
            isStudying: true,
            startTime: Date.now(), 
            time : currentTime // 브로드캐스트용 초기 시간
        };
    
    } else if (action === 'stop') {
        if (status && status.isStudying) {
            // 서버에서 실제 공부 시간 계산
            const elapsedSeconds = Math.floor((Date.now() - status.startTime) / 1000);
            const newTotalTime = status.totalTimeOnDB + elapsedSeconds;
            
            // 서버 상태 업데이트
            status.isStudying = false;
            status.totalTimeOnDB = newTotalTime;
            status.time = newTotalTime; // 브로드캐스트용 최종 시간

            // DB 저장 로직: 서버 계산 시간을 사용
            axios.post('http://127.0.0.1:8000/api/save-time/', { 
                userId: String(userId),
                currentTime: newTotalTime, 
                room: room
            })
            .then(response => {
                console.log(`[DB 저장 성공] User ${userId} - 최종 시간: ${newTotalTime}초`);
            })
            .catch(error => {
                console.error(`[DB 저장 실패] User ${userId} - 오류: ${error.message}`);
            });
        }
    }

    // 해당 룸의 모든 사용자에게 변경된 상태를 브로드캐스트
    io.to(room).emit('status_update', studyRoomsStatus[room]);
});

    socket.on('disconnect', () => {
        const roomId = socket.currentRoomId;
        const userId = socket.currentUserId;
        
        if (roomId && userId && studyRoomsStatus[roomId] && studyRoomsStatus[roomId][userId]) {
            const status = studyRoomsStatus[roomId][userId];

            if (status.isStudying) {
                // 공부 중이었다면, 자동 중지 및 최종 시간 계산
                const elapsedSeconds = Math.floor((Date.now() - status.startTime) / 1000);
                const newTotalTime = status.totalTimeOnDB + elapsedSeconds;

                // 서버 상태 업데이트
                status.isStudying = false;
                status.totalTimeOnDB = newTotalTime;
                status.time = newTotalTime;

                // DB 저장 로직 실행
                axios.post('http://127.0.0.1:8000/api/save-time/', { 
                    userId: userId,
                    currentTime: newTotalTime,
                    room: roomId, 
                })
                .then(response => {
                console.log(`[DB 저장 성공] User ${userId} - 최종 시간: ${newTotalTime}초`);
                })
                .catch(error => {
                    console.error(`[DB 저장 실패] User ${userId} - 오류: ${error.message}`);
                });

                // 해당 룸의 다른 사용자들에게 상태 변경 브로드캐스트
                io.to(roomId).emit('status_update', studyRoomsStatus[roomId]);
            }
        }
    });
});

server.listen(PORT, () => {
    console.log(`Socket.IO 서버가 ${PORT}번 포트에서 실행 중입니다.`);
});