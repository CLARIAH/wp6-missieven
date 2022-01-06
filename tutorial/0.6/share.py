# -*- coding: utf-8 -*-
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
# # Sharing data features
#
# ## Explore additional data
#
# Once you analyse a corpus, it is likely that you produce data that others can reuse.
# Maybe you have defined a set of proper name occurrences, or special numerals, or you have computed part-of-speech assignments.
#
# It is possible to turn these insights into *new features*, i.e. new `.tf` files with values assigned to specific nodes.
#
# ## Make your own data
#
# New data is a product of your own methods and computations in the first place.
# But how do you turn that data into new TF features?
# It turns out that the last step is not that difficult.
#
# If you can shape your data as a mapping (dictionary) from node numbers (integers) to values
# (strings or integers), then TF can turn that data into a feature file for you with one command.
#
# ## Share your new data
# You can then easily share your new features on GitHub, so that your colleagues everywhere 
# can try it out for themselves.
#
# You can add such data on the fly, by passing a `mod={org}/{repo}/{path}` parameter,
# or a bunch of them separated by commas.
#
# If the data is there, it will be auto-downloaded and stored on your machine.
#
# Let's do it.
#

# %load_ext autoreload
# %autoreload 2

# +
import collections

from tf.app import use
# -

A = use("missieven", hoist=globals())
# A = use("missieven:latest", checkout="latest", hoist=globals())
# A = use('missieven:clone', checkout="clone", hoist=globals())

# # Making data
#
# We illustrate the data creation part by creating a new feature, `number`.
# The idea is that we compute a number value for each word that looks like a number,
# but that contains OCR errors.

# We keep things simple.
#
# We are interested in words that contain only digits and letters, and where the number of digits is greater than de number of letters.
# We exclude words that consist of digits only.
#
# We only work in original letter content.
#
# Let's find them by hand coding.

import re
import collections

# +
results = []

digitRe = re.compile(r"[0-9]")

for w in F.otype.s("word"):
    chars = F.transo.v(w)
    if not chars:
        continue
    (letters, nDigits) = digitRe.subn("", chars)
    nLetters = len(chars) - nDigits
    if nLetters and nDigits > nLetters:
        results.append(w)
        
print(results[0:10])
len(results)
# -

# It happens quite a bit.
#
# Let's have a quick look at the text of the results

print("\n".join(sorted(F.transo.v(w) for w in results)[0:20]))

# We want to map characters to digits.
# To get a feel for that, inventarize the characters that occur in these words.
#
# For each character, count how often it occurs and give at most 10 examples.

# +
inventory = collections.defaultdict(list)

for w in results:
    for c in (trans := F.transo.v(w)) :
        if not c.isdigit():
            inventory[c].append(trans)
            
len(inventory)
# -

# Quite a bit of different characters.

for c in sorted(inventory):
    examples = inventory[c]
    n = len(examples)
    showExamples = ", ".join(sorted(examples)[0:10])
    print(f"{c} ({n:>4}x) {showExamples}")

# We decide to translate a few characters to numerals:

charMapping = {
    "o": 0,
    "ó": 0,
    "ö": 0,
    "Ö": 0,
    "I": 1,
    "J": 1,
    "ï": 1,
    "è": 6,
}


# Now we translate all numerals with this mapping, and if the result is numeric and does not start with a 0,
# we save the result in a mapping from nodes to numbers.

# +
def cmap(chars):
    n = "".join(str(charMapping.get(c, c)) for c in chars)
    return int(n) if not n.startswith("0") and n.isdigit() else None

number = {w: n for w in results if (n := cmap(F.transo.v(w)))}
len(number)
# -

print(number)

# # Saving data
#
# In [annotate](annotate.ipynb) we saw how to save features.
# We do the same for the `number` feature.

import os

GITHUB = os.path.expanduser('~/github')
ORG = 'annotation'
REPO = 'tutorials'
PATH = 'missieven/exercises/numerics'
VERSION = A.version

# Later on, we pass this version on, so that users of our data will get the shared data in exactly the same version as their core data.

# We have to specify a bit of metadata for this feature:

metaData = {
  'number': dict(
    valueType='int',
    description='numeric value of corrected number-like strings',
    creator='Dirk Roorda',
  ),
}

# Now we can give the save command:

location = f'{GITHUB}/{ORG}/{REPO}/{PATH}/tf'
TF.save(nodeFeatures=dict(number=number), metaData=metaData, location=location, module=VERSION)

