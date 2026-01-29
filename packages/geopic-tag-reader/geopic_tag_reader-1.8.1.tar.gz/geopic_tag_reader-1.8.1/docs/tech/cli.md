# `geopic-tag-reader`

GeoPicTagReader

**Usage**:

```console
$ geopic-tag-reader [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `read`: Reads EXIF metadata from a picture file,...
* `write`: Override certain exiftags of a picture and...

## `geopic-tag-reader read`

Reads EXIF metadata from a picture file, and prints results

**Usage**:

```console
$ geopic-tag-reader read [OPTIONS]
```

**Options**:

* `--image PATH`: Path to your JPEG image file  [required]
* `--ignore-exiv2-errors`: Do not stop execution even if Exiv2 throws errors
* `--lang TEXT`: Lang code (2 letters) to use for printing messages  [default: en]
* `--help`: Show this message and exit.

## `geopic-tag-reader write`

Override certain exiftags of a picture and write a new picture in another file

**Usage**:

```console
$ geopic-tag-reader write [OPTIONS]
```

**Options**:

* `--input PATH`: Path to your JPEG image file  [required]
* `--output PATH`: Output path where to write the updated image file. If not present, the input file will be overriten.
* `--capture-time TEXT`: override capture time of the image, formated in isoformat, like &#x27;2023-06-01T12:48:01Z&#x27;. Note that if no timezone offset is defined, the datetime will be taken as local time and localized using the picture position if available.
* `--longitude FLOAT`: override longitude of the image, in decimal degrees (WGS84 / EPSG:4326) (like `2.3522219` for Paris)
* `--latitude FLOAT`: override latitude of the image, in decimal degrees (WGS84 / EPSG:4326) (like `48.856614` for Paris)
* `--picture-type [flat|equirectangular]`: type of picture, `equirectangular` for 360° pictures, `flat` otherwise
* `--lang TEXT`: Lang code (2 letters) to use for printing messages  [default: en]
* `--help`: Show this message and exit.
