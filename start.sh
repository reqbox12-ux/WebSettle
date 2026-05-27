#!/bin/bash
# 라온스포츠 WebApp 시작 스크립트
# Port 8501: ERP (Streamlit)
# Port 8502: 지점 포털 (FastAPI)

echo "=========================================="
echo " 라온스포츠 WebApp 시작"
echo " ERP:    http://localhost:8501"
echo " 지점포털: http://localhost:8502"
echo "=========================================="

# FastAPI 지점 포털 백그라운드 실행
uvicorn branch_server:app \
    --host 0.0.0.0 \
    --port 8502 \
    --workers 1 &

FASTAPI_PID=$!
echo "[OK] 지점 포털 시작 (PID: $FASTAPI_PID)"

# Streamlit ERP 포어그라운드 실행 (메인 프로세스)
streamlit run app.py \
    --server.headless=true \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --browser.gatherUsageStats=false
