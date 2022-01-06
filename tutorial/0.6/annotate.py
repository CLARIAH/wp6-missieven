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
# # Annotate
#
# Text-Fabric is a tool for computing with read only datasets.
# How can you manually annotate an existing dataset?
#
# The scenario is: export the portions that must be annotated into a plain text file, accompanied with
# location information.
#
# Use an external tool, e.g. 
# [BRAT](https://brat.nlplab.org) to manually annotate that text.
#
# Read the resulting annotations, combine them with the location information,
# and export the result as a new feature or set of features.
#
# These new features can be published anywhere,
# see the [share](share.ipynb) tutorial,
# and users that want to make use of the new features, can tell Text-Fabric to fetch it from the
# published location alongside the main dataset.
#
# From this point on, the new features act as first class citizens in the dataset.
#
# Note how this does not involve modifying existing datasets!

# %load_ext autoreload
# %autoreload 2

import os
from tf.app import use

A = use("missieven", hoist=globals())
# A = use("missieven:latest", checkout="latest", hoist=globals())
# A = use('missieven:clone', checkout="clone", hoist=globals())

# Text-Fabric has support for exporting data together with location information and then importing new data
# and turning it into new features based on the location information.
#
# See [Recorder](https://annotation.github.io/text-fabric/tf/convert/recorder.html).
#
# We show the workflow by selecting a letter, exporting the original text material as plain text,
# manually annotating it for named entities with [BRAT](https://brat.nlplab.org) and then saving the output
# as a new feature `name`.

from tf.convert.recorder import Recorder

# # Text selection
#
# We choose volume 1 page 6:

p = A.nodeFromSectionStr("1 6")
for ln in L.d(p, otype="line"):
    A.plain(ln, fmt="layout-orig-notes")

# Quite a bit of names. Let's leave out the notes.

for ln in L.d(p, otype="line"):
    A.plain(ln, fmt="layout-orig")

# # Recording
#
# We'll prepare this portion of text for annotation outside TF.
#
# What needs to happen is, that we produce a text file and that we remember the postions of the relevant
# nodes in that text file.
#
# The [Recorder](https://annotation.github.io/text-fabric/tf/convert/recorder.html).
# lets you create a string from nodes,
# where the positions of the nodes in that string are remembered.
# You may add all kinds of material in between the texts of the nodes.
#
# And it is up to you how you represent the nodes.
#
# We can add strings to the recorder, and we can tell nodes to start and to stop.
#
# We add all words in all lines to the recorder, provided the words belong to the original material.
#
# We add line numbers to each line.

# +
# start a recorder
rec = Recorder()

for ln in L.d(p, otype="line"):
    # start a line node
    rec.start(ln)
    
    # add the line number
    rec.add(f"{F.n.v(ln)}. ")
    
    for w in L.d(ln, otype='word'):
        trans = F.transo.v(w)
        # if there is nothing in transo, it is not original text
        if not trans:
            continue
            
        # start a word node
        rec.start(w)
        
        # add the word and its trailing punctuation
        rec.add(f"{trans}{F.punco.v(w)}")
        
        # terminate the word node
        rec.end(w)
    
    # add a newline
    rec.add("\n")
    
    # terminate the line node
    rec.end(ln)
# -

# As a check, let's print the recorded text:

print(rec.text())

# and the recorded node positions.

for i in range(20, 30):
    print(f"pos {i}: {rec.positions()[i]}")

# This means that the character on position 20 in the plain text string is part of the text of node 1039 and of node 5054871.

# With one statement we write the recorded text and the postions to two files:

rec.write("exercises/v01-p0006.txt")


# !head -n 10 exercises/v01-p0006.txt

# !head -n 30 exercises/v01-p0006.txt.pos

