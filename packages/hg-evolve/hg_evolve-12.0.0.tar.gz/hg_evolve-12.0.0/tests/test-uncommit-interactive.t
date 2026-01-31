================================================
||  The test for `hg uncommit --interactive`  ||
================================================

Repo Setup
============

  $ . $TESTDIR/testlib/common.sh
  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > interactive = true
  > [extensions]
  > evolve =
  > EOF

  $ glog() {
  >   hg log -G --template '{rev}:{node|short}@{branch}({separate("/", obsolete, phase)}) {desc|firstline}\n' "$@"
  > }

  $ hg init repo
  $ cd repo

  $ touch a
  $ cat >> a << EOF
  > 1
  > 2
  > 3
  > 4
  > 5
  > EOF

  $ hg add a
  $ hg ci -m "The base commit"

Make sure aborting the interactive selection does no magic
----------------------------------------------------------

  $ hg status
  $ hg uncommit -i<<EOF
  > q
  > EOF
  diff --git a/a b/a
  new file mode 100644
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] q
  
  abort: user quit
  [250]
  $ hg status

Make a commit with multiple hunks
---------------------------------

  $ cat > a << EOF
  > -2
  > -1
  > 0
  > 1
  > 2
  > 3
  > foo
  > bar
  > 4
  > 5
  > babar
  > EOF

  $ hg diff
  diff -r 7733902a8d94 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,5 +1,11 @@
  +-2
  +-1
  +0
   1
   2
   3
  +foo
  +bar
   4
   5
  +babar

  $ hg ci -m "another one"

Not selecting anything to uncommit
==================================

  $ hg uncommit -i<<EOF
  > y
  > n
  > n
  > n
  > EOF
  diff --git a/a b/a
  3 hunks, 6 lines changed
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -1,3 +1,6 @@
  +-2
  +-1
  +0
   1
   2
   3
  discard change 1/3 to 'a'?
  (enter ? for help) [Ynesfdaq?] n
  
  @@ -1,5 +4,7 @@
   1
   2
   3
  +foo
  +bar
   4
   5
  discard change 2/3 to 'a'?
  (enter ? for help) [Ynesfdaq?] n
  
  @@ -4,2 +9,3 @@
   4
   5
  +babar
  discard change 3/3 to 'a'?
  (enter ? for help) [Ynesfdaq?] n
  
  abort: nothing selected to uncommit
  [255]
  $ hg status

Uncommit a chunk
================

  $ hg amend --extract -n "note on amend --extract" -i<<EOF
  > y
  > y
  > n
  > n
  > EOF
  diff --git a/a b/a
  3 hunks, 6 lines changed
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -1,3 +1,6 @@
  +-2
  +-1
  +0
   1
   2
   3
  discard change 1/3 to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -1,5 +4,7 @@
   1
   2
   3
  +foo
  +bar
   4
   5
  discard change 2/3 to 'a'?
  (enter ? for help) [Ynesfdaq?] n
  
  @@ -4,2 +9,3 @@
   4
   5
  +babar
  discard change 3/3 to 'a'?
  (enter ? for help) [Ynesfdaq?] n
  

  $ hg debugobsolete
  e9635f4beaf11f64a07ccc74684092b144c53d89 0 {7733902a8d94c789ca81d866bea1893d79442db6} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'uncommit', 'user': 'test'}
  f70fb463d5bf9f0ffd38f105521d96e9f2591bc1 678a59e5ff90754d5e94719bd82ad169be773c21 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'note': 'note on amend --extract', 'operation': 'uncommit', 'user': 'test'}
  $ hg log -l 2 -T '{rev}:{node|short} {join(extras, " ")}\n' --hidden
  3:678a59e5ff90 branch=default uncommit_source=f70fb463d5bf
  2:e9635f4beaf1 branch=default uncommit_source=f70fb463d5bf
  $ hg obslog
  @  678a59e5ff90 (3) another one
  |    amended(content) from f70fb463d5bf using uncommit by test (Thu Jan 01 00:00:00 1970 +0000)
  |      note: note on amend --extract
  |
  x  f70fb463d5bf (1) another one
  
The unselected part should be in the diff
-----------------------------------------

  $ hg diff
  diff -r 678a59e5ff90 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,3 +1,6 @@
  +-2
  +-1
  +0
   1
   2
   3

The commit should contain the rest of part
------------------------------------------

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 678a59e5ff90754d5e94719bd82ad169be773c21
  # Parent  7733902a8d94c789ca81d866bea1893d79442db6
  another one
  
  diff -r 7733902a8d94 -r 678a59e5ff90 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,5 +1,8 @@
   1
   2
   3
  +foo
  +bar
   4
   5
  +babar

