====================================
Testing head checking code: Case E-1
====================================

Mercurial checks for the introduction of new heads on push. Evolution comes
into play to detect if existing branches on the server are being replaced by
some of the new one we push.

This case is part of a series of tests checking this behavior.

Category F: case involving changeset on multiple topic
TestCase 1: moving a branch to another location

.. old-state:
..
.. * 1-changeset on topic Y
.. * 1-changeset on topic Z (above Y)
..
.. new-state:
..
.. * 1-changeset on topic Y
.. * 1-changeset on topic Z (rebased away from A0)
..
.. expected-result:
..
.. * push allowed
..
.. graph-summary:
..
..   B ø⇠◔ B' topic Z
..     | |
..   A ◔ |    topic Y
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
  $ hg topic -r . Y
  switching to topic Y
  changed topic on 1 changesets to "Y"
  $ hg topic Z
  $ mkcommit B0
  active topic 'Z' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg push
  pushing to $TESTTMP/E1/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 1 changes to 2 files (+1 heads)
  1 new obsolescence markers
  obsoleted 1 changesets
  $ hg up 0
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg topic Z
  marked working directory as topic: Z
  $ mkcommit B1
  $ hg debugobsolete `getid "desc(B0)" ` `getid "desc(B1)"`
  1 new obsolescence markers
  obsoleted 1 changesets
  $ hg log -G --hidden
  @  845eeb768064 [default//Z] (draft): B1
  |
  | x  e1494106e1ca [default//Z] (draft): B0
  | |
  | o  f5cd873e2965 [default//Y] (draft): A0
  |/
  | x  8aaa48160adc [default] (draft): A0
  |/
  o  1e4be0697311 [default] (public): root
  

Actual testing
--------------

  $ hg push
  pushing to $TESTTMP/E1/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  1 new obsolescence markers
  obsoleted 1 changesets

  $ cd ../..
