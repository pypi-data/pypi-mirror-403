Content divergence and trying to relocate a node on top of itself (issue5958)
https://bz.mercurial-scm.org/show_bug.cgi?id=5958

  $ . $TESTDIR/testlib/common.sh

  $ cat << EOF >> $HGRCPATH
  > [extensions]
  > rebase =
  > evolve =
  > EOF

  $ hg init issue5958
  $ cd issue5958

  $ echo hi > r0
  $ hg ci -qAm 'add r0'
  $ echo hi > foo.txt
  $ hg ci -qAm 'add foo.txt'
  $ hg metaedit -r . -d '0 2'
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

(Make changes in unrelated files so that we don't have any merge conflicts
during the rebase, but the two touched revisions aren't identical)

  $ echo hi > bar.txt
  $ hg add -q bar.txt
  $ hg amend -q
  $ hg metaedit -r 1 -d '0 1' --hidden
  2 new content-divergent changesets
  $ hg log -r tip
  changeset:   4:c17bf400a278
  tag:         tip
  parent:      0:a24ed8ad918c
  user:        test
  date:        Wed Dec 31 23:59:59 1969 -0000
  instability: content-divergent
  summary:     add foo.txt
  
  $ echo hi > baz.txt
  $ hg add -q baz.txt
  $ hg amend -q
  $ hg rebase -qr tip -d 4
  $ hg log -G
  @  changeset:   6:08bc7ba82799
  |  tag:         tip
  |  parent:      4:c17bf400a278
  |  user:        test
  |  date:        Wed Dec 31 23:59:58 1969 -0000
  |  instability: content-divergent
  |  summary:     add foo.txt
  |
  *  changeset:   4:c17bf400a278
  |  parent:      0:a24ed8ad918c
  |  user:        test
  |  date:        Wed Dec 31 23:59:59 1969 -0000
  |  instability: content-divergent
  |  summary:     add foo.txt
  |
  o  changeset:   0:a24ed8ad918c
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     add r0
  
  $ hg debugobsolete
  cc71ffbc7c002d7b45fb694f9c060bf2e6920672 0065551bd38fe59ea4a069a4db378550c60122d3 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '32', 'operation': 'metaedit', 'user': 'test'}
  0065551bd38fe59ea4a069a4db378550c60122d3 a25dd7af6cf6731ff93708abb2b1b889eae848a0 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  cc71ffbc7c002d7b45fb694f9c060bf2e6920672 c17bf400a2782394b1ca5fbbe59e30494f16dfdc 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '32', 'operation': 'metaedit', 'user': 'test'}
  a25dd7af6cf6731ff93708abb2b1b889eae848a0 1d1fc409af989f5c0843507e202d69a1ad16c5ef 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  1d1fc409af989f5c0843507e202d69a1ad16c5ef 08bc7ba82799f1e419190b0dac1b0e1c4b1355f9 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '12', 'operation': 'rebase', 'user': 'test'}
  $ hg obslog -a -r .
  @  08bc7ba82799 (6) add foo.txt
  |    rewritten(parent, content) from 1d1fc409af98 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  | *  c17bf400a278 (4) add foo.txt
  | |    date-changed(date) from cc71ffbc7c00 using metaedit by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  1d1fc409af98 (5) add foo.txt
  | |    amended(content) from a25dd7af6cf6 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  a25dd7af6cf6 (3) add foo.txt
  | |    amended(content) from 0065551bd38f using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  0065551bd38f (2) add foo.txt
  |/     date-changed(date) from cc71ffbc7c00 using metaedit by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  cc71ffbc7c00 (1) add foo.txt
  
  $ hg evolve --content-divergent
  merge:[4] add foo.txt
  with: [6] add foo.txt
  base: [1] add foo.txt
  rebasing "other" content-divergent changeset 08bc7ba82799 on a24ed8ad918c
  2 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at d519bd54a945

  $ hg log -G
  @  changeset:   8:d519bd54a945
  |  tag:         tip
  |  parent:      0:a24ed8ad918c
  |  user:        test
  |  date:        Wed Dec 31 23:59:58 1969 -0000
  |  summary:     add foo.txt
  |
  o  changeset:   0:a24ed8ad918c
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     add r0
  
test that resolution is consistent and independent of divergent changeset we initiate the resolution from

  $ hg strip . --config extensions.strip=
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/issue5958/.hg/strip-backup/d519bd54a945-5f6b2f65-backup.hg
  2 new content-divergent changesets
  $ hg up 4
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg evolve --content-divergent
  merge:[4] add foo.txt
  with: [7] add foo.txt
  base: [1] add foo.txt
  2 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at d519bd54a945
  $ hg log -G
  @  changeset:   8:d519bd54a945
  |  tag:         tip
  |  parent:      0:a24ed8ad918c
  |  user:        test
  |  date:        Wed Dec 31 23:59:58 1969 -0000
  |  summary:     add foo.txt
  |
  o  changeset:   0:a24ed8ad918c
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     add r0
  
