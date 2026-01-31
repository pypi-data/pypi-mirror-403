========================================================
Tests the resolution of content divergence: corner cases
========================================================

This file intend to cover cases that are specific enough to not fit in the
other cases.

  $ cat >> $HGRCPATH <<EOF
  > [alias]
  > glog = log -GT "{rev}:{node|short} {desc|firstline}\n ({bookmarks}) [{branch}] {phase}"
  > [diff]
  > git = 1
  > unified = 0
  > [ui]
  > logtemplate = {rev}:{node|short}@{branch}({phase}) {desc|firstline} [{instabilities}]\n
  > [experimental]
  > evolution.allowdivergence = True
  > [extensions]
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH
  $ mkcommit() {
  >    echo "$1" > "$1"
  >    hg add "$1"
  >    hg ci -m "add $1"
  > }

  $ mkcommits() {
  >   for i in $@; do mkcommit $i ; done
  > }

Basic test of divergence: two divergent changesets with the same parents
With --all --any we dedupe the divergent and solve the divergence once

  $ hg init test1
  $ cd test1
  $ echo a > a
  $ hg ci -Aqm "added a"
  $ echo b > b
  $ hg ci -Aqm "added b"

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo bdivergent > bdivergent1
  $ hg ci -Am "divergent"
  adding bdivergent1
  created new head

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo bdivergent > bdivergent2
  $ hg ci -Am "divergent"
  adding bdivergent2
  created new head

  $ hg prune -s 8374d2ddc3a4 "desc('added b')"
  1 changesets pruned
  $ hg prune -s 593c57f2117e "desc('added b')" --hidden
  1 changesets pruned
  2 new content-divergent changesets

  $ hg log -G
  @  3:8374d2ddc3a4@default(draft) divergent [content-divergent]
  |
  | *  2:593c57f2117e@default(draft) divergent [content-divergent]
  |/
  o  0:9092f1db7931@default(draft) added a []
  

  $ hg evolve --all --any --content-divergent --update
  merge:[2] divergent
  with: [3] divergent
  base: [1] added b
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 98ab969ac8fb
  $ hg log -G
  @  4:98ab969ac8fb@default(draft) divergent []
  |
  o  0:9092f1db7931@default(draft) added a []
  
  $ hg debugobsolete
  5f6d8a4bf34ab274ccc9f631c2536964b8a3666d 8374d2ddc3a4d48428c3d2f80e4fc86f13736f96 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'prune', 'user': 'test'}
  5f6d8a4bf34ab274ccc9f631c2536964b8a3666d 593c57f2117e33dd0884382f02789d948f548557 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'prune', 'user': 'test'}
  593c57f2117e33dd0884382f02789d948f548557 98ab969ac8fbe315e6d2c24a8eb5eab5b81e4242 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  8374d2ddc3a4d48428c3d2f80e4fc86f13736f96 98ab969ac8fbe315e6d2c24a8eb5eab5b81e4242 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog --all
  @    98ab969ac8fb (4) divergent
  |\     amended(content) from 593c57f2117e using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    amended(content) from 8374d2ddc3a4 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  593c57f2117e (2) divergent
  | |    rewritten(description, content) from 5f6d8a4bf34a using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  8374d2ddc3a4 (3) divergent
  |/     rewritten(description, content) from 5f6d8a4bf34a using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  5f6d8a4bf34a (1) added b
  

