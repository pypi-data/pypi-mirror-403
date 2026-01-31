===============================================
Testing content-divergence resolution: Case A.4
===============================================

Independent rewrites of same changeset can lead to content-divergence. In most
common cases, it can occur when multiple users rewrite the same changeset
independently and push it.

This test belongs to a series of tests checking the resolution of content-divergent
changesets.

Category A: no parents are obsolete
Testcase 4: both sides relocated forward to different location but aligned
Variants:
# a: local is ahead of other
# b: other is ahead of local

A.4 Both relocated forward
==========================

.. (Divergence reason):
..    local: relocated the changeset forward in the graph but on the same topo branch
..    other: relocated the changeset forward in the graph but on the same topo branch
.. Where we show that since both changesets relocated forward in the graph,
.. we can assume the reason for ahead one being ahead is that it's rebased on the latest changes and
.. its parent should be the resolution parent. So, we will relocate the other changeset to resolution
.. parent and perform 3-way merge.
..
.. (local):
..
..    D ø⇠○ D'
..      | |
..      | ○ C
..      | |
..      | ○ B
..      \ |
..        ○ A
..        |
..        ● O
..
.. (other):
..
..    D ø⇠○ D''
..      | |  ○ C
..      | | /
..      | ○ B
..      \ |
..        ○ A
..        |
..        ● O
..
.. (Resolution):
..     ○ D'''
..     |
..     ○ C
..     |
..     ○ B
..     |
..     ○ A
..     |
..     ● O
..

Setup
-----
  $ . $TESTDIR/testlib/content-divergence-util.sh
  $ setuprepos A.4
  creating test repo for test case A.4
  - upstream
  - local
  - other
  cd into `local` and proceed with env setup

initial

  $ cd upstream
  $ mkcommit A
  $ mkcommit B
  $ mkcommit C
  $ hg co -r 'desc(A)'
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ mkcommit D
  created new head
  $ cd ../local
  $ hg pull -qu
  $ hg rebase -r 'desc(D)' -d 'desc(C)'
  rebasing 4:6a418860e87b tip "D"

  $ cd ../other
  $ hg pull -qu
  $ hg rebase -r 'desc(D)' -d 'desc(B)'
  rebasing 4:6a418860e87b tip "D"
  $ hg push -q

  $ cd ../local
  $ hg push -q
  2 new content-divergent changesets
  $ hg pull -q
  2 new content-divergent changesets

Actual test of resolution
-------------------------

Variant_a: when local is ahead of other
---------------------------------------

  $ hg evolve -l
  d203ddccc9cc: D
    content-divergent: 5d3fd66cb347 (draft) (precursor 6a418860e87b)
  
  5d3fd66cb347: D
    content-divergent: d203ddccc9cc (draft) (precursor 6a418860e87b)
  
  $ hg log -G --hidden
  *  6:5d3fd66cb347 (draft): D [content-divergent]
  |
  | @  5:d203ddccc9cc (draft): D [content-divergent]
  | |
  | | x  4:6a418860e87b (draft): D
  | | |
  | o |  3:d90aa47aa5d3 (draft): C
  |/ /
  o /  2:f6fbb35d8ac9 (draft): B
  |/
  o  1:f5bc6836db60 (draft): A
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve --content-divergent
  merge:[5] D
  with: [6] D
  base: [4] D
  rebasing "other" content-divergent changeset 5d3fd66cb347 on d90aa47aa5d3
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 898f6bbfb21e

  $ hg log -G
  @  8:898f6bbfb21e (draft): D
  |
  o  3:d90aa47aa5d3 (draft): C
  |
  o  2:f6fbb35d8ac9 (draft): B
  |
  o  1:f5bc6836db60 (draft): A
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve -l

Variant_b: when other is ahead of local
---------------------------------------

  $ cd ../other
  $ hg pull -q
  2 new content-divergent changesets

  $ hg evolve -l
  5d3fd66cb347: D
    content-divergent: d203ddccc9cc (draft) (precursor 6a418860e87b)
  
  d203ddccc9cc: D
    content-divergent: 5d3fd66cb347 (draft) (precursor 6a418860e87b)
  
  $ hg log -G --hidden
  *  6:d203ddccc9cc (draft): D [content-divergent]
  |
  | @  5:5d3fd66cb347 (draft): D [content-divergent]
  | |
  | | x  4:6a418860e87b (draft): D
  | | |
  o | |  3:d90aa47aa5d3 (draft): C
  |/ /
  o /  2:f6fbb35d8ac9 (draft): B
  |/
  o  1:f5bc6836db60 (draft): A
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve --content-divergent
  merge:[5] D
  with: [6] D
  base: [4] D
  rebasing "divergent" content-divergent changeset 5d3fd66cb347 on d90aa47aa5d3
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at b2ef9cafa8ac

  $ hg log -G
  @  8:b2ef9cafa8ac (draft): D
  |
  o  3:d90aa47aa5d3 (draft): C
  |
  o  2:f6fbb35d8ac9 (draft): B
  |
  o  1:f5bc6836db60 (draft): A
  |
  o  0:a9bdc8b26820 (public): O
  
