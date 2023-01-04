from dataclasses import dataclass
from datetime import date
from enum import Enum

from bs4 import BeautifulSoup
from functional import seq

from roam import roam_date, markdown_date


class Color(Enum):
    """
    Probably most hacky part of this. Logic is that the colors are represented by images with the given index

    TODO: Fix the color detection.
    The issue is that these numbers are not constant. Whichever is 1 is the first color used for a highlight.
    Sometimes the last number is the book cover, and sometimes it's not (as is the case for the test file I used).
    """

    BLUE = 4
    RED = 5  # The book cover is 4
    YELLOW = 1
    GREEN = 2


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
