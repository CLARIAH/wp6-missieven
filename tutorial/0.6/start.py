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

# <img align="right" src="images/tf.png" width="128"/>
# <img align="right" src="images/dans.png"/>
# <img align="right" src="images/huygenslogo.png"/>
# <img align="right" src="images/logo.png"/>
#
# # Tutorial
#
# This notebook gets you started with using
# [Text-Fabric](https://annotation.github.io/text-fabric/) for coding in 
# [Missieven Corpus](https://github.com/Dans-labs/clariah-gm).
#
# Familiarity with the underlying
# [data model](https://annotation.github.io/text-fabric/tf/about/datamodel.html)
# is recommended.

# ## Installing Text-Fabric
#
# ### Python
#
# You need to have Python on your system. Most systems have it out of the box,
# but alas, that is python2 and we need at least python **3.6**.
#
# Install it from [python.org](https://www.python.org) or from
# [Anaconda](https://www.anaconda.com/download).
#
# ### TF itself
#
# ```
# pip3 install text-fabric
# ```
#
# ### Jupyter notebook
#
# You need [Jupyter](http://jupyter.org).
#
# If it is not already installed:
#
# ```
# pip3 install jupyter
# ```

# %load_ext autoreload
# %autoreload 2

import os, collections

from tf.app import use

# ## Corpus data
#
# Text-Fabric will fetch the Missieven corpus for you.
#
# It will fetch the newest version by default, but you can get other versions as well.
#
# The data will be stored under `text-fabric-data` in your home directory.

# # Incantation
#
# The simplest way to get going is by this *incantation*:

# For the very last version, use `hot`.
#
# For the latest release, use `latest`.
#
# If you have cloned the repos (TF app and data), use `clone`.
#
# If you do not want/need to upgrade, leave out the checkout specifiers.
#
# **After downloading new data it will take 1-2 minutes to optimize the data**.
#
# The optimized data will be stored in your system, and all subsequent use of this
# corpus will find that optimized data.

A = use('missieven:latest', checkout="latest", hoist=globals())
# A = use('missieven', hoist=globals())
# A = use('missieven:clone', checkout="clone", hoist=globals())
# A = use('missieven:hot', checkout="hot", hoist=globals())

# There is a lot of information in the report above, we'll look at that in a later chapter:
# [compute](compute.ipynb)

# # Getting around
#
# ## Where am I?
#
# All information in a Text-Fabric dataset is tied to nodes and edges.
# Nodes are integers, from 1 upwards, and the basic textual objects (*slots*) come first, in the order of the text.
# In this corpus, slots are words, and we have more than 5 millions of them.
#
# Here is how you can visualize a slot and see where you are, if you found the millionth word:

n = 1_000_000
A.plain(n)

# This word is in volume 4, page 717, line 28.
# You can click the passage specifier, and it will take you to the image of this page on the
# Missieven site maintained by the Huygens institute.
#
# ![fragment](images/GM4-717.png)

# ## How to get to ...?
#
# Suppose we want to move to volume 3, page 717.
# How do we find the node that corresponds to that page?

p = A.nodeFromSectionStr("3 717")
p

# This looks like a meaningless number, but like a barcode on a product, this is the key to all information
# about a thing. What kind of thing?

F.otype.v(p)

# We just asked for the value of the feature `otype` (object type) of node `p`, and it turned out to be a page.
# In the same way we can get the page number:

F.n.v(p)

# <img align="right" src="images/incantation.png" width="500"/>
#
# Which features are defined, and what they mean is dependent on the dataset.
# The dataset designer has provided metadata and documentation about features that are 
# accessible wherever you work with Text-Fabric.
# Just after the incantation you can expand the list of features amd click on any feature to jump to its documentation.

# We can also navigate to a specific line:

ln = A.nodeFromSectionStr("3 717:28")
print(f"node {ln} is {F.otype.v(ln)} {F.n.v(ln)}")

# We can also do this in a more structured way:

p = T.nodeFromSection((3, 717))
p

ln = T.nodeFromSection((3, 717, 28))
ln

# At this point, have a look at the 
# [cheatsheet](https://annotation.github.io/text-fabric/tf/cheatsheet.html)
# and find the documentation of these methods.

