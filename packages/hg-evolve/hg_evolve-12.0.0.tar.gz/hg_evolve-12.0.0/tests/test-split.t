test of the split command
-----------------------

  $ . $TESTDIR/testlib/common.sh

  $ cat >> $HGRCPATH <<EOF
  > [alias]
  > glog = log -G -T "{rev}:{node|short} {desc|firstline} ({phase})\n"
  > [diff]
  > git = 1
  > unified = 0
  > [commands]
  > commit.interactive.unified = 0
  > [ui]
  > interactive = true
  > [extensions]
  > evolve =
  > EOF
  $ mkcommit() {
  >    echo "$1" > "$1"
  >    hg add "$1"
  >    hg ci -m "add $1" $2 $3
  > }
  $ cat > $TESTTMP/editor.sh << '__EOF__'
  > NUM=$(cat "$TESTTMP/split-counter")
  > NUM=`expr "$NUM" + 1`
  > echo "$NUM" > "$TESTTMP/split-counter"
  > echo "split$NUM" > "$1"
  > __EOF__
  $ export HGEDITOR="\"sh\" \"$TESTTMP/editor.sh\""

Basic case, split a head
  $ hg init testsplit
  $ cd testsplit
  $ mkcommit _a
  $ mkcommit _b
  $ mkcommit _c --user other-test-user
  $ mkcommit _d
  $ echo "change to a" >> _a
  $ hg amend
  $ hg debugobsolete
  1334a80b33c3f9873edab728fbbcf500eab61d2e d2fe56e71366c2c5376c89960c281395062c0619 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}

Creating commits with the number of split
  $ echo 0 > $TESTTMP/split-counter
  $ hg split << EOF
  > y
  > y
  > y
  > n
  > Y
  > y
  > y
  > EOF
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  reverting _a
  adding _d
  diff --git a/_a b/_a
  1 hunks, 1 lines changed
  examine changes to '_a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -1,0 +2,1 @@* (glob)
  +change to a
  record change 1/2 to '_a'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/_d b/_d
  new file mode 100644
  examine changes to '_d'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +_d
  record change 2/2 to '_d'?
  (enter ? for help) [Ynesfdaq?] n
  
  created new head
  continue splitting? [Ycdq?] Y
  diff --git a/_d b/_d
  new file mode 100644
  examine changes to '_d'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +_d
  record this change to '_d'?
  (enter ? for help) [Ynesfdaq?] y
  
  no more changes to split

  $ hg debugobsolete
  1334a80b33c3f9873edab728fbbcf500eab61d2e d2fe56e71366c2c5376c89960c281395062c0619 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  d2fe56e71366c2c5376c89960c281395062c0619 2d8abdb827cdf71ca477ef6985d7ceb257c53c1b 033b3f5ae73db67c10de938fb6f26b949aaef172 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'split', 'user': 'test'}
  $ hg log -G
  @  changeset:   6:033b3f5ae73d
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     split2
  |
  o  changeset:   5:2d8abdb827cd
  |  parent:      2:52149352b372
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     split1
  |
  o  changeset:   2:52149352b372
  |  user:        other-test-user
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add _c
  |
  o  changeset:   1:37445b16603b
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add _b
  |
  o  changeset:   0:135f39f4bd78
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     add _a
  

Cannot split a commit with uncommitted changes
  $ hg up "desc(_c)"
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo "_cd" > _c
  $ hg split
  abort: uncommitted changes
  [20]
  $ hg up "desc(_c)" -C
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

Cannot split public changeset

  $ hg phase --rev 'desc("_a")'
  0: draft
  $ hg phase --rev 'desc("_a")' --public
  $ hg split --rev 'desc("_a")'
  abort: cannot split public changesets: 135f39f4bd78
  (see 'hg help phases' for details)
  [10]
  $ hg phase --rev 'desc("_a")' --draft --force

