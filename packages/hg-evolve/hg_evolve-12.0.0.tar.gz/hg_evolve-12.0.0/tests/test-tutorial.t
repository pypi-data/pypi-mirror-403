===============
Evolve Tutorial
===============

Initial setup
-------------

This Mercurial configuration example is used for testing.

.. Various setup

  $ cat >> $HGRCPATH << EOF
  > [ui]
  > # This is change the default output of log for clear tutorial
  > logtemplate ="{node|short} ({phase}): {desc}\n"
  > [diff]
  > # use "git" diff format, clearer and smarter format
  > git = 1
  > EOF

  $ hg init local
  $ cat >> local/.hg/hgrc << EOF
  > [paths]
  > remote = ../remote
  > other = ../other
  > [ui]
  > user = Babar the King
  > EOF

  $ hg init remote
  $ cat >> remote/.hg/hgrc << EOF
  > [paths]
  > local = ../local
  > [ui]
  > user = Celestine the Queen
  > EOF

  $ hg init other
  $ cat >> other/.hg/hgrc << EOF
  > [ui]
  > user = Princess Flore
  > EOF


This tutorial uses the following configuration for Mercurial:

A compact log template with phase data:

  $ hg showconfig ui | grep log
  ui.logtemplate="{node|short} ({phase}): {desc}\n"

Improved git format diff:

  $ hg showconfig diff
  diff.git=1

And of course, we enable the experimental extensions for mutable history:

  $ cat >> $HGRCPATH <<EOF
  > [extensions]
  > evolve = $TESTDIR/../hgext3rd/evolve/
  > # enabling rebase is also needed for now
  > rebase =
  > EOF

#if docgraph-ext
  $ . "$TESTDIR/testlib/docgraph_setup.sh" #rest-ignore
#endif

-----------------------
Single Developer Usage
-----------------------

This tutorial shows how to use evolution to rewrite history locally.


Fixing mistake with `hg amend`
--------------------------------

We are versioning a shopping list

  $ cd local
  $ cat  >> shopping << EOF
  > Spam
  > Whizzo butter
  > Albatross
  > Rat (rather a lot)
  > Jugged fish
  > Blancmange
  > Salmon mousse
  > EOF
  $ hg commit -A -m "Monthy Python Shopping list"
  adding shopping

Its first version is shared with the outside.

  $ hg push remote
  pushing to $TESTTMP/remote (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Later I add additional items to my list

  $ cat >> shopping << EOF
  > Egg
  > Sugar
  > Vinegar
  > Oil
  > EOF
  $ hg commit -m "adding condiment"
  $ cat >> shopping << EOF
  > Bananos
  > Pear
  > Apple
  > EOF
  $ hg commit -m "adding fruit"

The history is completely linear so far

  $ hg log -G
  @  4296f0622469 (draft): adding fruit
  |
  o  63ae8c44f4b6 (draft): adding condiment
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  
#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	1	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=1,
      		pin=true,
      		pos="1,1!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	0 -> 1	 [arrowhead=none,
      		penwidth=2.0];
      	2	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=2,
      		pin=true,
      		pos="1,2!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	1 -> 2	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

But a typo was made in Bananas!

  $ hg export tip
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 4296f0622469c1527d5dc020cf72bd7732c44c64
  # Parent  63ae8c44f4b6274d5580b4eea41a87623301c3e9
  adding fruit
  
  diff --git a/shopping b/shopping
  --- a/shopping
  +++ b/shopping
  @@ -9,3 +9,6 @@
   Sugar
   Vinegar
   Oil
  +Bananos
  +Pear
  +Apple

The faulty changeset is in the "draft" phase because it has not been exchanged with
the outside yet. The first one has been exchanged and is "public" (immutable).

  $ hg log -G
  @  4296f0622469 (draft): adding fruit
  |
  o  63ae8c44f4b6 (draft): adding condiment
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	1	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=1,
      		pin=true,
      		pos="1,1!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	0 -> 1	 [arrowhead=none,
      		penwidth=2.0];
      	2	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=2,
      		pin=true,
      		pos="1,2!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	1 -> 2	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

