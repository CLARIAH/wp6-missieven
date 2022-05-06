# Reproduction of results

The following commands run the complete conversion
from source material to text-fabric dataset.

## Preliminaries

Most programs are plain Python programs,
an optional program is written as a Jupyter Notebook.
Make sure you have a Python (at least 3.8) with, optionally, JupyterLab installed.

Clone this repository, we assume you clone it to `~/github/clariah/wp6-missieven`.
Also clone the related `wp6-missieven-search` repository.

```
mkdir -p ~/github/clariah
cd ~/github/clariah/wp6-missieven
git clone https://github.com/clariah/wp6-missieven
git clone https://github.com/clariah/wp6-missieven-search
cd programs
```

Now you are in the right directory for executing programs.

You can run (almost) all conversions and preparations in one go:

```
./tf1-14.sh
```

The only things that are not done are
*   the optional part in the Jupyter Notebook
*   publishing the generated search interface to GitHub Pages

Below we take you through all the steps one by one.

## Trim

Volumes 1-13 are trimmed from TEI to simplified TEI in four stages:

```
python3 trimTei 0
python3 trimTei 1
python3 trimTei 2
python3 trimTei 3
python3 trimTei 4
```

Volume 14 i-ii are trimmed from textual PDF in four stages:

```
python3 trimPdf.py pdf
python3 trimPdf.py struct
python3 trimPdf.py fine
python3 trimPdf.py xml
```

Now the directory `xml` has been generated,
with subdirectories for each volume, and XML files for each letter,
whose name is derived from the page number where the letter starts.
When there are several letters on one page, we use `a`, `b`, etc behind
the page number.

If you want to see the diagnostic messages from the conversion, consult the files generated in the `trimreport` and `pdfreport` directories.

## Generate TF

Text-Fabric data is generated from the xml files by running

```
python3 tfFromTrim.py
```

Now the directory `tf` has been created with a subdirectory for the 
version of the data.
The version is specified in `lib.py`.

When Text-Fabric uses the files in the `tf` directory, it will do
a one-time precomputation step, which generates a `.tf` directory
within the `tf` directory.

We can trigger the precomputation in advance by doing

```
python3 tfFromTrim.py loadonly
```

## Optional: Link version 0.4 to version 1.0

In order to be able to port annotations made on an earliers version of the data
to the newest version of the data,
we link the nodes of an earlier version to the nodes of the latest version.

**This is only needed to run the *annotation* tutorial.**

The mapping itself is a piece of TF data that ends up in the `tf` directory.

We do this by running the notebook

`map.ipynb`

## Generate the static javascript search interface

To make the static pages and their search interface work, we have to generate
specific data and publish it to GitHub pages.

```
text-fabric-make clariah/wp6-missieven ship
```

Do this if you have sufficient rights over the `clariah/wp6-missieven`
repository on GitHub.

For your own use, you can say

```
text-fabric-make clariah/wp6-missieven serve
```

which will generate the data locally and serve it from there to your browser.

Both steps will generate the `site` directory in the `text-fabric-search` repo.

Most of the machinery to generate this data is in Text-Fabric itself,
but there is also a corpus dependent piece of Python code involved,
together with some configuration in yaml files.

That is all in `https://github.com/clariah/wp6-missieven-search/blob/master/layeredsearch`.


# Text-Fabric documentation

Here are some parts of the TF docs that are relevant to the processes
described below:

*   [walker conversion](https://annotation.github.io/text-fabric/tf/convert/walker.html)
*   [layered search building](https://annotation.github.io/text-fabric/tf/client/make/build.html)
*   [layered search command line usage](https://annotation.github.io/text-fabric/tf/client/make/help.html)
*   [layered search user manual](https://annotation.github.io/text-fabric/tf/about/clientmanual.html)


