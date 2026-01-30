from pprint import pformat

import os

# from PIL import ExifTags
from exiftool import ExifToolHelper

# GPSINFO_TAG = next(tag for tag, name in ExifTags.TAGS.items() if name == "GPSInfo")


class Geo:
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    def __str__(self):
        return f"{self.latitude} {self.longitude}"

    def __repr__(self):
        return self.__str__()


class Photo:
    def __init__(self, path: str, exif_tool_helper: ExifToolHelper):
        self.path = path
        self._exif_tool_helper = exif_tool_helper

        self.geo = self._parse_geo(self.path)
        # with Image.open(path, mode="r") as image:
        #     pass

    def __str__(self):
        return pformat(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def _parse_geo(self, path: str) -> Geo:
        data: dict = self._exif_tool_helper.get_tags(
            path,
            [
                "Composite:GPSLatitude",
                "Composite:GPSLongitude",
            ],
            params=["-n"],
        )[0]
        latitude: float = data.get("Composite:GPSLatitude")
        longitude: float = data.get("Composite:GPSLongitude")

        if latitude and longitude:
            return Geo(latitude, longitude)
        return None

    def write_geo(self, geo: Geo):
        self._exif_tool_helper.set_tags(
            self.path,
            {
                "Composite:GPSLatitude": geo.latitude,
                "Composite:GPSLongitude": geo.longitude,
            },
            params=["-n", "-overwrite_original_in_place"],
        )
        pass

    def sync_timestamp_from_exif(self):
        os.system(f"exiv2 --quiet --Timestamp '{self.path}'")

    def rename_with_timestamp(self, fmt="%Y%m%d_%H%M%S"):
        os.system(f"exiv2 --quiet --rename {fmt} --Force '{self.path}'")