Luckily, I can use `hg commit --amend` to rewrite my faulty changeset!

  $ sed -i'' -e s/Bananos/Banana/ shopping
  $ hg diff
  diff --git a/shopping b/shopping
  --- a/shopping
  +++ b/shopping
  @@ -9,6 +9,6 @@
   Sugar
   Vinegar
   Oil
  -Bananos
  +Banana
   Pear
   Apple
  $ hg commit --amend

A new changeset with the correct changes replaces the old one.

  $ hg log -G
  @  6445b365ad1c (draft): adding fruit
  |
  o  63ae8c44f4b6 (draft): adding condiment
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  
#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	1	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=1,
      		pin=true,
      		pos="1,1!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	0 -> 1	 [arrowhead=none,
      		penwidth=2.0];
      	3	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=3,
      		pin=true,
      		pos="1,3!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	1 -> 3	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

  $ hg export tip
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 6445b365ad1c4905e7a120e45242d9f4b51ec48f
  # Parent  63ae8c44f4b6274d5580b4eea41a87623301c3e9
  adding fruit
  
  diff --git a/shopping b/shopping
  --- a/shopping
  +++ b/shopping
  @@ -9,3 +9,6 @@
   Sugar
   Vinegar
   Oil
  +Banana
  +Pear
  +Apple

Getting rid of branchy history
----------------------------------

While I was working on my list, someone made a change remotely.

  $ cd ../remote
  $ hg up -q
  $ sed -i'' -e 's/Spam/Spam Spam Spam/' shopping
  $ hg ci -m 'SPAM'
  $ cd ../local

I'll get this remote changeset when pulling

  $ hg pull remote
  pulling from $TESTTMP/remote (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  new changesets 9ca060c80d74
  (run 'hg heads' to see heads, 'hg merge' to merge)

I now have a new head. Note that this remote head is immutable.

  $ hg log -G
  o  9ca060c80d74 (public): SPAM
  |
  | @  6445b365ad1c (draft): adding fruit
  | |
  | o  63ae8c44f4b6 (draft): adding condiment
  |/
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	1	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=1,
      		pin=true,
      		pos="1,1!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	0 -> 1	 [arrowhead=none,
      		penwidth=2.0];
      	4	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=4,
      		pin=true,
      		pos="1,4!",
      		shape=circle,
      		style=filled,
      		width=1];
      	0 -> 4	 [arrowhead=none,
      		penwidth=2.0];
      	3	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=3,
      		pin=true,
      		pos="1,3!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	1 -> 3	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

Instead of merging my head with the new one. I'm going to rebase my work

  $ hg diff
  $ hg rebase --dest 9ca060c80d74 --source 63ae8c44f4b6
  rebasing 1:63ae8c44f4b6 "adding condiment"
  merging shopping
  rebasing 3:6445b365ad1c "adding fruit"
  merging shopping


My local work is now rebased on the remote one.

  $ hg log -G
  @  d300c8f961ce (draft): adding fruit
  |
  o  723e5a43d6d9 (draft): adding condiment
  |
  o  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  
#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=4,
      		pin=true,
      		pos="1,4!",
      		shape=circle,
      		style=filled,
      		width=1];
      	0 -> 4	 [arrowhead=none,
      		penwidth=2.0];
      	5	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=5,
      		pin=true,
      		pos="1,5!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	4 -> 5	 [arrowhead=none,
      		penwidth=2.0];
      	6	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=6,
      		pin=true,
      		pos="1,6!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	5 -> 6	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

Removing changesets
------------------------

I add new items to my list.

  $ cat >> shopping << EOF
  > car
  > bus
  > plane
  > boat
  > EOF
  $ hg ci -m 'transport'
  $ hg log -G
  @  7f938a07ecb2 (draft): transport
  |
  o  d300c8f961ce (draft): adding fruit
  |
  o  723e5a43d6d9 (draft): adding condiment
  |
  o  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

I have a new commit but I realize that don't want it. (Transport shopping list
does not fit well in my standard shopping list)

  $ hg prune . # "." is for working directory parent
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at d300c8f961ce
  1 changesets pruned

