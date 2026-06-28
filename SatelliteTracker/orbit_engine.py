import time
from datetime import datetime, timezone, timedelta
from skyfield.api import wgs84
from data_fetcher import SatelliteDataFetcher
import math

class OrbitEngine:
    def __init__ (self):
        # Initializes the physics engine using Skyfield's internal timescales
        self.fetcher = SatelliteDataFetcher()
        self.ts = self.fetcher.ts

    def get_location_by_time(self, satellite, target_datetime=None):
        """Returns the Latitude, Longitude, and Altitude at a specific time."""
        if target_datetime is None:
            target_datetime = datetime.now(timezone.utc)
            
        t = self.ts.from_datetime(target_datetime)
        geocentric = satellite.at(t)
        subpoint = wgs84.subpoint(geocentric)
        
        return {
            "time_utc": target_datetime,
            "latitude": subpoint.latitude.degrees,
            "longitude": subpoint.longitude.degrees,
            "altitude_km": subpoint.elevation.km
        }
    
    def get_orbit_path(self, satellite):

        try: 
            orbit_minutes = int((2 * math.pi) / satellite.model.no_kozai)
        except AttributeError:
            orbit_minutes = 90

        segments = []
        current_segment = []
        now = datetime.now(timezone.utc)
        prev_lon = None

        for i in range(orbit_minutes):
            future_time = now + timedelta(minutes=i)
            loc = self.get_location_by_time(satellite, target_datetime=future_time) 
            lon = loc["longitude"]
            lat = loc["latitude"]

            if prev_lon is not None and abs(lon - prev_lon) > 180:
                segments.append(current_segment)
                current_segment = []
            
            current_segment.append([lat, lon])
            prev_lon = lon
        
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def get_visibility_status(self, satellite, observer_lat, observer_lon, min_angle = 10.0):
        """
        Checks if the satellite is visible right now. 
        If it isn't, calculates exactly when it will be.
        """
        ground_station = wgs84.latlon(observer_lat, observer_lon)
        t_now = self.ts.now()

        # Checking where the satellite is right now
        difference = satellite - ground_station
        topocentric = difference.at(t_now)
        elevation, azimuth, distance = topocentric.altaz()

        # Return if high enough to be visible
        if elevation.degrees >= min_angle:
            return {
                "visible_now": True,
                "current_elevation": round(elevation.degrees, 2),
                "current_azimuth": round(azimuth.degrees, 2),
                "distance_km": round(distance.km, 2),
                "next_pass_utc": t_now.utc_datetime()
            }
        
        # If not visible right now, when will it be in the next 7 days
        t_future = self.ts.from_datetime(t_now.utc_datetime() + timedelta(days = 7))
        t_events, events = satellite.find_events(ground_station, t_now, t_future, altitude_degrees = min_angle)

        next_pass_time = None
        for ti, event in zip(t_events, events):
            if event == 0: # Above the horizon
                next_pass_time = ti.utc_datetime()
                break

        return {
            "visible_now": False,
            "current_elevation": round(elevation.degrees, 2),
            "next_pass_utc": next_pass_time
        }