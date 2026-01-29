from typing import Optional, Dict, List
import importlib.resources
import csv
from dataclasses import dataclass


# Per-make GPS estimated accuracy (in meters)
GPS_ACCURACY_MAKE = {
    # Diff GPS
    "stfmani": 2,
    "trimble": 2,
    "imajing": 2,
    # Good GPS
    "gopro": 4,
    "insta360": 4,
    "garmin": 4,
    "viofo": 4,
    "xiaoyi": 4,
    "blackvue": 4,
    "tectectec": 4,
    "arashi vision": 4,
    "qoocam": 4,
    "dji": 4,
    # Smartphone GPS
    "samsung": 5,
    "xiaomi": 5,
    "huawei": 5,
    "ricoh": 5,
    "lenovo": 5,
    "motorola": 5,
    "oneplus": 5,
    "apple": 5,
    "google": 5,
    "sony": 5,
    "wiko": 5,
    "asus": 5,
    "cubot": 5,
    "lge": 5,
    "fairphone": 5,
    "realme": 5,
    "symphony": 5,
    "crosscall": 5,
    "htc": 5,
    "homtom": 5,
    "hmd global": 5,
    "oppo": 5,
    "ulefone": 5,
}


@dataclass
class CameraMetadata:
    is_360: bool = False
    sensor_width: Optional[float] = None
    gps_accuracy: Optional[float] = None


CAMERAS: Dict[str, Dict[str, CameraMetadata]] = {}  # Make -> Model -> Metadata


def get_cameras() -> Dict[str, Dict[str, CameraMetadata]]:
    """
    Retrieve general metadata about cameras
    """

    if len(CAMERAS) > 0:
        return CAMERAS

    # Cameras.csv file is a composite of various sources:
    #  - Wikipedia's list of 360° cameras ( https://en.wikipedia.org/wiki/List_of_omnidirectional_(360-degree)_cameras )
    #  - OpenSfM's sensor widths ( https://github.com/mapillary/OpenSfM/blob/main/opensfm/data/sensor_data.json )

    with importlib.resources.open_text("geopic_tag_reader", "cameras.csv") as camerasCsv:
        camerasReader = csv.DictReader(camerasCsv, delimiter=";")
        for camera in camerasReader:
            make = camera["make"].lower()
            model = camera["model"].lower()
            sensorWidth = float(camera["sensor_width"]) if camera["sensor_width"] != "" else None
            is360 = camera["is_360"] == "1"
            gpsAccuracy = float(camera["gps_accuracy"]) if camera["gps_accuracy"] != "" else None

            # Override GPS Accuracy with Make one if necessary
            if gpsAccuracy is None and make in GPS_ACCURACY_MAKE:
                gpsAccuracy = GPS_ACCURACY_MAKE[make]

            # Append to general list
            if not make in CAMERAS:
                CAMERAS[make] = {}

            CAMERAS[make][model] = CameraMetadata(is360, sensorWidth, gpsAccuracy)

        return CAMERAS


def find_camera(make: Optional[str] = None, model: Optional[str] = None) -> Optional[CameraMetadata]:
    """
    Finds camera metadata based on make and model.

    >>> find_camera()

    >>> find_camera("GoPro")

    >>> find_camera("GoPro", "Max")
    CameraMetadata(is_360=True, sensor_width=6.17, gps_accuracy=4)
    >>> find_camera("GoPro", "Max 360")
    CameraMetadata(is_360=True, sensor_width=6.17, gps_accuracy=4)
    """

    # Check make and model are defined
    if not make or not model:
        return None

    # Find make
    cameras = get_cameras()
    matchMake = next((m for m in cameras.keys() if m in make.lower()), None)
    if matchMake is None:
        return None

    # Find model
    return next((cameras[matchMake][matchModel] for matchModel in cameras[matchMake].keys() if model.lower().startswith(matchModel)), None)


def is_360(make: Optional[str] = None, model: Optional[str] = None, width: Optional[int] = None, height: Optional[int] = None) -> bool:
    """
    Checks if given camera is equirectangular (360°) based on its make, model and dimensions (width, height).

    >>> is_360()
    False
    >>> is_360("GoPro")
    False
    >>> is_360("GoPro", "Max 360")
    True
    >>> is_360("GoPro", "Max 360", 2048, 1024)
    True
    >>> is_360("GoPro", "Max 360", 1024, 768)
    False
    >>> is_360("RICOH", "THETA S", 5376, 2688)
    True
    """

    # Check make and model are defined
    camera = find_camera(make, model)
    if not camera:
        return False

    # Check width and height are equirectangular
    if not ((width is None or height is None) or width == 2 * height):
        return False

    return camera.is_360
