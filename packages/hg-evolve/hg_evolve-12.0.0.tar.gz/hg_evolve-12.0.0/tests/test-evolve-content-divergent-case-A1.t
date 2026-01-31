===============================================
Testing content-divergence resolution: Case A.1
===============================================

Independent rewrites of same changeset can lead to content-divergence. In most
common cases, it can occur when multiple users rewrite the same changeset
independently and push it.

This test belongs to a series of tests checking the resolution of content-divergent
changesets.

Category A: no parents are obsolete
Testcase 1: no conflict: independent metadata changes only

A.1 No content changes on any side
==================================

.. (Divergence reason):
..    local: changed the description of changeset
..    other: changed the date of changeset
.. Where we show that since there is no content change in divergent changesets
.. we should only merge the metadata of changesets in a 3-way merge
..
.. (local):
..
..   A ø⇠○ A'
..     |/
..     ● O
..
.. (other):
..
..   A ø⇠○ A''
..     |/
..     ● O
..
.. (Resolution):
..
..     ○ A'''
..     |
..     ● O
..

Setup
-----
  $ . $TESTDIR/testlib/content-divergence-util.sh
  $ setuprepos A.1
  creating test repo for test case A.1
  - upstream
  - local
  - other
  cd into `local` and proceed with env setup

initial

  $ cd local
  $ mkcommit A0
  $ hg push -q
  $ hg amend -m "A1"
  $ hg log -G --hidden
  @  2:0d8c87cec5fc (draft): A1
  |
  | x  1:28b51eb45704 (draft): A0
  |/
  o  0:a9bdc8b26820 (public): O
  
  $ cd ../other
  $ hg pull -uq
  $ hg amend -d '0 1'
  $ hg push -q

  $ cd ../local
  $ hg pull -q
  2 new content-divergent changesets

Actual test of resolution
-------------------------
  $ hg evolve -l
  0d8c87cec5fc: A1
    content-divergent: ece7459c388a (draft) (precursor 28b51eb45704)
  
  ece7459c388a: A0
    content-divergent: 0d8c87cec5fc (draft) (precursor 28b51eb45704)
  
  $ hg log -G --hidden
  *  3:ece7459c388a (draft): A0 [content-divergent]
  |
  | @  2:0d8c87cec5fc (draft): A1 [content-divergent]
  |/
  | x  1:28b51eb45704 (draft): A0
  |/
  o  0:a9bdc8b26820 (public): O
  

  $ hg evolve --content-divergent
  merge:[2] A1
  with: [3] A0
  base: [1] A0
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 36c6c1f70ad9

  $ hg log -G
  @  4:36c6c1f70ad9 (draft): A1
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve -l
