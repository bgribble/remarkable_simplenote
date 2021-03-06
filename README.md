## remarkable-simplenote

Simple tool for syncing a Simplenote account with a reMarkable
cloud account.

There is no perfect mapping between reMarkable notebooks and
Simplenote notes, so there's some built-in opinions about how
the sync works.

## Status

The "Basic" case below works; that is, pull from simplenote and sync to 
reMarkable. I'm going to start on some of the offline OCR workflows next,
but at least now I get PDF versions of all my Simplenote notes on the 
reMarkable \o/

### Key tools

* Simplenote API: the `simplenote` Python package
* reMarkable API: the `rMapy` Python package
* text/markdown to PDF: `pandoc` document converter
* PDF to text (OCR): Tesseract, a Google OCR engine

### Sync model

Let's start with a few facts:

* Simplenote works in the "text domain". Simplenote items are
ultimately just formatted, annotated text.
* reMarkable works in the "document domain". Most of the content
on a reMarkable is unsearchable images of handwritten text and
PDFs imported from elsewhere.

So to sync these means that we have to transform Simplenote text
to files that can be rendered on the reMarkable, and do what we
can to extract text from reMarkable notebooks to put them into
Simplenote notes. Tracking changes on both ends will be tricky.

#### Out of scope

There are some sync pathways that are out of scope:

* Update reMarkable notebooks based on changes in Simplenote
  text. This would mean some crazy business like creating new
  notebook content with the typewritten text replacing the
  original handwritten text or something. Not going there.

* In fact, updating reMarkable notebooks in place at all. I don't
  want to take a chance of messing up notebook contents.

* Not totally off the table but very unlikely: Updating
  Simplenote text based on handwritten annotations on the PDF
  done on reMarkable.

#### Basic: Simplenote to reMarkable, one-way

Push all Simplenote notes, rendered into PDFs, into the right
folder on reMarkable.

"The right folder" is complicated, given that there are no folders
in SimpleNote. For my use case, it's important that my notes get
put into the right folder but the rules are pretty complicated; I
use a numeric filing system wherein the path can be inferred from
the title of the note but it's not an exact match. For example,
the title might be "101.12.02 Quarterly TPS Targets", which could
go into the folder "101 Important project/12 Planning/02 Q4 2020/" as a
file called "101.12.02 Quarterly TPS Targets.pdf".

I don't want to impose this on anybody else so I have some config to
control this. Since the above is the only folder strategy I am using,
I am only doing one other strategy, which is "all notes into the same
folder". If anyone else ever uses this tool I am happy to discuss other
folder strategies based on Simplenote tags or whatever.

The `folder_strategy` config var can either be `"jd_title"` for my special
Johnny Decimal title strategy, or `"bucket"` for all notes in one bucket. If you
choose `"bucket"`, `folder_bucket` should contain the visible name of the
reMarkable folder.


#### Improvement: reMarkable to Simplenote, one-way

Grab notebooks from a specified folder on the reMarkable. Run
them through an OCR process to extract text from the handwritten
notes. Push the OCRed text into notes on Simplenote with an
appropriate tag.

Note that if we do both of these first 2 steps, we end up with a
separate OCRed version of reMarkable notebook contents on the
device in a separate PDF.

This still isn't really a sync, since (for example) new
annotations on Simplenote notes done on the reMarkable, or
changes to the OCR'ed text of notes in Simplenote that were
originally from the reMarkable, will not be reflected back in
their source documents. In fact such changes will be discarded on
the next pull-push if the source doc ever changes.

#### Improvement: Support OCR corrections from Simplenote

If we hand-edit the notes synced from reMarkable to Simplenote,
it may be possible to preserve those changes for the future.
These are probably valuable changes to preserve since they are
likely to be OCR fixes.

Any way around this assumes that changes to the reMarkable
source notebook will end up being OCRed the same way under basic
editing operations.

