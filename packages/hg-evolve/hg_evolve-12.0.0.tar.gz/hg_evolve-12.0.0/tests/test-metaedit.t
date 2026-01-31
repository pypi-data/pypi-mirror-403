  $ . $TESTDIR/testlib/common.sh

  $ cat >> $HGRCPATH <<EOF
  > [alias]
  > glog = log -GT "{rev}:{node|short}@{branch}({phase}) {desc|firstline}"
  > gluf = log -GT "{separate(' ', rev, bookmarks)}: {desc|firstline} - {author|user} ({files})"
  > [extensions]
  > evolve =
  > EOF

##########################
importing Parren test
##########################

  $ cat << EOF >> $HGRCPATH
  > [ui]
  > logtemplate = "{separate(' ', rev, bookmarks)}: {desc|firstline} - {author|user}\n"
  > EOF

HG METAEDIT
===============================

Setup the Base Repo
-------------------

We start with a plain base repo::

  $ hg init $TESTTMP/metaedit; cd $TESTTMP/metaedit
  $ mkcommit "ROOT"
  $ hg phase --public "desc(ROOT)"
  $ mkcommit "A"
  $ mkcommit "B"
  $ hg up "desc(A)"
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ mkcommit "C"
  created new head
  $ mkcommit "D"
  $ echo "D'" > D
  $ hg bookmark bookmark-D
  $ hg amend -m "D2"
  $ hg up "desc(C)"
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  (leaving bookmark bookmark-D)
  $ mkcommit "E"
  created new head
  $ mkcommit "F"

Test
----

  $ hg log -G
  @  7: F - test
  |
  o  6: E - test
  |
  | o  5 bookmark-D: D2 - test
  |/
  o  3: C - test
  |
  | o  2: B - test
  |/
  o  1: A - test
  |
  o  0: ROOT - test
  
  $ hg update --clean .
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg metaedit -r 0
  abort: cannot edit commit information for public revisions
  [255]
  $ hg metaedit --fold
  abort: revisions must be specified with --fold
  [255]
  $ hg metaedit -r 0 --fold
  abort: cannot fold public changesets: ea207398892e
  (see 'hg help phases' for details)
  [10]
  $ hg metaedit 'desc(C) + desc(F)' --fold
  abort: cannot fold non-linear revisions (multiple roots given)
  [255]
  $ hg metaedit "desc(C)::desc(D2) + desc(E)" --fold
  abort: cannot fold non-linear revisions (multiple heads given)
  [255]
check that metaedit respects allowunstable
  $ hg metaedit '.^' --config 'experimental.evolution=createmarkers, allnewcommands'
  abort: cannot edit commit information in the middle of a stack
  (587528abfffe will become unstable and new unstable changes are not allowed)
  [255]
  $ hg metaedit 'desc(A)::desc(B)' --fold --config 'experimental.evolution=createmarkers, allnewcommands'
  abort: cannot fold changeset, as that will orphan 4 descendants
  (see 'hg help evolution.instability')
  [10]
  $ hg metaedit --user foobar
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg log --template '{rev}: {author}\n' -r 'desc(F):' --hidden
  7: test
  8: foobar
  $ hg log --template '{rev}: {author}\n' -r .
  8: foobar

