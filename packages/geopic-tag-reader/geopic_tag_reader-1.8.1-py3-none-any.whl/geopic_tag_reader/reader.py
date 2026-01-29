import xmltodict
import pyexiv2  # type: ignore
import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
import re
import json
from fractions import Fraction
from geopic_tag_reader import camera
import timezonefinder  # type: ignore
import pytz
from geopic_tag_reader.i18n import init as i18n_init
import math

# This is a fix for invalid MakerNotes leading to picture not read at all
# https://github.com/LeoHsiao1/pyexiv2/issues/58
pyexiv2.set_log_level(4)

tz_finder = timezonefinder.TimezoneFinder()


@dataclass
class CropValues:
    """Cropped equirectangular pictures metadata

    Attributes:
        fullWidth (int): Full panorama width
        fullHeight (int): Full panorama height
        width (int): Cropped area width
        height (int): Cropped area height
        left (int): Cropped area left offset
        top (int): Cropped area top offset
    """

    fullWidth: int
    fullHeight: int
    width: int
    height: int
    left: int
    top: int


@dataclass
class TimeBySource:
    """All datetimes read from available sources

    Attributes:
        gps (datetime): Time read from GPS clock
        camera (datetime): Time read from camera clock (DateTimeOriginal)
    """

    gps: Optional[datetime.datetime] = None
    camera: Optional[datetime.datetime] = None

    def getBest(self) -> Optional[datetime.datetime]:
        """Get the best available datetime to use"""
        if self.gps is not None and self.camera is None:
            return self.gps
        elif self.gps is None and self.camera is not None:
            return self.camera
        elif self.gps is None and self.camera is None:
            return None
        elif self.camera.microsecond > 0 and self.gps.microsecond == 0:  # type: ignore
            return self.camera
        else:
            return self.gps


@dataclass
class GeoPicTags:
    """Tags associated to a geolocated picture

    Attributes:
        lat (float): GPS Latitude (in WGS84)
        lon (float): GPS Longitude (in WGS84)
        ts (datetime): The capture date (date & time with timezone)
        heading (int): Picture GPS heading (in degrees, North = 0°, East = 90°, South = 180°, West = 270°). Value is computed based on image center (if yaw=0°)
        type (str): The kind of picture (flat, equirectangular)
        make (str): The camera manufacturer name
        model (str): The camera model name
        focal_length (float): The camera focal length (in mm)
        crop (CropValues): The picture cropped area metadata (optional)
        exif (dict[str, str]): Raw EXIF tags from picture (following Exiv2 naming scheme, see https://exiv2.org/metadata.html)
        tagreader_warnings (list[str]): List of thrown warnings during metadata reading
        altitude (float): altitude (in m) (optional)
        pitch (float): Picture pitch angle, compared to horizon (in degrees, bottom = -90°, horizon = 0°, top = 90°)
        roll (float): Picture roll angle, on a right/left axis (in degrees, left-arm down = -90°, flat = 0°, right-arm down = 90°)
        yaw (float): Picture yaw angle, on a vertical axis (in degrees, front = 0°, right = 90°, rear = 180°, left = 270°). This offsets the center image from GPS direction for a correct 360° sphere correction
        ts_by_source (TimeBySource): all read timestamps from image, for finer processing.
        sensor_width (float): The camera sensor width, that can be used to compute field of view (combined with focal length)
        field_of_view (int): How large picture is showing of horizon (in degrees)
        gps_accuracy (float): How precise the GPS position is (in meters)


    Implementation note: this needs to be sync with the PartialGeoPicTags structure
    """

    lat: float
    lon: float
    ts: datetime.datetime
    heading: Optional[int]
    type: str
    make: Optional[str]
    model: Optional[str]
    focal_length: Optional[float]
    crop: Optional[CropValues]
    exif: Dict[str, str] = field(default_factory=lambda: {})
    tagreader_warnings: List[str] = field(default_factory=lambda: [])
    altitude: Optional[float] = None
    pitch: Optional[float] = None
    roll: Optional[float] = None
    yaw: Optional[float] = None
    ts_by_source: Optional[TimeBySource] = None
    sensor_width: Optional[float] = None
    field_of_view: Optional[int] = None
    gps_accuracy: Optional[float] = None