Test divergence resolution when it yields to an empty commit (issue4950)
cdivergent2 contains the same content than cdivergent1 and they are divergent
versions of the revision _c

  $ hg up .^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ mkcommit _c
  created new head

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ mkcommit cdivergent1
  created new head

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo "cdivergent1" > cdivergent1
  $ hg add cdivergent1
  $ hg ci -m "add _c"
  created new head

  $ hg log -G
  @  7:b2ae71172042@default(draft) add _c []
  |
  | o  6:e3ff64ce8d4c@default(draft) add cdivergent1 []
  |/
  | o  5:48819a835615@default(draft) add _c []
  |/
  | o  4:98ab969ac8fb@default(draft) divergent []
  |/
  o  0:9092f1db7931@default(draft) added a []
  

  $ hg prune -s b2ae71172042 48819a835615
  1 changesets pruned
  $ hg prune -s e3ff64ce8d4c 48819a835615 --hidden
  1 changesets pruned
  2 new content-divergent changesets

  $ hg log -G
  @  7:b2ae71172042@default(draft) add _c [content-divergent]
  |
  | *  6:e3ff64ce8d4c@default(draft) add cdivergent1 [content-divergent]
  |/
  | o  4:98ab969ac8fb@default(draft) divergent []
  |/
  o  0:9092f1db7931@default(draft) added a []
  
  $ hg evolve --all --any --content-divergent
  merge:[6] add cdivergent1
  with: [7] add _c
  base: [5] add _c
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 6b3776664a25

  $ hg log -G
  @  8:6b3776664a25@default(draft) add cdivergent1 []
  |
  | o  4:98ab969ac8fb@default(draft) divergent []
  |/
  o  0:9092f1db7931@default(draft) added a []
  
  $ hg debugobsolete
  5f6d8a4bf34ab274ccc9f631c2536964b8a3666d 8374d2ddc3a4d48428c3d2f80e4fc86f13736f96 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'prune', 'user': 'test'}
  5f6d8a4bf34ab274ccc9f631c2536964b8a3666d 593c57f2117e33dd0884382f02789d948f548557 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'prune', 'user': 'test'}
  593c57f2117e33dd0884382f02789d948f548557 98ab969ac8fbe315e6d2c24a8eb5eab5b81e4242 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  8374d2ddc3a4d48428c3d2f80e4fc86f13736f96 98ab969ac8fbe315e6d2c24a8eb5eab5b81e4242 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  48819a83561596ef0aeac4082eaaa8afe4320f3a b2ae71172042972a8e8d2bc11e2b2fe4e0c3aa49 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'prune', 'user': 'test'}
  48819a83561596ef0aeac4082eaaa8afe4320f3a e3ff64ce8d4ce33b40d9f367a8ec472fec588ca3 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'prune', 'user': 'test'}
  e3ff64ce8d4ce33b40d9f367a8ec472fec588ca3 6b3776664a258aa4c7e13f90df20ae9170995217 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  b2ae71172042972a8e8d2bc11e2b2fe4e0c3aa49 6b3776664a258aa4c7e13f90df20ae9170995217 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog --all
  @    6b3776664a25 (8) add cdivergent1
  |\     reworded(description) from b2ae71172042 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    rewritten from e3ff64ce8d4c using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  b2ae71172042 (7) add _c
  | |    amended(content) from 48819a835615 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  e3ff64ce8d4c (6) add cdivergent1
  |/     rewritten(description, content) from 48819a835615 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  48819a835615 (5) add _c
  

  $ cd ..

Test None docstring issue of evolve divergent, which caused hg crush

  $ hg init test2
  $ cd test2
  $ mkcommits _a _b

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo bdivergent > bdivergent11
  $ hg ci -Am "bdivergent"
  adding bdivergent11
  created new head

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo bdivergent > bdivergent22
  $ hg ci -Am "bdivergent"
  adding bdivergent22
  created new head

  $ hg log -G
  @  3:6b096fb45070@default(draft) bdivergent []
  |
  | o  2:05a6b6a9e633@default(draft) bdivergent []
  |/
  | o  1:37445b16603b@default(draft) add _b []
  |/
  o  0:135f39f4bd78@default(draft) add _a []
  

  $ hg prune -s 6b096fb45070 37445b16603b
  1 changesets pruned
  $ hg prune -s 05a6b6a9e633 37445b16603b --hidden
  1 changesets pruned
  2 new content-divergent changesets
  $ hg log -G
  @  3:6b096fb45070@default(draft) bdivergent [content-divergent]
  |
  | *  2:05a6b6a9e633@default(draft) bdivergent [content-divergent]
  |/
  o  0:135f39f4bd78@default(draft) add _a []
  

  $ cat >$TESTTMP/test_extension.py  << EOF
  > from mercurial import merge
  > origupdate = merge._update
  > def newupdate(*args, **kwargs):
  >   return origupdate(*args, **kwargs)
  > merge._update = newupdate
  > EOF
  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > testextension=$TESTTMP/test_extension.py
  > EOF
  $ hg evolve
  nothing to evolve on current working copy parent
  (do you want to use --content-divergent)
  [2]
  $ hg evolve --content-divergent
  merge:[2] bdivergent
  with: [3] bdivergent
  base: [1] add _b
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at b87e0354d5cb

  $ hg log -G
  @  4:b87e0354d5cb@default(draft) bdivergent []
  |
  o  0:135f39f4bd78@default(draft) add _a []
  
  $ hg debugobsolete
  37445b16603b50165d5eb80735fb986c72a2dac1 6b096fb450709a194b21fb9b192fe9b1572c4af0 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'prune', 'user': 'test'}
  37445b16603b50165d5eb80735fb986c72a2dac1 05a6b6a9e633802d2bdd06e6d292982a767d930e 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'prune', 'user': 'test'}
  05a6b6a9e633802d2bdd06e6d292982a767d930e b87e0354d5cb081210298429d8b51de9871155a2 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  6b096fb450709a194b21fb9b192fe9b1572c4af0 b87e0354d5cb081210298429d8b51de9871155a2 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog --all
  @    b87e0354d5cb (4) bdivergent
  |\     amended(content) from 05a6b6a9e633 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    amended(content) from 6b096fb45070 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  05a6b6a9e633 (2) bdivergent
  | |    rewritten(description, content) from 37445b16603b using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  6b096fb45070 (3) bdivergent
  |/     rewritten(description, content) from 37445b16603b using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  37445b16603b (1) add _b
  

  $ cd ..

