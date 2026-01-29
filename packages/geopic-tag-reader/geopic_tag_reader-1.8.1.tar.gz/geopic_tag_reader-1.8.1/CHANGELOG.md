# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.8.1] - 2026-01-24

### Added

- Default GPS precision for DJI devices is estimated to 4 meters.

### Fixed

- Pictures with partial crop metadata which corresponds to a full 360° picture (crop width = full width & crop height = full height) are now accepted.
- Bad assertion, making `0` an invalid value for `MergeParams.maxDistance` parameter.

## [1.8.0] - 2025-05-25

### Changed

- Improved duplicates detection, now the whole sequence is deduplicated, not only the consecutive pictures
- **Breaking Change** Now the `duplicate_pictures` in the report is a list of `Duplicate` (instead of `Picture`), so we can get more information about the duplicate.

## [1.7.0] - 2025-05-25

### Changed

- Better support of cylindrical images.

## [1.6.0] - 2025-05-09

### Added

- Add a new method `getPictureMetadata` to extract metadata from already read metadata. This will be useful to parse again the metadata from a picture without rereading the file after updates of the metadata parsing.

### Changed

- Change signature of `camera.is_360` to specify `width` and `height` parameters as integers.
- Default GPS precision for Qoocam cameras is set to 4 meters.

## [1.5.0] - 2025-04-14

### Changed