Split a revision specified with -r
  $ echo "change to b" >> _b
  $ hg amend -m "_cprim"
  2 new orphan changesets
  $ hg evolve --all --update
  move:[5] split1
  atop:[7] _cprim
  move:[6] split2
  working directory is now at * (glob)
  $ hg log -r "desc(_cprim)" -v -p
  changeset:   7:b434287e665c
  parent:      1:37445b16603b
  user:        other-test-user
  date:        Thu Jan 01 00:00:00 1970 +0000
  files:       _b _c
  description:
  _cprim
  
  
  diff --git a/_b b/_b
  --- a/_b
  +++ b/_b
  @@ -1,0 +2,1 @@
  +change to b
  diff --git a/_c b/_c
  new file mode 100644
  --- /dev/null
  +++ b/_c
  @@ -0,0 +1,1 @@
  +_c
  
  $ hg split -r "desc(_cprim)" <<EOF
  > y
  > y
  > y
  > n
  > c
  > EOF
  2 files updated, 0 files merged, 2 files removed, 0 files unresolved
  reverting _b
  adding _c
  diff --git a/_b b/_b
  1 hunks, 1 lines changed
  examine changes to '_b'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -1,0 +2,1 @@* (glob)
  +change to b
  record change 1/2 to '_b'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/_c b/_c
  new file mode 100644
  examine changes to '_c'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +_c
  record change 2/2 to '_c'?
  (enter ? for help) [Ynesfdaq?] n
  
  created new head
  continue splitting? [Ycdq?] c
  2 new orphan changesets

Stop before splitting the commit completely creates a commit with all the
remaining changes

  $ hg debugobsolete
  1334a80b33c3f9873edab728fbbcf500eab61d2e d2fe56e71366c2c5376c89960c281395062c0619 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  d2fe56e71366c2c5376c89960c281395062c0619 2d8abdb827cdf71ca477ef6985d7ceb257c53c1b 033b3f5ae73db67c10de938fb6f26b949aaef172 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'split', 'user': 'test'}
  52149352b372d39b19127d5bd2d488b1b63f9f85 b434287e665ce757ee5463a965cb3d119ca9e893 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  2d8abdb827cdf71ca477ef6985d7ceb257c53c1b e2b4afde39803bd42bb1374b230fca1b1e8cc868 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  033b3f5ae73db67c10de938fb6f26b949aaef172 bb5e4f6020c74e7961a51fda635ea9df9b04dda8 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  b434287e665ce757ee5463a965cb3d119ca9e893 ead2066d1dbf14833fe1069df1b735e4e9468c40 1188c4216eba37f18a1de6558564601d00ff2143 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'split', 'user': 'test'}
  $ hg evolve --all --update
  move:[8] split1
  atop:[11] split4
  move:[9] split2
  working directory is now at d74c6715e706
  $ hg log -G
  @  changeset:   13:d74c6715e706
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     split2
  |
  o  changeset:   12:3f134f739075
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     split1
  |
  o  changeset:   11:1188c4216eba
  |  user:        other-test-user
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     split4
  |
  o  changeset:   10:ead2066d1dbf
  |  parent:      1:37445b16603b
  |  user:        other-test-user
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     split3
  |
  o  changeset:   1:37445b16603b
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add _b
  |
  o  changeset:   0:135f39f4bd78
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     add _a
  

Split should move bookmarks on the last split successor and preserve the
active bookmark as active
  $ hg book bookA
  $ hg book bookB
  $ echo "changetofilea" > _a
  $ hg amend
  $ hg book
     bookA                     14:7a6b35779b85
   * bookB                     14:7a6b35779b85
  $ hg log -G -r "3f134f739075::"
  @  changeset:   14:7a6b35779b85
  |  bookmark:    bookA
  |  bookmark:    bookB
  |  tag:         tip
  |  parent:      12:3f134f739075
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     split2
  |
  o  changeset:   12:3f134f739075
  |  user:        test
  ~  date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     split1
  
  $ hg split --user victor <<EOF
  > y
  > y
  > n
  > c
  > EOF
  (leaving bookmark bookB)
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  reverting _a
  adding _d
  diff --git a/_a b/_a
  1 hunks, 2 lines changed
  examine changes to '_a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -1,2 +1,1 @@
  -_a
  -change to a
  +changetofilea
  record change 1/2 to '_a'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/_d b/_d
  new file mode 100644
  examine changes to '_d'?
  (enter ? for help) [Ynesfdaq?] n
  
  created new head
  continue splitting? [Ycdq?] c
  $ hg log -G -r "3f134f739075::"
  @  changeset:   16:452a26648478
  |  bookmark:    bookA
  |  bookmark:    bookB
  |  tag:         tip
  |  user:        victor
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     split6
  |
  o  changeset:   15:1315679b77dc
  |  parent:      12:3f134f739075
  |  user:        victor
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     split5
  |
  o  changeset:   12:3f134f739075
  |  user:        test
  ~  date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     split1
  
  $ hg book
     bookA                     16:452a26648478
   * bookB                     16:452a26648478
 
