===============================================
Testing content-divergence resolution: Case A.2
===============================================

Independent rewrites of same changeset can lead to content-divergence. In most
common cases, it can occur when multiple users rewrite the same changeset
independently and push it.

This test belongs to a series of tests checking the resolution of content-divergent
changesets.

Category A: no parents are obsolete
Testcase 2: no conflict: both sides amended content changes (non-conflicting changes in same file)

A.2 both sides amended content changes
======================================

.. (Divergence reason):
..    local: amended some content changes in same file as "other" but non-conflicting
..    other: amended some content changes in same file as "local" but non-conflicting
.. Where we show that since both side amended some content changes without any relocation,
.. the most reasonable behaviour is to simply perform 3-way merge.
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
  $ setuprepos A.2
  creating test repo for test case A.2
  - upstream
  - local
  - other
  cd into `local` and proceed with env setup

initial

  $ cd local
  $ mkcommit A0
  $ hg push -q
  $ sed -i '1s/^/foo\n/' A0
  $ hg amend -m "A1"
  $ hg log -G --hidden
  @  2:e1f7c24563ba (draft): A1
  |
  | x  1:28b51eb45704 (draft): A0
  |/
  o  0:a9bdc8b26820 (public): O
  
  $ cd ../other
  $ hg pull -uq
  $ echo bar >> A0
  $ hg amend
  $ hg push -q

  $ cd ../local
  $ hg pull -q
  2 new content-divergent changesets

Actual test of resolution
-------------------------
  $ hg evolve -l
  e1f7c24563ba: A1
    content-divergent: 5fbe90f37421 (draft) (precursor 28b51eb45704)
  
  5fbe90f37421: A0
    content-divergent: e1f7c24563ba (draft) (precursor 28b51eb45704)
  
  $ hg log -G --hidden
  *  3:5fbe90f37421 (draft): A0 [content-divergent]
  |
  | @  2:e1f7c24563ba (draft): A1 [content-divergent]
  |/
  | x  1:28b51eb45704 (draft): A0
  |/
  o  0:a9bdc8b26820 (public): O
  

  $ hg evolve --content-divergent
  merge:[2] A1
  with: [3] A0
  base: [1] A0
  merging A0
  0 files updated, 1 files merged, 0 files removed, 0 files unresolved
  working directory is now at 414367a5568a

  $ hg log -Gp
  @  4:414367a5568a (draft): A1
  |  diff -r a9bdc8b26820 -r 414367a5568a A0
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/A0	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,3 @@
  |  +foo
  |  +A0
  |  +bar
  |
  o  0:a9bdc8b26820 (public): O
     diff -r 000000000000 -r a9bdc8b26820 O
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/O	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +O
  
  $ hg evolve -l
