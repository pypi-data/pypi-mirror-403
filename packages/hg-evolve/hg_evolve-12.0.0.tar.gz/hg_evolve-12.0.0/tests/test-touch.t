
  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > logtemplate={rev}:{node|short} {desc}\n
  > [alias]
  > glog = log -GT "{rev}: {desc}"
  > [extensions]
  > rebase =
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

  $ hg init repo
  $ cd repo
  $ echo A > a
  $ hg add a
  $ hg commit -m a

Basic usage

  $ hg log -G
  @  0:[0-9a-f]{12} a (re)
  
  $ hg touch .
  $ hg log -G
  @  1:[0-9a-f]{12} a (re)
  


Revive usage

  $ echo A > b
  $ hg add b
  $ hg commit -m ab --amend
  $ hg up --hidden 1
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  updated to hidden changeset * (glob)
  (hidden revision '*' was rewritten as: *) (glob)
  working directory parent is obsolete! (*) (glob)
  (use 'hg evolve' to update to its successor: *) (glob)
  $ hg log -G
  o  2:[0-9a-f]{12} ab (re)
  
  @  1:[0-9a-f]{12} a (re)
  
  $ hg touch .
  [1] a
  reviving this changeset will create divergence unless you make a duplicate.
  (a)llow divergence or (d)uplicate the changeset?  a
  2 new content-divergent changesets
  $ hg log -G
  @  3:[0-9a-f]{12} a (re)
  
  \*  2:[0-9a-f]{12} ab (re)
  
  $ hg prune 3
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at 000000000000
  1 changesets pruned

Duplicate

  $ hg touch --duplicate .
  $ hg log -G
  @  4:[0-9a-f]{12} (re)
  
  o  2:[0-9a-f]{12} ab (re)
  

Multiple touch

  $ echo C > c
  $ hg add c
  $ hg commit -m c
  $ echo D > d
  $ hg add d
  $ hg commit -m d
  $ hg log -G
  @  6:[0-9a-f]{12} d (re)
  |
  o  5:[0-9a-f]{12} c (re)
  |
  o  4:[0-9a-f]{12} (re)
  
  o  2:[0-9a-f]{12} ab (re)
  
  $ hg touch .^:.
  $ hg log -G
  @  8:[0-9a-f]{12} d (re)
  |
  o  7:[0-9a-f]{12} c (re)
  |
  o  4:[0-9a-f]{12} (re)
  
  o  2:[0-9a-f]{12} ab (re)
  

check move data kept after rebase on touch:

  $ touch gna1
  $ hg commit -Am gna1
  adding gna1
  $ hg mv gna1 gna2
  $ hg commit -m move
  $ hg st -C --change=tip
  A gna2
    gna1
  R gna1
  $ hg up .^
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved

  $ hg touch
  1 new orphan changesets

  $ hg log -G --hidden
  @  11:[0-9a-f]{12} gna1 (re)
  |
  . \*  10:[0-9a-f]{12} move (re)
  | |
  . x  9:[0-9a-f]{12} gna1 (re)
  |/
  o  8:[0-9a-f]{12} d (re)
  |
  o  7:[0-9a-f]{12} c (re)
  |
  . x  6:[0-9a-f]{12} d (re)
  | |
  . x  5:[0-9a-f]{12} c (re)
  |/
  o  4:[0-9a-f]{12} (re)
  
  x  3:[0-9a-f]{12} a (re)
  
  o  2:[0-9a-f]{12} ab (re)
  
  x  1:[0-9a-f]{12} a (re)
  
  x  0:[0-9a-f]{12} a (re)
  

  $ hg rebase -s 10 -d 11
  rebasing 10:[0-9a-f]{12} "move" (re)
  $ hg st -C --change=tip
  A gna2
    gna1
  R gna1

check that the --duplicate option does not create divergence

  $ hg touch --duplicate 10 --hidden
  1 new orphan changesets

check that reviving a changeset with no successor does not show the prompt

  $ hg prune 13
  1 changesets pruned
  $ hg touch 13 --hidden --note "testing with no successor"
  1 new orphan changesets
  $ hg debugobsolete
  * * 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'touch', 'user': 'test'} (glob)
  * * 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'} (glob)
  * * 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'touch', 'user': 'test'} (glob)
  * 0 {0000000000000000000000000000000000000000} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'prune', 'user': 'test'} (glob)
  * * 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'touch', 'user': 'test'} (glob)
  * * 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'touch', 'user': 'test'} (glob)
  * * 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'touch', 'user': 'test'} (glob)
  * * 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'} (glob)
  * 0 {*} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'prune', 'user': 'test'} (glob)
  * * 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'note': 'testing with no successor', 'operation': 'touch', 'user': 'test'} (glob)
  $ hg obslog -r 13 --no-origin --hidden
  x  [0-9a-f]{12} (.*) move (re)
       pruned using prune by test (Thu Jan 01 00:00:00 1970 +0000)
       rewritten(.*) as [0-9a-f]{12} using touch by test (.*) (re)
         note: testing with no successor
  