Lastest revision is selected if multiple are given to -r
  $ hg split -r "desc(_a)::"
  (leaving bookmark bookB)
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  adding _d
  diff --git a/_d b/_d
  new file mode 100644
  examine changes to '_d'?
  (enter ? for help) [Ynesfdaq?] abort: response expected
  [255]

Cannot split a commit that is not a head if instability is not allowed
  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution=createmarkers
  > evolutioncommands=split
  > EOF
  $ hg split -r "desc(split3)"
  abort: cannot split changeset, as that will orphan 4 descendants
  (see 'hg help evolution.instability')
  [10]

Changing evolution level to createmarkers
  $ echo "[experimental]" >> $HGRCPATH
  $ echo "evolution=createmarkers" >> $HGRCPATH

Running split without any revision operates on the parent of the working copy
  $ hg split << EOF
  > q
  > EOF
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  adding _d
  diff --git a/_d b/_d
  new file mode 100644
  examine changes to '_d'?
  (enter ? for help) [Ynesfdaq?] q
  
  abort: user quit
  [250]

Running split with tip revision, specified as unnamed argument
  $ hg split --rev . << EOF
  > q
  > EOF
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  adding _d
  diff --git a/_d b/_d
  new file mode 100644
  examine changes to '_d'?
  (enter ? for help) [Ynesfdaq?] q
  
  abort: user quit
  [250]

Running split with both unnamed and named revision arguments shows an error msg
  $ hg split  --rev . --rev .^ << EOF
  > q
  > EOF
  abort: more than one revset is given
  [255]

Split empty commit (issue5191)
  $ hg branch double//slash
  marked working directory as branch double//slash
  (branches are permanent and global, did you want a bookmark?)
  $ hg commit -m "empty"
  $ hg split
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

Check that split keeps the right topic

  $ hg up -r tip
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

Add topic to the hgrc

  $ echo "[extensions]" >> $HGRCPATH
  $ echo "topic=$(echo $(dirname $TESTDIR))/hgext3rd/topic/" >> $HGRCPATH
  $ hg debug-topic-namespace mynamespace
  marked working directory as topic namespace: mynamespace
  $ hg topic mytopic
  marked working directory as topic: mytopic
  $ echo babar > babar
  $ echo celeste > celeste
  $ hg add babar celeste
  $ hg commit -m "Works on mytopic" babar celeste --user victor
  active topic 'mytopic' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg log -r .
  changeset:   18:4f0e158045aa
  branch:      double//slash
  tag:         tip
  topic:       mytopic
  user:        victor
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Works on mytopic
  
  $ hg summary
  parent: 18:4f0e158045aa tip
   Works on mytopic
  branch: double//slash//mynamespace/mytopic
  commit: (clean)
  update: (current)
  phases: 9 draft
  topic:  mytopic

  $ hg log -r . -T '{rev}: {fqbn}\n'
  18: double//slash//mynamespace/mytopic

Split it

  $ hg split -U << EOF
  > Y
  > Y
  > N
  > c
  > Y
  > Y
  > EOF
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  adding babar
  adding celeste
  diff --git a/babar b/babar
  new file mode 100644
  examine changes to 'babar'?
  (enter ? for help) [Ynesfdaq?] Y
  
  @@ -0,0 +1,1 @@
  +babar
  record change 1/2 to 'babar'?
  (enter ? for help) [Ynesfdaq?] Y
  
  diff --git a/celeste b/celeste
  new file mode 100644
  examine changes to 'celeste'?
  (enter ? for help) [Ynesfdaq?] N
  
  continue splitting? [Ycdq?] c

