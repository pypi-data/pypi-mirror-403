import numpy


def as_of(lat, lon):
    return numpy.array([lat, lon])


earth_radius = 6371000  # of earth, in meter


def xyz_of(lat, lon):
    lat = numpy.radians(lat)
    lon = numpy.radians(lon)
    x = earth_radius * numpy.cos(lat) * numpy.cos(lon)
    y = earth_radius * numpy.cos(lat) * numpy.sin(lon)
    z = earth_radius * numpy.sin(lat)
    return numpy.array([x, y, z])


def precision_cutoff(lat_or_lon: float):
    return format(lat_or_lon, '.6f')
