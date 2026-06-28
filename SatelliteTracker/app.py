from flask import Flask, jsonify, render_template, request
from orbit_engine import OrbitEngine

# Initialize the Web App and Physics Engine
app = Flask(__name__)
print("[BOOT] Starting Orbit Engine for Web Server...")
engine = OrbitEngine()
all_sats = engine.fetcher.fetch_active_satellites()

# Serve the webpage
@app.route('/')
def home():
    return render_template('index.html')

# Send the full list of 8,000+ names to the browser
@app.route('/api/satellites')
def get_satellite_list():
    names = [s.name for s in all_sats]
    return jsonify(names)

# Create the API Endpoint for the frontend to fetch data from
@app.route('/api/telemetry')
def get_telemetry():
    # Grab the name from the browser's URL (Default to ISS if empty)
    target_name = request.args.get('name', 'ISS (ZARYA)')

    # Search the database for the matching satellite
    target_sat = next((s for s in all_sats if target_name.upper() in s.name.upper()), None)
    if not target_sat:
        return jsonify({"error": f"Could not find a satellite matching {target_name}"}), 404
    
    # Get coordinates from browser, defaults to Tel Aviv
    my_lat = float(request.args.get('lat', 32.0853))
    my_lon = float(request.args.get('lon', 34.7818))

    # Get the data
    loc = engine.get_location_by_time(target_sat)
    vis = engine.get_visibility_status(target_sat, my_lat, my_lon)
    
    path_coords = engine.get_orbit_path(target_sat)

    # Convert the Python datetime object into a string
    if vis.get("next_pass_utc") is not None:
        vis["next_pass_utc"] = vis["next_pass_utc"].isoformat()

    # Package as JSON for the browser
    return jsonify({
        "name": target_sat.name,
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
        "altitude_km": loc["altitude_km"],
        "visibility": vis,
        "path": path_coords
    })

if __name__ == '__main__':
    # Run the server on port 5000
    app.run(debug=True, port=5000)