The silly changeset is gone.

  $ hg log -G
  @  d300c8f961ce (draft): adding fruit
  |
  o  723e5a43d6d9 (draft): adding condiment
  |
  o  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=4,
      		pin=true,
      		pos="1,4!",
      		shape=circle,
      		style=filled,
      		width=1];
      	0 -> 4	 [arrowhead=none,
      		penwidth=2.0];
      	5	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=5,
      		pin=true,
      		pos="1,5!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	4 -> 5	 [arrowhead=none,
      		penwidth=2.0];
      	6	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=6,
      		pin=true,
      		pos="1,6!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	5 -> 6	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

Reordering changesets
------------------------


We create two changesets.


  $ cat >> shopping << EOF
  > Shampoo
  > Toothbrush
  > ... More bathroom stuff to come
  > Towel
  > Soap
  > EOF
  $ hg ci -m 'bathroom stuff'

  $ sed -i'' -e 's/Spam/Spam Spam Spam/g' shopping
  $ hg ci -m 'SPAM SPAM'
  $ hg log -G
  @  1c877d31b53f (draft): SPAM SPAM
  |
  o  d1928babc208 (draft): bathroom stuff
  |
  o  d300c8f961ce (draft): adding fruit
  |
  o  723e5a43d6d9 (draft): adding condiment
  |
  o  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

.. note:: We can't amend changeset 7e82d3f3c2cb or 9ca060c80d74 as they are immutable.

I now want to push to remote all my changes except the bathroom one, which I'm
not totally happy with yet. To be able to push "SPAM SPAM" I need a version of
"SPAM SPAM" which is not a child of "bathroom stuff".

You can use the 'grab' command for that.

.. note:: `grab` is an alias for `hg rebase --dest . --rev <target>; hg up <result>`

  $ hg up 'p1(d1928babc208)' # going on "bathroom stuff" parent
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg pick 1c877d31b53f # moving "SPAM SPAM" to the working directory parent
  picking 9:1c877d31b53f "SPAM SPAM"
  merging shopping
  $ hg log -G
  @  501b33037995 (draft): SPAM SPAM
  |
  | o  d1928babc208 (draft): bathroom stuff
  |/
  o  d300c8f961ce (draft): adding fruit
  |
  o  723e5a43d6d9 (draft): adding condiment
  |
  o  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=4,
      		pin=true,
      		pos="1,4!",
      		shape=circle,
      		style=filled,
      		width=1];
      	0 -> 4	 [arrowhead=none,
      		penwidth=2.0];
      	5	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=5,
      		pin=true,
      		pos="1,5!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	4 -> 5	 [arrowhead=none,
      		penwidth=2.0];
      	6	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=6,
      		pin=true,
      		pos="1,6!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	5 -> 6	 [arrowhead=none,
      		penwidth=2.0];
      	8	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=8,
      		pin=true,
      		pos="1,8!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	6 -> 8	 [arrowhead=none,
      		penwidth=2.0];
      	10	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=10,
      		pin=true,
      		pos="1,10!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	6 -> 10	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

We have a new version of "SPAM SPAM" without the bathroom stuff

  $ grep Spam shopping  # enough spam
  Spam Spam Spam Spam Spam Spam Spam Spam Spam
  $ grep Toothbrush shopping # no Toothbrush
  [1]
  $ hg export .
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 501b330379955b6bf194dc99504a477b1f2d3f89
  # Parent  d300c8f961ceefede93601dbe478c701e2ff5995
  SPAM SPAM
  
  diff --git a/shopping b/shopping
  --- a/shopping
  +++ b/shopping
  @@ -1,4 +1,4 @@
  -Spam Spam Spam
  +Spam Spam Spam Spam Spam Spam Spam Spam Spam
   Whizzo butter
   Albatross
   Rat (rather a lot)

To make sure I do not push unfinished changeset by mistake I move the "bathroom
stuff" changeset to the secret phase.

  $ hg phase --force --secret d1928babc208

