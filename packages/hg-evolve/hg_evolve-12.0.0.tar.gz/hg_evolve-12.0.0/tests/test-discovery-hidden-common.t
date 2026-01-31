test for discovery with some remote changesets hidden locally
=============================================================

  $ . $TESTDIR/testlib/common.sh

  $ cat << EOF >> $HGRCPATH
  > [phases]
  > publish = false
  > [extensions]
  > evolve =
  > [experimental]
  > verbose-obsolescence-exchange = 1
  > [ui]
  > logtemplate = "{rev} {node|short} {desc} {tags}\n"
  > ssh = "$PYTHON" "$RUNTESTDIR/dummyssh"
  > EOF

  $ hg init server
  $ hg clone ssh://user@dummy/server client
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd server
  $ mkcommit root
  $ mkcommit A0

second pull:

  $ hg -R ../client pull
  pulling from ssh://user@dummy/server
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  new changesets 1e4be0697311:8aaa48160adc (2 drafts)
  (run 'hg update' to get a working copy)
  $ hg -R ../client log -G
  o  1 8aaa48160adc A0 tip
  |
  o  0 1e4be0697311 root
  

more update

  $ hg tag --local stay-visible
  $ hg up 0
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ mkcommit A1
  created new head
  $ hg debugobsolete `getid 'desc(A0)'` `getid 'desc(A1)'`
  1 new obsolescence markers
  obsoleted 1 changesets

second pull:

  $ hg -R ../client pull
  pulling from ssh://user@dummy/server
  searching for changes
  OBSEXC: looking for common markers in 2 nodes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  1 new obsolescence markers
  obsoleted 1 changesets
  new changesets f6082bc4ffef (1 drafts)
  (run 'hg heads' to see heads)
  $ hg -R ../client log -G
  o  2 f6082bc4ffef A1 tip
  |
  o  0 1e4be0697311 root
  

more update:

  $ hg up 0
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ mkcommit A2
  created new head
  $ hg debugobsolete `getid 'desc(A1)'` `getid 'desc(A2)'`
  1 new obsolescence markers
  obsoleted 1 changesets

third pull:

  $ hg -R ../client pull
  pulling from ssh://user@dummy/server
  searching for changes
  OBSEXC: looking for common markers in 1 nodes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  1 new obsolescence markers
  obsoleted 1 changesets
  new changesets c1f8d089020f (1 drafts)
  (run 'hg heads' to see heads)
  $ hg -R ../client log -G
  o  3 c1f8d089020f A2 tip
  |
  o  0 1e4be0697311 root
  
