=========================================
Testing single head enforcement: Case B-3
=========================================

A repository is set to only accept a single head per name (typically named
branch). However, obsolete changesets can make this enforcement more
complicated, because they can be kept visible by other changeset on other
branch.

This case is part of a series of tests checking this behavior.

Category B: Involving obsolescence with topic
TestCase 3: Full superseding of a branch interleaved with another

.. old-state:
..
.. * 2 changesets on topic Y
.. * 2 changesets on topic X interleaved with the other
..
.. new-state:
..
.. * 2 changesets on topic X at the same location
.. * 2 changesets on topic Y superseding the other ones
..
.. expected-result:
..
.. * only one head detected
..
.. graph-summary:
..
..   D ●      (topic-Y)
..     |
..   C ø⇠◔ C' (topix-X)
..     | |
..   B ● |    (topic-Y)
..     | |
..   A ø⇠◔ A' (topic-X)
..     |/
..     ●

  $ . $TESTDIR/testlib/topic_setup.sh
  $ . $TESTDIR/testlib/push-checkheads-util.sh

Test setup
----------

  $ mkdir B3
  $ cd B3
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
  pushing to $TESTTMP/B3/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 3 changes to 4 files (+1 heads)
  1 new obsolescence markers
  obsoleted 1 changesets
  $ hg up 0
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  $ hg topic topic-X
  marked working directory as topic: topic-X
  $ mkcommit A1
  $ mkcommit C1
  $ hg debugobsolete `getid "desc(A0)"` `getid "desc(A1)"`
  1 new obsolescence markers
  obsoleted 1 changesets
  3 new orphan changesets
  $ hg debugobsolete `getid "desc(C0)"` `getid "desc(C1)"`
  1 new obsolescence markers
  obsoleted 1 changesets
  $ hg log -G --hidden
  @  9f6e6381b9aa [default//topic-X] (draft): C1
  |
  o  c1340bef453e [default//topic-X] (draft): A1
  |
  | *  850d57e10bfe [default//topic-Y] (draft): D0
  | |
  | x  fcdd583577e8 [default//topic-X] (draft): C0
  | |
  | *  030eec7a0fe2 [default//topic-Y] (draft): B0
  | |
  | x  5a47a98cd8e5 [default//topic-X] (draft): A0
  |/
  o  1e4be0697311 [default] (public): root
  

Actual testing
--------------

  $ hg push -r 'desc("C1")'
  pushing to $TESTTMP/B3/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files (+1 heads)
  2 new obsolescence markers
  obsoleted 2 changesets
  2 new orphan changesets
