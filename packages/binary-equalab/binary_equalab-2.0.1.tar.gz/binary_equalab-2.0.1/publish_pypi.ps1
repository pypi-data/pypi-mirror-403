# Script de Publicacion a PyPI para Binary EquaLab
# Autor: Malexnnn
# NOTA: Sin emojis para evitar problemas de codificacion en Windows

Write-Host "[INFO] Iniciando proceso de publicacion para Binary EquaLab CLI..." -ForegroundColor Cyan

# 1. Instalar herramientas
Write-Host "[WAIT] Verificando herramientas (build, twine)..." -ForegroundColor Yellow
pip install --upgrade build twine

# 2. Limpiar
if (Test-Path "dist") {
    Write-Host "[WAIT] Limpiando carpeta dist..." -ForegroundColor Yellow
    Remove-Item "dist" -Recurse -Force
}

# 3. Construir
Write-Host "[WAIT] Construyendo paquete (sdist + wheel)..." -ForegroundColor Yellow
python -m build

# 4. Validar
if (-not (Test-Path "dist")) {
    Write-Host "[ERROR] Fallo la construccion." -ForegroundColor Red
    exit 1
}

# 5. Subir
Write-Host "[INFO] Subiendo a PyPI..." -ForegroundColor Yellow
Write-Host "NOTA: Usa tu token de PyPI (__token__) como usuario." -ForegroundColor Gray
python -m twine upload dist/*

Write-Host "[DONE] Proceso finalizado." -ForegroundColor Green
write-Host "Instalar con: pip install binary-equalab" -ForegroundColor Cyan