# <img align="right" src="images/brat1.png" width="500"/>
#
# # Annotating
#
# We head over to a local installation of Brat
# and annotate our text.
#
# Left you see a quick and dirty manual annotation of some entities that I performed on
# the Brat interface, served locally.
#
# We captured the output of this annotation session into the file `v01-p0006.txt.ann`, it has the following contents:
#
# ```
# T1	Person 675 679	Nera
# T2	GPE 1181 1189	Ternnate
# #1	AnnotatorNotes T2	Ternate
# T3	Person 1203 1223	Coninck van Spagnien
# T4	GPE 1215 1223	Spagnien
# T5	Organization 1240 1254	Heeren Staeten
# T6	Person 1293 1300	Coninck
# T7	Person 1406 1413	Coninck
# T8	Organization 1457 1471	Heeren Staeten
# T9	GPE 1557 1562	Banda
# T10	GPE 1653 1662	Engelsche
# T11	Person 58 65	orancay
# T12	Person 663 670	arancay
# T13	Person 697 706	sabandaer
# T14	Person 794 802	orancaye
# T15	GPE 965 975	Hollanders
# T16	Person 1010 1019	Verhoeven
# T17	GPE 1154 1161	Ambojna
# #2	AnnotatorNotes T17	Amboina
# T18	GPE 1305 1310;1311 1322	ditto 24. plaetse
# #3	AnnotatorNotes T18	Ternate
# *	Alias T11 T14
# R1	Geographical_part Arg1:T2 Arg2:T18	
# ```
#
# Now we want to feed back these annotations as TF features on word nodes.
# The Recorder cannot anticipate the formats that tools like Brat deliver their results in.
# Therefore, it expects the data to be in a straightforward tabular format.
#
# In this case, we must do a small conversion to bring the output annotations
# into good shape, namely a tab separated file
# with columns `start end feature1 feature2 ...`
#
# Here we choose to expose the identifier (the `T`n values) as feature1
# and the kind of entity as feature2.
#
# In case there is a link between two entities, we want to assign
# the earliest `T`number to all entities involved.
#
# We also want to preserve the annotator notes.

# +
def brat2tsv(inh, outh):
    outh.write(f"start\tend\tentityId\tentityKind\tentityComment\n")
    entities = []
    notes = {}
    maps = {}
    for line in inh:
        fields = line.rstrip("\n").split("\t")
        if line.startswith("T"):
            id1 = fields[0]
            (kind, *positions) = fields[1].split()
            (start, end) = (positions[0], positions[-1])
            entities.append([start, end, id1, kind, ""])
        elif line.startswith("#"):
            id1 = fields[1].split()[1]
            notes[id1] = fields[2]
        elif line.startswith("*"):
            (kind, id1, id2) = fields[1].split()
            maps[id2] = id1
        elif line.startswith("R"):
            (id1, id2) = (f[5:] for f in fields[1].split()[1:])
            maps[id2] = id1
    for entity in entities:
        id1 = entity[2]
        if id1 in maps:
            entity[2] = maps[id1]
        if id1 in notes:
            entity[4] = notes[id1]
        line = "\t".join(entity)
        print(line)
        outh.write(f"{line}\n")

    print(maps)


with open("exercises/v01-p0006.txt.ann") as inh:
    with open("exercises/v01-p0006.txt.tsv", "w") as outh:
        brat2tsv(inh, outh)
# -

# Our recorder knows how to do transform this file in feature data.

features = rec.makeFeatures('exercises/v01-p0006.txt.tsv')

# Let's see.

for (feat, data) in features.items():
    print(feat)
    print("\t", data)

# We can show this prettier:

for (feat, data) in features.items():
    print(feat)
    for (node, value) in data.items():
        print(f"\t{F.otype.v(node)} {node} => {value}")

# Note that we assign entity features to line nodes as well.
#
# If that is undesired, we should not have instructed the Recorder to `rec.add(ln)` above.

# # Saving data
#
# The [documentation](https://annotation.github.io/text-fabric/tf/core/fabric.html#tf.core.fabric.FabricCore.save)
# explains how to save this data into text-fabric data files.
#
# We choose a location where to save it, the `exercises` directory next to this notebook.

import os

GITHUB = os.path.expanduser('~/github')
ORG = 'annotation'
REPO = 'tutorials'
PATH = 'missieven/exercises'
VERSION = A.version

# Note the version: we have built the version against a specific version of the data:

A.version

# Later on, we pass this version on, so that users of our data will get the shared data in exactly the same version as their core data.

# We have to specify a bit of metadata for this feature:

metaData = {
    "entityId": dict(
        valueType="str",
        description="identifier of a named entity",
        creator="Dirk Roorda",
    ),
    "entityKind": dict(
        valueType="str",
        description="kind of a named entity",
        creator="Dirk Roorda",
    ),
    "entityComment": dict(
        valueType="str",
        description="comment to a named entity",
        creator="Dirk Roorda",
    ),
}

# Now we can give the save command:

location = f'{GITHUB}/{ORG}/{REPO}/{PATH}/entities/tf'
TF.save(nodeFeatures=features, metaData=metaData, location=location, module=VERSION)

# # Sharing
#
# In [share](share.ipynb) we show how we can share and reuse these features.

# ---
#
# # Contents
#
# * **[start](start.ipynb)** start computing with this corpus
# * **[search](search.ipynb)** turbo charge your hand-coding with search templates
# * **[compute](compute.ipynb)** sink down a level and compute it yourself
# * **[exportExcel](exportExcel)** make tailor-made spreadsheets out of your results
# * **annotate** export text, annotate with BRAT, import annotations
# * **[share](share.ipynb)** draw in other people's data and let them use yours
#
# CC-BY Dirk Roorda
