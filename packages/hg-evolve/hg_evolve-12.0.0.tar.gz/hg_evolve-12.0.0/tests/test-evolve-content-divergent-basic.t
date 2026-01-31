=======================================================
Tests the resolution of content divergence: basic cases
=======================================================

This file intend to cover basic case of content divergence. See the other test
file for more advanced cases.

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
  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 5f6d8a4bf34ab274ccc9f631c2536964b8a3666d
  # Parent  9092f1db7931481f93b37d5c9fbcfc341bcd7318
  added b
  
  diff --git a/b b/b
  new file mode 100644
  --- /dev/null
  +++ b/b
  @@ -0,0 +1,1 @@
  +b

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo bdivergent > bdivergent1
  $ hg ci -Am "divergent"
  adding bdivergent1
  created new head
  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 593c57f2117e33dd0884382f02789d948f548557
  # Parent  9092f1db7931481f93b37d5c9fbcfc341bcd7318
  divergent
  
  diff --git a/bdivergent1 b/bdivergent1
  new file mode 100644
  --- /dev/null
  +++ b/bdivergent1
  @@ -0,0 +1,1 @@
  +bdivergent

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo bdivergent > bdivergent2
  $ hg ci -Am "divergent"
  adding bdivergent2
  created new head
  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 8374d2ddc3a4d48428c3d2f80e4fc86f13736f96
  # Parent  9092f1db7931481f93b37d5c9fbcfc341bcd7318
  divergent
  
  diff --git a/bdivergent2 b/bdivergent2
  new file mode 100644
  --- /dev/null
  +++ b/bdivergent2
  @@ -0,0 +1,1 @@
  +bdivergent

  $ hg prune -s 8374d2ddc3a4 "desc('added b')"
  1 changesets pruned
  $ hg prune -s 593c57f2117e "desc('added b')" --hidden
  1 changesets pruned
  2 new content-divergent changesets

  $ hg log -G --patch
  @  3:8374d2ddc3a4@default(draft) divergent [content-divergent]
  |  diff --git a/bdivergent2 b/bdivergent2
  |  new file mode 100644
  |  --- /dev/null
  |  +++ b/bdivergent2
  |  @@ -0,0 +1,1 @@
  |  +bdivergent
  |
  | *  2:593c57f2117e@default(draft) divergent [content-divergent]
  |/   diff --git a/bdivergent1 b/bdivergent1
  |    new file mode 100644
  |    --- /dev/null
  |    +++ b/bdivergent1
  |    @@ -0,0 +1,1 @@
  |    +bdivergent
  |
  o  0:9092f1db7931@default(draft) added a []
     diff --git a/a b/a
     new file mode 100644
     --- /dev/null
     +++ b/a
     @@ -0,0 +1,1 @@
     +a
  

  $ hg evolve --all --any --content-divergent
  merge:[2] divergent
  with: [3] divergent
  base: [1] added b
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 98ab969ac8fb
  $ hg log -G
  @  4:98ab969ac8fb@default(draft) divergent []
  |
  o  0:9092f1db7931@default(draft) added a []
  
  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 98ab969ac8fbe315e6d2c24a8eb5eab5b81e4242
  # Parent  9092f1db7931481f93b37d5c9fbcfc341bcd7318
  divergent
  
  diff --git a/bdivergent1 b/bdivergent1
  new file mode 100644
  --- /dev/null
  +++ b/bdivergent1
  @@ -0,0 +1,1 @@
  +bdivergent
  diff --git a/bdivergent2 b/bdivergent2
  new file mode 100644
  --- /dev/null
  +++ b/bdivergent2
  @@ -0,0 +1,1 @@
  +bdivergent

  $ cd ..

Extra setup
-----------

(the test below were initially in a different file)

  $ hg init cdiv
  $ cd cdiv
  $ echo ".*\.orig" > .hgignore
  $ hg add .hgignore
  $ hg ci -m "added hgignore"
  $ for ch in a b c d; do echo foo > $ch; hg add $ch; hg ci -qm "added "$ch; done;

  $ hg glog
  @  4:c41c793e0ef1 added d
  |   () [default] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

