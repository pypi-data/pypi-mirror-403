===============================================
Testing content-divergence resolution: Case B.1
===============================================

Independent rewrites of same changeset can lead to content-divergence. In most
common cases, it can occur when multiple users rewrite the same changeset
independently and push it.

This test belongs to a series of tests checking the resolution of content-divergent
changesets.

Category B: parents are obsolete
Testcase 1: one side amended changes and other rebased to in-between successor of basep1
Variants:
# a: default resolution
# b: minimal resolution using `experimental.evolution.divergence-resolution-minimal=True`

B.1 Relocated backward; Rebased to parent's successor
=====================================================

.. (Divergence reason):
..    local: rebased to the 'in-between' successor of basep1
..    other: amended some changes
.. The default resolution here is that we choose the final successor as resolution parent,
.. but this behavior can be changed to use the 'in-between' successor as resolution parent
.. by using a config option `experimental.evolution.divergence-resolution-minimal=True`
..
.. This test case is considered complicated and can change its behavior acc. to the user
.. feedback. For more, please look at section 'D-A3.1' in troubles-handling.rst
..
.. (local):
..
..      B ø → ○ B'
..        |   |
..      A ø → ø A' → ○ A''
..        |   |      |
..        |----      |
..        |-----------
..        |
..      O ●
..
.. (other):
..
..      B ø→○ B'
..        | /
..      A ○
..        |
..      O ●
..
.. (Resolution):
..
..     ○ B'''
..     |
..     ○ A''
..     |
..     ● O
..

Setup
-----
  $ . $TESTDIR/testlib/content-divergence-util.sh
  $ setuprepos B.1
  creating test repo for test case B.1
  - upstream
  - local
  - other
  cd into `local` and proceed with env setup

initial

  $ cd upstream
  $ mkcommit A
  $ mkcommit B
  $ cd ../local
  $ hg pull -qu
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [1] A
  $ echo fooA >> A
  $ hg amend -m 'new_A'
  1 new orphan changesets
  $ hg evolve
  move:[2] B
  atop:[3] new_A
  $ echo barA >> A
  $ hg amend -m 'latest_A'
  1 new orphan changesets

  $ cd ../other
  $ hg pull -qu
  $ echo fooB > B
  $ hg amend -m 'new_B'
  $ hg push -q

  $ cd ../local
  $ hg push -fq
  2 new orphan changesets
  2 new content-divergent changesets
  $ hg pull -q
  1 new orphan changesets
  2 new content-divergent changesets


Actual test of resolution
-------------------------

Variant_a: default resolution
-----------------------------
  $ hg evolve -l
  429afd16ac76: B
    orphan: 1ffcccee011c (obsolete parent)
    content-divergent: 807cc2b37fb3 (draft) (precursor f6fbb35d8ac9)
  
  807cc2b37fb3: new_B
    orphan: f5bc6836db60 (obsolete parent)
    content-divergent: 429afd16ac76 (draft) (precursor f6fbb35d8ac9)
  
  $ hg log -G
  *  6:807cc2b37fb3 (draft): new_B [orphan content-divergent]
  |
  | @  5:45ed635c7cfc (draft): latest_A
  | |
  | | *  4:429afd16ac76 (draft): B [orphan content-divergent]
  | | |
  | | x  3:1ffcccee011c (draft): new_A
  | |/
  x |  1:f5bc6836db60 (draft): A
  |/
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve --content-divergent
  merge:[4] B
  with: [6] new_B
  base: [2] B
  rebasing "divergent" content-divergent changeset 429afd16ac76 on 45ed635c7cfc
  rebasing "other" content-divergent changeset 807cc2b37fb3 on 45ed635c7cfc
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ hg log -G
  o  9:55f09418c9b0 (draft): new_B
  |
  @  5:45ed635c7cfc (draft): latest_A
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve -l


Variant_b: minimal resolution
-----------------------------

  $ cd ../other
  $ hg pull -q
  2 new orphan changesets
  2 new content-divergent changesets
  $ hg evolve -l
  807cc2b37fb3: new_B
    orphan: f5bc6836db60 (obsolete parent)
    content-divergent: 429afd16ac76 (draft) (precursor f6fbb35d8ac9)
  
  429afd16ac76: B
    orphan: 1ffcccee011c (obsolete parent)
    content-divergent: 807cc2b37fb3 (draft) (precursor f6fbb35d8ac9)
  
  $ hg log -G
  o  6:45ed635c7cfc (draft): latest_A
  |
  | *  5:429afd16ac76 (draft): B [orphan content-divergent]
  | |
  | x  4:1ffcccee011c (draft): new_A
  |/
  | @  3:807cc2b37fb3 (draft): new_B [orphan content-divergent]
  | |
  | x  1:f5bc6836db60 (draft): A
  |/
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve --content-divergent --config experimental.evolution.divergence-resolution-minimal=True
  merge:[3] new_B
  with: [5] B
  base: [2] B
  rebasing "divergent" content-divergent changeset 807cc2b37fb3 on 1ffcccee011c
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 6b611864f3f6

  $ hg log -G
  @  8:6b611864f3f6 (draft): new_B [orphan]
  |
  | o  6:45ed635c7cfc (draft): latest_A
  | |
  x |  4:1ffcccee011c (draft): new_A
  |/
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve -l
  6b611864f3f6: new_B
    orphan: 1ffcccee011c (obsolete parent)
  