class InvalidExifException(Exception):
    """Exception for invalid EXIF information from image"""

    def __init__(self, msg):
        super().__init__(msg)


class InvalidFractionException(Exception):
    """Exception for invalid list of fractions"""


@dataclass
class PartialGeoPicTags:
    """Tags associated to a geolocated picture when not all tags have been found

    Implementation note: this needs to be sync with the GeoPicTags structure
    """

    lat: Optional[float] = None
    lon: Optional[float] = None
    ts: Optional[datetime.datetime] = None
    heading: Optional[int] = None
    type: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    focal_length: Optional[float] = None
    crop: Optional[CropValues] = None
    exif: Dict[str, str] = field(default_factory=lambda: {})
    tagreader_warnings: List[str] = field(default_factory=lambda: [])
    altitude: Optional[float] = None
    pitch: Optional[float] = None
    roll: Optional[float] = None
    yaw: Optional[float] = None
    ts_by_source: Optional[TimeBySource] = None
    sensor_width: Optional[float] = None
    field_of_view: Optional[int] = None
    gps_accuracy: Optional[float] = None


class PartialExifException(Exception):
    """
    Exception for partial / missing EXIF information from image

    Contains a PartialGeoPicTags with all tags that have been read and the list of missing tags
    """

    def __init__(self, msg, missing_mandatory_tags: Set[str], partial_tags: PartialGeoPicTags):
        super().__init__(msg)
        self.missing_mandatory_tags = missing_mandatory_tags
        self.tags = partial_tags


def readPictureMetadata(picture: bytes, lang_code: str = "en") -> GeoPicTags:
    """Extracts metadata from picture file

    Args:
        picture (bytes): Picture file
        lang_code (str): Language code for translating error labels

    Returns:
        GeoPicTags: Extracted metadata from picture
    """

    data = {}
    with pyexiv2.ImageData(picture) as img:
        data.update(img.read_exif())
        data.update(img.read_iptc())
        data.update(img.read_xmp())
        width = img.get_pixel_width()
        height = img.get_pixel_height()

        imgComment = img.read_comment()
        if imgComment is not None and len(imgComment.strip()) > 0:
            data["Exif.Photo.UserComment"] = imgComment

    # Read Mapillary tags
    if "Exif.Image.ImageDescription" in data:
        # Check if data can be read
        imgDesc = data["Exif.Image.ImageDescription"]
        try:
            imgDescJson = json.loads(imgDesc)
            data.update(imgDescJson)
        except:
            pass

    return getPictureMetadata(data, width, height, lang_code)


