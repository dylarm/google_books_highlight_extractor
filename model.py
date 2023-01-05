from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from zipfile import ZipFile

from PIL import Image  # Pillow
from aenum import Enum, extend_enum
from bs4 import BeautifulSoup
from functional import seq

from roam import roam_date, markdown_date


class Color(Enum):
    """
    Probably most hacky part of this. Logic is that the colors are represented by images with the given index.

    The index is calculated by finding the dominant color in each image (assuming we're in the same directory as the
    html file, or are using a zip file). And since Google Play Book notes use the same color each time, matching is
    fairly simple.
    """

    pass


class GoogleColors(Enum):
    BLUE = (38, 198, 218)
    RED = (255, 112, 67)
    YELLOW = (251, 192, 45)
    GREEN = (139, 195, 74)


def color_distance(color):
    distances = {}
    for col in GoogleColors:  # noinspection
        sqdiff = [pow(x[0] - x[1], 2) for x in zip(col.value, color)]
        distances[col] = sum(sqdiff)
    return distances


def get_image_color(image) -> str:
    im = Image.open(image).convert("RGB")
    by_color = defaultdict(int)
    for pixel in im.getdata():
        by_color[pixel] += 1
    most_common = max(by_color, key=by_color.get)
    distances = color_distance(most_common)
    for name in distances:
        if distances[name] == 0:
            name = name.name  # Sorry
            break
        else:
            name = None
    return name  # noinspection


def extend_color_class(file: ZipFile | Path):
    # TODO: there is almost surely a better way to do this. But this works for now (famous last words)
    if isinstance(file, Path):
        image_dir = Path(f"{file.parent}/images/")
        image_names = image_dir.glob("*.png")
        for image in image_names:
            image_num = image.stem[-1]
            image_color = get_image_color(image)
            if image_color:
                extend_enum(Color, image_color, image_num)
    else:
        image_names = [name for name in file.namelist() if ".png" in name]
        for image in image_names:
            image_num = image.split(".")[0][-1]
            with file.open(image) as im:
                image_color = get_image_color(im)
            if image_color:
                extend_enum(Color, image_color, image_num)


@dataclass
class Highlight:
    book: str
    text: str
    note: str
    link: str
    page: str
    date: date
    color: Color

    @property
    def markdown_link(self):
        return f"[{self.book}: {self.page}]({self.link})"

    @property
    def color_attribute(self):
        return f"color::#{self.color.name.lower()}"

    @property
    def enhanced_color_attribute(self):
        return f"color:: {self.color.name.lower()}"

    @property
    def date_attribute(self):
        return f"date::[[{roam_date(self.date)}]]"

    @property
    def enhanced_date_attribute(self):
        return f"date:: {markdown_date(self.date)}"

    def as_roam_block_hierarchy(self):
        return {
            self.text: ([{self.note: []}] if self.note else [])
            + [
                {self.markdown_link: []},
                {self.date_attribute: []},
                {self.color_attribute: []},
            ]
        }

    def as_roam_markdown(self):
        return (
            seq(
                f" - {self.text}",
                f"   - {self.note}" if self.note else None,
                f"   - {self.markdown_link}",
                f"   - {self.date_attribute}",
                f"   - {self.color_attribute}",
            )
            .filter(lambda it: it is not None)
            .make_string("\n")
        )

    def as_enhanced_markdown(self, custom_css: bool = False):
        if custom_css:
            first_line = f"> [!{self.enhanced_color_attribute.split(' ')[1]}-highlight] {self.markdown_link}"
        elif self.note:
            first_line = "> [!note]"
        else:
            first_line = "> [!quote]"
        return (
            seq(
                first_line,
                f"> text:: {self.text}",
                f"> - note:: {self.note}" if self.note else None,
                f"> - {self.markdown_link}" if not custom_css else None,
                f"> - {self.enhanced_date_attribute}",
                f"> - {self.enhanced_color_attribute}" if not custom_css else None,
                "",
            )
            .filter(lambda it: it is not None)
            .make_string("\n")
        )

    def as_anki_csv_row(self):
        soup = BeautifulSoup()
        link = soup.new_tag("a", href=self.link, string=f"{self.book}: {self.page}")

        return [self.text, self.note, link, str(self.date), self.color.name.lower()]
