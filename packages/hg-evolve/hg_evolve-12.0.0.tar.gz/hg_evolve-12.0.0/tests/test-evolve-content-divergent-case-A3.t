===============================================
Testing content-divergence resolution: Case A.3
===============================================

Independent rewrites of same changeset can lead to content-divergence. In most
common cases, it can occur when multiple users rewrite the same changeset
independently and push it.

This test belongs to a series of tests checking the resolution of content-divergent
changesets.

Category A: no parents are obsolete
Testcase 3: one side relocated forward and other amended content changes
Variants:
# a: "local" is rebased forward
# b: "other" is rebased forward

A.3 Relocated forward; other side amended content changes
=========================================================

.. (Divergence reason):
..    local: relocated the changeset forward in the graph
..    other: amended some content changes
.. Where we show that since one side amended some changes and other just relocated,
.. the most reasonable behaviour is to relocate the amended one to the same parent as
.. relocated one and perform 3-way merge.
..
.. (local):
..
..    C ø⇠○ C'
..      | |
..      | ○ B
..      \ |
..        ○ A
..        |
..        ● O
..
.. (other):
..
..      C ø⇠○ C''
..        | |
..   B ○  | |
..      \ | /
..      A ○
..        |
..        ● O
..
.. (Resolution):
..
..     ○ C'''
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
  $ setuprepos A.3
  creating test repo for test case A.3
  - upstream
  - local
  - other
  cd into `local` and proceed with env setup

initial

  $ cd upstream
  $ mkcommit A
  $ mkcommit B
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [1] A
  $ mkcommit C
  created new head
  $ cd ../local
  $ hg pull -qu
  $ hg rebase -r 'desc(C)' -d 'desc(B)'
  rebasing 3:928c8849ec01 tip "C"

  $ cd ../other
  $ hg pull -qu
  $ echo newC > C
  $ hg amend
  $ hg push -q

  $ cd ../local
  $ hg push -fq
  2 new content-divergent changesets
  $ hg pull -q
  2 new content-divergent changesets

Actual test of resolution
-------------------------

Variant_a: when "local" is rebased forward
------------------------------------------
  $ hg evolve -l
  384129981c4b: C
    content-divergent: 710d96992b40 (draft) (precursor 928c8849ec01)
  
  710d96992b40: C
    content-divergent: 384129981c4b (draft) (precursor 928c8849ec01)
  
  $ hg log -G --hidden
  *  5:710d96992b40 (draft): C [content-divergent]
  |
  | @  4:384129981c4b (draft): C [content-divergent]
  | |
  +---x  3:928c8849ec01 (draft): C
  | |
  | o  2:f6fbb35d8ac9 (draft): B
  |/
  o  1:f5bc6836db60 (draft): A
  |
  o  0:a9bdc8b26820 (public): O
  

  $ hg evolve --content-divergent
  merge:[4] C
  with: [5] C
  base: [3] C
  rebasing "other" content-divergent changeset 710d96992b40 on f6fbb35d8ac9
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at b341bfa8675e

  $ hg log -G
  @  7:b341bfa8675e (draft): C
  |
  o  2:f6fbb35d8ac9 (draft): B
  |
  o  1:f5bc6836db60 (draft): A
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg log -pl 1
  7:b341bfa8675e (draft): C 
  diff -r f6fbb35d8ac9 -r b341bfa8675e C
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/C	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +newC
  
  $ hg evolve -l

Variant_b: when "other" is rebased forward
------------------------------------------

  $ cd ../other
  $ hg pull -q
  2 new content-divergent changesets
  $ hg evolve -l
  710d96992b40: C
    content-divergent: 384129981c4b (draft) (precursor 928c8849ec01)
  
  384129981c4b: C
    content-divergent: 710d96992b40 (draft) (precursor 928c8849ec01)
  
  $ hg log -G --hidden
  *  5:384129981c4b (draft): C [content-divergent]
  |
  | @  4:710d96992b40 (draft): C [content-divergent]
  | |
  | | x  3:928c8849ec01 (draft): C
  | |/
  o |  2:f6fbb35d8ac9 (draft): B
  |/
  o  1:f5bc6836db60 (draft): A
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve --content-divergent
  merge:[4] C
  with: [5] C
  base: [3] C
  rebasing "divergent" content-divergent changeset 710d96992b40 on f6fbb35d8ac9
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 0de314083dd2

  $ hg log -G
  @  7:0de314083dd2 (draft): C
  |
  o  2:f6fbb35d8ac9 (draft): B
  |
  o  1:f5bc6836db60 (draft): A
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve -l

  $ hg log -pl1
  7:0de314083dd2 (draft): C 
  diff -r f6fbb35d8ac9 -r 0de314083dd2 C
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/C	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +newC
  
