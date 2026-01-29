from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from geopic_tag_reader.model import PictureType
from enum import Enum
import timezonefinder  # type: ignore
import pytz
from geopic_tag_reader.i18n import init as i18n_init

try:
    import pyexiv2  # type: ignore
except ImportError:
    raise Exception(
        """Impossible to write the exif tags without the '[write-exif]' dependency (that will need to install libexiv2).
Install this package with `pip install geopic-tag-reader[write-exif]` to use this function"""
    )

tz_finder = timezonefinder.TimezoneFinder()


class UnsupportedExifTagException(Exception):
    """Exception for invalid key in additional tags"""

    def __init__(self, msg):
        super().__init__(msg)


class DirectionRef(str, Enum):
    """Indicates the reference for giving the direction of the image when it is captured."""

    magnetic_north = "M"
    true_north = "T"


@dataclass
class Direction:
    value: float
    ref: DirectionRef = DirectionRef.true_north


@dataclass
class PictureMetadata:
    capture_time: Optional[datetime] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    picture_type: Optional[PictureType] = None
    altitude: Optional[float] = None
    direction: Optional[Direction] = None
    additional_exif: Optional[dict] = None

    def has_change(self) -> bool:
        return (
            self.capture_time is not None
            or self.longitude is not None
            or self.latitude is not None
            or self.picture_type is not None
            or self.altitude is not None
            or self.direction is not None
            or self.additional_exif is not None
        )


FLOAT_PRECISION = 1000  # hardcoded for the moment, if needed we can put this in metadata


def _fraction(value: float):
    """Return a exif fraction from a float
    >>> _fraction(1.2)
    '1200/1000'
    >>> _fraction(0)
    '0/1000'
    """
    return f"{int(value * FLOAT_PRECISION)}/{FLOAT_PRECISION}"


def writePictureMetadata(picture: bytes, metadata: PictureMetadata, lang_code: str = "en") -> bytes:
    """
    Override exif metadata on raw picture and return updated bytes
    """

    _ = i18n_init(lang_code)

    if not metadata.has_change():
        return picture

    img = pyexiv2.ImageData(picture)

    updated_exif: Dict[str, Any] = {}
    updated_xmp: Dict[str, Any] = {}

    if metadata.capture_time:
        if metadata.capture_time.tzinfo is None:
            metadata.capture_time = localize_capture_time(metadata, img)
        updated_exif.update(_date_exif_tags(metadata.capture_time))

    if metadata.latitude is not None:
        updated_exif["Exif.GPSInfo.GPSLatitudeRef"] = "N" if metadata.latitude > 0 else "S"
        updated_exif["Exif.GPSInfo.GPSLatitude"] = _to_exif_dms(metadata.latitude)

    if metadata.longitude is not None:
        updated_exif["Exif.GPSInfo.GPSLongitudeRef"] = "E" if metadata.longitude > 0 else "W"
        updated_exif["Exif.GPSInfo.GPSLongitude"] = _to_exif_dms(metadata.longitude)

    if metadata.picture_type is not None:
        if metadata.picture_type == PictureType.equirectangular:
            # only add GPano tags for equirectangular pictures
            updated_xmp["Xmp.GPano.ProjectionType"] = metadata.picture_type.value
            updated_xmp["Xmp.GPano.UsePanoramaViewer"] = True
        else:
            # remove GPano tags for flat picture
            updated_xmp["Xmp.GPano.ProjectionType"] = None
            updated_xmp["Xmp.GPano.UsePanoramaViewer"] = None

    if metadata.altitude is not None:
        updated_exif["Exif.GPSInfo.GPSAltitude"] = _fraction(abs(metadata.altitude))
        updated_exif["Exif.GPSInfo.GPSAltitudeRef"] = 0 if metadata.altitude >= 0 else 1

    if metadata.direction is not None:
        direction = _fraction(abs(metadata.direction.value % 360.0))
        updated_exif["Exif.GPSInfo.GPSImgDirection"] = direction
        updated_exif["Exif.GPSInfo.GPSImgDirectionRef"] = metadata.direction.ref.value
        # also write GPano tag
        updated_xmp["Xmp.GPano.PoseHeadingDegrees"] = direction

    if metadata.additional_exif:
        for k, v in metadata.additional_exif.items():
            if k.startswith("Xmp."):
                updated_xmp.update({k: v})
            elif k.startswith("Exif."):
                updated_exif.update({k: v})
            else:
                raise UnsupportedExifTagException(_("Unsupported key in additional tags ({k})").format(k=k))

    if updated_exif:
        img.modify_exif(updated_exif)
    if updated_xmp:
        img.modify_xmp(updated_xmp)

    return img.get_bytes()


