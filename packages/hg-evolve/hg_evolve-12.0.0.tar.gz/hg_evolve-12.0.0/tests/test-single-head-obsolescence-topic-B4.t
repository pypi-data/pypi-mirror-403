=========================================
Testing single head enforcement: Case B-4
=========================================

A repository is set to only accept a single head per name (typically named
branch). However, obsolete changesets can make this enforcement more
complicated, because they can be kept visible by other changeset on other
branch.

This case is part of a series of tests checking this behavior.

Category B: Involving obsolescence with topic
TestCase 4: Partial rewrite of a branch to dis-interleave it

.. old-state:
..
.. * 2 changesets on topic X
.. * 2 changesets on topic Y interleaved with the other one
..
.. new-state:
..
.. * 2 changesets on topic Y at the same location
.. * 1 changeset on topic X untouched (the lower one)
.. * 1 changeset on topic X moved on the other one
..
.. expected-result:
..
.. * only one head detected
..
.. graph-summary:
..
..   D ●      (topic-Y)
..     |
..   C ø⇠◔ C' (topic-X)
..     | |
..   B ● |    (topic-Y)
..     |/
..   A ●      (topic-X)
..     |
..     ●

  $ . $TESTDIR/testlib/topic_setup.sh
  $ . $TESTDIR/testlib/push-checkheads-util.sh

Test setup
----------

  $ mkdir B4
  $ cd B4
  $ setuprepos single-head
  creating basic server and client repo
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client
  $ hg topic -r . topic-X
  switching to topic topic-X
  changed topic on 1 changesets to "topic-X"
  $ hg strip --config extensions.strip= --hidden 'hidden()' --no-backup # clean old A0
  $ hg topic topic-Y
  $ mkcommit B0
  active topic 'topic-Y' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg topic topic-X
  $ mkcommit C0
  $ hg topic topic-Y
  $ mkcommit D0
  $ hg push --new-branch
  pushing to $TESTTMP/B4/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 3 changes to 4 files (+1 heads)
  1 new obsolescence markers
  obsoleted 1 changesets
  $ hg up 'desc("A0")'
  switching to topic topic-X
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ hg topic topic-X
  $ mkcommit C1
  $ hg debugobsolete `getid "desc(C0)"` `getid "desc(C1)"`
  1 new obsolescence markers
  obsoleted 1 changesets
  1 new orphan changesets
  $ hg log -G --hidden
  @  b98a8bd4ca39 [default//topic-X] (draft): C1
  |
  | *  850d57e10bfe [default//topic-Y] (draft): D0
  | |
  | x  fcdd583577e8 [default//topic-X] (draft): C0
  | |
  | o  030eec7a0fe2 [default//topic-Y] (draft): B0
  |/
  o  5a47a98cd8e5 [default//topic-X] (draft): A0
  |
  o  1e4be0697311 [default] (public): root
  

Actual testing
--------------

(force push to make sure we get the changeset on the remote)

  $ hg push -r 'desc("C1")' --force
  pushing to $TESTTMP/B4/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  1 new obsolescence markers
  obsoleted 1 changesets
  1 new orphan changesets
