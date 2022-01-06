# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python3.9
#     language: python
#     name: python3
# ---

# <img align="right" src="images/tf.png"/>
# <img align="right" src="images/etcbc.png"/>
# <img align="right" src="images/logo.png"/>
#
# ---
#
# To get started: consult [start](start.ipynb)
#
# ---
#
# # Search Introduction
#
# *Search* in Text-Fabric is a template based way of looking for structural patterns in your dataset.
#
# Within Text-Fabric we have the unique possibility to combine the ease of formulating search templates for
# complicated syntactical patterns with the power of programmatically processing the results.
#
# This notebook will show you how to get up and running.
#
# ## Easy command
#
# Search is as simple as saying (just an example)
#
# ```python
# results = A.search(template)
# A.show(results)
# ```
#
# See all ins and outs in the
# [search template docs](https://annotation.github.io/text-fabric/tf/about/searchusage.html).

# # Incantation
#
# The ins and outs of installing Text-Fabric, getting the corpus, and initializing a notebook are
# explained in the [start tutorial](start.ipynb).

# %load_ext autoreload
# %autoreload 2

import unicodedata
from tf.app import use

A = use('missieven', hoist=globals())
# A = use('missieven:latest', checkout="latest", hoist=globals())
# A = use('missieven:clone', checkout="clone", hoist=globals())

# # Basic search command
#
# We start with the most simple form of issuing a query.
# Let's look for the words in volume 4, page 235, line 17
#
# All work involved in searching takes place under the hood.

query = '''
volume n=4
  page n=239
    line n<9
      word
'''
results = A.search(query)
A.table(results, skipCols="1 2 3")

# The hyperlinks take us to the online image of this page at the Huygens institute.
#
# Note that we can choose start and/or end points in the results list.

A.table(results, start=37, end=46, skipCols="1 2")

# We can show the results more fully with `show()`.

A.show(results, skipCols="1 2 3", condensed=True, condenseType="line")

# Now we pick all numerical words, or rather, words that contain a digit

query = '''
volume n=4
  page n=239
    line n<9
      word trans~[0-9]
'''
results = A.search(query)
A.show(results, skipCols="1 2 3", condensed=True)

# Lets look for all places where there is a remark by the editor:

query = '''
word remark
'''
results = A.search(query)

# We can narrow down to the page we just inspected:

query = '''
volume n=4
  page n=239
    word remark
'''
results = A.search(query)

# and show the results:

A.show(results, condensed=True)

# ---
#
# # Contents
#
# * **[start](start.ipynb)** start computing with this corpus
# * **search** turbo charge your hand-coding with search templates
# * **[compute](compute.ipynb)** sink down a level and compute it yourself
# * **[exportExcel](exportExcel.ipynb)** make tailor-made spreadsheets out of your results
# * **[annotate](annotate.ipynb)** export text, annotate with BRAT, import annotations
# * **[share](share.ipynb)** draw in other people's data and let them use yours
#
# CC-BY Dirk Roorda