# Here is the data in text-fabric format: a feature file

with open(f"{location}/{VERSION}/number.tf") as fh:
    print(fh.read())

# # Sharing data
#
# How to share your own data is explained in the
# [documentation](https://annotation.github.io/text-fabric/tf/about/datasharing.html).
#
# Here we show it step by step for the `number` feature.
#
# If you commit your changes to the exercises repo, and have done a `git push origin master`,
# you already have shared your data!
#
# **Keep it simple for small datasets:
# For small feature datasets, you are done.**
#
# If it gets serious, there is support for releases and efficient data transfer.
# Here is how:
#
# **Note (releases)**
#
# If you want to make a stable release, so that you can keep developing, while your users fall back
# on the stable data, you can make a new release.
#
# Go to the GitHub website for that, go to your repo, and click *Releases* and follow the nudges.
#
# **Note (release binaries)**
#
# If you want to make it even smoother for your users, you can zip the data and attach it as a binary to the release just created.
#
# We need to zip the data in exactly the right directory structure. Text-Fabric can do that for us.
#

# + language="sh"
#
# text-fabric-zip annotation/tutorials/missieven/exercises/numerics/tf
# -

# All versions have been zipped, but it works OK if you only attach the newest version to the newest release.
#
# If a user asks for an older version in this release, the system can still find it.

# # Use the data
#
# We can use the data by calling it up when we say `use('missieven', ...)`
# where we put in a data module argument on the dots.
# We will also call up the entity data we created in the [annotate](annotate.ipynb) chapter.
#
# Note that for each module we can specify flags like `:latest`, `:hot`, `clone`.
#
# If you are the author of the data, and want to test it, use `:clone`: it takes the data from where you saved it.
#
# If you are a new user of the data, use `:hot` (get latest commit) or `:latest` (get latest release)
# to download the data.
#
# If you have downloaded the data before, leave out the flag.

A = use(
    "missieven",
    hoist=globals(),
    mod=(
        "annotation/tutorials/missieven/exercises/numerics/tf:hot"
        ","
        "annotation/tutorials/missieven/exercises/entities/tf:hot"
    ),
)

# <img align="right" src="images/sharing.png" width="800"/>
#
# Above you see a new sections in the feature list that you can expand to see 
# which features that module contributed.
#
# Now, suppose did not know much about these feature, then we would like to do a few basic checks.
#
# A good start it to do inspect a frequency list of the values of the new features,
# and then to perform a query looking for the nodes that have these features.
#
# We do that for the entity features and for the number feature.

# ## Entities

F.entityId.freqList()

F.entityKind.freqList()

F.entityComment.freqList()

# Let's query all words that have an entity notation:

query = """
word entityId entityKind* entityComment*
"""
results = A.search(query)

# Here we query all word where the `entityId` is present.
# We also mention the `entityKind` and `entityComment` features, but with a `*` behind them.
# That is a criterion that is always True, so these mentions do not alter the result list.
# But now these features do occur in the query, and when we show results, these features will be shown.

A.show(results, condensed=True)

# **Observation**
#
# It's not only words that have entity features, also the lines themselves have gotten such annotations.
#
# It turns out that it is not very useful to annotate *lines* with entities this way.
# It would be better to annotate them with the number of entities they contain.
# That is our feedback to the creator of these annotations, and because we know the GitHub repo that they are from,
# we can file an [issue](https://github.com/annotation/tutorials/issues/3)!

# ## Numerics

F.number.freqList()

# We see that the values that we have generated before.

# Let's show the original and the number side by side.

results = A.search('''
word number transo*
''')

A.show(results, start=1, end=10)

# # All together!
#
# If more researchers have shared data modules, you can draw them all in.
#
# Then you can design queries that use features from all these different sources.
#
# In that way, you build your own research on top of the work of others.

# Hover over the features to see where they come from, and you'll see they come from your local github repo.

# ---
#
# # Contents
#
# * **[start](start.ipynb)** start computing with this corpus
# * **[search](search.ipynb)** turbo charge your hand-coding with search templates
# * **[compute](compute.ipynb)** sink down a level and compute it yourself
# * **[exportExcel](exportExcel.ipynb)** make tailor-made spreadsheets out of your results
# * **[annotate](annotate.ipynb)** export text, annotate with BRAT, import annotations
# * **share** draw in other people's data and let them use yours
#
# CC-BY Dirk Roorda
