=================================================================
Test automatic unstability resolution for multiple advanced cases
=================================================================

There are dedicated test case for each instability, but this file check some
basic case for each type.

XXX dispatching each these test case in appropriate file would make sense.

  $ cat >> $HGRCPATH <<EOF
  > [extensions]
  > rebase =
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

  $ glog() {
  >   hg log -G --template \
  >     '{rev}:{node|short}@{branch}({phase}) bk:[{bookmarks}] {desc|firstline}\n' "$@"
  > }

Test evolve removing the orphan changeset being evolved

  $ hg init empty
  $ cd empty
  $ echo a > a
  $ hg ci -Am adda a
  $ echo b > b
  $ hg ci -Am addb b
  $ echo a >> a
  $ hg ci -m changea
  $ hg bookmark changea
  $ hg up 1
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark changea)
  $ echo a >> a
  $ hg amend -m changea
  1 new orphan changesets
  $ hg evolve -v --confirm
  move:[2] changea
  atop:[3] changea
  perform evolve? [Ny] n
  abort: evolve aborted by user
  [255]
  $ echo y | hg evolve -v --confirm --config ui.interactive=True
  move:[2] changea
  atop:[3] changea
  perform evolve? [Ny] y
  hg rebase -r cce2c55b8965 -d fb9d051ec0a4
  resolving manifests
  evolution of 2:cce2c55b8965 created no changes to commit

  $ glog --hidden
  @  3:fb9d051ec0a4@default(draft) bk:[changea] changea
  |
  | x  2:cce2c55b8965@default(draft) bk:[] changea
  | |
  | x  1:102a90ea7b4a@default(draft) bk:[] addb
  |/
  o  0:07f494440405@default(draft) bk:[] adda
  
  $ hg debugobsolete
  102a90ea7b4a3361e4082ed620918c261189a36a fb9d051ec0a450a4aa2ffc8c324979832ef88065 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  cce2c55b896511e0b6e04173c9450ba822ebc740 0 {102a90ea7b4a3361e4082ed620918c261189a36a} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}

Test evolve of orphan that run into conflict

  $ hg status -A
  C a
  C b
  $ hg pdiff a
  diff -r 07f494440405 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,2 @@
   a
  +a
  $ echo 'newer a' >> a
  $ hg ci -m 'newer a'
  $ hg gdown
  gdown have been deprecated in favor of previous
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [3] changea
  $ echo 'a' > a
  $ hg amend
  1 new orphan changesets
  $ hg evolve --update
  move:[4] newer a
  atop:[5] changea
  merging a
  warning: conflicts while merging a! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ hg revert -r "orphan()" a
  $ hg diff
  diff -r 66719795a494 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,3 @@
   a
  +a
  +newer a
  $ hg evolve --continue
  abort: unresolved merge conflicts (see 'hg help resolve')
  [20]
  $ hg resolve -m a
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 4:3655f0f50885 "newer a"
  working directory is now at 99ec7503cf5a

Stabilize phase-divergent changesets with a different parent
============================================================

(the same-parent case is handled in test-evolve.t)

  $ glog
  @  6:99ec7503cf5a@default(draft) bk:[] newer a
  |
  o  5:66719795a494@default(draft) bk:[changea] changea
  |
  o  0:07f494440405@default(draft) bk:[] adda
  

Add another commit

  $ hg gdown
  gdown have been deprecated in favor of previous
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [5] changea
  $ echo 'c' > c
  $ hg add c
  $ hg commit -m 'add c'
  created new head

Get a successors of 8 on it

  $ hg pick 99ec7503cf5a
  picking 6:99ec7503cf5a "newer a"

Add real change to the successors

  $ echo 'babar' >> a
  $ hg amend

Make precursors public

  $ hg phase --hidden --public 99ec7503cf5a
  1 new phase-divergent changesets
  $ glog
  @  9:998db519ac88@default(draft) bk:[] newer a
  |
  o  7:7bc2f5967f5e@default(draft) bk:[] add c
  |
  | o  6:99ec7503cf5a@default(public) bk:[] newer a
  |/
  o  5:66719795a494@default(public) bk:[changea] changea
  |
  o  0:07f494440405@default(public) bk:[] adda
  

Stabilize!

  $ hg evolve --any --dry-run --phase-divergent
  recreate:[9] newer a
  atop:[6] newer a
  hg rebase --rev 998db519ac88 --dest 66719795a494;
  hg update 99ec7503cf5a;
  hg revert --all --rev 998db519ac88;
  hg commit --message "phase-divergent update to 998db519ac88"
  $ hg evolve --any --confirm --phase-divergent
  recreate:[9] newer a
  atop:[6] newer a
  perform evolve? [Ny] n
  abort: evolve aborted by user
  [255]
  $ echo y | hg evolve --any --confirm --config ui.interactive=True --phase-divergent
  recreate:[9] newer a
  atop:[6] newer a
  perform evolve? [Ny] y
  rebasing to destination parent: 66719795a494
  committed as 1e688a4b6db8
  working directory is now at 1e688a4b6db8
  $ glog
  @  11:1e688a4b6db8@default(draft) bk:[] phase-divergent update to 99ec7503cf5a:
  |
  | o  7:7bc2f5967f5e@default(draft) bk:[] add c
  | |
  o |  6:99ec7503cf5a@default(public) bk:[] newer a
  |/
  o  5:66719795a494@default(public) bk:[changea] changea
  |
  o  0:07f494440405@default(public) bk:[] adda
  
  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 1e688a4b6db81db9b647e9045aff0fcbc5c32b8d
  # Parent  99ec7503cf5a2cd545f41792129becc4172e9e9d
  phase-divergent update to 99ec7503cf5a:
  
  newer a
  
  diff -r 99ec7503cf5a -r 1e688a4b6db8 a
  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,3 +1,4 @@
   a
   a
   newer a
  +babar
