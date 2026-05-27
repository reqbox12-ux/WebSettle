@echo off
title 라온스포츠 직원포털 FastAPI (포트 8502)
echo ============================================
echo  라온스포츠 지점 포털 (FastAPI) 시작
echo  접속주소: http://localhost:8502
echo ============================================
py -m uvicorn branch_server:app --host 0.0.0.0 --port 8502 --reload
pause
