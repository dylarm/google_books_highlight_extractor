# Google Books highlights and notes extractor
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
![python 3.7, 3.9, 3.10, 3.11](https://img.shields.io/badge/python-v3.7%7Cv3.9%7Cv3.10%7Cv3.11-blue)

A script to extract highlights and notes from Google Books highlight document in Google Drive.

**Why**. The highlights document is ok to read, but if you want to use the highlights/notes elsewhere, there is no way for you to do this besides manually copying notes one by one.  
The specific use case is adding them to [RoamResearch](https://roamresearch.com/), [Anki](https://apps.ankiweb.net/), and [Obsidian](https://obsidian.md/).

This script is going to extract:
* Highlight
* Note (if present)
* Reference to the position in a book where the highlight originates from
* Date when the highlight was made
* Highlight color


### How to use this:

Assuming you have already downloaded this repository,

1. Go to the Google Document created by the Google Books with highlights for the book you're interested in;
2. Download it as HTML: File → Download → Web Page (html, zipped);
3. OPTIONAL: Uncompress the archive that you got on the previous step;
4. Install dependencies if any are missing (see requirements.txt) - although I recommend doing so inside your preferred virtual environment
5. Run export_books.py with the file as input. E.g: 
    * Markdown, unzipped html + images `python export_books.py local /path/to/file.html -o output.md -b "Book name" --since yesterday`
    * Extended Markdown, zip file `python export_books.py local /path/to/archive.zip -o output.md -b "Book name" -t emd -c`
    * Roam Graph `python export_books.py roam /path/to/file.html -b "Book name" --since yesterday --graph stvad-api --api-key <key> --graph-token <token>` 

The file `custom_callouts.css` is provided so that you may use it as needed in Obsidian.

#### Output formats

This script supports the following output formats:

1. **Markdown** - store output to local Markdown file
    - **"Plain"** - Formatted to be pasted in Roam
    - **Extended** - Uses block quotes / callout blocks for quotes and notes, and formatted for using in Obsidian with Dataview
    - **Extended, custom CSS** - Like extended, but colors each block according to the Google color and puts the title/link in the first line
2. **CSV** - store output to local CSV file. Structured in a way that it's easy to import into Anki
3. **Roam Graph** - this method uses Roam API to add highlights directly to the book's page in your Roam Graph (You'd need API token to use this)

**Full options:** 
```
Usage: export_books.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  local  Output results locally
  roam   Store highlights to a Roam Graph

---

Usage: export_books.py local [OPTIONS] FILE

  Output results locally

Options:
  -b, --book-name TEXT            Book name, would be appended to the source
                                  reference  [required]
  --since TEXT                    Starting point to take highlights from
                                  (supports natural language)  [default:
                                  1970-01-01]
  -o, --output FILENAME           Output file [default: stdout]
  -t, --export-type [md|csv|emd]  Markdown, CSV, or 'Extended' Markdown
                                  [default: md]
  -c, --custom-css                Create callout blocks (block quotes) of the
                                  highlights from a custom CSS file
  --help                          Show this message and exit.


---

Usage: export_books.py roam [OPTIONS] FILE

  Store highlights to a Roam Graph

Options:
  -b, --book-name TEXT  Book name, would be appended to the source reference
                        [required]
  --since TEXT          Starting point to take highlights from (supports
                        natural language)
  -g, --graph TEXT      The name of the Roam graph to store highlights to
                        [required]
  --api-key TEXT        Roam API key  [required]. Also can be supplied through env variable ROAM_API_KEY
  --graph-token TEXT    Roam Graph token  [required]. Also can be supplied through env variable ROAM_GRAPH_TOKEN.
  --help                Show this message and exit.
```

## Improvements from this fork:
- [x] Simplify regular Markdown output
- [x] Add ability to create "call-out blocks" for Markdown (specifically for Obsidian, but will present as block quotes in regular markdown)
  - [x] Specify different blocks for different situations (highlight vs note)
  - [x] Custom call-out blocks by color (according to CSS)
- [x] Programmatically index the colors
- [x] Use downloaded zip file instead of having to extract it first
  - This is going to require extensive reworking, since matching the images to colors is in `models.py` which is imported by `export_books.py` before any file has been specified
  - And as-is, the `Color` class needs to stay in `models.py` because it's a part of the dataclass `Highlight`
- [ ] Add ability to specify date format - likely regular strftime format, and only for local output
- [ ] Automatically determine book name, making `--book-name` optional