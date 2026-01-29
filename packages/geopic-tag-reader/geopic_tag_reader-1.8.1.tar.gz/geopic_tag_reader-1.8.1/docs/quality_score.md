# :white_check_mark: Quality score

Panoramax offers a _Quality Score_ for each picture in its web viewer. It allows easy map filtering and comprehensive display of high-quality pictures availability.

The grade is shown to users as a A/B/C/D/E score (A is the best, E the worst), and shown graphically through this scale (inspired by [Nutri-Score](https://en.wikipedia.org/wiki/Nutri-Score)):

![Quality score graphics](./images/quality_score.png)

## :material-calculator: Score computation

Quality score is based on two indicators:

- :material-crosshairs-gps: __GPS position accuracy__: how precisely the GPS coordinates are set, in meters. This is 1/5 of the score.
- :material-camera-iris: __Horizontal pixel density__: how many pixels we have on horizon per _field of view_ degree. This is 4/5 of the score.

They are displayed through web viewer in picture metadata popup:

![Metadata popup and score display](./images/quality_score_viewer.png)

!!! info

	We know that this is a pretty simple indicator. Many other information could be taken into account (blurriness, light...) and may be used in the future. We started with something simple to make the _quality score_ available on as many pictures as possible. You can [come and help us](https://docs.panoramax.fr/how-to-contribute/#contribute-to-the-development) to make this happen sooner :grinning:

### :material-crosshairs-gps: GPS position accuracy

This indicator allows to know if we can rely or not on GPS position, based on its precision. It is expressed as a decimal value in meters. The grade is a 5-star rating, and is applied based on these values:

| GPS Accuracy      | Grade |
| ----------------- | ----- |
| <= 1 m            |  5/5  |
| <= 2 m            |  4/5  |
| <= 5 m            |  3/5  |
| <= 10 m           |  2/5  |
| > 10 m or unknown |  1/5  |

The value is read from picture EXIF metadata. We rely on the following tags:

- __Horizontal positioning error__ (`Exif.GPSInfo.GPSHPositioningError` or `Xmp.exif.GPSHPositioningError`) : expected positioning error in meters.
- __Dilution of precision__ (`Exif.GPSInfo.GPSDOP` or `Xmp.exif.GPSDOP`) : indicator of expected precision on coordinates (<= 1 means good precision for the sensor, >= 5 is not good, [more info on Wikipedia](https://en.wikipedia.org/wiki/Dilution_of_precision_(navigation))).
- __Is the GPS differential__ (`Exif.GPSInfo.GPSDifferential` or `Xmp.exif.GPSDifferential`) : indicates if GPS sensor is using [Differential GPS](https://en.wikipedia.org/wiki/Differential_GPS) or not. If yes, we expect a better precision.

These are used to define a precision value in meters. If none of these tags are set, we also rely on a default value for several camera vendors (based on `Make` and `Model` EXIF tags).

So, to get a good grade on GPS precision, you can (in order):

- Set a precise _Horizontal positioning error_
- Set a value for _Differential GPS_ and/or _Dilution of precision_
- Set values for _Make_ and _Model_ if you use a common camera


!!! info

	If you find the shown value not reflecting the real precision of your GPS sensor, feel free to contact us with an example link. We tried to make precision estimates on a large set of cameras, but we may have missed some :material-map-search:

### :material-camera-iris: Horizontal pixel density

This indicator allows to have an idea of how high the picture resolution is, independently of its field of view (360° or classic picture). The formula is: `picture width in pixels / field of view in degrees`. We have in result a number of pixels per FOV degree. The grade is a 5-star rating, and is applied based on these values:

| Grade | Density for 360° | Density for non 360°         |
| ----- | ---------------- |  --------------------------- |
| 5/5   | >= 30 px/deg     | Not possible                 |
| 4/5   | >= 15 px/deg     | >= 30 px/deg                 |
| 3/5   | < 15px/deg       | >= 15px/deg                  |
| 2/5   | Not possible     | >= 10 px/deg                 |
| 1/5   | Unknown value    | < 10 px/deg or unknown value |

!!! info

	A different rating is applied for 360°, as they offer a nicer user experience on web viewer. Note that if you're a technical reuser, the API offers raw values for each indicator, allowing you to do your own custom rating.

The value is computed from picture width in pixels, and some EXIF metadata. We rely on the following tags:

- __Focal length__ (`Exif.Image.FocalLength` or `Exif.Photo.FocalLength`): distance in millimeters between the nodal point of the lens and the camera sensor.
- __Focal length (35mm equivalent)__ (`Exif.Image.FocalLengthIn35mmFilm` or `Exif.Photo.FocalLengthIn35mmFilm`): same as focal length, but in 35mm film equivalent.
- __Make and model__ (`Exif.Image.Make` and `Exif.Image.Make`): camera model, which is used to find camera sensor width.
- __Projection type__ (for 360° pictures, `Xmp.GPano.ProjectionType`): to mark a picture as 360°

Based on these information, we are able to compute the _field of view_ (how wide the camera can look horizontally).

As these information are hard to deduce, you may carefully set all of them in EXIF metadata.

!!! info

	If you have pictures with an unknown value for this grade, it's probably because we miss information on your camera model. Make sure your pictures have required information, and contact us with the camera _sensor width_ so we can add it in our listing.