def getPictureMetadata(data: dict, width: int, height: int, lang_code: str = "en") -> GeoPicTags:
    """Extracts metadata from already read metadata.

    This method is useful when you already have the metadata read by `readPictureMetadata` and you want to extract the metadata from it.

    Args:
        data (dict): Raw EXIF tags / iptc / xmp / description from picture. MUST be comming from a previsou parse by the `readPictureMetadata` method.
        width (int): Picture width
        height (int): Picture height
        lang_code (str): Language code for translating error labels

    Returns:
        GeoPicTags: Extracted metadata from picture
    """

    _ = i18n_init(lang_code)
    warnings = []

    # Sanitize charset information
    for k, v in data.items():
        if isinstance(v, str):
            data[k] = re.sub(r"charset=[^\s]+", "", v).strip()

    # Parse latitude/longitude
    lat, lon, llw = decodeLatLon(data, "Exif.GPSInfo", _)
    if len(llw) > 0:
        warnings.extend(llw)

    if lat is None:
        lat, lon, llw = decodeLatLon(data, "Xmp.exif", _)
        if len(llw) > 0:
            warnings.extend(llw)

    if lat is None and isExifTagUsable(data, "MAPLatitude", float) and isExifTagUsable(data, "MAPLongitude", float):
        lat = float(data["MAPLatitude"])
        lon = float(data["MAPLongitude"])

    # Check coordinates validity
    if lat is not None and (lat < -90 or lat > 90):
        raise InvalidExifException(_("Read latitude is out of WGS84 bounds (should be in [-90, 90])"))
    if lon is not None and (lon < -180 or lon > 180):
        raise InvalidExifException(_("Read longitude is out of WGS84 bounds (should be in [-180, 180])"))

    # Parse GPS date/time
    gpsTs, llw = decodeGPSDateTime(data, "Exif.GPSInfo", _, lat, lon)

    if len(llw) > 0:
        warnings.extend(llw)

    if gpsTs is None:
        gpsTs, llw = decodeGPSDateTime(data, "Xmp.exif", _, lat, lon)
        if len(llw) > 0:
            warnings.extend(llw)

    if gpsTs is None and isExifTagUsable(data, "MAPGpsTime"):
        try:
            year, month, day, hour, minutes, seconds, milliseconds = [int(dp) for dp in data["MAPGpsTime"].split("_")]
            gpsTs = datetime.datetime(
                year,
                month,
                day,
                hour,
                minutes,
                seconds,
                milliseconds * 1000,
                tzinfo=datetime.timezone.utc,
            )

        except Exception as e:
            warnings.append(_("Skipping Mapillary date/time as it was not recognized: {v}").format(v=data["MAPGpsTime"]))

    # Parse camera date/time
    cameraTs = None
    for exifGroup, dtField, subsecField in [
        ("Exif.Photo", "DateTimeOriginal", "SubSecTimeOriginal"),
        ("Exif.Image", "DateTimeOriginal", "SubSecTimeOriginal"),
        ("Exif.Image", "DateTime", "SubSecTimeOriginal"),
        ("Xmp.GPano", "SourceImageCreateTime", "SubSecTimeOriginal"),
        ("Xmp.exif", "DateTimeOriginal", "SubsecTimeOriginal"),  # Case matters
    ]:
        if cameraTs is None:
            cameraTs, llw = decodeDateTimeOriginal(data, exifGroup, dtField, subsecField, _, lat, lon)
            if len(llw) > 0:
                warnings.extend(llw)

        if cameraTs is not None:
            break
    tsSources = TimeBySource(gps=gpsTs, camera=cameraTs) if gpsTs or cameraTs else None
    d = tsSources.getBest() if tsSources is not None else None

    # GPS Heading
    heading = None
    if isExifTagUsable(data, "Exif.GPSInfo.GPSImgDirection", Fraction):
        heading = int(round(float(Fraction(data["Exif.GPSInfo.GPSImgDirection"]))))

    elif "MAPCompassHeading" in data and isExifTagUsable(data["MAPCompassHeading"], "TrueHeading", float):
        heading = int(round(float(data["MAPCompassHeading"]["TrueHeading"])))

    if heading is None:
        warnings.append(_("No heading value was found, this reduces usability of picture"))

    # Yaw / Pitch / roll
    yaw = None
    pitch = None
    roll = None
    exifYPRFields = {
        "yaw": ["Xmp.Camera.Yaw", "Xmp.GPano.PoseHeadingDegrees"],
        "pitch": ["Xmp.Camera.Pitch", "Xmp.GPano.PosePitchDegrees"],
        "roll": ["Xmp.Camera.Roll", "Xmp.GPano.PoseRollDegrees"],
    }
    for ypr in exifYPRFields:
        for exifTag in exifYPRFields[ypr]:
            foundValue = None
            # Look for float or fraction
            if isExifTagUsable(data, exifTag, float):
                foundValue = float(data[exifTag])
            elif isExifTagUsable(data, exifTag, Fraction):
                foundValue = float(Fraction(data[exifTag]))

            # Save found value
            if foundValue is not None:
                if ypr == "yaw" and yaw is None:
                    yaw = foundValue
                elif ypr == "pitch" and pitch is None:
                    pitch = foundValue
                elif ypr == "roll" and roll is None:
                    roll = foundValue

    # Make and model
    make = data.get("Exif.Image.Make") or data.get("MAPDeviceMake")
    model = data.get("Exif.Image.Model") or data.get("MAPDeviceModel")

    if make is not None:
        make = decodeMakeModel(make).strip()

    if model is not None:
        model = decodeMakeModel(model).strip()

    if make is not None and model is not None and model.startswith(make) and len(model) > len(make):
        model = model.replace(make, "").strip()

    if make is None and model is None:
        warnings.append(_("No make and model value found, no assumption on focal length or GPS precision can be made"))

    cameraMetadata = camera.find_camera(make, model)

    # Cropped pano data
    crop = None
    if (
        (isExifTagUsable(data, "Xmp.GPano.FullPanoWidthPixels", int) or isExifTagUsable(data, "Xmp.GPano.FullPanoHeightPixels", int))
        and isExifTagUsable(data, "Xmp.GPano.CroppedAreaImageWidthPixels", int)
        and isExifTagUsable(data, "Xmp.GPano.CroppedAreaImageHeightPixels", int)
        and isExifTagUsable(data, "Xmp.GPano.CroppedAreaLeftPixels", int)
        and isExifTagUsable(data, "Xmp.GPano.CroppedAreaTopPixels", int)
    ):
        w = int(data["Xmp.GPano.CroppedAreaImageWidthPixels"])
        h = int(data["Xmp.GPano.CroppedAreaImageHeightPixels"])
        l = int(data["Xmp.GPano.CroppedAreaLeftPixels"])
        t = int(data["Xmp.GPano.CroppedAreaTopPixels"])

        # Compute full width & height, even if one is missing
        fw = None
        fh = None
        if isExifTagUsable(data, "Xmp.GPano.FullPanoWidthPixels", int):
            fw = int(data["Xmp.GPano.FullPanoWidthPixels"])
        if isExifTagUsable(data, "Xmp.GPano.FullPanoHeightPixels", int):
            fh = int(data["Xmp.GPano.FullPanoHeightPixels"])
        if fw is None:
            fw = fh * 2  # type: ignore
            # Center image horizontally if full weight is guessed
            if fw > w and l == 0:
                l = math.floor((fw - w) / 2)
        if fh is None:
            fh = math.floor(fw / 2)  # type: ignore
            # Center image vertically if full height is guessed
            if fh > h and t == 0:
                t = math.floor((fh - h) / 2)

        if fw > w or fh > h:
            crop = CropValues(fw, fh, w, h, l, t)

    # Skip images where crop width/height equals full width/length
    elif (
        isExifTagUsable(data, "Xmp.GPano.CroppedAreaImageWidthPixels", int)
        and isExifTagUsable(data, "Xmp.GPano.CroppedAreaImageHeightPixels", int)
        and isExifTagUsable(data, "Xmp.GPano.FullPanoWidthPixels", int)
        and isExifTagUsable(data, "Xmp.GPano.FullPanoHeightPixels", int)
        and int(data["Xmp.GPano.FullPanoHeightPixels"]) == int(data["Xmp.GPano.CroppedAreaImageHeightPixels"])
        and int(data["Xmp.GPano.FullPanoWidthPixels"]) == int(data["Xmp.GPano.CroppedAreaImageWidthPixels"])
    ):
        pass

    elif (
        isExifTagUsable(data, "Xmp.GPano.CroppedAreaImageWidthPixels", int)
        or isExifTagUsable(data, "Xmp.GPano.CroppedAreaImageHeightPixels", int)
        or isExifTagUsable(data, "Xmp.GPano.CroppedAreaLeftPixels", int)
        or isExifTagUsable(data, "Xmp.GPano.CroppedAreaTopPixels", int)
    ):
        raise InvalidExifException("EXIF tags contain partial cropped area metadata")

    # Type
    pic_type = None
    # 360° based on GPano EXIF tag
    if isExifTagUsable(data, "Xmp.GPano.ProjectionType"):
        pic_type = data["Xmp.GPano.ProjectionType"]

        # Check for cylindrical
        if pic_type == "cylindrical" and crop is not None:
            pic_type = "equirectangular"
    # 360° based on known models
    elif camera.is_360(make, model, width, height):
        pic_type = "equirectangular"
    # Flat by default
    else:
        pic_type = "flat"

    # Focal length
    focalLength = decodeFloat(data, ["Exif.Image.FocalLength", "Exif.Photo.FocalLength"])
    focalLength35mm = decodeFloat(data, ["Exif.Image.FocalLengthIn35mmFilm", "Exif.Photo.FocalLengthIn35mmFilm"])
    scaleFactor35efl = focalLength35mm / focalLength if focalLength and focalLength35mm else None

    if focalLength is None and pic_type != "equirectangular":
        warnings.append(_("No focal length value was found, this prevents calculating field of view"))

    # Sensor width
    sensorWidth = None
    if cameraMetadata is not None:
        sensorWidth = cameraMetadata.sensor_width

    # Field of view
    fieldOfView = None
    if pic_type == "equirectangular":  # 360°
        fieldOfView = 360
    elif sensorWidth is not None and focalLength is not None:  # Based on camera metadata
        fieldOfView = round(math.degrees(2 * math.atan(sensorWidth / (2 * focalLength))))
    elif focalLength is not None and scaleFactor35efl is not None:  # Using EXIF Tags
        fieldOfView = compute_fov(focalLength, scaleFactor35efl)

    # Altitude
    altitude = None
    if isExifTagUsable(data, "Exif.GPSInfo.GPSAltitude", Fraction):
        altitude_raw = int(round(float(Fraction(data["Exif.GPSInfo.GPSAltitude"]))))
        ref = -1 if data.get("Exif.GPSInfo.GPSAltitudeRef") == "1" else 1
        altitude = altitude_raw * ref

    # GPS accuracy
    gpshposEstimated = False
    gpshpos = decodeFloat(data, ["Exif.GPSInfo.GPSHPositioningError", "Xmp.exif.GPSHPositioningError"], 2)
    gpsdop = decodeFloat(data, ["Exif.GPSInfo.GPSDOP", "Xmp.exif.GPSDOP"], 2)

    gpsdiff = None
    if isExifTagUsable(data, "Exif.GPSInfo.GPSDifferential", int):
        gpsdiff = int(data["Exif.GPSInfo.GPSDifferential"])
    elif isExifTagUsable(data, "Xmp.exif.GPSDifferential", int):
        gpsdiff = int(data["Xmp.exif.GPSDifferential"])

    if gpshpos is None:
        if gpsdop is not None and gpsdop > 0:
            gpshposEstimated = True
            if gpsdiff == 1:  # DOP with a DGPS -> consider GPS nominal error as 1 meter
                gpshpos = gpsdop
            else:  # DOP without DGPS -> consider GPS nominal error as 3 meters in average
                gpshpos = round(3 * gpsdop, 2)
        elif gpsdiff == 1:  # DGPS only -> return 2 meters precision
            gpshpos = 2
            gpshposEstimated = True
        elif cameraMetadata is not None and cameraMetadata.gps_accuracy is not None:  # Estimate based on model
            gpshpos = cameraMetadata.gps_accuracy
            gpshposEstimated = True
        elif make is not None and make.lower() in camera.GPS_ACCURACY_MAKE:
            gpshpos = camera.GPS_ACCURACY_MAKE[make.lower()]
            gpshposEstimated = True

    if gpshpos is None:
        warnings.append(_("No GPS accuracy value found, this prevents computing a quality score"))
    elif gpshposEstimated:
        warnings.append(_("No GPS horizontal positioning error value found, GPS accuracy can only be estimated"))

    # Errors display
    errors = []
    missing_fields = set()
    if lat is None or lon is None or (lat == 0 and lon == 0):
        # Note: we consider that null island is not a valid position
        errors.append(_("No GPS coordinates or broken coordinates in picture EXIF tags"))
        if not lat:
            missing_fields.add("lat")
        if not lon:
            missing_fields.add("lon")
    if d is None:
        errors.append(_("No valid date in picture EXIF tags"))
        missing_fields.add("datetime")

    if errors:
        if len(errors) > 1:
            listOfErrors = _("The picture is missing mandatory metadata:")
            errorSep = "\n\t- "
            listOfErrors += errorSep + errorSep.join(errors)
        else:
            listOfErrors = errors[0]

        raise PartialExifException(
            listOfErrors,
            missing_fields,
            PartialGeoPicTags(
                lat,
                lon,
                d,
                heading,
                pic_type,
                make,
                model,
                focalLength,
                crop,
                exif=data,
                tagreader_warnings=warnings,
                altitude=altitude,
                pitch=pitch,
                roll=roll,
                yaw=yaw,
                ts_by_source=tsSources,
                sensor_width=sensorWidth,
                field_of_view=fieldOfView,
                gps_accuracy=gpshpos,
            ),
        )

    assert lon is not None and lat is not None and d is not None  # at this point all those fields cannot be null
    return GeoPicTags(
        lat,
        lon,
        d,
        heading,
        pic_type,
        make,
        model,
        focalLength,
        crop,
        exif=data,
        tagreader_warnings=warnings,
        altitude=altitude,
        pitch=pitch,
        roll=roll,
        yaw=yaw,
        ts_by_source=tsSources,
        sensor_width=sensorWidth,
        field_of_view=fieldOfView,
        gps_accuracy=gpshpos,
    )