we can now push our change:

  $ hg push remote
  pushing to $TESTTMP/remote (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  5 new obsolescence markers

for simplicity's sake we get the bathroom change in line again

  $ hg pick d1928babc208
  picking 8:d1928babc208 "bathroom stuff"
  merging shopping
  $ hg phase --draft .
  $ hg log -G
  @  39b19dc3d1e4 (draft): bathroom stuff
  |
  o  501b33037995 (public): SPAM SPAM
  |
  o  d300c8f961ce (public): adding fruit
  |
  o  723e5a43d6d9 (public): adding condiment
  |
  o  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=4,
      		pin=true,
      		pos="1,4!",
      		shape=circle,
      		style=filled,
      		width=1];
      	0 -> 4	 [arrowhead=none,
      		penwidth=2.0];
      	5	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=5,
      		pin=true,
      		pos="1,5!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4 -> 5	 [arrowhead=none,
      		penwidth=2.0];
      	6	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=6,
      		pin=true,
      		pos="1,6!",
      		shape=circle,
      		style=filled,
      		width=1];
      	5 -> 6	 [arrowhead=none,
      		penwidth=2.0];
      	10	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=10,
      		pin=true,
      		pos="1,10!",
      		shape=circle,
      		style=filled,
      		width=1];
      	6 -> 10	 [arrowhead=none,
      		penwidth=2.0];
      	11	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=11,
      		pin=true,
      		pos="1,11!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	10 -> 11	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

Splitting change
------------------

This part is not written yet, but you can use either the `histedit` extension
or the `uncommit` command to split a change.

#if hg69
  $ hg help uncommit
  hg uncommit [OPTION]... [FILE]...
  
  move changes from parent revision to working directory
  
  Changes to selected files in the checked out revision appear again as
  uncommitted changed in the working directory. A new revision without the
  selected changes is created, becomes the checked out revision, and obsoletes
  the previous one.
  
  The --include option specifies patterns to uncommit. The --exclude option
  specifies patterns to keep in the commit.
  
  The --rev argument let you change the commit file to a content of another
  revision. It still does not change the content of your file in the working
  directory.
  
  Return 0 if changed files are uncommitted.
  
  options ([+] can be repeated):
  
   -a --all                 uncommit all changes when no arguments given
   -r --rev REV             revert commit content to REV instead
      --revert              discard working directory changes after uncommit
   -n --note TEXT           store a note on uncommit
   -I --include PATTERN [+] include names matching the given patterns
   -X --exclude PATTERN [+] exclude names matching the given patterns
   -m --message TEXT        use text as commit message
   -l --logfile FILE        read commit message from file
   -d --date DATE           record the specified date as commit date
   -u --user USER           record the specified user as committer
   -D --current-date        record the current date as commit date
   -U --current-user        record the current user as committer
  
  (some details hidden, use --verbose to show complete help)
#endif


The edit command of histedit can be used to split changeset:


Collapsing change
------------------

The tutorial part is not written yet but can use `hg fold`:

#if hg69
  $ hg help fold
  hg fold [OPTION]... [-r] REV...
  
  aliases: squash
  
  fold multiple revisions into a single one
  
  With --from, folds all the revisions linearly between the given revisions and
  the parent of the working directory.
  
  With --exact, folds only the specified revisions while ignoring the parent of
  the working directory. In this case, the given revisions must form a linear
  unbroken chain.
  
  options ([+] can be repeated):
  
   -r --rev REV [+]  revision to fold
      --exact        only fold specified revisions
      --from         fold revisions linearly to working copy parent
   -n --note TEXT    store a note on fold
   -m --message TEXT use text as commit message
   -l --logfile FILE read commit message from file
   -d --date DATE    record the specified date as commit date
   -u --user USER    record the specified user as committer
   -D --current-date record the current date as commit date
   -U --current-user record the current user as committer
  
  (some details hidden, use --verbose to show complete help)
#endif


-----------------------
Collaboration
-----------------------


Sharing mutable changesets
----------------------------

To share mutable changesets with others, just check that the repo you interact
with is "not publishing". Otherwise you will get the previously observe
behavior where exchanged changeset are automatically published.

  $ cd ../remote
  $ hg -R ../local/ showconfig phases
  [1]