Uncommiting on dirty working directory
======================================

  $ hg status
  M a
  $ hg diff
  diff -r 678a59e5ff90 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,3 +1,6 @@
  +-2
  +-1
  +0
   1
   2
   3

  $ hg uncommit -n "testing uncommit on dirty wdir" -i<<EOF
  > y
  > n
  > y
  > EOF
  diff --git a/a b/a
  2 hunks, 3 lines changed
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -1,5 +1,7 @@
   1
   2
   3
  +foo
  +bar
   4
   5
  discard change 1/2 to 'a'?
  (enter ? for help) [Ynesfdaq?] n
  
  @@ -4,2 +6,3 @@
   4
   5
  +babar
  discard change 2/2 to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  patching file a
  Hunk #1 succeeded at 2 with fuzz 1 (offset 0 lines).

  $ hg diff
  diff -r ef651ea03f87 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,3 +1,6 @@
  +-2
  +-1
  +0
   1
   2
   3
  @@ -5,3 +8,4 @@
   bar
   4
   5
  +babar

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID ef651ea03f873a6d70aeeb9ac351d4f65c84fb3b
  # Parent  7733902a8d94c789ca81d866bea1893d79442db6
  another one
  
  diff -r 7733902a8d94 -r ef651ea03f87 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,5 +1,7 @@
   1
   2
   3
  +foo
  +bar
   4
   5

Checking the obsolescence history

  $ hg debugobsolete
  e9635f4beaf11f64a07ccc74684092b144c53d89 0 {7733902a8d94c789ca81d866bea1893d79442db6} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'uncommit', 'user': 'test'}
  f70fb463d5bf9f0ffd38f105521d96e9f2591bc1 678a59e5ff90754d5e94719bd82ad169be773c21 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'note': 'note on amend --extract', 'operation': 'uncommit', 'user': 'test'}
  7ca9935a62f11b39b60c7fb8861377c7d45b3e99 0 {7733902a8d94c789ca81d866bea1893d79442db6} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'uncommit', 'user': 'test'}
  678a59e5ff90754d5e94719bd82ad169be773c21 ef651ea03f873a6d70aeeb9ac351d4f65c84fb3b 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'note': 'testing uncommit on dirty wdir', 'operation': 'uncommit', 'user': 'test'}
  $ hg log -l 4 -T '{rev}:{node|short} {join(extras, " ")}\n' --hidden
  5:ef651ea03f87 branch=default uncommit_source=678a59e5ff90
  4:7ca9935a62f1 branch=default uncommit_source=678a59e5ff90
  3:678a59e5ff90 branch=default uncommit_source=f70fb463d5bf
  2:e9635f4beaf1 branch=default uncommit_source=f70fb463d5bf
  $ hg obslog
  @  ef651ea03f87 (5) another one
  |    amended(content) from 678a59e5ff90 using uncommit by test (Thu Jan 01 00:00:00 1970 +0000)
  |      note: testing uncommit on dirty wdir
  |
  x  678a59e5ff90 (3) another one
  |    amended(content) from f70fb463d5bf using uncommit by test (Thu Jan 01 00:00:00 1970 +0000)
  |      note: note on amend --extract
  |
  x  f70fb463d5bf (1) another one
  

Push the changes back to the commit and more commits for more testing

  $ hg amend
  $ glog
  @  6:f4c93db9c5cd@default(draft) another one
  |
  o  0:7733902a8d94@default(draft) The base commit
  
  $ touch foo
  $ echo "hey" >> foo
  $ hg ci -Am "Added foo"
  adding foo

Testing uncommiting a whole changeset and also for a file addition
==================================================================

  $ hg uncommit -i<<EOF
  > y
  > y
  > EOF
  diff --git a/foo b/foo
  new file mode 100644
  examine changes to 'foo'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +hey
  discard this change to 'foo'?
  (enter ? for help) [Ynesfdaq?] y
  
  new changeset is empty
  (use 'hg prune .' to remove it)

  $ hg status
  A foo
  $ hg diff
  diff -r 665843692be0 foo
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +hey

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 665843692be04cb0619d8ad1f81ec31c7b33f366
  # Parent  f4c93db9c5cde0d4ab20badcb9c514cfbf7b9e38
  Added foo
  
  $ hg amend

Testing to uncommit removed files completely
============================================

  $ hg rm a
  $ hg ci -m "Removed a"
  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 24fcae345f93a1161b224f849c3a9ab362f76f44
  # Parent  3f44e16f88daf37e5798606082ae9895eb90fc4d
  Removed a
  
  diff -r 3f44e16f88da -r 24fcae345f93 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,11 +0,0 @@
  --2
  --1
  -0
  -1
  -2
  -3
  -foo
  -bar
  -4
  -5
  -babar

