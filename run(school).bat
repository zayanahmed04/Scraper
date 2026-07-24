@echo off

:loop

echo Starting scraper...

call venv\Scripts\activate
echo venv activated

python -u "D:\Scraper\fb_reels_downloader.py"

echo.
echo Finished or stopped.
echo Waiting 10 seconds before retrying...

timeout /t 10

goto loop