The local repo does not have any specific configuration for `phases.publish`.
It is ``true`` by default.

  $ hg pull local
  pulling from $TESTTMP/local (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  1 new obsolescence markers
  new changesets 39b19dc3d1e4
  (run 'hg update' to get a working copy)
  $ hg log -G
  o  39b19dc3d1e4 (public): bathroom stuff
  |
  o  501b33037995 (public): SPAM SPAM
  |
  o  d300c8f961ce (public): adding fruit
  |
  o  723e5a43d6d9 (public): adding condiment
  |
  @  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

We do not want to publish the "bathroom changeset". Let's rollback the last transaction.

.. warning:: `rollback` is actually a dangerous kind of internal command that is deprecated and should not be exposed to user. Please forget you read about it until someone fix this tutorial.

  $ hg rollback
  repository tip rolled back to revision 4 (undo pull)
  $ hg log -G
  o  501b33037995 (public): SPAM SPAM
  |
  o  d300c8f961ce (public): adding fruit
  |
  o  723e5a43d6d9 (public): adding condiment
  |
  @  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

Let's make the local repo "non publishing".

  $ echo '[phases]' >> ../local/.hg/hgrc
  $ echo 'publish=false' >> ../local/.hg/hgrc
  $ echo '[phases]' >> .hg/hgrc
  $ echo 'publish=false' >> .hg/hgrc
  $ hg showconfig phases
  phases.publish=false
  $ hg -R ../local/ showconfig phases
  phases.publish=false


I can now exchange mutable changeset between "remote" and "local" repository.

  $ hg pull local
  pulling from $TESTTMP/local (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  1 new obsolescence markers
  new changesets 39b19dc3d1e4 (1 drafts)
  (run 'hg update' to get a working copy)
  $ hg log -G
  o  39b19dc3d1e4 (draft): bathroom stuff
  |
  o  501b33037995 (public): SPAM SPAM
  |
  o  d300c8f961ce (public): adding fruit
  |
  o  723e5a43d6d9 (public): adding condiment
  |
  @  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

Rebasing unstable change after pull
----------------------------------------------

Remotely someone add a new changeset on top of the mutable "bathroom" on.

  $ hg up 39b19dc3d1e4 -q
  $ cat >> shopping << EOF
  > Giraffe
  > Rhino
  > Lion
  > Bear
  > EOF
  $ hg ci -m 'animals'

But at the same time, locally, this same "bathroom changeset" was updated.

  $ cd ../local
  $ hg up 39b19dc3d1e4 -q
  $ sed -i'' -e 's/... More bathroom stuff to come/Bath Robe/' shopping
  $ hg commit --amend
  $ hg log -G
  @  5486682f4225 (draft): bathroom stuff
  |
  o  501b33037995 (public): SPAM SPAM
  |
  o  d300c8f961ce (public): adding fruit
  |
  o  723e5a43d6d9 (public): adding condiment
  |
  o  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=4,
      		pin=true,
      		pos="1,4!",
      		shape=circle,
      		style=filled,
      		width=1];
      	0 -> 4	 [arrowhead=none,
      		penwidth=2.0];
      	5	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=5,
      		pin=true,
      		pos="1,5!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4 -> 5	 [arrowhead=none,
      		penwidth=2.0];
      	6	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=6,
      		pin=true,
      		pos="1,6!",
      		shape=circle,
      		style=filled,
      		width=1];
      	5 -> 6	 [arrowhead=none,
      		penwidth=2.0];
      	10	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=10,
      		pin=true,
      		pos="1,10!",
      		shape=circle,
      		style=filled,
      		width=1];
      	6 -> 10	 [arrowhead=none,
      		penwidth=2.0];
      	12	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=12,
      		pin=true,
      		pos="1,12!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	10 -> 12	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