def _date_exif_tags(capture_time: datetime) -> Dict[str, str]:
    """
    Add date time in Exif:
    * DateTimeOriginal (and SubSecTimeOriginal OffsetTimeOriginal when available) as local time
    * GPSDateStamp/GPSTimeStamp as UTC time
    """
    tags = {}
    # for capture time, override GPSInfo time and DatetimeOriginal
    tags["Exif.Photo.DateTimeOriginal"] = capture_time.strftime("%Y-%m-%d %H:%M:%S")

    tags["Exif.Photo.SubSecTimeOriginal"] = capture_time.strftime("%f")
    offset = capture_time.utcoffset()
    tags["Exif.Photo.OffsetTimeOriginal"] = format_offset(offset)

    utc_dt = capture_time.astimezone(tz=pytz.UTC)
    tags["Exif.GPSInfo.GPSDateStamp"] = utc_dt.strftime("%Y-%m-%d")
    tags["Exif.GPSInfo.GPSTimeStamp"] = utc_dt.strftime("%H/1 %M/1 %S/1")
    return tags


def format_offset(offset: Optional[timedelta]) -> str:
    """Format offset for OffsetTimeOriginal. Format is like "+02:00" for paris offset
    >>> format_offset(timedelta(hours=5, minutes=45))
    '+05:45'
    >>> format_offset(timedelta(hours=-3))
    '-03:00'
    """
    if offset is None:
        return "+00:00"
    offset_hour, remainer = divmod(offset.total_seconds(), 3600)
    return f"{'+' if offset_hour >= 0 else '-'}{int(abs(offset_hour)):02}:{int(remainer/60):02}"


def localize_capture_time(metadata: PictureMetadata, img_metadata: pyexiv2.ImageData) -> datetime:
    """
    Localize a datetime in the timezone of the picture
    If the picture does not contains GPS position, the datetime will not be modified.
    """
    assert metadata.capture_time
    dt = metadata.capture_time

    if metadata.longitude is not None and metadata.latitude is not None:
        # if the coord have been overrided, read it instead of the picture's
        lon = metadata.longitude
        lat = metadata.latitude
    else:
        exif = img_metadata.read_exif()
        try:
            raw_lon = exif["Exif.GPSInfo.GPSLongitude"]
            lon_ref = exif.get("Exif.GPSInfo.GPSLongitudeRef", "E")
            raw_lat = exif["Exif.GPSInfo.GPSLatitude"]
            lat_ref = exif.get("Exif.GPSInfo.GPSLatitudeRef", "N")
            lon = _from_dms(raw_lon) * (1 if lon_ref == "E" else -1)
            lat = _from_dms(raw_lat) * (1 if lat_ref == "N" else -1)
        except KeyError:
            return metadata.capture_time  # canot localize, returning same date

    if not lon or not lat:
        return dt  # canot localize, returning same date

    tz_name = tz_finder.timezone_at(lng=lon, lat=lat)
    if not tz_name:
        return dt  # cannot find timezone, returning same date

    tz = pytz.timezone(tz_name)

    return tz.localize(dt)


def _from_dms(val: str) -> float:
    """Convert exif lat/lon represented as degre/minute/second into decimal
    >>> _from_dms("1/1 55/1 123020/13567")
    1.9191854417991367
    >>> _from_dms("49/1 0/1 1885/76")
    49.00688961988304
    """
    deg_raw, min_raw, sec_raw = val.split(" ")
    deg_num, deg_dec = deg_raw.split("/")
    deg = float(deg_num) / float(deg_dec)
    min_num, min_dec = min_raw.split("/")
    min = float(min_num) / float(min_dec)
    sec_num, sec_dec = sec_raw.split("/")
    sec = float(sec_num) / float(sec_dec)

    return float(deg) + float(min) / 60 + float(sec) / 3600


def _to_dms(value: float) -> Tuple[int, int, float]:
    """Return degree/minute/seconds for a decimal
    >>> _to_dms(38.889469)
    (38, 53, 22.0884)
    >>> _to_dms(43.7325)
    (43, 43, 57.0)
    >>> _to_dms(-43.7325)
    (43, 43, 57.0)
    """
    value = abs(value)
    deg = int(value)
    min = (value - deg) * 60
    sec = (min - int(min)) * 60

    return deg, int(min), round(sec, 8)


def _to_exif_dms(value: float) -> str:
    """Return degree/minute/seconds string formated for the exif metadata for a decimal
    >>> _to_exif_dms(38.889469)
    '38/1 53/1 55221/2500'
    """
    from fractions import Fraction

    d, m, s = _to_dms(value)
    f = Fraction.from_float(s).limit_denominator()  # limit fraction precision
    num_s, denomim_s = f.as_integer_ratio()
    return f"{d}/1 {m}/1 {num_s}/{denomim_s}"
