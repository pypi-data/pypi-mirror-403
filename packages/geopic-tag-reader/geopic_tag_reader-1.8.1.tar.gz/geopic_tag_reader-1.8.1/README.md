# ![Panoramax](https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Panoramax.svg/40px-Panoramax.svg.png) Panoramax

__Panoramax__ is a digital resource for sharing and using 📍📷 field photos. Anyone can take photographs of places visible from the public streets and contribute them to the Panoramax database. This data is then freely accessible and reusable by all. More information available at [gitlab.com/panoramax](https://gitlab.com/panoramax) and [panoramax.fr](https://panoramax.fr/).


# 📷 GeoPic Tag Reader

This repository only contains the Python library to __read and write standardized metadata__ from geolocated pictures EXIF metadata. It can be used completely apart from all Panoramax components for your own projects and needs.

## Features

This tool allows you to:

- 🔍 Analyse various EXIF variables to extract standardized metadata for geolocated pictures applications (coordinates, date, orientation, altitude...)
- ✏️ Edit a picture to change its EXIF variables through a simpler command
- 💻 Either as Python code or as a command-line utility


## Install

The library can be installed easily, for a quick glance:

```bash
pip install geopic_tag_reader
geopic-tag-reader --help
```

To know more about install and other options, see [install documentation](./docs/install.md).

If at some point you're lost or need help, you can contact us through [issues](https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/issues) or by [email](mailto:panieravide@riseup.net).


## Usage

This library can be used both from command-line or as Python module.

### As command-line

To see all available commands:

```bash
geopic-tag-reader --help
```

To read metadata from a single picture:

```bash
geopic-tag-reader read --image /path/to/my_image.jpg
```

To edit metadata of a single picture, for example change its capture date:

```bash
geopic-tag-reader write \
	--input /path/to/original_image.jpg \
	--capture-time "2023-01-01T12:56:38Z" \
	--output /path/to/edited_image.jpg
```

[Full documentation is also available here](./docs/index.md).

### As Python library

In your own script, for reading and writing a picture metadata, you can use:

```python
from geopic_tag_reader import reader, writer, model

# Open image as binary file
img = open("my_picture.jpg", "rb")
imgBytes = img.read()
img.close()

# Read EXIF metadata
metadata = reader.readPictureMetadata(imgBytes)
print(metadata)

# Edit picture EXIF metadata
editedMetadata = writer.PictureMetadata(
	picture_type = model.PictureType.equirectangular,
	direction = writer.Direction(125)
)
editedImgBytes = writer.writePictureMetadata(imgBytes, editedMetadata)

# Save edited file
editedImg = open("my_new_picture.jpg", "wb")
editedImg.write(editedImgBytes)
editedImg.close()
```

[Full documentation is also available here](./docs/tech/api_reference.md).


## Contributing

Pull requests are welcome. For major changes, please open an [issue](https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/issues) first to discuss what you would like to change.

More information about developing is available in [documentation](./docs/develop.md).


## ⚖️ License

Copyright (c) Panoramax team 2022-2024, [released under MIT license](https://gitlab.com/panoramax/server/geo-picture-tag-reader/-/blob/main/LICENSE).
