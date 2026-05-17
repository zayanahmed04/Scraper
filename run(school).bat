@echo off
:loop
echo Starting gallery-dl...
gallery-dl --cookies "D:\fb_data\cookies.txt" --download-archive "D:\fb_data\archive.txt" -d "D:\fb_data" "https://www.facebook.com/photo/?fbid=1454822136689952&set=pb.100064865372661.-2207520000&setextract"
echo.
echo Finished or stopped. Waiting 30 minutes before retrying...
timeout /t 1800
goto loop