Check that the topic is still here

  $ hg log -r "tip~1::"
  changeset:   19:d8d795e8424a
  branch:      double//slash
  topic:       mytopic
  parent:      17:db45bd0f0e52
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     split7
  
  changeset:   20:d6d47657e765
  branch:      double//slash
  tag:         tip
  topic:       mytopic
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     split8
  
  $ hg topic
   * mytopic (2 changesets)

  $ hg log -r "tip~1::" -T '{rev}: {fqbn}\n'
  19: double//slash//mynamespace/mytopic
  20: double//slash//mynamespace/mytopic

Check commit extras

  $ hg log -r "tip~1::" -T '{rev}: {join(extras, " ")}\n'
  19: branch=double//slash topic=mytopic topic-namespace=mynamespace
  20: branch=double//slash topic=mytopic topic-namespace=mynamespace

Test split the first commit on a branch

  $ touch SPLIT1 SPLIT2
  $ hg add SPLIT1 SPLIT2
  $ hg branch another-branch
  marked working directory as branch another-branch
  $ hg commit -m "To be split"
  $ hg log -G -l 3
  @  changeset:   21:94981e5d988e
  |  branch:      another-branch
  |  tag:         tip
  |  topic:       mytopic
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     To be split
  |
  o  changeset:   20:d6d47657e765
  |  branch:      double//slash
  |  topic:       mytopic
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     split8
  |
  o  changeset:   19:d8d795e8424a
  |  branch:      double//slash
  ~  topic:       mytopic
     parent:      17:db45bd0f0e52
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     split7
  
  $ hg export .
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Branch another-branch
  # Node ID 94981e5d988ea23cf2b17f6c07c39edc0f174b01
  # Parent  d6d47657e765570283ec03fc68836d9eb297c4b3
  # EXP-Topic-Namespace mynamespace
  # EXP-Topic mytopic
  To be split
  
  diff --git a/SPLIT1 b/SPLIT1
  new file mode 100644
  diff --git a/SPLIT2 b/SPLIT2
  new file mode 100644

  $ hg split -r . << EOF
  > Y
  > N
  > Y
  > Y
  > EOF
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  adding SPLIT1
  adding SPLIT2
  diff --git a/SPLIT1 b/SPLIT1
  new file mode 100644
  examine changes to 'SPLIT1'?
  (enter ? for help) [Ynesfdaq?] Y
  
  diff --git a/SPLIT2 b/SPLIT2
  new file mode 100644
  examine changes to 'SPLIT2'?
  (enter ? for help) [Ynesfdaq?] N
  
  continue splitting? [Ycdq?] Y
  diff --git a/SPLIT2 b/SPLIT2
  new file mode 100644
  examine changes to 'SPLIT2'?
  (enter ? for help) [Ynesfdaq?] Y
  
  no more changes to split

The split changesets should be on the 'another-branch'
  $ hg log -G -l 3
  @  changeset:   23:61661257a937
  |  branch:      another-branch
  |  tag:         tip
  |  topic:       mytopic
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     split10
  |
  o  changeset:   22:a05395d0b421
  |  branch:      another-branch
  |  topic:       mytopic
  |  parent:      20:d6d47657e765
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     split9
  |
  o  changeset:   20:d6d47657e765
  |  branch:      double//slash
  ~  topic:       mytopic
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     split8
  

Try splitting the first changeset of a branch then cancel

  $ hg branch yet-another-branch
  marked working directory as branch yet-another-branch
  $ touch SPLIT3 SPLIT4
  $ hg add SPLIT3 SPLIT4
  $ hg commit -m "To be split again"

  $ hg up "tip~1"
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved

  $ hg log -G -l 2
  o  changeset:   24:cffbaf700768
  |  branch:      yet-another-branch
  |  tag:         tip
  |  topic:       mytopic
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     To be split again
  |
  @  changeset:   23:61661257a937
  |  branch:      another-branch
  ~  topic:       mytopic
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     split10
  
  $ hg branch
  another-branch

  $ hg split -r tip << EOF
  > Y
  > q
  > EOF
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  adding SPLIT3
  adding SPLIT4
  diff --git a/SPLIT3 b/SPLIT3
  new file mode 100644
  examine changes to 'SPLIT3'?
  (enter ? for help) [Ynesfdaq?] Y
  
  diff --git a/SPLIT4 b/SPLIT4
  new file mode 100644
  examine changes to 'SPLIT4'?
  (enter ? for help) [Ynesfdaq?] q
  
  abort: user quit
  [250]

  $ hg branch
  another-branch

  $ hg log -G -l 2
  o  changeset:   24:cffbaf700768
  |  branch:      yet-another-branch
  |  tag:         tip
  |  topic:       mytopic
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     To be split again
  |
  @  changeset:   23:61661257a937
  |  branch:      another-branch
  ~  topic:       mytopic
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     split10
  

