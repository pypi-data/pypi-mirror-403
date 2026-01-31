Test the 'effect-flags' feature

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
  > rebase =
  > [experimental]
  > evolution.effect-flags = 1
  > EOF

  $ hg init $TESTTMP/effect-flags
  $ cd $TESTTMP/effect-flags
  $ mkcommit ROOT

amend touching the description only
-----------------------------------

  $ mkcommit A0
  $ hg amend -m "A1"

check result

  $ hg debugobsolete --rev .
  471f378eab4c5e25f6c77f785b27c936efb22874 fdf9bde5129a28d4548fadd3f62b265cdd3b7a2e 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'operation': 'amend', 'user': 'test'}
  $ hg obslog .
  @  fdf9bde5129a (2) A1
  |    reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  471f378eab4c (1) A0
  
  $ hg log --hidden -r "desc(A0)"
  changeset:   1:471f378eab4c
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    reworded using amend as 2:fdf9bde5129a
  summary:     A0
  

amend touching the user only
----------------------------

  $ mkcommit B0
  $ hg amend -u "bob <bob@bob.com>"

check result

  $ hg debugobsolete --rev .
  ef4a313b1e0ade55718395d80e6b88c5ccd875eb 5485c92d34330dac9d7a63dc07e1e3373835b964 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '16', 'operation': 'amend', 'user': 'test'}
  $ hg obslog .
  @  5485c92d3433 (4) B0
  |    reauthored(user) from ef4a313b1e0a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  ef4a313b1e0a (3) B0
  
  $ hg log --hidden -r "ef4a313b1e0a"
  changeset:   3:ef4a313b1e0a
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    reauthored using amend as 4:5485c92d3433
  summary:     B0
  

amend touching the date only
----------------------------

  $ mkcommit B1
  $ hg amend -d "42 0"

check result

  $ hg debugobsolete --rev .
  2ef0680ff45038ac28c9f1ff3644341f54487280 4dd84345082e9e5291c2e6b3f335bbf8bf389378 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '32', 'operation': 'amend', 'user': 'test'}
  $ hg obslog .
  @  4dd84345082e (6) B1
  |    date-changed(date) from 2ef0680ff450 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  2ef0680ff450 (5) B1
  
  $ hg log --hidden -r "2ef0680ff450"
  changeset:   5:2ef0680ff450
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    date-changed using amend as 6:4dd84345082e
  summary:     B1
  

amend touching the branch only
----------------------------

  $ mkcommit B2
  $ hg branch my-branch
  marked working directory as branch my-branch
  (branches are permanent and global, did you want a bookmark?)
  $ hg amend

check result

  $ hg debugobsolete --rev .
  bd3db8264ceebf1966319f5df3be7aac6acd1a8e 14a01456e0574f0e0a0b15b2345486a6364a8d79 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '64', 'operation': 'amend', 'user': 'test'}
  $ hg obslog .
  @  14a01456e057 (8) B2
  |    branch-changed(branch) from bd3db8264cee using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  bd3db8264cee (7) B2
  
  $ hg log --hidden -r "bd3db8264cee"
  changeset:   7:bd3db8264cee
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    branch-changed using amend as 8:14a01456e057
  summary:     B2
  

  $ hg up default
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved

rebase (parents change)
-----------------------

  $ mkcommit C0
  $ mkcommit D0
  $ hg rebase -r . -d 'desc(B0)'
  rebasing 10:c85eff83a034 tip "D0"

check result

  $ hg debugobsolete --rev .
  c85eff83a0340efd9da52b806a94c350222f3371 da86aa2f19a30d6686b15cae15c7b6c908ec9699 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  $ hg obslog .
  @  da86aa2f19a3 (11) D0
  |    rebased(parent) from c85eff83a034 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  c85eff83a034 (10) D0
  
  $ hg log --hidden -r "c85eff83a034"
  changeset:   10:c85eff83a034
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    rebased using rebase as 11:da86aa2f19a3
  summary:     D0
  

amend touching the diff
-----------------------

  $ mkcommit E0
  $ echo 42 >> E0
  $ hg amend

check result

  $ hg debugobsolete --rev .
  ebfe0333e0d96f68a917afd97c0a0af87f1c3b5f 75781fdbdbf58a987516b00c980bccda1e9ae588 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  $ hg obslog .
  @  75781fdbdbf5 (13) E0
  |    amended(content) from ebfe0333e0d9 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  ebfe0333e0d9 (12) E0
  
  $ hg log --hidden -r "ebfe0333e0d9"
  changeset:   12:ebfe0333e0d9
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    amended using amend as 13:75781fdbdbf5
  summary:     E0
  

