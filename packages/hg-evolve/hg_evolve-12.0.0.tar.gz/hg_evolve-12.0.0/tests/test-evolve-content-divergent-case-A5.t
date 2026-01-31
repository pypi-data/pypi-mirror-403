===============================================
Testing content-divergence resolution: Case A.5
===============================================

Independent rewrites of same changeset can lead to content-divergence. In most
common cases, it can occur when multiple users rewrite the same changeset
independently and push it.

This test belongs to a series of tests checking the resolution of content-divergent
changesets.

Category A: no parents are obsolete
Testcase 5: one side relocated backward and other rebased to parent's successor
Variants:
# a: "local" is relocated backward
# b: "other" is relocated backward

A.5 Relocated backward; Rebased to parent's successor
=====================================================

.. (Divergence reason):
..    local: relocated the changeset backward in the graph
..    other: rebased to the successor of parent
.. Since one side rebased to the successor of parent and other cset relocated backward,
.. the most reasonable behaviour is to set the parent of "backward-relocated" cset
.. as resolution parent of divergence.
..
.. (local):
..
..      C ø⇠○ C'
..        | |
..      B ○ |
..        | /
..      A ○
..        |
..      O ●
..
.. (other):
..
..      C ø⇠○ C''
..        | |
..      B ø⇠○ B'
..        | /
..      A ○
..        |
..      O ●
..
.. (Resolution):
..
..   B'○  ○ C'''
..     | /
..   A ○
..     |
..   O ●
..

Setup
-----
  $ . $TESTDIR/testlib/content-divergence-util.sh
  $ setuprepos A.5
  creating test repo for test case A.5
  - upstream
  - local
  - other
  cd into `local` and proceed with env setup

initial

  $ cd upstream
  $ mkcommit A
  $ mkcommit B
  $ mkcommit C
  $ cd ../local
  $ hg pull -qu
  $ hg rebase -r 'desc(C)' -d 'desc(A)'
  rebasing 3:d90aa47aa5d3 tip "C"

  $ cd ../other
  $ hg pull -qu
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [2] B
  $ echo newB > B
  $ hg amend
  1 new orphan changesets
  $ hg next
  move:[3] C
  atop:[4] B
  working directory is now at f085ae420789
  $ hg push -q

  $ cd ../local
  $ hg push -fq
  2 new content-divergent changesets
  $ hg pull -q
  2 new content-divergent changesets


Actual test of resolution
-------------------------

Variant_a: when "local" is rebased backward
-------------------------------------------
  $ hg evolve -l
  b80b2bbeb664: C
    content-divergent: f085ae420789 (draft) (precursor d90aa47aa5d3)
  
  f085ae420789: C
    content-divergent: b80b2bbeb664 (draft) (precursor d90aa47aa5d3)
  
  $ hg log -G
  *  6:f085ae420789 (draft): C [content-divergent]
  |
  o  5:7db72af2e30d (draft): B
  |
  | @  4:b80b2bbeb664 (draft): C [content-divergent]
  |/
  o  1:f5bc6836db60 (draft): A
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve --content-divergent
  merge:[4] C
  with: [6] C
  base: [3] C
  rebasing "other" content-divergent changeset f085ae420789 on f5bc6836db60
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 88b737dc9dd8

  $ hg log -G
  @  8:88b737dc9dd8 (draft): C
  |
  | o  5:7db72af2e30d (draft): B
  |/
  o  1:f5bc6836db60 (draft): A
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve -l


Variant_b: when "other" is rebased backward
-------------------------------------------

  $ cd ../other
  $ hg pull -q
  2 new content-divergent changesets
  $ hg evolve -l
  f085ae420789: C
    content-divergent: b80b2bbeb664 (draft) (precursor d90aa47aa5d3)
  
  b80b2bbeb664: C
    content-divergent: f085ae420789 (draft) (precursor d90aa47aa5d3)
  
  $ hg log -G
  *  6:b80b2bbeb664 (draft): C [content-divergent]
  |
  | @  5:f085ae420789 (draft): C [content-divergent]
  | |
  | o  4:7db72af2e30d (draft): B
  |/
  o  1:f5bc6836db60 (draft): A
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve --content-divergent
  merge:[5] C
  with: [6] C
  base: [3] C
  rebasing "divergent" content-divergent changeset f085ae420789 on f5bc6836db60
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at fa4ff8bb3531

  $ hg log -G
  @  8:fa4ff8bb3531 (draft): C
  |
  | o  4:7db72af2e30d (draft): B
  |/
  o  1:f5bc6836db60 (draft): A
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve -l