Merging branch difference
-------------------------

Creating content-divergence with branch change where base, divergent and other
have different branches

  $ hg branch -r . foobar
  changed branch on 1 changesets

  $ hg up c41c793e0ef1 --hidden
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset c41c793e0ef1
  (hidden revision 'c41c793e0ef1' was rewritten as: 9e5dffcb3d48)
  working directory parent is obsolete! (c41c793e0ef1)
  (use 'hg evolve' to update to its successor: 9e5dffcb3d48)
  $ echo bar > d
  $ hg branch watwat
  marked working directory as branch watwat
  $ hg amend
  2 new content-divergent changesets

  $ hg glog
  @  6:264b04f771fb added d
  |   () [watwat] draft
  | *  5:9e5dffcb3d48 added d
  |/    () [foobar] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg evolve --content-divergent --no-all --config ui.interactive=True << EOF
  > c
  > EOF
  merge:[6] added d
  with: [5] added d
  base: [4] added d
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  content divergent changesets on different branches.
  choose branch for the resolution changeset. (a) default or (b) watwat or (c) foobar?  c
  working directory is now at 15ee7f765bf7

  $ hg glog
  @  7:15ee7f765bf7 added d
  |   () [foobar] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

Testing merging of commit messages
-----------------------------------

When base and one of the divergent has same commit messages and other divergent
has different one

  $ echo wat > d
  $ hg amend

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved

  $ echo bar > d
  $ hg ci -Aqm "added a d with bar in it, expect some beers"

  $ hg prune -r 'predecessors(desc("added d") - obsolete())' -s . --hidden
  1 changesets pruned
  2 new content-divergent changesets

  $ hg glog
  @  9:59081c9c425a added a d with bar in it, expect some beers
  |   () [default] draft
  | *  8:e6f07f2f33a9 added d
  |/    () [foobar] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg evolve --content-divergent --no-all
  merge:[9] added a d with bar in it, expect some beers
  with: [8] added d
  base: [7] added d
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 34e78e1673c1

  $ hg glog
  @  10:34e78e1673c1 added a d with bar in it, expect some beers
  |   () [default] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

When base has different message and both divergents has same one

  $ echo foo > d
  $ hg amend -m "foo to d"

  $ hg up 'predecessors(.)' --hidden
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 34e78e1673c1
  (hidden revision '34e78e1673c1' was rewritten as: c9d0d72972b0)
  working directory parent is obsolete! (34e78e1673c1)
  (use 'hg evolve' to update to its successor: c9d0d72972b0)
  $ echo babar > d
  $ hg amend -m "foo to d"
  2 new content-divergent changesets

  $ hg glog
  @  12:b4dadb3b47a7 foo to d
  |   () [default] draft
  | *  11:c9d0d72972b0 foo to d
  |/    () [default] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg evolve --content-divergent --no-all
  merge:[12] foo to d
  with: [11] foo to d
  base: [10] added a d with bar in it, expect some beers
  merging d
  warning: conflicts while merging d! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo foobar > d
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  working directory is now at cfd599de811a

  $ hg glog
  @  13:cfd599de811a foo to d
  |   () [default] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

