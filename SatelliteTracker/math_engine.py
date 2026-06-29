import math

class ViewAngleCalculator:
    # WGS84 Earth Ellipsoid Constants
    a = 6378.137          # Earth's equatorial radius in kilometers
    e2 = 0.00669437999    # Earth's orbital eccentricity squared (squash factor)

    @classmethod
    def get_view_angles(cls, sat_lat, sat_lon, sat_alt_km, obs_lat, obs_lon, obs_alt_km = 0.0):
        """Calculates Azimuth, Elevation, and Distance from an observer to a satellite."""

        # Convert Observer and Satellite to 3D Earth-Centered (ECEF) Coordinates
        obs_x, obs_y, obs_z = cls._geodetic_to_ecef(obs_lat, obs_lon, obs_alt_km)
        sat_x, sat_y, sat_z = cls._geodetic_to_ecef(sat_lat, sat_lon, sat_alt_km)

        # Find the raw Vector Difference
        dx = sat_x - obs_x
        dy = sat_y - obs_y
        dz = sat_z - obs_z

        # Rotate the 3D space to match the observer's Horizon (East-North-Up)
        e, n, u = cls._ecef_to_enu(dx, dy, dz, obs_lat, obs_lon)

        # Get final angles
        distance_km = math.sqrt(e**2 + n**2 + u**2)

        elevation_rad = math.asin(u / distance_km)
        elevation_deg = math.degrees(elevation_rad)

        azimuth_rad = math.atan2(e, n)
        azimuth_deg = math.degrees(azimuth_rad) % 360.0

        return elevation_deg, azimuth_deg, distance_km
    
    @classmethod
    def geodetic_to_ecef(cls, lat_deg, lon_deg, alt_km):
        """Converts Latitude/Longitude into 3D Cartesian coordinates from Earth's core."""
        lat_rad = math.radians(lat_deg)
        lon_rad = math.radians(lon_deg)

        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)

        # N is the radius of curvature in the prime vertical
        N = cls.a / math.sqrt(1 - cls.e2 * sin_lat**2)

        x = (N + alt_km) * cos_lat * cos_lon
        y = (N + alt_km) * cos_lat * sin_lon
        z = (N * (1 - cls.e2) + alt_km) * sin_lat

        return x, y, z
    
    @classmethod
    def _ecef_to_enu(cls, dx, dy, dz, obs_lat_deg, obs_lon_deg):
        """Rotates a 3D Earth-Centered vector to a Local Horizon vector."""
        lat_rad = math.radians(obs_lat_deg)
        lon_rad = math.radians(obs_lon_deg)
        
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)
        
        # Matrix Multiplication (Observer Rotation)
        e = -sin_lon * dx + cos_lon * dy
        n = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
        u = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
        
        return e, n, u