Finding split successors for the correct ancestor (issue6648)
https://bz.mercurial-scm.org/show_bug.cgi?id=6648

  $ . $TESTDIR/testlib/common.sh

  $ cat << EOF >> $HGRCPATH
  > [extensions]
  > evolve =
  > EOF

  $ hg init issue6648
  $ cd issue6648

  $ echo hi > foo
  $ hg commit -qAm 'r0'
  $ echo foo >> foo
  $ echo foo >> foosplit
  $ hg commit -qAm 'r1_splitme'
  $ echo bar > bar
  $ hg commit -qAm 'r2_obsoleteme'
  $ echo baz > baz
  $ hg commit -qAm 'r3'

  $ hg prune -r 2
  1 changesets pruned
  1 new orphan changesets
  $ hg split -r 1 --no-interactive foosplit
  1 files updated, 0 files merged, 3 files removed, 0 files unresolved
  reverting foo
  adding foosplit
  created new head
  no more changes to split

  $ hg update -r 2
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory parent is obsolete! (5c9b6cf2edc5)
  (use 'hg evolve' to update to its parent successor)

  $ hg log -G
  o  changeset:   5:983ec6453b57
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     r1_splitme
  |
  o  changeset:   4:9ca7a4996099
  |  parent:      0:e9326971c0ba
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     r1_splitme
  |
  | *  changeset:   3:c1e686af368d
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  instability: orphan
  | |  summary:     r3
  | |
  | @  changeset:   2:5c9b6cf2edc5
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  obsolete:    pruned using prune
  | |  summary:     r2_obsoleteme
  | |
  | x  changeset:   1:acdff8eea54c
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    split using split as 4:9ca7a4996099, 5:983ec6453b57
  |    summary:     r1_splitme
  |
  o  changeset:   0:e9326971c0ba
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     r0
  

handling obsolete wdp works

  $ hg evolve
  update:[5] r1_splitme
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at 983ec6453b57

stabilizing the orphan works

  $ hg evolve
  move:[3] r3
  atop:[5] r1_splitme