* When edits are made to the Simplenote note, record diff output
  between the original OCR text and the edited text. This can be
  done on the fly if we store a version history.

* If subsequent changes are made to the reMarkable source doc,
  apply the previous diff after doing OCR on the new version.
  Heuristic the crap out of it to try to DTRT on chunks that
  don't apply.

#### Improvement: Support handwritten edits to Simplenote notes

I don't know how overlays to PDF docs created in the reMarkable
are represented. Almost definitely we couldn't support editing in
the body of a PDF by like strikethroughs or other kinds of
editing annotations.  But we could possibly support append-only
edits if the handwritten text can be OCRed separately from the
PDF content.

### Sync pathways

#### Simplenote --> reMarkable

This is the most straightforward path. The Simplenote API allows
us to download the whole account's worth of data and keep it in
sync with our local document store.

We can then render each note into a PDF file using pandoc and
sync it up to the reMarkable cloud via the reMarkable API.

#### reMarkable --> Simplenote

The `rmapy` API allows us to download metadata and content of
reMarkable notebooks (and PDFs and ePubs). Eventually we might be able to
OCR this content and push to Simplenote notes, who knows!

### Installation

From a the top level of the source tree,

```
pip install .
```

This will install needed Python dependencies, but you will also
need to install a few non-Python tools for processing documents:

* `pandoc` (converting markdown to PDF)
* a PDF engine for `pandoc`, I use `wkhtmltopdf`
* `exiftool`, a file metadata reader/writer

You will need a local directory to store config and sync cache;
it will be created automatically on first run, and defaults to
`~/.remarkable_simplenote/`. If you choose another local
directory, pass `--path=<dir>` on the command line.


### Configuration

Configuration is pulled from a Python "conffile" formatted file
called `config` in the local cache directory, so by default
`~/.remarkable_simplenote/config`.

Here's mine:

```
[default]
simplenote_user= <username>
simplenote_pass= <password>
folder_strategy=jd_title
folder_match=start
folder_bucket=Notes
pdf_engine=wkhtmltopdf
pdf_engine_opts=-T 0mm -B 0mm -L 10mm -R 0mm --user-style-sheet /home/grib/.remarkable_simplenote/wkhtmltopdf.css
```

If using `wkhtmltopdf` as the PDF engine, you probably want to
create a CSS file to style the notes more nicely. Here's the
basic one that I use:

```
body,p,li {
  font-family: Arial, sans-serif;
  font-size: 16px;
}
```

### Invocation
```
usage: remarkable_simplenote [-h] [--pull [{remarkable,simplenote} ...]]
                             [--push [{remarkable,simplenote} ...]]
                             [--path PATH] [--force-pull] [--force-sync]
                             [--force-push]

Sync reMarkable and Simplenote

optional arguments:
  -h, --help            show this help message and exit
  --pull [{remarkable,simplenote} ...]
                        Pull content from the specified source(s)
  --push [{remarkable,simplenote} ...]
                        Push content to the specified destination(s)
  --path PATH           Local config/cache folder
  --force-pull          Pull remote content even if unneeded
  --force-sync          Convert pull to push even if unneeded
  --force-push          Push data to remote even if unneeded
```

First data is pull-synced to the local store from the named
remote sources ("pull"), then the pulled data is format-converted
and processed into the push queue ("sync"), then the push queue
is push-synced to the named sources ("push").

If the `--force-THING` option is not passed, we try to do the
minimum amount of work possible by looking at object version
numbers.

You can do this process either in a single pass, as in
```
remarkable_simplenote --pull simplenote --push remarkable
```
or in separate pull and push steps.

"sync" happens automatically after "pull", so it's not necessary to
mention it on the command line unless you want to force it, such
as if you need to change your wkhtmltopdf stylesheet and want to
rebuild all the pdfs. In that case you can just run the sync by
itself:

```
remarkable_simplenote --force-sync
```