def decodeMakeModel(value) -> str:
    """Python 2/3 compatible decoding of make/model field."""
    if hasattr(value, "decode"):
        try:
            return value.decode("utf-8").replace("\x00", "")
        except UnicodeDecodeError:
            return value
    else:
        return value.replace("\x00", "")


def isValidManyFractions(value: str) -> bool:
    try:
        return len(decodeManyFractions(value)) > 0
    except:
        return False


def decodeManyFractions(value: str) -> List[Fraction]:
    """Try to decode a list of fractions, separated by spaces"""

    try:
        vals = [Fraction(v.strip()) for v in value.split(" ")]
        if len([True for v in vals if v.denominator == 0]) > 0:
            raise InvalidFractionException()
        return vals

    except:
        raise InvalidFractionException()


def decodeFloat(data: dict, tags: List[str], precision: Optional[int] = None) -> Optional[float]:
    """
    Tries to read float-like value from many EXIF tags (looks for decimal value and fraction)
    """

    for tag in tags:
        v = None
        if isExifTagUsable(data, tag, float):
            v = float(data[tag])
        elif isExifTagUsable(data, tag, Fraction):
            v = float(Fraction(data[tag]))
        if v is not None:
            return round(v, precision) if precision is not None else v

    return None


def decodeLatLon(data: dict, group: str, _: Callable[[str], str]) -> Tuple[Optional[float], Optional[float], List[str]]:
    """Reads GPS info from given group to get latitude/longitude as float coordinates"""

    lat, lon = None, None
    warnings = []

    if isExifTagUsable(data, f"{group}.GPSLatitude", List[Fraction]) and isExifTagUsable(data, f"{group}.GPSLongitude", List[Fraction]):
        latRaw = decodeManyFractions(data[f"{group}.GPSLatitude"])
        if len(latRaw) == 3:
            if not isExifTagUsable(data, f"{group}.GPSLatitudeRef"):
                warnings.append(_("GPSLatitudeRef not found, assuming GPSLatitudeRef is North"))
                latRef = 1
            else:
                latRef = -1 if data[f"{group}.GPSLatitudeRef"].startswith("S") else 1
            lat = latRef * (float(latRaw[0]) + float(latRaw[1]) / 60 + float(latRaw[2]) / 3600)

            lonRaw = decodeManyFractions(data[f"{group}.GPSLongitude"])
            if len(lonRaw) != 3:
                raise InvalidExifException(_("Broken GPS coordinates in picture EXIF tags"))

            if not isExifTagUsable(data, f"{group}.GPSLongitudeRef"):
                warnings.append(_("GPSLongitudeRef not found, assuming GPSLongitudeRef is East"))
                lonRef = 1
            else:
                lonRef = -1 if data[f"{group}.GPSLongitudeRef"].startswith("W") else 1
            lon = lonRef * (float(lonRaw[0]) + float(lonRaw[1]) / 60 + float(lonRaw[2]) / 3600)

    if lat is None and lon is None:
        rawLat, rawLon = None, None
        if isExifTagUsable(data, f"{group}.GPSLatitude", float) and isExifTagUsable(data, f"{group}.GPSLongitude", float):
            rawLat = float(data[f"{group}.GPSLatitude"])
            rawLon = float(data[f"{group}.GPSLongitude"])
        elif isExifTagUsable(data, f"{group}.GPSLatitude", Fraction) and isExifTagUsable(data, f"{group}.GPSLongitude", Fraction):
            rawLat = float(Fraction(data[f"{group}.GPSLatitude"]))
            rawLon = float(Fraction(data[f"{group}.GPSLongitude"]))

        if rawLat and rawLon:
            latRef = 1
            if not isExifTagUsable(data, f"{group}.GPSLatitudeRef"):
                warnings.append(_("GPSLatitudeRef not found, assuming GPSLatitudeRef is North"))
            else:
                latRef = -1 if data[f"{group}.GPSLatitudeRef"].startswith("S") else 1

            lonRef = 1
            if not isExifTagUsable(data, f"{group}.GPSLongitudeRef"):
                warnings.append(_("GPSLongitudeRef not found, assuming GPSLongitudeRef is East"))
            else:
                lonRef = -1 if data[f"{group}.GPSLongitudeRef"].startswith("W") else 1

            lat = latRef * rawLat
            lon = lonRef * rawLon

    return (lat, lon, warnings)


