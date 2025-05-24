#!/bin/bash

echo "서버 재시작 스크립트 실행 중..."

# 기존 프로세스 찾기 및 종료
echo "기존 서버 프로세스 확인 중..."
SERVER_PID=$(lsof -i :5007 -t)

if [ ! -z "$SERVER_PID" ]; then
    echo "포트 5007 사용 중인 프로세스 발견: $SERVER_PID - 종료 중..."
    kill -9 $SERVER_PID
    echo "프로세스 종료됨"
else
    echo "실행 중인 서버가 없습니다"
fi

# 서버 시작
echo "서버 시작 중..."
python app.py