When all three base, divergent and other has different commit messages creating
conflicts

  $ echo bar > d
  $ hg amend -m "bar to d, expect beers"

  $ hg up 'predecessors(.)' --hidden
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset cfd599de811a
  (hidden revision 'cfd599de811a' was rewritten as: ba0941ffb747)
  working directory parent is obsolete! (cfd599de811a)
  (use 'hg evolve' to update to its successor: ba0941ffb747)
  $ echo wat > d
  $ hg amend -m "wat to d, wat?"
  2 new content-divergent changesets

  $ hg glog
  @  15:4127dd63df67 wat to d, wat?
  |   () [default] draft
  | *  14:ba0941ffb747 bar to d, expect beers
  |/    () [default] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg evolve --content-divergent --no-all
  merge:[15] wat to d, wat?
  with: [14] bar to d, expect beers
  base: [13] foo to d
  merging d
  warning: conflicts while merging d! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo watbar > d
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ cat > editor.sh <<EOF
  > #!/bin/sh
  > printf "**showing editors text**\n\n"
  > cat \$1
  > printf "\n**done showing editors text**\n\n"
  > cat > \$1 <<ENDOF
  > watbar to d
  > ENDOF
  > EOF

  $ HGEDITOR='sh ./editor.sh' hg evolve --continue
  **showing editors text**
  
  HG: Conflicts while merging changeset description of content-divergent changesets.
  HG: Resolve conflicts in commit messages to continue.
  
  <<<<<<< divergent
  wat to d, wat?||||||| base
  foo to d=======
  bar to d, expect beers>>>>>>> other
  
  **done showing editors text**
  
  working directory is now at b4c8664fa327

  $ hg glog
  @  16:b4c8664fa327 watbar to d
  |   () [default] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ cd ..

Stabilize content-divergent changesets with same parent
=======================================================


  $ glog() {
  >   hg log -G --template \
  >     '{rev}:{node|short}@{branch}({phase}) bk:[{bookmarks}] {desc|firstline}\n' "$@"
  > }

  $ hg init content-divergent-savanna
  $ cd content-divergent-savanna
  $ echo a > a
  $ hg add a
  $ hg ci -m 'root'
  $ hg phase --public .
  $ cat << EOF >> a
  > flore
  > arthur
  > zephir
  > some
  > less
  > conflict
  > EOF
  $ hg ci -m 'More addition'
  $ glog
  @  1:867e43582046@default(draft) bk:[] More addition
  |
  o  0:6569b5a81c7e@default(public) bk:[] root
  
  $ echo 'babar' >> a
  $ hg amend
  $ hg up --hidden 'min(desc("More addition"))'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 867e43582046
  (hidden revision '867e43582046' was rewritten as: fc6349f931da)
  working directory parent is obsolete! (867e43582046)
  (use 'hg evolve' to update to its successor: fc6349f931da)
  $ mv a a.old
  $ echo 'jungle' > a
  $ cat a.old >> a
  $ rm a.old
  $ hg amend
  2 new content-divergent changesets
  $ glog
  @  3:051337a45e7c@default(draft) bk:[] More addition
  |
  | *  2:fc6349f931da@default(draft) bk:[] More addition
  |/
  o  0:6569b5a81c7e@default(public) bk:[] root
  

Stabilize it

  $ hg evolve -qn --confirm --content-divergent --no-all
  merge:[3] More addition
  with: [2] More addition
  base: [1] More addition
  perform evolve? [Ny] n
  abort: evolve aborted by user
  [255]
  $ echo y | hg evolve -qn --confirm --config ui.interactive=True --content-divergent --no-all
  merge:[3] More addition
  with: [2] More addition
  base: [1] More addition
  perform evolve? [Ny] y
  hg update -c 051337a45e7c &&
  hg merge fc6349f931da &&
  hg commit -m "auto merge resolving conflict between 051337a45e7c and fc6349f931da"&&
  hg up -C 867e43582046 &&
  hg revert --all --rev tip &&
  hg commit -m "`hg log -r 051337a45e7c --template={desc}`";
  $ hg evolve -v --content-divergent --no-all
  merge:[3] More addition
  with: [2] More addition
  base: [1] More addition
  merging "other" content-divergent changeset fc6349f931da
  resolving manifests
  merging a
  0 files updated, 1 files merged, 0 files removed, 0 files unresolved
  committing files:
  a
  committing manifest
  committing changelog
  working directory is now at 6aa6f90a9f68
  $ hg st
  $ glog
  @  4:6aa6f90a9f68@default(draft) bk:[] More addition
  |
  o  0:6569b5a81c7e@default(public) bk:[] root
  
  $ hg summary
  parent: 4:6aa6f90a9f68 tip
   More addition
  branch: default
  commit: (clean)
  update: (current)
  phases: 1 draft
  $ hg export . --config diff.unified=3
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 6aa6f90a9f684b8a4b698234e25c5dad7328b199
  # Parent  6569b5a81c7e307ddc076550e8c0f6d75b6effcd
  More addition
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,9 @@
  +jungle
   a
  +flore
  +arthur
  +zephir
  +some
  +less
  +conflict
  +babar

