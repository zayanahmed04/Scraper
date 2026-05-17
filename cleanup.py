import os
from datetime import datetime
import stat

folder = r"D:\fb_data\facebook\Beaconhouse Jauhar Campus\Beaconhouse Jauhar Campus's photos (pb.100064865372661.-2207520000)"
cutoff_max = datetime(2025, 5, 31, 23, 59, 59)
cutoff_min = datetime(2010, 1, 1, 0, 0, 0)

deleted = 0
kept = 0

for root, dirs, files in os.walk(folder):
    for file in files:
        filepath = os.path.join(root, file)
        try:
            modified = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            if modified > cutoff_max or modified < cutoff_min:
                os.chmod(filepath, stat.S_IWRITE)
                os.remove(filepath)
                print(f"Deleted: {file} ({modified.strftime('%Y-%m-%d')})")
                deleted += 1
            else:
                kept += 1
        except Exception as e:
            print(f"Skipped: {file} — {e}")

print(f"\nDone. {kept} files kept, {deleted} files deleted.")