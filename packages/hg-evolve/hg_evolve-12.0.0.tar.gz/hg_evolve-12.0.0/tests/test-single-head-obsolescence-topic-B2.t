=========================================
Testing single head enforcement: Case B-2
=========================================

A repository is set to only accept a single head per name (typically named
branch). However, obsolete changesets can make this enforcement more
complicated, because they can be kept visible by other changeset on other
branch.

This case is part of a series of tests checking this behavior.

Category B: Involving obsolescence with topic
TestCase 2: A branch is split in two, effectively creating two heads

.. old-state:
..
.. * 2 changesets on topic X
.. * 2 changesets on topic Y on top of them.
..
.. new-state:
..
.. * 2 changesets on topic Y at the same location
.. * 1 changeset on topic X unchanged
.. * 1 changeset on topic X superseding the other ones
..
.. expected-result:
..
.. * two heads detected
..
.. graph-summary:
..
..   D ●      (topic-Y)
..     |
..   C ●      (topic-Y)
..     |
..   B ø⇠◔ B' (topic-X)
..     | |
..   A ● |    (topic-X)
..     |/
..     ●

  $ . $TESTDIR/testlib/topic_setup.sh
  $ . $TESTDIR/testlib/push-checkheads-util.sh

Test setup
----------

  $ mkdir B2
  $ cd B2
  $ setuprepos single-head
  creating basic server and client repo
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client
  $ hg topic -r . topic-X
  switching to topic topic-X
  changed topic on 1 changesets to "topic-X"
  $ hg strip --config extensions.strip= --hidden 'hidden()' --no-backup # clean old A0
  $ mkcommit B0
  $ hg branch double//slash
  marked working directory as branch double//slash
  $ hg topic topic-Y
  $ mkcommit C0
  active topic 'topic-Y' grew its first changeset
  (see 'hg help topics' for more information)
  $ mkcommit D0
  $ hg push --new-branch
  pushing to $TESTTMP/B2/server
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
  $ mkcommit B1
  $ hg debugobsolete `getid "desc(B0)"` `getid "desc(B1)"`
  1 new obsolescence markers
  obsoleted 1 changesets
  2 new orphan changesets
  $ hg log -G --hidden
  @  5a4735b75167 [default//topic-X] (draft): B1
  |
  | *  3fd0fd6ca824 [double//slash//topic-Y] (draft): D0
  | |
  | *  5997ab5a8285 [double//slash//topic-Y] (draft): C0
  | |
  | x  1c1f62b56685 [default//topic-X] (draft): B0
  | |
  | o  5a47a98cd8e5 [default//topic-X] (draft): A0
  |/
  o  1e4be0697311 [default] (public): root
  

Actual testing
--------------

(force push to make sure we get the changeset on the remote)

  $ hg push -r 'desc("B1")' --force
  pushing to $TESTTMP/B2/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  transaction abort!
  rollback completed
  abort: rejecting multiple heads on branch "default//topic-X"
  (2 heads: 5a47a98cd8e5 5a4735b75167)
  [255]