Check conflict during content-divergence resolution
---------------------------------------------------


  $ hg up --hidden 'min(desc("More addition"))'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 867e43582046
  (hidden revision '867e43582046' was rewritten as: 6aa6f90a9f68)
  working directory parent is obsolete! (867e43582046)
  (use 'hg evolve' to update to its successor: 6aa6f90a9f68)
  $ echo 'gotta break' >> a
  $ hg amend
  2 new content-divergent changesets

# reamend so that the case is not the first precursor.

  $ hg amend -m "More addition (2)"
  $ hg phase 'contentdivergent()'
  4: draft
  6: draft

  $ glog
  @  6:13c1b75640a1@default(draft) bk:[] More addition (2)
  |
  | *  4:6aa6f90a9f68@default(draft) bk:[] More addition
  |/
  o  0:6569b5a81c7e@default(public) bk:[] root
  

  $ hg evolve -qn --content-divergent --no-all
  hg update -c 13c1b75640a1 &&
  hg merge 6aa6f90a9f68 &&
  hg commit -m "auto merge resolving conflict between 13c1b75640a1 and 6aa6f90a9f68"&&
  hg up -C 867e43582046 &&
  hg revert --all --rev tip &&
  hg commit -m "`hg log -r 13c1b75640a1 --template={desc}`";
  $ hg evolve --content-divergent --no-all
  merge:[6] More addition (2)
  with: [4] More addition
  base: [1] More addition
  merging a
  warning: conflicts while merging a! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ cat > a <<EOF
  > jungle
  > a
  > flore
  > arthur
  > zephir
  > some
  > less
  > conflict
  > babar
  > EOF

  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  working directory is now at 22dc0f618f0d
  $ glog
  @  7:22dc0f618f0d@default(draft) bk:[] More addition (2)
  |
  o  0:6569b5a81c7e@default(public) bk:[] root
  
  $ hg exp  --config diff.unified=3
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 22dc0f618f0d8714c611e7a683ad229a575f167c
  # Parent  6569b5a81c7e307ddc076550e8c0f6d75b6effcd
  More addition (2)
  
  diff --git a/a b/a
  --- a/a
  +++ b/a
  @@ -1,1 +1,9 @@
  +jungle
   a
  +flore
  +arthur
  +zephir
  +some
  +less
  +conflict
  +babar
  $ cd ..

Check case where one side undo some of the common predecessors change
---------------------------------------------------------------------

