Orphan changeset and trying to relocate a node on top of itself (issue6097)
https://bz.mercurial-scm.org/show_bug.cgi?id=6097

  $ . $TESTDIR/testlib/common.sh

  $ cat << EOF >> $HGRCPATH
  > [extensions]
  > rebase =
  > evolve =
  > EOF

  $ hg init issue6097
  $ cd issue6097

  $ echo apricot > a
  $ hg ci -qAm apricot

  $ echo banana > b
  $ hg ci -qAm banana

Let's go back to amend 0 and make an orphan out of 1

  $ hg up -q 0
  $ echo coconut > c
  $ hg add -q c
  $ hg ci --amend -m 'apricot and coconut'
  1 new orphan changesets

Now rebase the successor of 0 on top of 1

  $ hg rebase -r . -d 1
  rebasing 2:32acf8fb1b23 tip "apricot and coconut"
  1 new orphan changesets

Pruning 1 just to get it out of the way

  $ hg prune -q 1

Note how both the regular DAG and the obsolescence graph are linear, but the
paths from 3 to 0 are different: 3-1-0 and 3-2-0

  $ hg log -G
  @  changeset:   3:2868fe6df617
  |  tag:         tip
  |  parent:      1:e0486f65907d
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: orphan
  |  summary:     apricot and coconut
  |
  x  changeset:   1:e0486f65907d
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  obsolete:    pruned using prune
  |  summary:     banana
  |
  x  changeset:   0:692cc7b6212c
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     obsolete:    rewritten using amend, rebase as 3:2868fe6df617
     summary:     apricot
  

  $ hg debugobsolete
  692cc7b6212c102a9eafcf04ed2e4bfca5023754 32acf8fb1b2325c727135dcd65153745a031a125 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  32acf8fb1b2325c727135dcd65153745a031a125 2868fe6df617a3045cf668e4ab1c486a8692abd1 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '12', 'operation': 'rebase', 'user': 'test'}
  e0486f65907dac7107e72a247386845e6a9fd83b 0 {692cc7b6212c102a9eafcf04ed2e4bfca5023754} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'prune', 'user': 'test'}
  $ hg obslog
  @  2868fe6df617 (3) apricot and coconut
  |    rewritten(parent, content) from 32acf8fb1b23 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  32acf8fb1b23 (2) apricot and coconut
  |    rewritten(description, content) from 692cc7b6212c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  692cc7b6212c (0) apricot
  

  $ hg evolve -r .
  move:[3] apricot and coconut
  atop:[-1] 
  working directory is now at bb847d1d3a5f

  $ hg log -G
  @  changeset:   4:bb847d1d3a5f
     tag:         tip
     parent:      -1:000000000000
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     apricot and coconut
  

  $ hg debugobsolete
  692cc7b6212c102a9eafcf04ed2e4bfca5023754 32acf8fb1b2325c727135dcd65153745a031a125 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  32acf8fb1b2325c727135dcd65153745a031a125 2868fe6df617a3045cf668e4ab1c486a8692abd1 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '12', 'operation': 'rebase', 'user': 'test'}
  e0486f65907dac7107e72a247386845e6a9fd83b 0 {692cc7b6212c102a9eafcf04ed2e4bfca5023754} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'prune', 'user': 'test'}
  2868fe6df617a3045cf668e4ab1c486a8692abd1 bb847d1d3a5f3de90f4fd5e845b69d848568401a 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog
  @  bb847d1d3a5f (4) apricot and coconut
  |    rebased(parent) from 2868fe6df617 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  2868fe6df617 (3) apricot and coconut
  |    rewritten(parent, content) from 32acf8fb1b23 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  32acf8fb1b23 (2) apricot and coconut
  |    rewritten(description, content) from 692cc7b6212c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  692cc7b6212c (0) apricot
  
