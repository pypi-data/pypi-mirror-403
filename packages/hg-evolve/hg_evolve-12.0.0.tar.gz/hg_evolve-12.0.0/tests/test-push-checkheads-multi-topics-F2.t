====================================
Testing head checking code: Case E-2
====================================

Mercurial checks for the introduction of new heads on push. Evolution comes
into play to detect if existing branches on the server are being replaced by
some of the new one we push.

This case is part of a series of tests checking this behavior.

Category F: case involving changeset on multiple branch
TestCase 2: moving interleaved branch away from each other

.. old-state:
..
.. * 2-changeset on topic Y
.. * 1-changeset on topic Z (between the two other)
..
.. new-state:
..
.. * 2-changeset on topic Y, aligned
.. * 1-changeset on topic Z (at the same location)
..
.. expected-result:
..
.. * push allowed
..
.. graph-summary:
..
..   C ø⇠◔ C' topic Y
..     | |
..   B ◔ |    topic Z
..     | |
..   A ø⇠◔ A' topic Y
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
  $ hg strip --config extensions.strip= --hidden 'hidden()' # clean old A0
  saved backup bundle to $TESTTMP/E1/client/.hg/strip-backup/8aaa48160adc-19166392-backup.hg
  $ hg topic Z
  $ mkcommit B0
  active topic 'Z' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg topic Y
  $ mkcommit C0
  $ hg push
  pushing to $TESTTMP/E1/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 2 changes to 3 files (+1 heads)
  1 new obsolescence markers
  obsoleted 1 changesets
  $ hg up 0
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ hg topic Y
  marked working directory as topic: Y
  $ mkcommit A1
  $ mkcommit C1
  $ hg debugobsolete `getid "desc(A0)" ` `getid "desc(A1)"`
  1 new obsolescence markers
  obsoleted 1 changesets
  2 new orphan changesets
  $ hg debugobsolete `getid "desc(C0)" ` `getid "desc(C1)"`
  1 new obsolescence markers
  obsoleted 1 changesets
  $ hg log -G --hidden
  @  0e26ba57d799 [default//Y] (draft): C1
  |
  o  fb4a34222909 [default//Y] (draft): A1
  |
  | x  345721b128e8 [default//Y] (draft): C0
  | |
  | *  e1494106e1ca [default//Z] (draft): B0
  | |
  | x  f5cd873e2965 [default//Y] (draft): A0
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
