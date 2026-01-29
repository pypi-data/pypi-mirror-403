# Pictures metadata

Panoramax have some prerequisites for a pictures to be accepted:

- Position 📍
- Capture time ⏲️

Those metadata are usually integrated inside the picture file (in what is called [EXIF tags](https://en.wikipedia.org/wiki/Exif)). For some complex use cases, those tags can also be given alongside the picture to the uploading API.

## :octicons-file-binary-16: Exif tags

Exif tags are quite complex and usually one metadata can be read from several EXIF tags. In order to handle many camera vendors, Panoramax will try to read each metadata from several EXIF tags.

!!! note

    The following documentation uses the [Exiv2](https://exiv2.org) notation for EXIF tags as it gives a unique identifier for an EXIF tag, and is the notation used by the API to expose those tags.

!!! note

    Panoramax accepts both __360° and classic/flat pictures__.

### 📍 GPS coordinates

📍 GPS coordinates are read from:

- `Exif.GPSInfo.GPSLatitude`/`Exif.GPSInfo.GPSLatitudeRef`, `Exif.GPSInfo.GPSLongitude`/`Exif.GPSInfo.GPSLongitudeRef`
- or `Xmp.exif.GPSLatitude`/`Xmp.exif.GPSLatitudeRef`, `Xmp.exif.GPSLongitude`/`Xmp.exif.GPSLongitudeRef`
- or in [Mapillary](https://www.mapillary.com/) tags: `MAPLatitude`/`MAPLongitude`

### ⏲️ Capture time

⏲️ Capture time is read from:

- `Exif.GPSInfo.GPSDateStamp`
- `Exif.GPSInfo.GPSDateTime`
- `Xmp.exif.GPSDateStamp`
- `Xmp.exif.GPSDateTime`
- `Exif.Image.DateTimeOriginal`
- `Exif.Photo.DateTimeOriginal`
- `Exif.Image.DateTime`
- `Xmp.GPano.SourceImageCreateTime`
- or in [Mapillary](https://www.mapillary.com/) tags: `MAPGpsTime`

### Optional metadata

The following EXIF tags are recognized and used if defined, but are **optional**:

#### 🧭 Image orientation

Image orientation is read from

- `GPSImgDirection`
- or in [Mapillary](https://www.mapillary.com/) tags: `MAPCompassHeading`

#### :material-timer: Milliseconds in date

Milliseconds in date is read from `SubSecTimeOriginal`.

#### :material-panorama-sphere-outline: 360° or flat

To detect if a picture is 360° / spherical, we use `GPano:ProjectionType` or an heuristic based on the model of the camera and dimension of the picture ([see doc for more details](./tech/api_reference.md#camera)).

#### 📷 Make and model

Camera vendor (`make`) is read from:

- `Exif.Image.Make`
- or in [Mapillary](https://www.mapillary.com/) tags: `MAPDeviceMake`

Camera model is read from:

- `Exif.Image.Model`
- or in [Mapillary](https://www.mapillary.com/) tags: `MAPDeviceModel`

#### Focal length

Camera focal length (basic and 35mm-equivalent, to get precise field of view) is read from:

- `Exif.Image.FocalLength`
- `Exif.Photo.FocalLength`
- `Exif.Image.FocalLengthIn35mmFilm`
- `Exif.Photo.FocalLengthIn35mmFilm`

#### :octicons-horizontal-rule-16: Yaw, Pitch and Roll

Yaw value is read from:

- `Xmp.Camera.Yaw`
- `Xmp.GPano.PoseHeadingDegrees`

Pitch value is read from:

- `Xmp.Camera.Pitch`
- `Xmp.GPano.PosePitchDegrees`

Roll value is read from:

- `Xmp.Camera.Roll`
- `Xmp.GPano.PoseRollDegrees`

#### ⛰️ Altitude

Altitude is read from:

- `Exif.GPSInfo.GPSAltitude`

## :simple-python: Using as Python library

All this metadata reading logic has been extracted in a python library.

[:octicons-arrow-right-24: How to use as a Python library](./tech/api_reference.md)

## :octicons-terminal-16: Using as Command-line tool

A command-line tool is also available to quickly read and write a picture's metadata.

[:octicons-arrow-right-24: How to use the command-line tool](./tech/cli.md)
