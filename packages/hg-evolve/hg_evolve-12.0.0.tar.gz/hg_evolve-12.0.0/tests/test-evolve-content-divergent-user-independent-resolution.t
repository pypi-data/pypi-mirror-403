=====================================
Testing content-divergence resolution
=====================================

Independent rewrites of same changeset can lead to content-divergence. In most
common cases, it can occur when multiple users rewrite the same changeset
independently and push it.

This test aims to check that the resolution of content-divergent changesets is
independent of the user resolving the divergence. In other words, the two users
resolving the same divergence should end up with the same result.

Setup
-----
  $ . $TESTDIR/testlib/content-divergence-util.sh
  $ setuprepos user-independent-resolution
  creating test repo for test case user-independent-resolution
  - upstream
  - local
  - other
  cd into `local` and proceed with env setup

initial

  $ cd upstream
  $ mkcommit A0

  $ cd ../local
  $ hg pull -uq
  $ hg amend -m "A1" --config devel.default-date='172800 19800'

  $ cd ../other
  $ hg pull -uq
  $ hg amend -d '2 0' --config devel.default-date='86400 7200'
  $ hg push -q

  $ cd ../local
  $ hg push --force -q
  2 new content-divergent changesets
  $ hg pull -q
  2 new content-divergent changesets

'local' amended desc, 'other' amended date
------------------------------------------
  $ hg log -G
  *  3:1a0af03d20ad (draft): A0 [content-divergent]
  |
  | @  2:0d8c87cec5fc (draft): A1 [content-divergent]
  |/
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve --content-div
  merge:[2] A1
  with: [3] A0
  base: [1] A0
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 276e2aee8fe1
  $ hg log -G
  @  4:276e2aee8fe1 (draft): A1
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve -l

'local' amended date, 'other' amended desc
------------------------------------------
  $ cd ../other
  $ hg pull -q
  2 new content-divergent changesets
  $ hg log -G
  *  3:0d8c87cec5fc (draft): A1 [content-divergent]
  |
  | @  2:1a0af03d20ad (draft): A0 [content-divergent]
  |/
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve --content-div
  merge:[3] A1
  with: [2] A0
  base: [1] A0
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 276e2aee8fe1

  $ hg log -G
  @  4:276e2aee8fe1 (draft): A1
  |
  o  0:a9bdc8b26820 (public): O
  
  $ hg evolve -l

both users can push/pull without any issue
------------------------------------------

  $ hg push
  pushing to $TESTTMP/user-independent-resolution/upstream
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 1 files (+1 heads)
  2 new obsolescence markers
  obsoleted 2 changesets
  $ hg pull ../local
  pulling from ../local
  searching for changes
  no changes found
  $ hg debugobsolete -r tip
  0d8c87cec5fc1540b7c0324332375d530856fb56 276e2aee8fe1d3aae5e21dfee47be818fba8d7fc 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '32', 'operation': 'evolve', 'user': 'test'}
  1a0af03d20ad8b4e3a99d30620c8734efe076900 276e2aee8fe1d3aae5e21dfee47be818fba8d7fc 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'operation': 'evolve', 'user': 'test'}
  28b51eb45704506b5c603decd6bf7ac5e0f6a52f 0d8c87cec5fc1540b7c0324332375d530856fb56 0 (Fri Jan 02 18:30:00 1970 -0530) {'ef1': '1', 'operation': 'amend', 'user': 'test'}
  28b51eb45704506b5c603decd6bf7ac5e0f6a52f 1a0af03d20ad8b4e3a99d30620c8734efe076900 0 (Thu Jan 01 22:00:00 1970 -0200) {'ef1': '32', 'operation': 'amend', 'user': 'test'}

  $ cd ../local
  $ hg push
  pushing to $TESTTMP/user-independent-resolution/upstream
  searching for changes
  no changes found
  [1]
  $ hg pull ../other
  pulling from ../other
  searching for changes
  no changes found
  $ hg debugobsolete -r tip
  0d8c87cec5fc1540b7c0324332375d530856fb56 276e2aee8fe1d3aae5e21dfee47be818fba8d7fc 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '32', 'operation': 'evolve', 'user': 'test'}
  1a0af03d20ad8b4e3a99d30620c8734efe076900 276e2aee8fe1d3aae5e21dfee47be818fba8d7fc 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'operation': 'evolve', 'user': 'test'}
  28b51eb45704506b5c603decd6bf7ac5e0f6a52f 0d8c87cec5fc1540b7c0324332375d530856fb56 0 (Fri Jan 02 18:30:00 1970 -0530) {'ef1': '1', 'operation': 'amend', 'user': 'test'}
  28b51eb45704506b5c603decd6bf7ac5e0f6a52f 1a0af03d20ad8b4e3a99d30620c8734efe076900 0 (Thu Jan 01 22:00:00 1970 -0200) {'ef1': '32', 'operation': 'amend', 'user': 'test'}