# ## Explore the neighbourhood
#
# We show how to find the nodes of the lines in the page, how to print the text of those lines, and how to find the individual words.
#
# Text-Fabric has an API called `Locality` (or simply `L`) to explore spatially related nodes.
#
# From a node we can go `up`, `down`, `previous` and `next`. Here we go down.

lines = L.d(p, otype="line")
lines

# # Display
#
# Text-Fabric has a high-level display API to show textual material in various ways.
#
# Here is a plain view.

for line in lines:
    A.plain(line)

# We can show the text in another text format.
# Formats have been defined by the dataset designer, they are not built in into Text-Fabric.
# Let's see what the designer has provided in this regard:

T.formats

# Some formats show all text, others editorial texts only, and some show original letter content only.
#
# The formats that start with `text-` yield plain Unicode text.
#
# The formats that start with `layout-` deliver formatted HTML.
# We have designed the layout in such a way that the text types (editorial, original) are distinguished.
#
# The default format is `text-orig-full`.
#
# Let's switch to `layout-full-notes`, which will also show the footnotes in place.

for line in lines:
    A.plain(line, fmt="layout-full-notes")

# If we want to skip the remarks we can choose `layout-remark-notes`:

for line in lines:
    A.plain(line, fmt="layout-remark-notes")

# Or, without the footnotes:

for line in lines:
    A.plain(line, fmt="layout-remark")

# Just the original text:

for line in lines:
    A.plain(line, fmt="layout-orig")

# # Drilling down
#
# Lets navigate to individual words, we pick a few lines from this page we have seen in various ways.

# +
ln = A.nodeFromSectionStr("3 717:33")
A.plain(ln)

words = L.d(ln, otype="word")
words
# -

# Let's make a table of the words of lines 31 - 33 and the values of some features that they carry, namely:
# `trans`, `transo`, `transr`, `punc`, `remark`, `fnote`

# +
features = "trans transo transr punc remark fnote".split()

table = []

for lno in range(31, 34):
    ln = T.nodeFromSection((3, 717, lno))
    for w in L.d(ln, otype="word"):
        row = tuple(Fs(feature).v(w) for feature in features)
        table.append(row)

table
# -

# We can show that more prettily in a markdown table, but it is a bit of a hassle to compose
# the markdown string.
# Once we have that, we can pass it to a method in the Text-Fabric API that displays it as markdown.

# +
NL = "\n"

mdHead = f"""
{" | ".join(features)}
{" | ".join("---" for _ in features)}
"""

mdData = "\n".join(
    f"""{" | ".join(str(c or "").replace(NL, " ") for c in row)}"""
    for row in table
)

A.dm(f"""{mdHead}{mdData}""")
# -

# Note that the dataset designer has the text strings of all words into the feature `trans`;
# editorial words also go into `transr`, bit not into `transo`;
# original words go into `transo`, but not into `transr`.
#
# The existence of these features is mainly to make it possible to define the selective text formats
# we have seen above.

# If constructing a low level dataset is too low-level for your taste,
# we can just collect a bunch of nodes and feed it to a higher-level display function of Text-Fabric:

# +
table = []

for lno in range(31, 34):
    ln = T.nodeFromSection((3, 717, lno))
    for w in L.d(ln, otype="word"):
        table.append((w,))

table
# -

# Before we ask Text-Fabric to display this, we tell it the features we're interested in.

A.displaySetup(extraFeatures=features)
A.show(table, condensed=True)

# Where this machinery really shines is when it comes to displaying the results of queries.
# See [search](search.ipynb).

# ---
#
# # Next steps
#
# By now you have an impression how to orient yourself in the Missieven dataset.
# The next steps will show you how to get powerful: searching and computing.
#
# After that it is time for collecting results, use them in new annotations and share them.
#
# * **start** start computing with this corpus
# * **[search](search.ipynb)** turbo charge your hand-coding with search templates
# * **[compute](compute.ipynb)** sink down a level and compute it yourself
# * **[exportExcel](exportExcel.ipynb)** make tailor-made spreadsheets out of your results
# * **[annotate](annotate.ipynb)** export text, annotate with BRAT, import annotations
# * **[share](share.ipynb)** draw in other people's data and let them use yours
#
# CC-BY Dirk Roorda
