@echo off
setlocal

:: Definisce il percorso della cartella
set "folderPath=C:\Elsy\Flexin_DB_Backupper\config_files"

:: Crea la cartella se non esiste
if not exist "%folderPath%" (
    mkdir "%folderPath%"
)

:: Definisce il percorso del file
set "filePath=%folderPath%\general_config.ini"

:: Crea o sovrascrive il file con il contenuto richiesto
(
    echo [CONNECTIONS]
    echo.
    echo [AUTOINCREMENT]
    echo last_val = 0
) > "%filePath%"

echo File creato e popolato: %filePath%

endlocal
exit /b

