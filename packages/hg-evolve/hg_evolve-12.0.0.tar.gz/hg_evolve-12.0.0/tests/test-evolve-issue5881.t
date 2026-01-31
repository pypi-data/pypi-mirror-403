Test for issue 5881 present at https://bz.mercurial-scm.org/show_bug.cgi?id=5881
===============================================================================
which is about that if the working copy parent  is obsolete then evolve update
to its successor revision and stop; it doesn't continue to evolve remaining
revisions those were suppossed to evovle.

Setup
=====

  $ . $TESTDIR/testlib/common.sh

  $ cat >> $HGRCPATH <<EOF
  > [phases]
  > publish = False
  > [extensions]
  > evolve =
  > EOF

  $ hg init issue5881
  $ cd issue5881

Prepare the directory by creating an orphan and update to its obsolete parent:

  $ for ch in a b c; do echo $ch > $ch; hg ci -Am "added "$ch; done;
  adding a
  adding b
  adding c
  $ hg up 1 -q
  $ hg ci --amend -m "updated b"
  1 new orphan changesets
  $ hg up 1
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory parent is obsolete! (5f6d8a4bf34a)
  (use 'hg evolve' to update to its successor: e6048a693c0d)

  $ hg glog
  o  3:e6048a693c0d updated b
  |   () draft
  | *  2:155349b645be added c
  | |   () draft orphan
  | @  1:5f6d8a4bf34a added b
  |/    () draft
  o  0:9092f1db7931 added a
      () draft

Test `hg evolve` evolve all the revisions specified by user:
  $ hg evolve -r .::
  update:[3] updated b
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at e6048a693c0d
  move:[2] added c
  atop:[3] updated b
  working directory is now at e6048a693c0d
