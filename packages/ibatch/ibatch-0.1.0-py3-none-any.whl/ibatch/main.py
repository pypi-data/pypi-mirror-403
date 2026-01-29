import os
import sys
from pathlib import Path

import click
import statistics

from exiftool import ExifToolHelper
from ibatch.photo import Geo

from .photo import Photo

EXIF_TOOL_HELPER = ExifToolHelper()
SUPPORTED_EXTENSIONS = [
    ".jpg",
    ".JPG",
    ".jpeg",
    ".JPEG",
    ".avif",
    ".AVIF",
]
TYPE_DIR = click.Path(
    exists=True, file_okay=False, dir_okay=True, readable=True, writable=True
)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("src", type=TYPE_DIR)
@click.pass_context
def all(context, src):
    context.invoke(geo, src=src)
    context.invoke(timestamp, src=src)
    context.invoke(rename, src=src)


@cli.command()
@click.argument("src", type=TYPE_DIR)
def rename(src):
    source_directory = Path(src)
    click.echo(f"Renaming files in {source_directory}")

    photos: list[Photo] = load_photos(source_directory)
    click.echo(f"Found {len(photos)} photos")

    for photo in photos:
        photo.rename_with_timestamp()

    click.echo("Done.")


@cli.command()
@click.argument("src", type=TYPE_DIR)
def timestamp(src):
    source_directory = Path(src)
    click.echo(f"Fixing file timestamps in {source_directory}")

    photos: list[Photo] = load_photos(source_directory)
    click.echo(f"Found {len(photos)} photos")

    for photo in photos:
        photo.sync_timestamp_from_exif()

    click.echo("Done.")


@cli.command()
@click.argument("src", type=TYPE_DIR)
def geo(src):
    source_directory = Path(src)
    click.echo(f"Fixing geolocation in {source_directory}")

    photos: list[Photo] = load_photos(source_directory)
    click.echo(f"Found {len(photos)} photos")

    if not len(photos):
        click.echo("Nothing to do.")
        return

    photos_with_geo: list[Photo] = filter_photos_with_geo(photos)
    click.echo(f"Found {len(photos_with_geo)} photos with geolocation data")

    if len(photos) == len(photos_with_geo):
        click.echo("Nothing to do.")
        return

    coordinates: Geo = None

    if len(photos_with_geo):
        mean_geo: Geo = calculate_mean_geo(photos_with_geo)
        click.echo(f"Mean location: {mean_geo}")
        click.echo(
            f"https://www.openstreetmap.org/?mlat={mean_geo.latitude}&mlon={mean_geo.longitude}"
        )
        if click.prompt(
            "Apply coordinates", type=bool, prompt_suffix="? ", default=True
        ):
            coordinates = mean_geo

    if not coordinates:
        latitude = click.prompt("Enter Latitude:", type=float)
        longitude = click.prompt("Enter Longitude:", type=float)
        coordinates = Geo(latitude, longitude)
        click.echo(
            f"https://www.openstreetmap.org/?mlat={coordinates.latitude}&mlon={coordinates.longitude}"
        )
        if not click.prompt(
            "Apply coordinates", type=bool, prompt_suffix="? ", default=True
        ):
            sys.exit(1)

    click.echo(f"Applying coordinates {coordinates}")

    photos_without_geo: list[Photo] = list(set(photos).difference(set(photos_with_geo)))

    for photo in photos_without_geo:
        photo.write_geo(coordinates)

    click.echo(f"Updated {len(photos_without_geo)} photos.")


def filter_photos_with_geo(photos: list[Photo]) -> list[Photo]:
    geo: list = []
    for photo in photos:
        if photo.geo:
            geo.append(photo)
    return geo


def load_photos(directory: Path) -> list[Photo]:
    directory_list = [os.path.join(directory, file) for file in os.listdir(directory)]
    files = filter_supported_files(directory_list)
    photos: list[Photo] = [Photo(file, EXIF_TOOL_HELPER) for file in files]
    return photos


def filter_supported_files(files: list):
    filtered_files = []
    for file in files:
        for ext in SUPPORTED_EXTENSIONS:
            if file.endswith(ext):
                filtered_files.append(file)
    return filtered_files


def calculate_mean_geo(photos: list[Photo]) -> Geo:
    latitudes: list[float] = [photo.geo.latitude for photo in photos]
    longitudes: list[float] = [photo.geo.longitude for photo in photos]

    latitudes_stripped: list[float] = remove_outliers(latitudes)
    longitudes_stripped: list[float] = remove_outliers(longitudes)

    latitude = statistics.mean(latitudes_stripped)
    longitude = statistics.mean(longitudes_stripped)

    return Geo(latitude, longitude)


def remove_outliers(data: list[float], n: float = 2) -> list[float]:
    mean = statistics.mean(data)
    std_dev = statistics.stdev(data)
    return [x for x in data if (mean - n * std_dev) < x < (mean + n * std_dev)]


if __name__ == "__main__":
    cli()