def decodeDateTimeOriginal(
    data: dict,
    exifGroup: str,
    datetimeField: str,
    subsecField: str,
    _: Callable[[str], str],
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> Tuple[Optional[datetime.datetime], List[str]]:
    d = None
    warnings = []
    dtField = f"{exifGroup}.{datetimeField}"
    ssField = f"{exifGroup}.{subsecField}"

    if d is None and isExifTagUsable(data, dtField):
        try:
            dateRaw = data[dtField][:10].replace(":", "-")
            timeRaw = data[dtField][11:].split(":")
            hourRaw = int(timeRaw[0])
            minutesRaw = int(timeRaw[1])
            secondsRaw, microsecondsRaw, msw = decodeSecondsAndMicroSeconds(
                timeRaw[2] if len(timeRaw) >= 3 else "0",
                data[ssField] if isExifTagUsable(data, ssField, float) else "0",
                _,
            )
            warnings += msw

            d = datetime.datetime.combine(
                datetime.date.fromisoformat(dateRaw),
                datetime.time(
                    hourRaw,
                    minutesRaw,
                    secondsRaw,
                    microsecondsRaw,
                ),
            )

            # Timezone handling
            # Try to read from EXIF
            tz = decodeTimeOffset(data, f"{exifGroup}.OffsetTime{'Original' if 'DateTimeOriginal' in dtField else ''}")
            if tz is not None:
                d = d.replace(tzinfo=tz)

            # Otherwise, try to deduct from coordinates
            elif lon is not None and lat is not None:
                tz_name = tz_finder.timezone_at(lng=lon, lat=lat)
                if tz_name is not None:
                    d = pytz.timezone(tz_name).localize(d)
                # Otherwise, default to UTC + warning
                else:
                    d = d.replace(tzinfo=datetime.timezone.utc)
                    warnings.append(_("Precise timezone information not found, fallback to UTC"))

            # Otherwise, default to UTC + warning
            else:
                d = d.replace(tzinfo=datetime.timezone.utc)
                warnings.append(_("Precise timezone information not found (and no GPS coordinates to help), fallback to UTC"))

        except ValueError as e:
            warnings.append(
                _("Skipping original date/time (from {datefield}) as it was not recognized: {v}").format(datefield=dtField, v=data[dtField])
            )

    return (d, warnings)


def decodeTimeOffset(data: dict, offsetTimeField: str) -> Optional[datetime.tzinfo]:
    if isExifTagUsable(data, offsetTimeField, datetime.tzinfo):
        return datetime.datetime.fromisoformat(f"2020-01-01T00:00:00{data[offsetTimeField]}").tzinfo
    return None


def decodeGPSDateTime(
    data: dict, group: str, _: Callable[[str], str], lat: Optional[float] = None, lon: Optional[float] = None
) -> Tuple[Optional[datetime.datetime], List[str]]:
    d = None
    warnings = []

    if d is None and isExifTagUsable(data, f"{group}.GPSDateStamp"):
        try:
            dateRaw = data[f"{group}.GPSDateStamp"].replace(":", "-").replace("\x00", "").replace("/", "-")

            # Time
            if isExifTagUsable(data, f"{group}.GPSTimeStamp", List[Fraction]):
                timeRaw = decodeManyFractions(data[f"{group}.GPSTimeStamp"])
            elif isExifTagUsable(data, f"{group}.GPSTimeStamp", datetime.time):
                timeRaw = data[f"{group}.GPSTimeStamp"].split(":")
            elif isExifTagUsable(data, f"{group}.GPSDateTime", List[Fraction]):
                timeRaw = decodeManyFractions(data[f"{group}.GPSDateTime"])
            else:
                timeRaw = None
                warnings.append(
                    _("GPSTimeStamp and GPSDateTime don't contain supported time format (in {group} group)").format(group=group)
                )

            if timeRaw:
                seconds, microseconds, msw = decodeSecondsAndMicroSeconds(
                    str(float(timeRaw[2])),
                    "0",  # No SubSecTimeOriginal, it's only for DateTimeOriginal
                    _,
                )

                warnings += msw

                d = datetime.datetime.combine(
                    datetime.date.fromisoformat(dateRaw),
                    datetime.time(
                        int(float(timeRaw[0])),  # float->int to avoid DeprecationWarning
                        int(float(timeRaw[1])),
                        seconds,
                        microseconds,
                        tzinfo=datetime.timezone.utc,
                    ),
                )

                # Set timezone from coordinates
                if lon is not None and lat is not None:
                    tz_name = tz_finder.timezone_at(lng=lon, lat=lat)
                    if tz_name is not None:
                        d = d.astimezone(pytz.timezone(tz_name))

        except ValueError as e:
            warnings.append(
                _("Skipping GPS date/time ({group} group) as it was not recognized: {v}").format(
                    group=group, v=data[f"{group}.GPSDateStamp"]
                )
            )

    return (d, warnings)


def decodeSecondsAndMicroSeconds(secondsRaw: str, microsecondsRaw: str, _: Callable[[str], str]) -> Tuple[int, int, List[str]]:
    warnings = []

    # Read microseconds from SubSecTime field
    if microsecondsRaw.endswith(".0"):
        microsecondsRaw = microsecondsRaw.replace(".0", "")
    microseconds = int(str(microsecondsRaw)[:6].ljust(6, "0"))

    # Check if seconds is decimal, and should then be used for microseconds
    if "." in secondsRaw:
        secondsParts = secondsRaw.split(".")
        seconds = int(secondsParts[0])
        microsecondsFromSeconds = int(secondsParts[1][:6].ljust(6, "0"))

        # Check if microseconds from decimal seconds is not mismatching microseconds from SubSecTime field
        if microseconds != microsecondsFromSeconds and microseconds > 0 and microsecondsFromSeconds > 0:
            warnings.append(
                _(
                    "Microseconds read from decimal seconds value ({microsecondsFromSeconds}) is not matching value from EXIF field ({microseconds}). Max value will be kept."
                ).format(microsecondsFromSeconds=microsecondsFromSeconds, microseconds=microseconds)
            )
        microseconds = max(microseconds, microsecondsFromSeconds)
    else:
        seconds = int(secondsRaw)

    return (seconds, microseconds, warnings)


def isExifTagUsable(exif, tag, expectedType: Any = str) -> bool:
    """Is a given EXIF tag usable (not null and not an empty string)

    Args:
        exif (dict): The EXIF tags
        tag (str): The tag to check
        expectedType (class): The expected data type

    Returns:
        bool: True if not empty
    """

    try:
        if not tag in exif:
            return False
        elif expectedType == List[Fraction]:
            return isValidManyFractions(exif[tag])
        elif expectedType == Fraction:
            try:
                Fraction(exif[tag])
                return True
            except:
                return False
        elif expectedType == datetime.time:
            try:
                datetime.time.fromisoformat(exif[tag])
                return True
            except:
                return False
        elif expectedType == datetime.tzinfo:
            try:
                datetime.datetime.fromisoformat(f"2020-01-01T00:00:00{exif[tag]}")
                return True
            except:
                return False
        elif not (expectedType in [float, int] or isinstance(exif[tag], expectedType)):
            return False
        elif not (expectedType != str or len(exif[tag].strip().replace("\x00", "")) > 0):
            return False
        elif not (expectedType not in [float, int] or float(exif[tag]) is not None):
            return False
        else:
            return True
    except ValueError:
        return False


def compute_fov(focal_length, scale_factor_35efl, focus_distance=None) -> int:
    """
    Computes horizontal field of view (only for rectilinear sensors)
    Based on ExifTool computation.

    Args:
        focal_length (float): focal length (in mm)
        scale_factor_35efl (float): scale factor for 35mm-equivalent sensor
        focus_distance (float, optional): focus distance

    Returns:
        int: the computed field of view
    """

    if not focal_length or not scale_factor_35efl:
        raise Exception("Missing focal length or scale factor")

    correction_factor = 1.0
    if focus_distance:
        d = 1000 * focus_distance - focal_length
        if d > 0:
            correction_factor += focal_length / d

    fd2 = math.atan2(36, 2 * focal_length * scale_factor_35efl * correction_factor)
    fov_degrees = fd2 * 360 / math.pi

    return round(fov_degrees)
