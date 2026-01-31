=========================================
Testing single head enforcement: Case B-5
=========================================

A repository is set to only accept a single head per name (typically named
branch). However, obsolete changesets can make this enforcement more
complicated, because they can be kept visible by other changeset on other
branch.

This case is part of a series of tests checking this behavior.

Category B: Involving obsolescence with topic
TestCase 5: Obsoleting a merge reveals two heads

.. old-state:
..
.. * 3 changesets on topic X (2 on their own branch + 1 merge)
.. * 1 changeset on topic Y (child of the merge)
..
.. new-state:
..
.. * 2 changesets on topic X (merge is obsolete) each a head
.. * 1 changeset on topic Y keeping the merge visible
..
.. expected-result:
..
.. * 2 heads detected (because we skip the merge).
..
.. graph-summary:
..
..   C ●      (topic-Y)
..     |
..   M ⊗      (topic-X)
..     |\
..   A ● ● B  (topic-X)
..     |/
..     ●

  $ . $TESTDIR/testlib/topic_setup.sh
  $ . $TESTDIR/testlib/push-checkheads-util.sh

Test setup
----------

  $ mkdir B5
  $ cd B5
  $ setuprepos single-head
  creating basic server and client repo
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client
  $ hg topic -r . topic-X
  switching to topic topic-X
  changed topic on 1 changesets to "topic-X"
  $ hg strip --config extensions.strip= --hidden 'hidden()' --no-backup # clean old A0
  $ hg up 0
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg topic topic-X
  marked working directory as topic: topic-X
  $ mkcommit B0
  $ hg merge
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m 'M0'
  $ hg topic topic-Y
  $ mkcommit C0
  active topic 'topic-Y' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg push --new-branch
  pushing to $TESTTMP/B5/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 2 changes to 3 files (+1 heads)
  1 new obsolescence markers
  obsoleted 1 changesets
  $ hg up 0
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ mkcommit A1
  $ mkcommit B1
  $ hg debugobsolete `getid "desc(M0)"` --record-parents
  1 new obsolescence markers
  obsoleted 1 changesets
  1 new orphan changesets
  $ hg log -G --hidden
  @  262c8c798096 [default] (draft): B1
  |
  o  f6082bc4ffef [default] (draft): A1
  |
  | *  339fd31549ed [default//topic-Y] (draft): C0
  | |
  | x    33b3d4185449 [default//topic-X] (draft): M0
  | |\
  +---o  d3826ff42cf7 [default//topic-X] (draft): B0
  | |
  | o  5a47a98cd8e5 [default//topic-X] (draft): A0
  |/
  o  1e4be0697311 [default] (public): root
  

Actual testing
--------------

(force push to make sure we get the changeset on the remote)

  $ hg push -r 'desc("C0")' --force
  pushing to $TESTTMP/B5/server
  searching for changes
  no changes found
  transaction abort!
  rollback completed
  abort: rejecting multiple heads on branch "default//topic-X"
  (2 heads: 5a47a98cd8e5 d3826ff42cf7)
  [255]
