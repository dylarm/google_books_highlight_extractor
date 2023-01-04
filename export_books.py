import csv
import functools
import logging as log
from datetime import datetime, date
from sys import stdout
from typing import IO, Iterable

import click
import dateparser
from bs4 import BeautifulSoup, Tag
from functional import seq

from model import Highlight, Color
from roam import Roam, RoamError, Page, Block

log.basicConfig(level=log.INFO)


def save_md(file: IO, highlights: seq, custom_css: bool):
    file.write(highlights.map(lambda it: it.as_roam_markdown()).make_string("\n"))


def save_emd(file: IO, highlights: seq, custom_css: bool):
    file.write(
        highlights.map(lambda it: it.as_enhanced_markdown(custom_css)).make_string("\n")
    )


def save_csv(file, highlights: seq):
    writer = csv.writer(file)
    writer.writerows(highlights.map(lambda it: it.as_anki_csv_row()))


save_map = {"md": save_md, "csv": save_csv, "emd": save_emd}


@click.group()
def cli():
    pass


def common_params(func):
    @click.argument("file", type=click.File())
    @click.option(
        "-b",
        "--book-name",
        required=True,
        help="Book name, would be appended to the source reference",
    )
    @click.option(
        "--since",
        default="1970-01-01",
        help="Starting point to take highlights from (supports natural language)",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@cli.command(help="Output results locally")
@common_params
@click.option(
    "-o", "--output", default=stdout, help="Output file", type=click.File(mode="w")
)
@click.option("-t", "--export-type", default="md", type=click.Choice(save_map.keys()))
@click.option(
    "-c",
    "--custom-css",
    is_flag=True,
    show_default=True,
    default=False,
    help="Create callout blocks (block quotes) of the highlights from a custom CSS file",
)
def local(file, book_name, since, output, export_type, custom_css):
    highlights = find_highlights(file, book_name, dateparser.parse(since).date())

    save_map[export_type](output, highlights, custom_css)


@cli.command(help="Store highlights to a Roam Graph")
@common_params
@click.option(
    "-g",
    "--graph",
    required=True,
    help="The name of the Roam graph to store highlights to",
)
@click.option("--api-key", required=True, help="Roam API key", envvar="ROAM_API_KEY")
@click.option(
    "--graph-token", required=True, help="Roam Graph token", envvar="ROAM_GRAPH_TOKEN"
)
def roam(file, book_name, since, graph, api_key, graph_token):
    highlights = find_highlights(file, book_name, dateparser.parse(since).date())

    client = Roam(graph, api_key, graph_token)
    RoamSaver(client).save(book_name, highlights)


class RoamSaver:
    def __init__(self, roam_client: Roam, header_block_name: str = "#highlights"):
        self.roam = roam_client
        self.header_block_name = header_block_name

    def save(self, book: str, highlights: Iterable[Highlight]):
        page = self.create_book_page(book)
        block = self.create_header_block(page)
        result = (
            seq(highlights)
            .map(lambda it: it.as_roam_block_hierarchy())
            .reverse()
            .map(lambda it: self.roam.create_block(block.uid, it))
        )

        log.info(result)

    def create_book_page(self, book) -> Page:
        try:
            page = self.roam.create_page(book)
            # todo create metadata block
            return page
        except RoamError as e:
            if e.type == RoamError.object_exists:
                log.info(e)
                return self.roam.get_page_by_title(book)
            else:
                raise

    def create_header_block(self, page: Page) -> Block:
        children = self.roam.get_children_by_string(page.uid, self.header_block_name)

        if children:
            return children[0]

        return self.roam.create_block(page.uid, {self.header_block_name: []})[0]


def find_highlights(file, book_name: str, since: date = date.min):
    """
    The extraction is based on the structure of the HTML file the export from Google Docs would give you for the
    document containing the notes. 1 cell table container, inside of which there is another table that contains cells
    for Image, Highlight, Note and Date.
    """
    soup = BeautifulSoup(file.read(), "html.parser")
    containers = soup.find_all(rowspan=1, colspan=1)
    return (
        seq(containers)
        .map(lambda tag: tag.find_all(rowspan=1, colspan=1))
        .filter(lambda quote_tags: len(quote_tags) != 0)
        .map(lambda tags: parse_highlight(*tags, book=book_name))
        .filter(lambda it: it is not None)
        .filter(lambda it: it.date >= since)
    )


def parse_color(color_container: Tag) -> Color:
    color_tag: Tag = color_container.find("img")

    name_color_map = {f"images/image{color.value}.png": color for color in Color}

    return name_color_map[color_tag["src"]]


def parse_highlight(color_container, quote, link, book):
    try:
        text, *note, date_tag = quote.find_all("span")
        link_tag: Tag = link.find("a")
        return Highlight(
            book,
            text.get_text(),
            extract_note(note),
            link_tag["href"],
            link_tag.string,
            datetime.strptime(date_tag.get_text(), "%B %d, %Y").date(),
            parse_color(color_container),
        )
    except Exception as e:
        print(quote, e)
        return None


def extract_note(note_tags):
    try:
        _, note_tag, _ = note_tags
        return note_tag.get_text()
    except:
        return ""


if __name__ == "__main__":
    cli()