- Update all required libraries (especially [timezonefinder](https://github.com/jannikmi/timezonefinder/) and its [h3-py](https://github.com/uber/h3-py) dependency) to avoid an installation issue on Windows.
- Minimal required version is now python 3.9 (it was needed by a dependency, and python 3.8 has reached end of life on october 2024).

## [1.4.2] - 2025-02-10

### Fixed

- Change the relative angle computation for capture duplicates detection. This new computation is more accurate and should detect more duplicates.

## [1.4.1] - 2025-02-03

### Added

- Field of view is also computed based on focal length and its equivalent in 35mm format (based on ExifTool formula).

### Fixed

- GPS horizontal precision and dilution of precision are also read from fraction values.

## [1.4.0] - 2025-01-06

### Added

- Camera general metadata (sensor width, 360° devices, GPS average accuracy) is made available through a single CSV file named `cameras.csv`. This make info centralized and will lighten camera info in Panoramax API.
- New fields are offered in GeoPicTags: `sensor_width, gps_accuracy, field_of_view`

## [1.3.3] - 2024-11-24

### Added

- Warnings are shown if any useful metadata is missing for computing a quality score (make, model, GPS accuracy...).
- New languages : 🇵🇱, 🇳🇱, 🇭🇺, 🇪🇸, 🇩🇪 (thanks to all translators !)

## [1.3.2] - 2024-10-22

### Changed

- Update some dependencies and especially pyexiv2 that is now compatible with python 3.13

## [1.3.1] - 2024-10-09

### Changed

- Checks for 360° pictures now use the width/height from image itself (instead of metadata, that could not be set)

## [1.3.0] - 2024-09-30

### Changed

- Reader offers a new property `ts_by_source` to distinguish read datetime from GPS and camera.
- Sequence sorting uses same timestamp source through all pictures (GPS if available, camera else, fallback with other value if two timestamps are identical).
- Sequence splits uses whenever possible same timestamp source.

### Fixed

- Documentation links were not up-to-date in README file.
- Sub-seconds values and time offset are applied only if part of the same EXIF group.

## [1.2.0] - 2024-07-30

### Added

- A new module `sequence` is available through Python to dispatch a set of pictures (based on their metadata) into several sequences, based on de-duplicate and split parameters. This is based on existing code previously stored in [command-line client](https://gitlab.com/panoramax/clients/cli), moved here to be shared between API and CLI.

### Changed

- Reader offers a `yaw` value (360° sphere correction), distinct from `heading` (GPS direction). EXIF tags are read a bit differently to reflect this : `yaw` comes from `Xmp.Camera.Yaw & Xmp.GPano.PoseHeadingDegrees`, `heading` from `Exif.GPSInfo.GPSImgDirection & MAPCompassHeading`.

### Removed
- Previously used values `Exif.GPSInfo.GPS(Pitch|Roll)` and `Xmp.GPano.InitialView(Pitch|Roll)Degrees` are dropped, first one for not being standard, second one for not being correct to use for pitch/roll (prefer `Xmp.GPano.Pose(Pitch|Roll)Degrees`).

## [1.1.5] - 2024-07-10

### Fixed

- PyPI package was missing built translation files (MO files).

## [1.1.4] - 2024-07-10

### Changed

- Updated 🇫🇷 French 🥖 locale.

### Fixed

- Translation process with Weblate was not taking into account new labels from code.

## [1.1.3] - 2024-07-10

### Changed

- Translations are handled per function call, language code passed as parameter for reader and writer.

## [1.1.2] - 2024-06-25

### Added

- Support of translations for warning/error messages.

### Changed

- Update docs to match organization rename on Gitlab from GeoVisio to Panoramax
- Test for 360° pictures recognition based on make & model handles different string cases

## [1.1.1] - 2024-04-26

### Added

- Reader now handles pitch & roll values from various EXIF/XMP tags.

## [1.1.0] - 2024-04-17

### Changed

- Encoding information (`charset=...`) is now stripped out of text EXIF tags.
- `GeoPicTags` objects returns `ts` as a Python `datetime` object (instead of decimal epoch).
- Improved timezone handling in reader, GPS coordinates are used to find appropriate timezone when no timezone is defined in EXIF tags. If a UTC fallback is done, a warning is thrown.

## [1.0.6] - 2024-04-02

### Changed

- Bump some dependencies, the most important one being [typer](https://typer.tiangolo.com/) since it removes the need for typer-cli.

## [1.0.5] - 2024-03-06

### Fixed

- Automatic detection of 360° pictures based on make and model also checks for image dimensions (to avoid false positive, when 360° camera can also take flat pictures).
- Slash character in GPS date stamp was not correctly interpreted.

## [1.0.4] - 2024-02-12

### Changed

- When using date/time not coming from GPS, offset time EXIF field are also read (`Exif.Photo.OffsetTimeOriginal` or `Exif.Photo.OffsetTime` depending on used date/time EXIF tag).

## [1.0.3] - 2023-12-18

### Added

- Support reading date from EXIF fields `Exif.Image.DateTime` and `Xmp.GPano.SourceImageCreateTime`.
- Auto-detect if a picture is 360° based on make and model.

### Fixed

- Avoid failures for pictures with invalid offset for maker notes (due to PyExiv2 log level).

## [1.0.2] - 2023-11-20

### Added

- A warning is thrown when microseconds values between decimal seconds and sub-second time fields are not matching.

### Changed

- Fraction values for date, time and GPS coordinates are supported.

## [1.0.1] - 2023-11-17

### Fixed

- `DateTimeOriginal` field wasn't correctly read when seconds value was decimal.

## [1.0.0] - 2023-10-18

### Added

- Add subseconds to written metadata
- Read altitude in metadata
- Write direction and altitude metadata
- Add `additional_exif` tags in `writePictureMetadata`

### Changed

- EXIF list of tags now uses the [Exiv2](https://exiv2.org/metadata.html) notation (example `Exif.Image.Artist`) in returned data. To do this, pyexiv2 dependency is always necessary, and Pillow dependency has been removed. As a consequence, `readPictureMetadata` function **now takes in input `bytes`** read from picture file instead of Pillow image. This is a breaking change.
- Use overriden metadata is available to localize overriden capture_time

## [0.4.1] - 2023-09-08

### Added

- Latitude and longitude values are checked to verify they fit into WGS84 projection bounds (-180, -90, 180, 90).

## [0.4.0] - 2023-09-01

### Added

- When a picture does not contain a mandatory exif tag (coordinates or datetime), a `PartialExifException` is thrown containing some information about what has been parsed and what is missing.

## [0.3.1] - 2023-07-31

### Added

- A way to write exif lon/lat and type tags.

## [0.3.0] - 2023-07-31

### Added

- Support of any date/time separator for EXIF tag `DateTimeOriginal`
- A way to write exif tags. To use this, you need to install this library with the extra `[write-exif]`.

## [0.2.0] - 2023-07-13

### Added

- Support of cropped equirectangular panoramas

### Changed

- Support python 3.8

## [0.1.3]

### Changed

- Bump [Typer](typer.tiangolo.com/) version, and use fork of [Typer-cli](https://gitlab.com/panoramax/server/infra/typer-cli)

## [0.1.2]

### Added

- Full typing support ([PEP 484](https://peps.python.org/pep-0484/) and [PEP 561](https://peps.python.org/pep-0561/))

## [0.1.1]

### Added

- Support of Mapillary tags stored in EXIF tag `ImageDescription`

## [0.1.0]

### Added

- If GPS Date or time can't be read, fallbacks to Original Date EXIF tag associated with a reader warning
- New EXIF tags are supported: `GPSDateTime`

### Changed

- `tag_reader:warning` property has been moved from EXIF, and is now available as a direct property named `tagreader_warnings` of `GeoPicTags` class
- Reader now supports `GPSLatitude` and `GPSLongitude` stored as decimal values instead of tuple
- Reader now supports reading `FocalLength` written in `NUMBER/NUMBER` format
- If EXIF tags for heading `PoseHeadingDegrees` and `GPSImgDirection` have contradicting values, we use by default `GPSImgDirection` value and issue a warning, instead of raising an error

### Fixed

- EXIF tag `SubsecTimeOriginal` was not correctly read due to a typo

## [0.0.2] - 2023-05-10

### Added

- EXIF tag `UserComment` is now read and available in raw `exif` tags
- If not set, `GPSLatitudeRef` defaults to North and `GPSLongitudeRef` defaults to East
- A new `tag_reader:warning` property lists non-blocking warnings raised while reading EXIF tags

## [0.0.1] - 2023-03-31

### Added

- EXIF tag reading methods extracted from [Panoramax/GeoVisio API](https://gitlab.com/panoramax/server/api)

[Unreleased]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.8.1...main
[1.8.1]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.8.0...1.8.1
[1.8.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.7.0...1.8.0
[1.7.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.6.0...1.7.0
[1.6.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.5.0...1.6.0
[1.5.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.4.2...1.5.0
[1.4.2]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.4.1...1.4.2
[1.4.1]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.4.0...1.4.1
[1.4.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.3.3...1.4.0
[1.3.3]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.3.2...1.3.3
[1.3.2]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.3.1...1.3.2
[1.3.1]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.3.0...1.3.1
[1.3.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.2.0...1.3.0
[1.2.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.1.5...1.2.0
[1.1.5]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.1.4...1.1.5
[1.1.4]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.1.3...1.1.4
[1.1.3]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.1.2...1.1.3
[1.1.2]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.1.1...1.1.2
[1.1.1]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.1.0...1.1.1
[1.1.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.0.6...1.1.0
[1.0.6]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.0.5...1.0.6
[1.0.5]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.0.4...1.0.5
[1.0.4]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.0.3...1.0.4
[1.0.3]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.0.2...1.0.3
[1.0.2]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.0.1...1.0.2
[1.0.1]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/1.0.0...1.0.1
[1.0.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/0.4.1...1.0.0
[0.4.1]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/0.4.0...0.4.1
[0.4.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/0.3.1...0.4.0
[0.3.1]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/0.3.0...0.3.1
[0.3.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/0.2.0...0.3.0
[0.2.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/0.1.3...0.2.0
[0.1.3]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/0.1.2...0.1.3
[0.1.2]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/0.1.1...0.1.2
[0.1.1]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/0.1.0...0.1.1
[0.1.0]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/0.0.2...0.1.0
[0.0.2]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/compare/0.0.1...0.0.2
[0.0.1]: https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/commits/0.0.1
