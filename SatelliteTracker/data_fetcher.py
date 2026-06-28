import os
import csv
import urllib.request

opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')]
urllib.request.install_opener(opener)

from skyfield.api import load, Loader, EarthSatellite

class SatelliteDataFetcher:
    def __init__ (self, data_dir = './data'):
        # Initializes the fetcher and creates a local data directory if it doesn't exist.
        self.data_dir = data_dir
        self.ts = load.timescale()

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"[INIT] Created local data directory at: {self.data_dir}")

    def fetch_active_satellites(self):
        # Using CelesTrak's modern GP/OMM API in CSV format
        url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=csv'
        local_filename = os.path.join(self.data_dir, 'active_satellites.csv')

        # Initialize Skyfield's native loader pointing to our directory
        skyfield_loader = Loader(self.data_dir)

        # Updated to Chrome Browser Header
        headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/csv, application/csv, */*'
                }

        # Check if we need to download a new file   
        download_needed = True     
        if os.path.exists(local_filename):
            file_age_days = skyfield_loader.days_old('active_satellites.csv')
            print(f"[CACHE] Local data found. File age: {file_age_days:.2f} days.")

            if file_age_days <= 1.0:
                print("[CACHE] Using local cache (less than 24 hours old).")
                download_needed = False
            else:
              print("[CACHE] Data is older than 24 hours. Refreshing...")
        
        if download_needed:
            print("[FETCH] Downloading active satellite database safely...")
            try:
                req = urllib.request.Request(url, headers = headers)
                with urllib.request.urlopen(req) as response:
                    with open(local_filename, 'wb') as f:
                        f.write(response.read())
                print("[FETCH] Download complete.")
            except Exception as e:
                print(f"[ERROR] Failed to download data: {e}")
                # If download fails but old file exists, fallback to old file instead of crashing
                if os.path.exists(local_filename):
                    print("[FALLBACK] Using expired local data due to download failure.")
                else:
                    raise e
        
        satellites = []
        with open(local_filename, mode = 'r', encoding = 'utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    sat = EarthSatellite.from_omm(self.ts, row)
                    satellites.append(sat)
                except Exception:
                    continue
        
        print(f"[SUCCESS] Loaded {len(satellites)} active satellites into memory.")
        return satellites