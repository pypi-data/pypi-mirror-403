This test file test the #6028 issue

evolve fails with mercurial.error.ProgrammingError: unsupported changeid '' of type <type 'str'>

https://bz.mercurial-scm.org/show_bug.cgi?id=6028

Global setup
============

  $ . $TESTDIR/testlib/common.sh
  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > interactive = true
  > [phases]
  > publish=False
  > [extensions]
  > evolve =
  > topic =
  > EOF

Test
====

  $ hg init $TESTTMP/issue-6028
  $ cd $TESTTMP/issue-6028

create initial commit

  $ echo "0" > 0
  $ hg ci -Am 0
  adding 0

start new topics "a" and "b" both from 0

  $ hg up default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg topics a
  marked working directory as topic: a
  $ echo "a" > a
  $ hg ci -Am a
  adding a
  active topic 'a' grew its first changeset
  (see 'hg help topics' for more information)

  $ hg up default
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg topics b
  marked working directory as topic: b
  $ echo "b" > b
  $ hg ci -Am b
  adding b
  active topic 'b' grew its first changeset
  (see 'hg help topics' for more information)

create branch "integration" from 0, merge topics "a" and "b" into it

  $ hg up default
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg branch integration
  marked working directory as branch integration

  $ hg merge a
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "merged a"

  $ hg merge b
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "merged b"

commit a bad file on topic "a", merge it into "integration"

  $ hg up a
  switching to topic a
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo "a bad commit" >> a_bad_commit
  $ hg add a_bad_commit
  $ hg ci -m "a bad commit"
  $ hg up integration
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg merge a
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "merged a bad commit"

add more commits on both topics and merge them into "integration"

  $ hg up a
  switching to topic a
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo "aa" >> a
  $ hg ci -m "aa"
  $ hg up integration
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg merge a
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "merged aa"

  $ hg up b
  switching to topic b
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo "bb" >> b
  $ hg ci -m "bb"
  $ hg up integration
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg merge b
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "merged bb"

create instability by pruning two changesets, one in a topic, one a merge

  $ hg log -r 5:6 -T '{rev}: {desc}\n'
  5: a bad commit
  6: merged a bad commit

  $ hg prune -r 5:6
  2 changesets pruned
  3 new orphan changesets

  $ hg up 4
  2 files updated, 0 files merged, 1 files removed, 0 files unresolved

start the evolve

  $ hg evolve --update --no-all
  move:[8] merged aa
  atop:[4] merged b
  working directory is now at c920dd828523

checking that we didn't write an empty topic file when relocating the commit on disk

  $ test -f .hg/topic
  [1]

casually checking issue6141: position of p2 is not changed

  $ hg log -r 'predecessors(.) + .'
  changeset:   8:3f6f25057afb
  branch:      integration
  parent:      6:cfc4c333724f
  parent:      7:61eff7f7bb6c
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    rebased using evolve as 11:c920dd828523
  summary:     merged aa
  
  changeset:   11:c920dd828523
  branch:      integration
  tag:         tip
  parent:      4:e33aee2c715e
  parent:      7:61eff7f7bb6c
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  instability: orphan
  summary:     merged aa
  

test that we successfully got rid of the bad file

  $ hg diff --git -r 'predecessors(.)' -r '.'
  diff --git a/a_bad_commit b/a_bad_commit
  deleted file mode 100644
  --- a/a_bad_commit
  +++ /dev/null
  @@ -1,1 +0,0 @@
  -a bad commit

evolve creates an obsolete changeset above as 11

  $ hg evolve -l
  61eff7f7bb6c: aa
    orphan: 487c225d33af (obsolete parent)
  
  2b5a7b3298d9: merged bb
    orphan: 3f6f25057afb (obsolete parent)
  
  c920dd828523: merged aa
    orphan: 61eff7f7bb6c (orphan parent)
  
  $ hg evolve -r .
  skipping c920dd828523, consider including orphan ancestors

test that the suggestion works

  $ hg evolve -r 'parents(".")::'
  move:[7] aa
  atop:[1] a
  switching to topic a
  move:[11] merged aa
  move:[10] merged bb
  working directory is now at bdbfa73836d6

  $ hg evolve -l