Public phase

  $ hg phase --public -r 2
  $ hg touch 2
  abort: cannot touch public changesets: * (glob)
  (see 'hg help phases' for details)
  [10]
  $ hg touch --duplicate 2

Reviving merge commit

  $ hg up 12
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg merge 15
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m merge
  $ hg st --change .
  A a
  A b
  $ hg prune -r .
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  working directory is now at * (glob)
  1 changesets pruned
  $ hg touch 16 --hidden
  $ hg glog -r '12+15+17'
  o    17: merge
  |\
  | o  15: ab
  |
  @  12: move
  |
  ~
  $ hg st --change 17
  A a
  A b

  $ cd ..

Check that touching a merge commit doesn't lose file changes (issue 6416)

  $ hg init issue-6416
  $ cd issue-6416
  $ echo base > base
  $ hg ci -Aqm base
  $ echo left1 > left1
  $ hg ci -Aqm left1
  $ echo left2 > left2
  $ hg ci -Aqm left2
  $ hg up 0 -q
  $ echo right1 > right1
  $ hg ci -Aqm right1
  $ echo right2 > right2
  $ hg ci -Aqm right2
  $ hg up 2 -q
  $ hg merge 4 -q
  $ hg ci -m merge
  $ hg touch tip
  $ hg glog --hidden
  @    6: merge
  |\
  +---x  5: merge
  | |/
  | o  4: right2
  | |
  | o  3: right1
  | |
  o |  2: left2
  | |
  o |  1: left1
  |/
  o  0: base
  
  $ hg glog --hidden --rev 'min(desc("merge"))' --rev 'max(desc("merge"))'
  @    6: merge
  |\
  ~ ~
  x    5: merge
  |\
  ~ ~
  $ hg status --hidden --change 'min(desc("merge"))'
  A right1
  A right2
  $ hg status --hidden --change 'max(desc("merge"))'
  A right1
  A right2
  $ hg status --hidden --rev 'min(desc("merge"))' --rev 'max(desc("merge"))'
  $ cd ..

Check that touching a merge commit doesn't lose copies

  $ hg init merge-copies
  $ cd merge-copies
  $ echo base > base
  $ hg ci -Aqm base
  $ echo left > left
  $ hg cp base copy-on-left
  $ hg ci -Aqm left
  $ hg up 0 -q
  $ echo right > right
  $ hg cp base copy-on-right
  $ hg ci -Aqm right
  $ hg up 1 -q
  $ hg merge 2 -q
  $ hg cp left merge-copy-left
  $ hg cp right merge-copy-right
  $ hg ci -m merge
  $ hg touch tip
  $ hg glog --hidden
  @    4: merge
  |\
  +---x  3: merge
  | |/
  | o  2: right
  | |
  o |  1: left
  |/
  o  0: base
  
  $ hg glog --hidden --rev 'min(desc("merge"))' --rev 'max(desc("merge"))'
  @    4: merge
  |\
  ~ ~
  x    3: merge
  |\
  ~ ~
  $ hg debugpathcopies 'min(desc("base"))' 'min(desc("merge"))'
  base -> copy-on-left
  base -> copy-on-right
  $ hg debugpathcopies 'min(desc("base"))' 'max(desc("merge"))'
  base -> copy-on-left
  base -> copy-on-right
  $ hg debugpathcopies 'min(desc("left"))' 'min(desc("merge"))'
  base -> copy-on-right
  left -> merge-copy-left
  $ hg debugpathcopies 'min(desc("left"))' 'max(desc("merge"))'
  base -> copy-on-right
  left -> merge-copy-left
  $ hg debugpathcopies 'min(desc("right"))' 'min(desc("merge"))'
  base -> copy-on-left
  right -> merge-copy-right
  $ hg debugpathcopies 'min(desc("right"))' 'max(desc("merge"))'
  base -> copy-on-left
  right -> merge-copy-right
  $ cd ..

Make sure touch doesn't fail to warn about divergence (issue6107)

  $ hg init touchdiv
  $ cd touchdiv
  $ echo c > c
  $ hg add c
  $ hg ci -m "added c"

  $ hg amend -m "modified c"
  $ hg prune . -q

  $ hg touch -r "desc('added c')" --hidden
  $ hg touch -r "desc('modified c')" --hidden
  [1] modified c
  reviving this changeset will create divergence unless you make a duplicate.
  (a)llow divergence or (d)uplicate the changeset?  a
  2 new content-divergent changesets

But -A allows divergence

  $ hg touch -r "desc('modified c')" --hidden -A
  1 new content-divergent changesets

  $ cd ..

Touch preserves copies

  $ hg init copies
  $ cd copies
  $ echo a > a
  $ hg ci -Aqm a
  $ hg cp a b
  $ hg ci -Aqm 'copy a to b'
  $ hg status --copies --change .
  A b
    a
  $ hg touch
  $ hg status --copies --change .
  A b
    a
  $ cd ..