TODO: support this
  $ hg metaedit '.^::.'
  abort: editing multiple revisions without --fold is not currently supported
  [255]

  $ HGEDITOR=cat hg metaedit '.^::.' --fold --note 'folding changesets using metaedit,
  > and newlines'
  abort: note cannot contain a newline
  [255]
  $ HGEDITOR=cat hg metaedit '.^::.' --fold --note "folding changesets using metaedit"
  HG: This is a fold of 2 changesets.
  HG: Commit message of changeset 6.
  
  E
  
  HG: Commit message of changeset 8.
  
  F
  
  
  
  HG: Enter commit message.  Lines beginning with 'HG:' are removed.
  HG: Leave message empty to abort commit.
  HG: --
  HG: user: test
  HG: branch 'default'
  HG: added E
  HG: added F
  2 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ hg glog -r .
  @  9:a08d35fd7d9d@default(draft) E
  |
  ~

  $ hg debugobsolete
  e2abbe8ca2ec6ffca6fd7a19d4158c58ff461723 f3d001339afd30d27fcd91e713274a78233528c8 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  587528abfffe33d49f94f9d6223dbbd58d6197c6 212b2a2b87cdbae992f001e9baba64db389fbce7 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '16', 'operation': 'metaedit', 'user': 'test'}
  c2bd843aa2468b30bb56d69d4f5fef95b85986f2 a08d35fd7d9d0f8cb33d5bd2074e9bafb5cbc70f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'fold-id': 'c5832a81', 'fold-idx': '1', 'fold-size': '2', 'note': 'folding changesets using metaedit', 'operation': 'metaedit', 'user': 'test'}
  212b2a2b87cdbae992f001e9baba64db389fbce7 a08d35fd7d9d0f8cb33d5bd2074e9bafb5cbc70f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '29', 'fold-id': 'c5832a81', 'fold-idx': '2', 'fold-size': '2', 'note': 'folding changesets using metaedit', 'operation': 'metaedit', 'user': 'test'}
  $ hg obslog -r . --no-origin
  @    a08d35fd7d9d (9) E
  |\
  x |  212b2a2b87cd (8) F
  | |    folded(description, user, parent, content) as a08d35fd7d9d using metaedit by test (Thu Jan 01 00:00:00 1970 +0000)
  | |      note: folding changesets using metaedit
  | |
  | x  c2bd843aa246 (6) E
  |      folded(description, content) as a08d35fd7d9d using metaedit by test (Thu Jan 01 00:00:00 1970 +0000)
  |        note: folding changesets using metaedit
  |
  x  587528abfffe (7) F
       reauthored(user) as 212b2a2b87cd using metaedit by test (Thu Jan 01 00:00:00 1970 +0000)
  
  $ hg obslog -r .
  @    a08d35fd7d9d (9) E
  |\     folded(description, user, parent, content) from 212b2a2b87cd, c2bd843aa246 using metaedit by test (Thu Jan 01 00:00:00 1970 +0000)
  | |      note: folding changesets using metaedit
  | |
  x |  212b2a2b87cd (8) F
  | |    reauthored(user) from 587528abfffe using metaedit by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  c2bd843aa246 (6) E
  |
  x  587528abfffe (7) F
  
  $ hg debugobsolete --rev . --exclusive
  212b2a2b87cdbae992f001e9baba64db389fbce7 a08d35fd7d9d0f8cb33d5bd2074e9bafb5cbc70f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '29', 'fold-id': 'c5832a81', 'fold-idx': '2', 'fold-size': '2', 'note': 'folding changesets using metaedit', 'operation': 'metaedit', 'user': 'test'}
  c2bd843aa2468b30bb56d69d4f5fef95b85986f2 a08d35fd7d9d0f8cb33d5bd2074e9bafb5cbc70f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'fold-id': 'c5832a81', 'fold-idx': '1', 'fold-size': '2', 'note': 'folding changesets using metaedit', 'operation': 'metaedit', 'user': 'test'}

no new commit is created here because the date is the same
  $ HGEDITOR=cat hg metaedit
  E
  
  
  F
  
  
  HG: Enter commit message.  Lines beginning with 'HG:' are removed.
  HG: Leave message empty to abort commit.
  HG: --
  HG: user: test
  HG: branch 'default'
  HG: added E
  HG: added F
  nothing changed

  $ hg glog -r '.^::.'
  @  9:a08d35fd7d9d@default(draft) E
  |
  o  3:3260958f1169@default(draft) C
  |
  ~

metaedit should preserve the original date of the edited commit (issue5994)

  $ hg metaedit --config devel.default-date=
  nothing changed

metaedit doesn't create new commit if message and user aren't changed

  $ hg metaedit --config devel.default-date= --user test --message 'E
  > 
  > 
  > F'
  nothing changed

  $ hg metaedit --config devel.default-date= --date "42 0"
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg log -r '.^::.' --template '{rev}: {desc|firstline}\n'
  3: C
  10: E

  $ hg up .^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg metaedit --user foobar2 tip
  $ hg log --template '{rev}: {author}\n' -r "user(foobar):" --hidden
  8: foobar
  9: test
  10: test
  11: foobar2
  $ hg diff -r "10" -r "11" --hidden

'fold' one commit
  $ HGUSER=foobar3 hg metaedit "desc(D2)" --fold -U
  1 changesets folded
  $ hg log -r "tip" --template '{rev}: {author}\n'
  12: foobar3
  $ hg debugobsolete --rev 'tip' --exclusive
  f3d001339afd30d27fcd91e713274a78233528c8 07a6525ddaf5de1ab33352806abb5724a0954f3f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '16', 'operation': 'metaedit', 'user': 'foobar3'}

working on merge commits too

  $ hg up -q 11
  $ hg merge -q 12
  $ hg ci -m 'merge commit'
  $ hg st --change .
  A D
  $ hg metaedit --user someone-else
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg st --change .
  A D
  $ hg gluf
  @    14: merge commit - someone-else ()
  |\
  | o  12 bookmark-D: D2 - foobar3 (D)
  | |
  o |  11: E - foobar2 (E F)
  |/
  o  3: C - test (C)
  |
  | o  2: B - test (B)
  |/
  o  1: A - test (A)
  |
  o  0: ROOT - test (ROOT)
  
  $ hg metaedit --user mr-squasher -r 3:14 --fold --message squashed
  4 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg st --change .
  A C
  A D
  A E
  A F
  $ hg gluf
  @  15 bookmark-D: squashed - mr-squasher (C D E F)
  |
  | o  2: B - test (B)
  |/
  o  1: A - test (A)
  |
  o  0: ROOT - test (ROOT)
  
  $ hg files
  A
  C
  D
  E
  F
  ROOT
