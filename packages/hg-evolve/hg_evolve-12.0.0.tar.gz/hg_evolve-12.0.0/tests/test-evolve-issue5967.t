hg evolve --continue and obsmarkers after conflict resolution with no changes to commit (issue5967)
https://bz.mercurial-scm.org/show_bug.cgi?id=5967

  $ . $TESTDIR/testlib/common.sh

  $ hg init issue5967
  $ cd issue5967
  $ cat > .hg/hgrc << EOF
  > [alias]
  > glog = log -GT "{rev}: {desc}"
  > [extensions]
  > evolve=
  > EOF

  $ echo apple > a
  $ hg ci -qAm 'apple'
  $ echo banana > a
  $ hg ci -m 'banana'

Amending revision 0 in a way that causes conflicts

  $ hg prev
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [0] apple
  $ echo apricot > a
  $ hg amend -m 'apricot'
  1 new orphan changesets

  $ hg glog
  @  2: apricot
  
  *  1: banana
  |
  x  0: apple
  

Trying to evolve, then manually discarding changes from revision 1

  $ hg evolve
  move:[1] banana
  atop:[2] apricot
  merging a
  warning: conflicts while merging a! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo apricot > a
  $ hg resolve --mark a
  (no more unresolved files)
  continue: hg evolve --continue

This will correctly notice that revision 1 can be dropped

  $ hg evolve --continue
  evolving 1:dd9b5dd30cd6 "banana"
  evolution of 1:dd9b5dd30cd6 created no changes to commit
  $ hg glog
  @  2: apricot
  

This is important: 1 should not have a successor (especially not revision 2)

  $ hg debugobsolete
  3ba7db0ce860a189d1fd1fd7675f0e871652ed16 4d6fec23dcc4c3e4ccce8b1d3b79f62ee927c2be 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  dd9b5dd30cd6b703d126d55b34165fd6ec5717c9 0 {3ba7db0ce860a189d1fd1fd7675f0e871652ed16} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  $ hg olog --all
  @  4d6fec23dcc4 (2) apricot
  |    rewritten(description, content) from 3ba7db0ce860 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  3ba7db0ce860 (0) apple
  
  $ hg olog --hidden --all 1
  x  dd9b5dd30cd6 (1) banana
       pruned using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  
