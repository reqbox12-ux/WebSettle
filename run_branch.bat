@echo off
title 라온스포츠 직원포털 (포트 8502)
echo ============================================
echo  라온스포츠 직원 랜딩페이지 시작
echo  접속주소: http://localhost:8502
echo ============================================
py -m streamlit run branch_app.py --server.port 8502
pause