When we pull from remote again we get an unstable state!

  $ hg pull remote
  pulling from $TESTTMP/remote (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  1 new orphan changesets
  new changesets 0609f95eccab (1 drafts)
  (run 'hg update' to get a working copy)

The new changeset "animal" is based on an old changeset of "bathroom". You can
see both version showing up in the log.

  $ hg log -G
  *  0609f95eccab (draft): animals
  |
  | @  5486682f4225 (draft): bathroom stuff
  | |
  x |  39b19dc3d1e4 (draft): bathroom stuff
  |/
  o  501b33037995 (public): SPAM SPAM
  |
  o  d300c8f961ce (public): adding fruit
  |
  o  723e5a43d6d9 (public): adding condiment
  |
  o  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=4,
      		pin=true,
      		pos="1,4!",
      		shape=circle,
      		style=filled,
      		width=1];
      	0 -> 4	 [arrowhead=none,
      		penwidth=2.0];
      	5	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=5,
      		pin=true,
      		pos="1,5!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4 -> 5	 [arrowhead=none,
      		penwidth=2.0];
      	6	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=6,
      		pin=true,
      		pos="1,6!",
      		shape=circle,
      		style=filled,
      		width=1];
      	5 -> 6	 [arrowhead=none,
      		penwidth=2.0];
      	10	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=10,
      		pin=true,
      		pos="1,10!",
      		shape=circle,
      		style=filled,
      		width=1];
      	6 -> 10	 [arrowhead=none,
      		penwidth=2.0];
      	11	 [fillcolor="#DFDFFF",
      		fixedsize=true,
      		group=default_alt,
      		height=1,
      		label=11,
      		pin=true,
      		pos="2,11!",
      		shape=pentagon,
      		style="dotted, filled",
      		width=1];
      	10 -> 11	 [arrowhead=none,
      		penwidth=2.0];
      	12	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=12,
      		pin=true,
      		pos="1,12!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	10 -> 12	 [arrowhead=none,
      		penwidth=2.0];
      	11 -> 12	 [arrowtail=none,
      		dir=back,
      		minlen=0,
      		penwidth=2.0,
      		style=dashed];
      	13	 [fillcolor="#FF4F4F",
      		fixedsize=true,
      		group=default_alt,
      		height=1,
      		label=13,
      		pin=true,
      		pos="2,13!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	11 -> 13	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

The older version 39b19dc3d1e4 never ceased to exist in the local repo. It was
just hidden and excluded from pull and push.

.. note:: In hgview there is a nice dotted relation highlighting 5486682f4225 as a new version of 39b19dc3d1e4. This is not yet ported to ``hg log -G``.

There is now an **unstable** changeset in this history. Mercurial will refuse to
share it with the outside:

  $ hg push other
  pushing to $TESTTMP/other (glob)
  searching for changes
  abort: push includes orphan changeset: 0609f95eccab!
  (use 'hg evolve' to get a stable history or --force to ignore warnings)
  [255]
 

To resolve this unstable state, you need to rebase 0609f95eccab onto
5486682f4225. The `hg evolve` command will do this for you.

It has a --dry-run option to only suggest the next move.

  $ hg evolve --dry-run
  move:[13] animals
  atop:[12] bathroom stuff
  hg rebase -r 0609f95eccab -d 5486682f4225

Let's do it

  $ hg evolve
  move:[13] animals
  atop:[12] bathroom stuff
  merging shopping

The old version of bathroom is hidden again.

  $ hg log -G
  o  3266db1117c9 (draft): animals
  |
  @  5486682f4225 (draft): bathroom stuff
  |
  o  501b33037995 (public): SPAM SPAM
  |
  o  d300c8f961ce (public): adding fruit
  |
  o  723e5a43d6d9 (public): adding condiment
  |
  o  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

And let's update to the newly evolved changeset.

  $ hg update
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=4,
      		pin=true,
      		pos="1,4!",
      		shape=circle,
      		style=filled,
      		width=1];
      	0 -> 4	 [arrowhead=none,
      		penwidth=2.0];
      	5	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=5,
      		pin=true,
      		pos="1,5!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4 -> 5	 [arrowhead=none,
      		penwidth=2.0];
      	6	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=6,
      		pin=true,
      		pos="1,6!",
      		shape=circle,
      		style=filled,
      		width=1];
      	5 -> 6	 [arrowhead=none,
      		penwidth=2.0];
      	10	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=10,
      		pin=true,
      		pos="1,10!",
      		shape=circle,
      		style=filled,
      		width=1];
      	6 -> 10	 [arrowhead=none,
      		penwidth=2.0];
      	12	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=12,
      		pin=true,
      		pos="1,12!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	10 -> 12	 [arrowhead=none,
      		penwidth=2.0];
      	14	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=14,
      		pin=true,
      		pos="1,14!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	12 -> 14	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