Check prompt options
--------------------

Look at the help (both record and split helps)

  $ hg split -r tip << EOF
  > Y
  > ?
  > d
  > ?
  > q
  > EOF
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  adding SPLIT3
  adding SPLIT4
  diff --git a/SPLIT3 b/SPLIT3
  new file mode 100644
  examine changes to 'SPLIT3'?
  (enter ? for help) [Ynesfdaq?] Y
  
  diff --git a/SPLIT4 b/SPLIT4
  new file mode 100644
  examine changes to 'SPLIT4'?
  (enter ? for help) [Ynesfdaq?] ?
  
  y - yes, record this change
  n - no, skip this change
  e - edit this change manually
  s - skip remaining changes to this file
  f - record remaining changes to this file
  d - done, skip remaining changes and files
  a - record all changes to all remaining files
  q - quit, recording no changes
  ? - ? (display help)
  examine changes to 'SPLIT4'?
  (enter ? for help) [Ynesfdaq?] d
  
  continue splitting? [Ycdq?] ?
  y - yes, continue selection
  c - commit, select all remaining changes
  d - discard, discard remaining changes
  q - quit, abort the split
  ? - ?, display help
  continue splitting? [Ycdq?] q
  transaction abort!
  rollback completed
  abort: user quit
  [255]

discard some of changeset during split

  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution=all
  > evolutioncommands=
  > EOF

  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Branch another-branch
  # Node ID 61661257a93759374255a4c05fcd9b8a78bbe399
  # Parent  a05395d0b42120af8bfb222d19f01008b1342c15
  # EXP-Topic-Namespace mynamespace
  # EXP-Topic mytopic
  split10
  
  diff --git a/SPLIT2 b/SPLIT2
  new file mode 100644
  $ hg add SPLIT3
  $ hg amend
  1 new orphan changesets
  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Branch another-branch
  # Node ID e6ca7ba1372dc452769c51a56d853c8ede26d9fa
  # Parent  a05395d0b42120af8bfb222d19f01008b1342c15
  # EXP-Topic-Namespace mynamespace
  # EXP-Topic mytopic
  split10
  
  diff --git a/SPLIT2 b/SPLIT2
  new file mode 100644
  diff --git a/SPLIT3 b/SPLIT3
  new file mode 100644
  $ hg split << EOF
  > Y
  > d
  > d
  > EOF
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  adding SPLIT2
  adding SPLIT3
  diff --git a/SPLIT2 b/SPLIT2
  new file mode 100644
  examine changes to 'SPLIT2'?
  (enter ? for help) [Ynesfdaq?] Y
  
  diff --git a/SPLIT3 b/SPLIT3
  new file mode 100644
  examine changes to 'SPLIT3'?
  (enter ? for help) [Ynesfdaq?] d
  
  continue splitting? [Ycdq?] d
  discarding remaining changes
  forgetting SPLIT3
  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Branch another-branch
  # Node ID bb8f1c282ddf89515bd07bd63a84962ab51ac277
  # Parent  a05395d0b42120af8bfb222d19f01008b1342c15
  # EXP-Topic-Namespace mynamespace
  # EXP-Topic mytopic
  split12
  
  diff --git a/SPLIT2 b/SPLIT2
  new file mode 100644
  $ hg status
  ? SPLIT3
  ? SPLIT4

Test restricting the split to a subset of files
-----------------------------------------------

  $ hg add SPLIT3 SPLIT4
  $ hg amend

Only run on 2 files

(remaining changes gathered with unmatched one)