Test to make sure that evolve don't fall into unrecoverable state (issue6053)
------------------------------------------------------------------------------

It happened when two divergent csets has different parent (need relocation)
and resolution parent is obsolete. So this issue triggered when during
relocation we hit conflicts. So lets make the repo as described.

  $ hg init localside
  $ cd localside
  $ for ch in a b c d e; do
  > echo $ch > $ch;
  > hg add $ch;
  > hg ci -m "added "$ch;
  > done;

  $ hg glog
  @  4:8d71eadcc9df added e
  |   () [default] draft
  o  3:9150fe93bec6 added d
  |   () [default] draft
  o  2:155349b645be added c
  |   () [default] draft
  o  1:5f6d8a4bf34a added b
  |   () [default] draft
  o  0:9092f1db7931 added a
      () [default] draft

  $ echo ee > e
  $ hg amend -m "updated e"
  $ hg up 1 -q

To make sure we hit conflict while relocating
  $ echo dd > d
  $ echo ee > e
  $ hg add d e
  $ hg ci -m "updated e"
  created new head

Lets create divergence
  $ hg prune 4 -s . --hidden
  1 changesets pruned
  2 new content-divergent changesets

Making obsolete resolution parent
  $ hg prune 3
  1 changesets pruned
  1 new orphan changesets

  $ hg glog
  @  6:de4ea3103326 updated e
  |   () [default] draft
  | *  5:ff6f7cd76a7c updated e
  | |   () [default] draft
  | x  3:9150fe93bec6 added d
  | |   () [default] draft
  | o  2:155349b645be added c
  |/    () [default] draft
  o  1:5f6d8a4bf34a added b
  |   () [default] draft
  o  0:9092f1db7931 added a
      () [default] draft

In this case, we have two divergent changeset:
- one did not changed parent
- the other did changed parent