Not examining the file
----------------------

  $ hg uncommit -i<<EOF
  > n
  > EOF
  diff --git a/a b/a
  deleted file mode 100644
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] n
  
  abort: nothing selected to uncommit
  [255]

Examining the file
------------------
XXX: there is a bug in interactive selection as it is not letting to examine the
file. Tried with curses too. In the curses UI, if you just unselect the hunks
and the not file mod thing at the top, it will show the same "nothing unselected
to uncommit" message which is a bug in interactive selection.

  $ hg uncommit -i<<EOF
  > y
  > EOF
  diff --git a/a b/a
  deleted file mode 100644
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  new changeset is empty
  (use 'hg prune .' to remove it)

  $ hg diff
  diff -r 3778ffc6315b a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,11 +0,0 @@
  --2
  --1
  -0
  -1
  -2
  -3
  -foo
  -bar
  -4
  -5
  -babar
  $ hg status
  R a
  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 3778ffc6315b9cefdb01c218413677c23bf5bc9f
  # Parent  3f44e16f88daf37e5798606082ae9895eb90fc4d
  Removed a
  

  $ hg prune .
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 3f44e16f88da
  1 changesets pruned
  $ hg revert --all
  undeleting a

  $ glog
  @  10:3f44e16f88da@default(draft) Added foo
  |
  o  6:f4c93db9c5cd@default(draft) another one
  |
  o  0:7733902a8d94@default(draft) The base commit
  

Testing when a new file is added in the last commit
===================================================

  $ echo "foo" >> foo
  $ touch x
  $ echo "abcd" >> x
  $ hg add x
  $ hg ci -m "Added x"
  $ hg uncommit -i<<EOF
  > y
  > y
  > y
  > n
  > EOF
  diff --git a/foo b/foo
  1 hunks, 1 lines changed
  examine changes to 'foo'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -1,1 +1,2 @@
   hey
  +foo
  discard change 1/2 to 'foo'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/x b/x
  new file mode 100644
  examine changes to 'x'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +abcd
  discard change 2/2 to 'x'?
  (enter ? for help) [Ynesfdaq?] n
  

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 5fcbf1c538b13186c920c63ca6a7dab443ad6663
  # Parent  3f44e16f88daf37e5798606082ae9895eb90fc4d
  Added x
  
  diff -r 3f44e16f88da -r 5fcbf1c538b1 x
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/x	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +abcd

  $ hg diff
  diff -r 5fcbf1c538b1 foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,2 @@
   hey
  +foo

  $ hg status
  M foo

  $ hg revert --all
  reverting foo

Testing between the stack and with dirty working copy
=====================================================

  $ glog
  @  16:5fcbf1c538b1@default(draft) Added x
  |
  o  10:3f44e16f88da@default(draft) Added foo
  |
  o  6:f4c93db9c5cd@default(draft) another one
  |
  o  0:7733902a8d94@default(draft) The base commit
  
  $ hg up f4c93db9c5cd
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved

  $ touch bar
  $ echo "foo" >> bar
  $ hg add bar
  $ hg status
  A bar
  ? foo.orig

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID f4c93db9c5cde0d4ab20badcb9c514cfbf7b9e38
  # Parent  7733902a8d94c789ca81d866bea1893d79442db6
  another one
  
  diff -r 7733902a8d94 -r f4c93db9c5cd a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,5 +1,11 @@
  +-2
  +-1
  +0
   1
   2
   3
  +foo
  +bar
   4
   5
  +babar

  $ hg uncommit -i<<EOF
  > y
  > n
  > n
  > y
  > EOF
  diff --git a/a b/a
  3 hunks, 6 lines changed
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -1,3 +1,6 @@
  +-2
  +-1
  +0
   1
   2
   3
  discard change 1/3 to 'a'?
  (enter ? for help) [Ynesfdaq?] n
  
  @@ -1,5 +4,7 @@
   1
   2
   3
  +foo
  +bar
   4
   5
  discard change 2/3 to 'a'?
  (enter ? for help) [Ynesfdaq?] n
  
  @@ -4,2 +9,3 @@
   4
   5
  +babar
  discard change 3/3 to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  patching file a
  Hunk #1 succeeded at 1 with fuzz 1 (offset -1 lines).
  2 new orphan changesets

  $ hg diff
  diff -r 98a3d38b1b81 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -8,3 +8,4 @@
   bar
   4
   5
  +babar
  diff -r 98a3d38b1b81 bar
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/bar	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +foo

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 98a3d38b1b812aeca00a61a5554dfa228d632b9e
  # Parent  7733902a8d94c789ca81d866bea1893d79442db6
  another one
  
  diff -r 7733902a8d94 -r 98a3d38b1b81 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,5 +1,10 @@
  +-2
  +-1
  +0
   1
   2
   3
  +foo
  +bar
   4
   5
  $ hg status
  M a
  A bar
  ? foo.orig

