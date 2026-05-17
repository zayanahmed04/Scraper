import os
import sqlite3

folder = r"D:\fb_data\facebook\Beaconhouse Jauhar Campus\Beaconhouse Jauhar Campus's photos (pb.100064865372661.-2207520000)"
archive_path = r"D:\fb_data\archive.sqlite3"

# Connect to archive database
conn = sqlite3.connect(archive_path)
conn.execute("CREATE TABLE IF NOT EXISTS archive (entry TEXT PRIMARY KEY) WITHOUT ROWID")

count = 0
for root, dirs, files in os.walk(folder):
    for file in files:
        if file.endswith(('.jpg', '.jpeg', '.png', '.mp4', '.webp')):
            # Extract the ID from filename (without extension)
            file_id = os.path.splitext(file)[0]
            entry = f"facebook {file_id}"
            try:
                conn.execute("INSERT OR IGNORE INTO archive VALUES (?)", (entry,))
                count += 1
            except:
                pass

conn.commit()
conn.close()
print(f"Done. {count} entries added to archive.")