So we can do a 3 way merges merges. on one side we have changes (the parent
change) and on the other one we don't, we should apply the change.

  $ hg evolve --list --rev 'contentdivergent()'
  ff6f7cd76a7c: updated e
    orphan: 9150fe93bec6 (obsolete parent)
    content-divergent: de4ea3103326 (draft) (precursor 8d71eadcc9df)
  
  de4ea3103326: updated e
    content-divergent: ff6f7cd76a7c (draft) (precursor 8d71eadcc9df)
  

  $ hg glog --hidden --rev '::(ff6f7cd76a7c+de4ea3103326+8d71eadcc9df)'
  @  6:de4ea3103326 updated e
  |   () [default] draft
  | *  5:ff6f7cd76a7c updated e
  | |   () [default] draft
  | | x  4:8d71eadcc9df added e
  | |/    () [default] draft
  | x  3:9150fe93bec6 added d
  | |   () [default] draft
  | o  2:155349b645be added c
  |/    () [default] draft
  o  1:5f6d8a4bf34a added b
  |   () [default] draft
  o  0:9092f1db7931 added a
      () [default] draft

  $ hg evolve --content-divergent --any --update --config ui.interactive=true <<EOF
  > c
  > EOF
  merge:[5] updated e
  with: [6] updated e
  base: [4] added e
  rebasing "divergent" content-divergent changeset ff6f7cd76a7c on 5f6d8a4bf34a
  file 'd' was deleted in local [local] but was modified in other [other].
  You can use (c)hanged version, leave (d)eleted, or leave (u)nresolved.
  What do you want to do? c
  0 files updated, 1 files merged, 0 files removed, 0 files unresolved
  working directory is now at 8bcf0a598b0d

  $ hg glog -l1
  @  8:8bcf0a598b0d updated e
  |   () [default] draft
  ~

  $ hg debugobsolete
  8d71eadcc9dfb21a924e75a5796c2f011bdc55a4 ff6f7cd76a7c97d938e8fe87f0fc816b66929435 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  8d71eadcc9dfb21a924e75a5796c2f011bdc55a4 de4ea3103326293994c634101e780724346ee89f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'prune', 'user': 'test'}
  9150fe93bec603cd88d05cda9f6ff13420cb53e9 0 {155349b645beebee15325a9a22dd0c9ef8fbbbd3} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'prune', 'user': 'test'}
  ff6f7cd76a7c97d938e8fe87f0fc816b66929435 8da34ee32eee606a1fca89e76ce48dcfb0e2598b 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  8da34ee32eee606a1fca89e76ce48dcfb0e2598b 8bcf0a598b0d242cb58758d78acd77e874251eef 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  de4ea3103326293994c634101e780724346ee89f 8bcf0a598b0d242cb58758d78acd77e874251eef 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog --all
  @    8bcf0a598b0d (8) updated e
  |\     amended(content) from 8da34ee32eee using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    rewritten from de4ea3103326 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  8da34ee32eee (7) updated e
  | |    rebased(parent) from ff6f7cd76a7c using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  de4ea3103326 (6) updated e
  | |    rewritten(description, parent, content) from 8d71eadcc9df using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  ff6f7cd76a7c (5) updated e
  |/     rewritten(description, content) from 8d71eadcc9df using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  8d71eadcc9df (4) added e
  

  $ cd ..

Check that canceling of file deletion are merge correctly
---------------------------------------------------------

File addition/deletion tend to have special processing. So we better test them directory

  $ hg init non-public
  $ cd non-public
  $ echo a > a
  $ echo b > b
  $ echo c > c
  $ echo d > d
  $ hg ci -Aqm initial

oops, we meant to delete just 'a', but we deleted 'b' and 'c' too

  $ hg rm a b c
  $ hg ci -m 'delete a'
  $ hg revert -r .^ b
  $ hg amend

create some content divergence

  $ hg co dff6e52f5e41 --hidden
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  updated to hidden changeset dff6e52f5e41
  (hidden revision 'dff6e52f5e41' was rewritten as: 0825dcee2670)
  working directory parent is obsolete! (dff6e52f5e41)
  (use 'hg evolve' to update to its successor: 0825dcee2670)
  $ hg revert -r .^ c
  $ hg amend
  2 new content-divergent changesets
  $ hg glog --hidden
  @  3:92ecd58f9b05 delete a
  |   () [default] draft
  | *  2:0825dcee2670 delete a
  |/    () [default] draft
  | x  1:dff6e52f5e41 delete a
  |/    () [default] draft
  o  0:75d2b02c4a5c initial
      () [default] draft

Resolve the divergence, only "a" should be removed

  $ hg evolve --content-divergent --update
  merge:[2] delete a
  with: [3] delete a
  base: [1] delete a
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at b1badc7ab394
  $ hg glog
  @  4:b1badc7ab394 delete a
  |   () [default] draft
  o  0:75d2b02c4a5c initial
      () [default] draft

  $ hg diff --change .
  diff --git a/a b/a
  deleted file mode 100644
  --- a/a
  +++ /dev/null
  @@ -1,1 +0,0 @@
  -a

  $ hg debugobsolete
  dff6e52f5e419381c070159c8038ac948f59283f 0825dcee2670349e749f1df45857fca34f61e350 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  dff6e52f5e419381c070159c8038ac948f59283f 92ecd58f9b05d6c0a1c3833a79359eea4b0268ff 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  0825dcee2670349e749f1df45857fca34f61e350 b1badc7ab394c2b9ed21e2961de43c71c2e2288f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  92ecd58f9b05d6c0a1c3833a79359eea4b0268ff b1badc7ab394c2b9ed21e2961de43c71c2e2288f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog --all
  @    b1badc7ab394 (4) delete a
  |\     amended(content) from 0825dcee2670 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    amended(content) from 92ecd58f9b05 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  0825dcee2670 (2) delete a
  | |    amended(content) from dff6e52f5e41 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  92ecd58f9b05 (3) delete a
  |/     amended(content) from dff6e52f5e41 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  dff6e52f5e41 (1) delete a
  