amend with multiple effect (desc and meta)
-------------------------------------------

  $ mkcommit F0
  $ hg branch my-other-branch
  marked working directory as branch my-other-branch
  $ hg amend -m F1 -u "bob <bob@bob.com>" -d "42 0"

check result

  $ hg debugobsolete --rev .
  fad47e5bd78e6aa4db1b5a0a1751bc12563655ff a94e0fd5f1c81d969381a76eb0d37ce499a44fae 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '113', 'operation': 'amend', 'user': 'test'}
  $ hg obslog .
  @  a94e0fd5f1c8 (15) F1
  |    rewritten(description, user, date, branch) from fad47e5bd78e using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  fad47e5bd78e (14) F0
  
  $ hg log --hidden -r "fad47e5bd78e"
  changeset:   14:fad47e5bd78e
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    rewritten using amend as 15:a94e0fd5f1c8
  summary:     F0
  

rebase not touching the diff
----------------------------

  $ cat << EOF > H0
  > 0
  > 1
  > 2
  > 3
  > 4
  > 5
  > 6
  > 7
  > 8
  > 9
  > 10
  > EOF
  $ hg add H0
  $ hg commit -m 'H0'
  $ echo "H1" >> H0
  $ hg commit -m "H1"
  $ hg up -r "desc(H0)"
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cat << EOF > H0
  > H2
  > 0
  > 1
  > 2
  > 3
  > 4
  > 5
  > 6
  > 7
  > 8
  > 9
  > 10
  > EOF
  $ hg commit -m "H2"
  created new head
  $ hg rebase -s "desc(H1)" -d "desc(H2)" -t :merge3
  rebasing 17:b57fed8d8322 "H1"
  merging H0
  $ hg debugobsolete
  471f378eab4c5e25f6c77f785b27c936efb22874 fdf9bde5129a28d4548fadd3f62b265cdd3b7a2e 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'operation': 'amend', 'user': 'test'}
  ef4a313b1e0ade55718395d80e6b88c5ccd875eb 5485c92d34330dac9d7a63dc07e1e3373835b964 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '16', 'operation': 'amend', 'user': 'test'}
  2ef0680ff45038ac28c9f1ff3644341f54487280 4dd84345082e9e5291c2e6b3f335bbf8bf389378 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '32', 'operation': 'amend', 'user': 'test'}
  bd3db8264ceebf1966319f5df3be7aac6acd1a8e 14a01456e0574f0e0a0b15b2345486a6364a8d79 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '64', 'operation': 'amend', 'user': 'test'}
  c85eff83a0340efd9da52b806a94c350222f3371 da86aa2f19a30d6686b15cae15c7b6c908ec9699 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  ebfe0333e0d96f68a917afd97c0a0af87f1c3b5f 75781fdbdbf58a987516b00c980bccda1e9ae588 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  fad47e5bd78e6aa4db1b5a0a1751bc12563655ff a94e0fd5f1c81d969381a76eb0d37ce499a44fae 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '113', 'operation': 'amend', 'user': 'test'}
  b57fed8d83228a8ae3748d8c3760a77638dd4f8c e509e2eb3df5d131ff7c02350bf2a9edd0c09478 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  $ hg obslog tip
  o  e509e2eb3df5 (19) H1
  |    rebased(parent) from b57fed8d8322 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  b57fed8d8322 (17) H1
  
  $ hg log --hidden -r "b57fed8d8322"
  changeset:   17:b57fed8d8322
  branch:      my-other-branch
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    rebased using rebase as 19:e509e2eb3df5
  summary:     H1
  
amend closing the branch should be detected as meta change
----------------------------------------------------------

  $ hg branch closedbranch
  marked working directory as branch closedbranch
  $ mkcommit G0
  $ mkcommit I0
  $ hg commit --amend --close-branch

check result

  $ hg obslog .
  @  12c6238b5e37 (22) I0
  |    meta-changed(meta) from 2f599e54c1c6 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  2f599e54c1c6 (21) I0
  
  $ hg log --hidden -r "2f599e54c1c6"
  changeset:   21:2f599e54c1c6
  branch:      closedbranch
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    meta-changed using amend as 22:12c6238b5e37
  summary:     I0
  
