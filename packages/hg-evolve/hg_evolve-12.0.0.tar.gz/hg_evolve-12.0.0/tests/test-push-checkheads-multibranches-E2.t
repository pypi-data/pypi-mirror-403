====================================
Testing head checking code: Case E-2
====================================

Mercurial checks for the introduction of new heads on push. Evolution comes
into play to detect if existing branches on the server are being replaced by
some of the new one we push.

This case is part of a series of tests checking this behavior.

Category E: case involving changeset on multiple branch
TestCase 8: moving interleaved branch away from each other

.. old-state:
..
.. * 2-changeset on branch default
.. * 1-changeset on branch double//slash (between the two other)
..
.. new-state:
..
.. * 2-changeset on branch default, aligned
.. * 1-changeset on branch double//slash (at the same location)
..
.. expected-result:
..
.. * push allowed
..
.. graph-summary:
..
..   C ø⇠◔ C'
..     | |
..   B ◔ |
..     | |
..   A ø⇠◔ A'
..     |/
..     ●

  $ . $TESTDIR/testlib/topic_setup.sh
  $ . $TESTDIR/testlib/push-checkheads-util.sh

Test setup
----------

  $ mkdir E1
  $ cd E1
  $ setuprepos
  creating basic server and client repo
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client
  $ hg branch double//slash
  marked working directory as branch double//slash
  (branches are permanent and global, did you want a bookmark?)
  $ mkcommit B0
  $ hg branch default --force
  marked working directory as branch default
  $ mkcommit C0
  created new head
  (consider using topic for lightweight branches. See 'hg help topic')
  $ hg push --new-branch
  pushing to $TESTTMP/E1/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  $ hg up 0
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ mkcommit A1
  created new head
  (consider using topic for lightweight branches. See 'hg help topic')
  $ mkcommit C1
  $ hg debugobsolete `getid "desc(A0)" ` `getid "desc(A1)"`
  1 new obsolescence markers
  obsoleted 1 changesets
  2 new orphan changesets
  $ hg debugobsolete `getid "desc(C0)" ` `getid "desc(C1)"`
  1 new obsolescence markers
  obsoleted 1 changesets
  $ hg log -G --hidden
  @  0c76bc104656 [default] (draft): C1
  |
  o  f6082bc4ffef [default] (draft): A1
  |
  | x  c7f1f02ffefc [default] (draft): C0
  | |
  | *  1fd532b11e77 [double//slash] (draft): B0
  | |
  | x  8aaa48160adc [default] (draft): A0
  |/
  o  1e4be0697311 [default] (public): root
  

Actual testing
--------------

  $ hg push -r 'desc("C1")'
  pushing to $TESTTMP/E1/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files (+1 heads)
  2 new obsolescence markers
  obsoleted 2 changesets
  1 new orphan changesets

  $ cd ../..
