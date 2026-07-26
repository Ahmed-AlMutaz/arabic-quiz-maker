@echo off
chcp 65001 > nul
title Quiz Maker AI Enterprise - التشغيل التلقائي وإصلاح المنظومة

echo ======================================================================
echo              Quiz Maker AI Enterprise - تشغيل المنظومة
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/4] جاري إيقاف وتنظيف أي حاويات قديمة أو معلقة...
docker compose down --remove-orphans

echo.
echo [2/4] جاري بناء وتشغيل خدمات النظام (API, Qdrant, MongoDB, Redis)...
docker compose up -d --build

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [خطأ] تعذر تشغيل Docker Compose! يرجى التأكد من تشغيل Docker Desktop أولاً.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/4] جاري التحقق من جاهزية المحرك والخدمات على http://localhost:8010/ ...
timeout /t 3 /nobreak > nul

echo.
echo [4/4] فتح واجهة المستخدم في المتصفح تلقائياً...
start http://localhost:8010/

echo.
echo ======================================================================
echo          تم تشغيل جميع الخدمات بنجاح! المنظومة تعمل الآن.
echo      الرابط: http://localhost:8010/
echo ======================================================================
echo.
pause
