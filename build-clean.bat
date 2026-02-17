@echo off
REM Script para limpar cache do Docker e fazer build limpo
REM Uso: build-clean.bat

echo ========================================
echo Limpando cache do Docker...
echo ========================================

REM Parar containers
echo.
echo Parando containers n8n...
docker-compose down 2>nul

REM Remover imagens antigas
echo.
echo Removendo imagens antigas...
docker rmi n8n-custom-head-dados 2>nul
for /f "tokens=*" %%i in ('docker images -f "dangling=true" -q') do docker rmi %%i 2>nul

REM Limpar build cache
echo.
echo Limpando build cache...
docker builder prune -af

echo.
echo ========================================
echo Iniciando build limpo...
echo ========================================

REM Fazer build com docker-compose
docker-compose build --no-cache

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo [SUCCESS] Build concluido com sucesso!
    echo ========================================
    echo.
    echo Para iniciar o n8n, execute:
    echo   docker-compose up -d
    echo.
    echo Para ver logs:
    echo   docker-compose logs -f
) else (
    echo.
    echo ========================================
    echo [ERRO] Erro no build!
    echo ========================================
    exit /b 1
)

pause