adding content in files to make sure that it prompt us to select the changes,
as it won't prompt if a file has no changes at hunk level and passed in cli
(for more look into hg db72f9f6580e which made it to not prompt "examine changes to fileX"
for files which are explicitly mentioned by user)
  $ echo sp2 > SPLIT2
  $ echo sp3 > SPLIT3
  $ echo sp4 > SPLIT4
  $ hg amend

  $ hg split SPLIT2 SPLIT3 << EOF
  > y
  > s
  > c
  > EOF
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  adding SPLIT2
  adding SPLIT3
  adding SPLIT4
  diff --git a/SPLIT2 b/SPLIT2
  new file mode 100644
  @@ -0,0 +1,1 @@
  +sp2
  record change 1/2 to 'SPLIT2'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/SPLIT3 b/SPLIT3
  new file mode 100644
  @@ -0,0 +1,1 @@
  +sp3
  record change 2/2 to 'SPLIT3'?
  (enter ? for help) [Ynesfdaq?] s
  
  continue splitting? [Ycdq?] c

  $ hg status --change '.~1'
  A SPLIT2
  $ hg status --change '.'
  A SPLIT3
  A SPLIT4
  $ hg fold --from '.~1'
  2 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

(no remaining changes)

  $ hg split SPLIT2 SPLIT3 << EOF
  > y
  > s
  > y
  > y
  > EOF
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  adding SPLIT2
  adding SPLIT3
  adding SPLIT4
  diff --git a/SPLIT2 b/SPLIT2
  new file mode 100644
  @@ -0,0 +1,1 @@
  +sp2
  record change 1/2 to 'SPLIT2'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/SPLIT3 b/SPLIT3
  new file mode 100644
  @@ -0,0 +1,1 @@
  +sp3
  record change 2/2 to 'SPLIT3'?
  (enter ? for help) [Ynesfdaq?] s
  
  continue splitting? [Ycdq?] y
  diff --git a/SPLIT3 b/SPLIT3
  new file mode 100644
  @@ -0,0 +1,1 @@
  +sp3
  record this change to 'SPLIT3'?
  (enter ? for help) [Ynesfdaq?] y
  
  no more changes to split

  $ hg status --change '.~2'
  A SPLIT2
  $ hg status --change '.~1'
  A SPLIT3
  $ hg status --change '.'
  A SPLIT4
  $ hg fold --from '.~2'
  3 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

(only all matched selected)

  $ hg split SPLIT2 SPLIT3 << EOF
  > y
  > y
  > EOF
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  adding SPLIT2
  adding SPLIT3
  adding SPLIT4
  diff --git a/SPLIT2 b/SPLIT2
  new file mode 100644
  @@ -0,0 +1,1 @@
  +sp2
  record change 1/2 to 'SPLIT2'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/SPLIT3 b/SPLIT3
  new file mode 100644
  @@ -0,0 +1,1 @@
  +sp3
  record change 2/2 to 'SPLIT3'?
  (enter ? for help) [Ynesfdaq?] y
  
  no more changes to split
  $ hg status --change '.~1'
  A SPLIT2
  A SPLIT3
  $ hg status --change '.'
  A SPLIT4
  $ hg fold --from '.~1'
  2 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

Check that discard does not alter unmatched files

  $ hg split SPLIT2 SPLIT3 << EOF
  > y
  > s
  > d
  > EOF
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  adding SPLIT2
  adding SPLIT3
  adding SPLIT4
  diff --git a/SPLIT2 b/SPLIT2
  new file mode 100644
  @@ -0,0 +1,1 @@
  +sp2
  record change 1/2 to 'SPLIT2'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/SPLIT3 b/SPLIT3
  new file mode 100644
  @@ -0,0 +1,1 @@
  +sp3
  record change 2/2 to 'SPLIT3'?
  (enter ? for help) [Ynesfdaq?] s
  
  continue splitting? [Ycdq?] d
  discarding remaining changes
  no more changes to split
  $ hg status --change '.~1'
  A SPLIT2
  $ hg status --change '.'
  A SPLIT4
  $ hg fold --from '.~1'
  2 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg add SPLIT3
  $ hg amend

Non interractive run
--------------------

No patterns

  $ hg split --no-interactive
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  adding SPLIT2
  adding SPLIT3
  adding SPLIT4
  abort: no files of directories specified
  (do you want --interactive)
  [255]

