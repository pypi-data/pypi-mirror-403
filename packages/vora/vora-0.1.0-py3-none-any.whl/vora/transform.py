import numpy as np
from pyproj import Proj
from pyproj import Transformer
from pyproj.network import set_network_enabled
set_network_enabled(True) # download from network if not found locally

crs_wgs84_egm2008 = "EPSG:4326+3855" # WGS84 (Lat/Lon) + EGM2008 (Vertical Height)
crs_ecef = "EPSG:4978" # WGS84 ECEF (Geocentric - x, y, z)
# geodetic -> ecef
to_ecef = Transformer.from_crs(crs_wgs84_egm2008, crs_ecef, always_xy=True) # 'always_xy=True' in transformer means input order is (lon, lat, z)
# ecef -> geodetic
to_geodetic = Transformer.from_crs(crs_ecef, crs_wgs84_egm2008, always_xy=True) # 'always_xy=True' in transformer means input order is (lon, lat, z)

def lonlat_elevation_to_xyz_3d(lon, lat, elevation):
    x, y, z = to_ecef.transform(lon, lat, elevation)
    return x, y, z

def xyz_to_lonlat_elevation_3d(x, y, z):
    lon, lat, elevation = to_geodetic.transform(x, y, z)
    return lon, lat, elevation

def lonlat_radius_to_xyz_sphere(lon, lat, R=1):
    # R: radius of the sphere (e.g., Earth's mean radius ~ 6371 km)
    # R in the same unit as output x, y, z (e.g., meters)
    phi = np.radians(lat)
    lambda_ = np.radians(lon)
    x = R * np.cos(phi) * np.cos(lambda_)
    y = R * np.cos(phi) * np.sin(lambda_)
    z = R * np.sin(phi)
    return x, y, z

def xyz_to_lonlat_radius_sphere(x, y, z):
    R = np.sqrt(x**2 + y**2 + z**2)
    phi = np.arcsin(z / R)
    lambda_ = np.arctan2(y, x)
    lat = np.degrees(phi)
    lon = np.degrees(lambda_)
    return lon, lat, R

def lonlat_to_xy_2d(lon, lat, lon0=None, lat0=None):
    """
    works for smaller area that can be approximated as a plane
    """
    if lon0 is None: lon0 = np.median(lon)
    if lat0 is None: lat0 = np.median(lat)
    proj = Proj(f"+proj=aeqd +lon_0={lon0} +lat_0={lat0} +units=m")
    x, y = proj(lon, lat)
    return x, y