We can push this evolution to remote.

  $ hg push remote
  pushing to $TESTTMP/remote (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files (+1 heads)
  2 new obsolescence markers
  obsoleted 2 changesets

Remote get a warning that current working directory is based on an obsolete
changeset.

  $ cd ../remote
  $ hg pull local # we up again to trigger the warning. it was displayed during the push
  pulling from $TESTTMP/local (glob)
  searching for changes
  no changes found

Now let's see where we are, and update to the successor.

  $ hg parents
  0609f95eccab (draft): animals
  working directory parent is obsolete! (0609f95eccab)
  (use 'hg evolve' to update to its successor: 3266db1117c9)
  $ hg evolve
  update:[8] animals
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 3266db1117c9

Relocating unstable change after prune
----------------------------------------------

The remote guy keeps working.

  $ sed -i'' -e 's/Spam/Spam Spam Spam Spam/g' shopping
  $ hg commit -m "SPAM SPAM SPAM"

I'm pulling its work locally.

  $ cd ../local
  $ hg pull remote
  pulling from $TESTTMP/remote (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets fff8c3d068b6 (1 drafts)
  (run 'hg update' to get a working copy)
  $ hg log -G
  o  fff8c3d068b6 (draft): SPAM SPAM SPAM
  |
  @  3266db1117c9 (draft): animals
  |
  o  5486682f4225 (draft): bathroom stuff
  |
  o  501b33037995 (public): SPAM SPAM
  |
  o  d300c8f961ce (public): adding fruit
  |
  o  723e5a43d6d9 (public): adding condiment
  |
  o  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=4,
      		pin=true,
      		pos="1,4!",
      		shape=circle,
      		style=filled,
      		width=1];
      	0 -> 4	 [arrowhead=none,
      		penwidth=2.0];
      	5	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=5,
      		pin=true,
      		pos="1,5!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4 -> 5	 [arrowhead=none,
      		penwidth=2.0];
      	6	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=6,
      		pin=true,
      		pos="1,6!",
      		shape=circle,
      		style=filled,
      		width=1];
      	5 -> 6	 [arrowhead=none,
      		penwidth=2.0];
      	10	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=10,
      		pin=true,
      		pos="1,10!",
      		shape=circle,
      		style=filled,
      		width=1];
      	6 -> 10	 [arrowhead=none,
      		penwidth=2.0];
      	12	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=12,
      		pin=true,
      		pos="1,12!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	10 -> 12	 [arrowhead=none,
      		penwidth=2.0];
      	14	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=14,
      		pin=true,
      		pos="1,14!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	12 -> 14	 [arrowhead=none,
      		penwidth=2.0];
      	15	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=15,
      		pin=true,
      		pos="1,15!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	14 -> 15	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

In the mean time I noticed you can't buy animals in a super market and I prune the animal changeset:

  $ hg prune 3266db1117c9
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 5486682f4225
  1 changesets pruned
  1 new orphan changesets