Selecting unrelated file
(should we abort?)

  $ hg split --no-interactive SPLIT1
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  adding SPLIT2
  adding SPLIT3
  adding SPLIT4
  no more changes to split
  $ hg status --change '.'
  A SPLIT2
  A SPLIT3
  A SPLIT4

Selecting one file

  $ hg split --no-interactive SPLIT2
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  adding SPLIT2
  adding SPLIT3
  adding SPLIT4
  no more changes to split
  $ hg status --change '.~1'
  A SPLIT2
  $ hg status --change '.'
  A SPLIT3
  A SPLIT4
  $ hg fold --from '.~1'
  2 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

Selecting two files

  $ hg split --no-interactive SPLIT2 SPLIT3
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  adding SPLIT2
  adding SPLIT3
  adding SPLIT4
  no more changes to split
  $ hg status --change '.~1'
  A SPLIT2
  A SPLIT3
  $ hg status --change '.'
  A SPLIT4
  $ hg fold --from '.~1'
  2 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

Selecting all files
(should we abort?)

  $ hg split --no-interactive .
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  adding SPLIT2
  adding SPLIT3
  adding SPLIT4
  no more changes to split
  $ hg status --change '.'
  A SPLIT2
  A SPLIT3
  A SPLIT4

  $ cd ..

Testing that `hg evolve` choose right destination after split && prune (issue5686)
--------------------------------------------------------------------------------

Prepare the repository:
  $ hg init issue5686
  $ cd issue5686
  $ echo p > p
  $ hg ci -Amp
  adding p

  $ for ch in a b; do echo $ch > $ch; done;
  $ hg ci -Am "added a and b"
  adding a
  adding b
  $ echo c > c
  $ hg ci -Amc
  adding c
  $ hg glog
  @  2:ab6ca3ebca74 c (draft)
  |
  o  1:79f47e067e66 added a and b (draft)
  |
  o  0:a5a1faba8d26 p (draft)
  

Splitting the revision 1 to SPLIT1 and SPLIT2 which contains file a and b resp:
  $ echo 0 > $TESTTMP/split-counter
  $ hg split -r 1 <<EOF
  > y
  > y
  > n
  > y
  > y
  > y
  > EOF
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  adding a
  adding b
  diff --git a/a b/a
  new file mode 100644
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +a
  record change 1/2 to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/b b/b
  new file mode 100644
  examine changes to 'b'?
  (enter ? for help) [Ynesfdaq?] n
  
  created new head
  (consider using topic for lightweight branches. See 'hg help topic')
  continue splitting? [Ycdq?] y
  diff --git a/b b/b
  new file mode 100644
  examine changes to 'b'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +b
  record this change to 'b'?
  (enter ? for help) [Ynesfdaq?] y
  
  no more changes to split
  1 new orphan changesets

  $ hg glog -p
  @  4:5cf253fa63fa split2 (draft)
  |  diff --git a/b b/b
  |  new file mode 100644
  |  --- /dev/null
  |  +++ b/b
  |  @@ -0,0 +1,1 @@
  |  +b
  |
  o  3:88437e073cd4 split1 (draft)
  |  diff --git a/a b/a
  |  new file mode 100644
  |  --- /dev/null
  |  +++ b/a
  |  @@ -0,0 +1,1 @@
  |  +a
  |
  | *  2:ab6ca3ebca74 c (draft)
  | |  diff --git a/c b/c
  | |  new file mode 100644
  | |  --- /dev/null
  | |  +++ b/c
  | |  @@ -0,0 +1,1 @@
  | |  +c
  | |
  | x  1:79f47e067e66 added a and b (draft)
  |/   diff --git a/a b/a
  |    new file mode 100644
  |    --- /dev/null
  |    +++ b/a
  |    @@ -0,0 +1,1 @@
  |    +a
  |    diff --git a/b b/b
  |    new file mode 100644
  |    --- /dev/null
  |    +++ b/b
  |    @@ -0,0 +1,1 @@
  |    +b
  |
  o  0:a5a1faba8d26 p (draft)
     diff --git a/p b/p
     new file mode 100644
     --- /dev/null
     +++ b/p
     @@ -0,0 +1,1 @@
     +p
  