The goal is to make sure we merge using the right base.

  $ hg init predecessors-as-merge-base
  $ cd predecessors-as-merge-base
  $ cat << EOF > numbers
  > 1
  > 2
  > 3
  > 4
  > 5
  > 6
  > 7
  > 8
  > 9
  > EOF
  $ cat << EOF > letters
  > a
  > b
  > c
  > d
  > e
  > f
  > g
  > h
  > i
  > EOF
  $ cat << EOF > romans
  > I
  > II
  > III
  > IV
  > V
  > VI
  > VII
  > VIII
  > IX
  > EOF
  $ hg add numbers letters romans
  $ hg commit -m root
  $ cat << EOF > numbers
  > 1
  > 2
  > 3
  > four
  > 5
  > 6
  > 7
  > 8
  > 9
  > EOF
  $ cat << EOF > letters
  > a
  > b
  > c
  > D
  > e
  > f
  > g
  > h
  > i
  > EOF
  $ hg commit -m E1
  $ cat << EOF > numbers
  > 1
  > 2
  > 3
  > 4
  > 5
  > 6
  > seven
  > 8
  > 9
  > EOF
  $ cat << EOF > romans
  > I
  > II
  > III
  > IV
  > V
  > vi
  > VII
  > VIII
  > IX
  > EOF
  $ hg commit --amend -m E2
  $ hg --hidden update -r 'desc(E1)'
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 4a250e5bd992
  (hidden revision '4a250e5bd992' was rewritten as: 084ae625fa51)
  working directory parent is obsolete! (4a250e5bd992)
  (use 'hg evolve' to update to its successor: 084ae625fa51)
  $ cat << EOF > numbers
  > one
  > 2
  > 3
  > four
  > 5
  > 6
  > 7
  > 8
  > 9
  > EOF
  $ cat << EOF > letters
  > a
  > b
  > c
  > d
  > e
  > f
  > g
  > h
  > i
  > EOF
  $ cat << EOF > romans
  > I
  > ii
  > III
  > IV
  > V
  > VI
  > VII
  > VIII
  > IX
  > EOF
  $ hg commit --amend -m E3
  2 new content-divergent changesets
  $ hg log -G --patch --hidden
  @  3:19ed1bf64a2c@default(draft) E3 [content-divergent]
  |  diff --git a/numbers b/numbers
  |  --- a/numbers
  |  +++ b/numbers
  |  @@ -1,1 +1,1 @@
  |  -1
  |  +one
  |  @@ -4,1 +4,1 @@
  |  -4
  |  +four
  |  diff --git a/romans b/romans
  |  --- a/romans
  |  +++ b/romans
  |  @@ -2,1 +2,1 @@
  |  -II
  |  +ii
  |
  | *  2:084ae625fa51@default(draft) E2 [content-divergent]
  |/   diff --git a/letters b/letters
  |    --- a/letters
  |    +++ b/letters
  |    @@ -4,1 +4,1 @@
  |    -d
  |    +D
  |    diff --git a/numbers b/numbers
  |    --- a/numbers
  |    +++ b/numbers
  |    @@ -7,1 +7,1 @@
  |    -7
  |    +seven
  |    diff --git a/romans b/romans
  |    --- a/romans
  |    +++ b/romans
  |    @@ -6,1 +6,1 @@
  |    -VI
  |    +vi
  |
  | x  1:4a250e5bd992@default(draft) E1 []
  |/   diff --git a/letters b/letters
  |    --- a/letters
  |    +++ b/letters
  |    @@ -4,1 +4,1 @@
  |    -d
  |    +D
  |    diff --git a/numbers b/numbers
  |    --- a/numbers
  |    +++ b/numbers
  |    @@ -4,1 +4,1 @@
  |    -4
  |    +four
  |
  o  0:6d1fdf6de7e2@default(draft) root []
     diff --git a/letters b/letters
     new file mode 100644
     --- /dev/null
     +++ b/letters
     @@ -0,0 +1,9 @@
     +a
     +b
     +c
     +d
     +e
     +f
     +g
     +h
     +i
     diff --git a/numbers b/numbers
     new file mode 100644
     --- /dev/null
     +++ b/numbers
     @@ -0,0 +1,9 @@
     +1
     +2
     +3
     +4
     +5
     +6
     +7
     +8
     +9
     diff --git a/romans b/romans
     new file mode 100644
     --- /dev/null
     +++ b/romans
     @@ -0,0 +1,9 @@
     +I
     +II
     +III
     +IV
     +V
     +VI
     +VII
     +VIII
     +IX
  
  $ hg evolve --list
  084ae625fa51: E2
    content-divergent: 19ed1bf64a2c (draft) (precursor 4a250e5bd992)
  
  19ed1bf64a2c: E3
    content-divergent: 084ae625fa51 (draft) (precursor 4a250e5bd992)
  
  $ hg debugobsolete
  4a250e5bd992a897655e3b6f238e12452cf063e9 084ae625fa51ca8c441ba1d2bf0f974b21671017 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  4a250e5bd992a897655e3b6f238e12452cf063e9 19ed1bf64a2cc2a824df5ac33a436eca1ae0475d 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  $ hg obslog --all --patch
  *  084ae625fa51 (2) E2
  |    rewritten(description, content) from 4a250e5bd992 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 4a250e5bd992 -r 084ae625fa51 changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -E1
  |      +E2
  |
  |      diff --git a/numbers b/numbers
  |      --- a/numbers
  |      +++ b/numbers
  |      @@ -4,1 +4,1 @@
  |      -four
  |      +4
  |      @@ -7,1 +7,1 @@
  |      -7
  |      +seven
  |      diff --git a/romans b/romans
  |      --- a/romans
  |      +++ b/romans
  |      @@ -6,1 +6,1 @@
  |      -VI
  |      +vi
  |
  |
  | @  19ed1bf64a2c (3) E3
  |/     rewritten(description, content) from 4a250e5bd992 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r 4a250e5bd992 -r 19ed1bf64a2c changeset-description
  |        --- a/changeset-description
  |        +++ b/changeset-description
  |        @@ -1,1 +1,1 @@
  |        -E1
  |        +E3
  |
  |        diff --git a/letters b/letters
  |        --- a/letters
  |        +++ b/letters
  |        @@ -4,1 +4,1 @@
  |        -D
  |        +d
  |        diff --git a/numbers b/numbers
  |        --- a/numbers
  |        +++ b/numbers
  |        @@ -1,1 +1,1 @@
  |        -1
  |        +one
  |        diff --git a/romans b/romans
  |        --- a/romans
  |        +++ b/romans
  |        @@ -2,1 +2,1 @@
  |        -II
  |        +ii
  |
  |
  x  4a250e5bd992 (1) E1
  

  $ hg evolve --content-divergent --rev 'desc("E3")'
  merge:[2] E2
  with: [3] E3
  base: [1] E1
  merging numbers
  merging romans
  1 files updated, 2 files merged, 0 files removed, 0 files unresolved
  working directory is now at e7cb08a7241a
  $ hg status
  $ hg amend -m 'E4'
  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 50bb00cad3206c79d231a621e319772302a88d8d
  # Parent  6d1fdf6de7e2d9fc9b098aa286b60785bbeaab7a
  E4
  
  diff --git a/numbers b/numbers
  --- a/numbers
  +++ b/numbers
  @@ -1,1 +1,1 @@
  -1
  +one
  @@ -7,1 +7,1 @@
  -7
  +seven
  diff --git a/romans b/romans
  --- a/romans
  +++ b/romans
  @@ -2,1 +2,1 @@
  -II
  +ii
  @@ -6,1 +6,1 @@
  -VI
  +vi
  $ hg log -G
  @  5:50bb00cad320@default(draft) E4 []
  |
  o  0:6d1fdf6de7e2@default(draft) root []
  
  $ hg debugobsolete
  4a250e5bd992a897655e3b6f238e12452cf063e9 084ae625fa51ca8c441ba1d2bf0f974b21671017 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  4a250e5bd992a897655e3b6f238e12452cf063e9 19ed1bf64a2cc2a824df5ac33a436eca1ae0475d 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  084ae625fa51ca8c441ba1d2bf0f974b21671017 e7cb08a7241a98c908db298b61fc033b27f648c7 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'evolve', 'user': 'test'}
  19ed1bf64a2cc2a824df5ac33a436eca1ae0475d e7cb08a7241a98c908db298b61fc033b27f648c7 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'evolve', 'user': 'test'}
  e7cb08a7241a98c908db298b61fc033b27f648c7 50bb00cad3206c79d231a621e319772302a88d8d 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'operation': 'amend', 'user': 'test'}
  $ hg obslog --patch
  @  50bb00cad320 (5) E4
  |    reworded(description) from e7cb08a7241a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r e7cb08a7241a -r 50bb00cad320 changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,4 +1,1 @@
  |      -<<<<<<< divergent
  |      -E2||||||| base
  |      -E1=======
  |      -E3>>>>>>> other
  |      +E4
  |
  |
  x    e7cb08a7241a (4) <<<<<<< divergent
  |\     rewritten(description, content) from 084ae625fa51 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |      diff -r 084ae625fa51 -r e7cb08a7241a changeset-description
  | |      --- a/changeset-description
  | |      +++ b/changeset-description
  | |      @@ -1,1 +1,4 @@
  | |      -E2
  | |      +<<<<<<< divergent
  | |      +E2||||||| base
  | |      +E1=======
  | |      +E3>>>>>>> other
  | |
  | |      diff --git a/letters b/letters
  | |      --- a/letters
  | |      +++ b/letters
  | |      @@ -4,1 +4,1 @@
  | |      -D
  | |      +d
  | |      diff --git a/numbers b/numbers
  | |      --- a/numbers
  | |      +++ b/numbers
  | |      @@ -1,1 +1,1 @@
  | |      -1
  | |      +one
  | |      diff --git a/romans b/romans
  | |      --- a/romans
  | |      +++ b/romans
  | |      @@ -2,1 +2,1 @@
  | |      -II
  | |      +ii
  | |
  | |    rewritten(description, content) from 19ed1bf64a2c using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |      diff -r 19ed1bf64a2c -r e7cb08a7241a changeset-description
  | |      --- a/changeset-description
  | |      +++ b/changeset-description
  | |      @@ -1,1 +1,4 @@
  | |      -E3
  | |      +<<<<<<< divergent
  | |      +E2||||||| base
  | |      +E1=======
  | |      +E3>>>>>>> other
  | |
  | |      diff --git a/numbers b/numbers
  | |      --- a/numbers
  | |      +++ b/numbers
  | |      @@ -4,1 +4,1 @@
  | |      -four
  | |      +4
  | |      @@ -7,1 +7,1 @@
  | |      -7
  | |      +seven
  | |      diff --git a/romans b/romans
  | |      --- a/romans
  | |      +++ b/romans
  | |      @@ -6,1 +6,1 @@
  | |      -VI
  | |      +vi
  | |
  | |
  x |  084ae625fa51 (2) E2
  | |    rewritten(description, content) from 4a250e5bd992 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  | |      diff -r 4a250e5bd992 -r 084ae625fa51 changeset-description
  | |      --- a/changeset-description
  | |      +++ b/changeset-description
  | |      @@ -1,1 +1,1 @@
  | |      -E1
  | |      +E2
  | |
  | |      diff --git a/numbers b/numbers
  | |      --- a/numbers
  | |      +++ b/numbers
  | |      @@ -4,1 +4,1 @@
  | |      -four
  | |      +4
  | |      @@ -7,1 +7,1 @@
  | |      -7
  | |      +seven
  | |      diff --git a/romans b/romans
  | |      --- a/romans
  | |      +++ b/romans
  | |      @@ -6,1 +6,1 @@
  | |      -VI
  | |      +vi
  | |
  | |
  | x  19ed1bf64a2c (3) E3
  |/     rewritten(description, content) from 4a250e5bd992 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r 4a250e5bd992 -r 19ed1bf64a2c changeset-description
  |        --- a/changeset-description
  |        +++ b/changeset-description
  |        @@ -1,1 +1,1 @@
  |        -E1
  |        +E3
  |
  |        diff --git a/letters b/letters
  |        --- a/letters
  |        +++ b/letters
  |        @@ -4,1 +4,1 @@
  |        -D
  |        +d
  |        diff --git a/numbers b/numbers
  |        --- a/numbers
  |        +++ b/numbers
  |        @@ -1,1 +1,1 @@
  |        -1
  |        +one
  |        diff --git a/romans b/romans
  |        --- a/romans
  |        +++ b/romans
  |        @@ -2,1 +2,1 @@
  |        -II
  |        +ii
  |
  |
  x  4a250e5bd992 (1) E1
  