More uncommit on the same dirty working copy
=============================================

  $ hg uncommit -i<<EOF
  > y
  > y
  > n
  > EOF
  diff --git a/a b/a
  2 hunks, 5 lines changed
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -1,3 +1,6 @@
  +-2
  +-1
  +0
   1
   2
   3
  discard change 1/2 to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -1,5 +4,7 @@
   1
   2
   3
  +foo
  +bar
   4
   5
  discard change 2/2 to 'a'?
  (enter ? for help) [Ynesfdaq?] n
  

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 9c6818648d9e694d2decfde377c6821191c5bfd5
  # Parent  7733902a8d94c789ca81d866bea1893d79442db6
  another one
  
  diff -r 7733902a8d94 -r 9c6818648d9e a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,5 +1,7 @@
   1
   2
   3
  +foo
  +bar
   4
   5

  $ hg diff
  diff -r 9c6818648d9e a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,3 +1,6 @@
  +-2
  +-1
  +0
   1
   2
   3
  @@ -5,3 +8,4 @@
   bar
   4
   5
  +babar
  diff -r 9c6818648d9e bar
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/bar	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +foo

  $ hg status
  M a
  A bar
  ? foo.orig

Interactive uncommit with a pattern
-----------------------------------

(more setup)

  $ hg ci -m 'roaming changes'
  $ cat > b << EOF
  > a
  > b
  > c
  > d
  > e
  > f
  > h
  > EOF
  $ hg add b
  $ hg ci -m 'add b'
  $ echo 'celeste' >> a
  $ echo 'i' >> b
  $ hg ci -m 'some more changes'
  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID bbdfefb59fb08650a9a663367ab18a3c2d072691
  # Parent  4f15d398b049b07eb4f4c98d3466a7f708e61735
  some more changes
  
  diff -r 4f15d398b049 -r bbdfefb59fb0 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -9,3 +9,4 @@
   4
   5
   babar
  +celeste
  diff -r 4f15d398b049 -r bbdfefb59fb0 b
  --- a/b	Thu Jan 01 00:00:00 1970 +0000
  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  @@ -5,3 +5,4 @@
   e
   f
   h
  +i

  $ hg uncommit -i a << DONE
  > y
  > DONE
  diff --git a/a b/a
  1 hunks, 1 lines changed
  @@ -9,3 +9,4 @@
   4
   5
   babar
  +celeste
  discard this change to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  $ hg status
  M a
  ? foo.orig
  $ hg diff
  diff -r 0873ba67273f a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -9,3 +9,4 @@
   4
   5
   babar
  +celeste
  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 0873ba67273ff5654e032c98df89be8cf431cb63
  # Parent  4f15d398b049b07eb4f4c98d3466a7f708e61735
  some more changes
  
  diff -r 4f15d398b049 -r 0873ba67273f b
  --- a/b	Thu Jan 01 00:00:00 1970 +0000
  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  @@ -5,3 +5,4 @@
   e
   f
   h
  +i

(reset)

  $ cat << EOF  > a
  > -3
  > -2
  > -1
  > 0
  > 1
  > 2
  > 3
  > foo
  > bar
  > 4
  > 5
  > babar
  > celeste
  > EOF
  $ hg amend 

Same but do not select some change in 'a'

  $ hg uncommit -i a << DONE
  > y
  > n
  > DONE
  diff --git a/a b/a
  2 hunks, 2 lines changed
  @@ -1,3 +1,4 @@
  +-3
   -2
   -1
   0
  discard change 1/2 to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -9,3 +10,4 @@
   4
   5
   babar
  +celeste
  discard change 2/2 to 'a'?
  (enter ? for help) [Ynesfdaq?] n
  
  $ hg status
  M a
  ? foo.orig

  $ hg diff
  diff -r 72c07d186be7 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,3 +1,4 @@
  +-3
   -2
   -1
   0

  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 72c07d186be791e6fa80bfdaf85f493dca503df2
  # Parent  4f15d398b049b07eb4f4c98d3466a7f708e61735
  some more changes
  
  diff -r 4f15d398b049 -r 72c07d186be7 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -9,3 +9,4 @@
   4
   5
   babar
  +celeste
  diff -r 4f15d398b049 -r 72c07d186be7 b
  --- a/b	Thu Jan 01 00:00:00 1970 +0000
  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  @@ -5,3 +5,4 @@
   e
   f
   h
  +i

  $ cat b
  a
  b
  c
  d
  e
  f
  h
  i