Now if we prune revision 4 the expected destination of orphan cset 2 is 3. Lets
check evolve does as expected:
Pruning revision 4 (current one):
  $ hg prune .
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at 88437e073cd4
  1 changesets pruned
  $ hg evolve -r 2
  move:[2] c
  atop:[3] split1
  $ hg glog
  o  5:21a63bd6ee88 c (draft)
  |
  @  3:88437e073cd4 split1 (draft)
  |
  o  0:a5a1faba8d26 p (draft)
  
  $ cd ..

Testing that `hg split` preserve the phase of splitting cset(issue6048)
-----------------------------------------------------------------------

Prepare the repository:
  $ hg init issue6048
  $ cd issue6048
  $ echo a > a
  $ hg ci -Am "added a"
  adding a

  $ echo b > b
  $ echo c > c
  $ hg add b c
  $ hg ci -m "added b c" --secret

  $ hg glog -l1 -p --git
  @  1:12e9cc39ba19 added b c (secret)
  |  diff --git a/b b/b
  ~  new file mode 100644
     --- /dev/null
     +++ b/b
     @@ -0,0 +1,1 @@
     +b
     diff --git a/c b/c
     new file mode 100644
     --- /dev/null
     +++ b/c
     @@ -0,0 +1,1 @@
     +c
  
Splitting
  $ echo 0 > $TESTTMP/split-counter
  $ hg split -r . << EOF
  > y
  > y
  > n
  > c
  > EOF
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  adding b
  adding c
  diff --git a/b b/b
  new file mode 100644
  examine changes to 'b'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +b
  record change 1/2 to 'b'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/c b/c
  new file mode 100644
  examine changes to 'c'?
  (enter ? for help) [Ynesfdaq?] n
  
  created new head
  (consider using topic for lightweight branches. See 'hg help topic')
  continue splitting? [Ycdq?] c

  $ hg glog --git -p
  @  3:1f8c09b13fa2 split2 (secret)
  |  diff --git a/c b/c
  |  new file mode 100644
  |  --- /dev/null
  |  +++ b/c
  |  @@ -0,0 +1,1 @@
  |  +c
  |
  o  2:bcba06966846 split1 (secret)
  |  diff --git a/b b/b
  |  new file mode 100644
  |  --- /dev/null
  |  +++ b/b
  |  @@ -0,0 +1,1 @@
  |  +b
  |
  o  0:9092f1db7931 added a (draft)
     diff --git a/a b/a
     new file mode 100644
     --- /dev/null
     +++ b/a
     @@ -0,0 +1,1 @@
     +a
  
  $ cd ..

Discard after splitting into more than one changeset

  $ hg init discard-after-many
  $ cd discard-after-many

  $ echo a > a
  $ echo b > b
  $ echo c > c
  $ hg add a b c
  $ hg ci -m 'a b c'

XXX: this shouldn't ask to re-examine changes in b and definitely shouldn't revert b

  $ echo 0 > $TESTTMP/split-counter
  $ hg split << EOF
  > f
  > d
  > y
  > f
  > d
  > d
  > EOF
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  adding a
  adding b
  adding c
  diff --git a/a b/a
  new file mode 100644
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] f
  
  diff --git a/b b/b
  new file mode 100644
  examine changes to 'b'?
  (enter ? for help) [Ynesfdaq?] d
  
  created new head
  (consider using topic for lightweight branches. See 'hg help topic')
  continue splitting? [Ycdq?] y
  diff --git a/b b/b
  new file mode 100644
  examine changes to 'b'?
  (enter ? for help) [Ynesfdaq?] f
  
  diff --git a/c b/c
  new file mode 100644
  examine changes to 'c'?
  (enter ? for help) [Ynesfdaq?] d
  
  continue splitting? [Ycdq?] d
  discarding remaining changes
  forgetting c

  $ hg glog -p
  @  2:c2c6f4d8c766 split2 (draft)
  |  diff --git a/b b/b
  |  new file mode 100644
  |  --- /dev/null
  |  +++ b/b
  |  @@ -0,0 +1,1 @@
  |  +b
  |
  o  1:fb91c6249a20 split1 (draft)
     diff --git a/a b/a
     new file mode 100644
     --- /dev/null
     +++ b/a
     @@ -0,0 +1,1 @@
     +a
  

  $ cd ..