The animals changeset is still displayed because the "SPAM SPAM SPAM" changeset
is neither dead or obsolete. My repository is in an unstable state again.

  $ hg log -G
  *  fff8c3d068b6 (draft): SPAM SPAM SPAM
  |
  x  3266db1117c9 (draft): animals
  |
  @  5486682f4225 (draft): bathroom stuff
  |
  o  501b33037995 (public): SPAM SPAM
  |
  o  d300c8f961ce (public): adding fruit
  |
  o  723e5a43d6d9 (public): adding condiment
  |
  o  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=4,
      		pin=true,
      		pos="1,4!",
      		shape=circle,
      		style=filled,
      		width=1];
      	0 -> 4	 [arrowhead=none,
      		penwidth=2.0];
      	5	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=5,
      		pin=true,
      		pos="1,5!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4 -> 5	 [arrowhead=none,
      		penwidth=2.0];
      	6	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=6,
      		pin=true,
      		pos="1,6!",
      		shape=circle,
      		style=filled,
      		width=1];
      	5 -> 6	 [arrowhead=none,
      		penwidth=2.0];
      	10	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=10,
      		pin=true,
      		pos="1,10!",
      		shape=circle,
      		style=filled,
      		width=1];
      	6 -> 10	 [arrowhead=none,
      		penwidth=2.0];
      	12	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=12,
      		pin=true,
      		pos="1,12!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	10 -> 12	 [arrowhead=none,
      		penwidth=2.0];
      	14	 [fillcolor="#DFDFFF",
      		fixedsize=true,
      		group=default_alt,
      		height=1,
      		label=14,
      		pin=true,
      		pos="2,14!",
      		shape=pentagon,
      		style="dotted, filled",
      		width=1];
      	12 -> 14	 [arrowhead=none,
      		penwidth=2.0];
      	15	 [fillcolor="#FF4F4F",
      		fixedsize=true,
      		group=default_alt,
      		height=1,
      		label=15,
      		pin=true,
      		pos="2,15!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	14 -> 15	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

  $ hg log -r "orphan()"
  fff8c3d068b6 (draft): SPAM SPAM SPAM

#if docgraph-ext
  $ hg docgraph -r "orphan()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	15	 [fillcolor="#FF4F4F",
      		fixedsize=true,
      		group=default_alt,
      		height=1,
      		label=15,
      		pin=true,
      		pos="1,15!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      }
#endif

The --update flag of `hg evolve` automatically updates to the tipmost evolved
changeset.

  $ hg evolve --update
  move:[15] SPAM SPAM SPAM
  atop:[12] bathroom stuff
  merging shopping
  working directory is now at c33e56ec23a8

  $ hg log -G
  @  c33e56ec23a8 (draft): SPAM SPAM SPAM
  |
  o  5486682f4225 (draft): bathroom stuff
  |
  o  501b33037995 (public): SPAM SPAM
  |
  o  d300c8f961ce (public): adding fruit
  |
  o  723e5a43d6d9 (public): adding condiment
  |
  o  9ca060c80d74 (public): SPAM
  |
  o  7e82d3f3c2cb (public): Monthy Python Shopping list
  

#if docgraph-ext
  $ hg docgraph -r "all()" --sphinx-directive --rankdir LR #rest-ignore
  .. graphviz::
  
      strict digraph "Mercurial graph" {
      	graph [rankdir=LR,
      		splines=polyline
      	];
      	node [label="\N"];
      	0	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=0,
      		pin=true,
      		pos="1,0!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=4,
      		pin=true,
      		pos="1,4!",
      		shape=circle,
      		style=filled,
      		width=1];
      	0 -> 4	 [arrowhead=none,
      		penwidth=2.0];
      	5	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=5,
      		pin=true,
      		pos="1,5!",
      		shape=circle,
      		style=filled,
      		width=1];
      	4 -> 5	 [arrowhead=none,
      		penwidth=2.0];
      	6	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=6,
      		pin=true,
      		pos="1,6!",
      		shape=circle,
      		style=filled,
      		width=1];
      	5 -> 6	 [arrowhead=none,
      		penwidth=2.0];
      	10	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=10,
      		pin=true,
      		pos="1,10!",
      		shape=circle,
      		style=filled,
      		width=1];
      	6 -> 10	 [arrowhead=none,
      		penwidth=2.0];
      	12	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=12,
      		pin=true,
      		pos="1,12!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	10 -> 12	 [arrowhead=none,
      		penwidth=2.0];
      	16	 [fillcolor="#7F7FFF",
      		fixedsize=true,
      		group=default,
      		height=1,
      		label=16,
      		pin=true,
      		pos="1,16!",
      		shape=pentagon,
      		style=filled,
      		width=1];
      	12 -> 16	 [arrowhead=none,
      		penwidth=2.0];
      }
#endif

Handling Divergent amend
----------------------------------------------

We can detect that multiple diverging amendments have been made.
The `evolve` command can solve this situation. But all corner case are not
handled now.

This section needs to be written.
