# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python 3
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
# # Computing "by hand"
#
# We descend to a more concrete level, and interact with the data by means of a bit of hand-coding.
#
# Familiarity with the underlying
# [data model](https://annotation.github.io/text-fabric/tf/about/datamodel.html)
# is recommended.

# %load_ext autoreload
# %autoreload 2

import os, collections

from tf.app import use

A = use('missieven', hoist=globals())
# A = use('missieven:latest', checkout="latest", hoist=globals())
# A = use('missieven:clone', checkout="clone", hoist=globals())

# # Features
# The data of the corpus is organized in features.
# They are *columns* of data.
# Think of the text as a gigantic spreadsheet, where row 1 corresponds to the
# first word, row 2 to the second word, and so on, for all words, several millions, in this corpus.
#
# Each piece of information about the words, including the text of the words, constitute a column in that spreadsheet.
#
# Instead of putting that information in one big table, the data is organized in separate columns.
# We call those columns **features**.

# You can see which features have been loaded, and if you click on a feature name, you find its documentation.
# If you hover over a name, you see where the feature is located on your system.
#
# Edge features are marked by **_bold italic_** formatting.

# # Counting

# +
A.indent(reset=True)
A.info("Counting nodes ...")

i = 0
for n in N.walk():
    i += 1

A.info("{} nodes".format(i))
# -

# # Node types

F.otype.slotType

F.otype.all

C.levels.data

# The second column is the average size (in words) of the node type mentioned in the first column.
#
# The third and fourth column are the node numbers of the first and the last node of that kind.

for (typ, av, start, end) in C.levels.data:
    print(
        f"{end - start + 1:>7} x {typ:<7} having an average size of {int(round(av)):>6} words"
    )

# We can show the text in another text format.

# # Feature statistics

# There are no linguistic features (yet).

# # Word matters
#
# We can only work with the surface forms of words, there is no concept of lexeme in the corpus (yet).
#
# ## Top 20 frequent words

for (w, amount) in F.trans.freqList("word")[0:20]:
    print(f"{amount:>6} {w}")

# ## Hapaxes
#
# We look for words that occur only once.
#
# We are only interested in words that are completely alphabetic, i.e. words that do not have numbers
# or other non-letters in them.

hapaxes1 = sorted(w for (w, amount) in F.trans.freqList('word') if amount == 1 and w.isalpha())
len(hapaxes1)

for lx in hapaxes1[0:20]:
    print(lx)

# ### Small occurrence base
#
# The occurrence base of a word are the missives (letters) in which the word occurs.
#
# **N.B. (terminology)**
# Here *letter* means a document that has been sent to a recipient. This corpus consists of *missives*
# which are letters.
#
# We look only in the content of the original missives.

# +
occurrenceBase = collections.defaultdict(set)

A.indent(reset=True)
A.info("compiling occurrence base ...")
for s in F.otype.s("letter"):
    title = F.title.v(s)
    for w in L.d(s, otype="word"):
        trans = F.transo.v(w)
        if not trans or not trans.isalpha():
            continue
        occurrenceBase[trans].add(title)
A.info("done")
A.info(f"{len(occurrenceBase)} entries")
# -

# An overview of how many words have how big occurrence bases:

# +
occurrenceSize = collections.Counter()

for (w, letters) in occurrenceBase.items():
    occurrenceSize[len(letters)] += 1

occurrenceSize = sorted(
    occurrenceSize.items(),
    key=lambda x: (-x[1], x[0]),
)

for (size, amount) in occurrenceSize[0:10]:
    print(f"letters {size:>4} : {amount:>6} words")
print("...")
for (size, amount) in occurrenceSize[-10:]:
    print(f"letters {size:>4} : {amount:>6} words")
# -

# Let's give the predicate *private* to those words whose occurrence base is a single missive.

privates = {w for (w, base) in occurrenceBase.items() if len(base) == 1}
len(privates)

# ### Peculiarity of missives
#
# As a final exercise with missives, lets make a list of all them, and show their
#
# * total number of words
# * number of private words
# * the percentage of private words: a measure of the peculiarity of the missive

# +
letterList = []

empty = set()
ordinary = set()

for d in F.otype.s("letter"):
    letter = F.title.v(d)
    if len(letter) > 50:
        letter = f"{letter[0:22]} .. {letter[-22:]}"
    words = {
        trans
        for w in L.d(d, otype="word")
        if (trans := F.transo.v(w)) and trans.isalpha()
    }
    a = len(words)
    if not a:
        empty.add(letter)
        continue
    o = len({w for w in words if w in privates})
    if not o:
        ordinary.add(letter)
        continue
    p = 100 * o / a
    letterList.append((letter, a, o, p))

letterList = sorted(letterList, key=lambda e: (-e[3], -e[1], e[0]))

print(f"Found {len(empty):>4} empty letters")
print(f"Found {len(ordinary):>4} ordinary letters (i.e. without private words)")

# +
print(
    "{:<50}{:>5}{:>5}{:>5}\n{}".format(
        "missive",
        "#all",
        "#own",
        "%own",
        "-" * 35,
    )
)

for x in letterList[0:20]:
    print("{:<50} {:>4} {:>4} {:>4.1f}%".format(*x))
print("...")
for x in letterList[-20:]:
    print("{:<50} {:>4} {:>4} {:>4.1f}%".format(*x))
# -

# ---
#
# # Next steps
#
# By now you have an impression how to compute around in the Missieven.
# While this is still the beginning, I hope you already sense the power of unlimited programmatic access
# to all the bits and bytes in the data set.
#
# Here are a few directions for unleashing that power.
#
# * **[start](start.ipynb)** start computing with this corpus
# * **[search](search.ipynb)** turbo charge your hand-coding with search templates
# * **compute** sink down a level and compute it yourself
# * **[exportExcel](exportExcel.ipynb)** make tailor-made spreadsheets out of your results
# * **[annotate](annotate.ipynb)** export text, annotate with BRAT, import annotations
# * **[share](share.ipynb)** draw in other people's data and let them use yours
#
# CC-BY Dirk Roorda
