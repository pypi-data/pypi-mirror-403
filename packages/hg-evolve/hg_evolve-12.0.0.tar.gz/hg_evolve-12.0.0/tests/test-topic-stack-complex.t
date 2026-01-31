Testing `hg stack` on complex cases when we have multiple successors because of
divergence, split etc.
  $ . "$TESTDIR/testlib/topic_setup.sh"

Setup

  $ cat << EOF >> $HGRCPATH
  > [experimental]
  > evolution = all
  > evolution.allowdivergence = True
  > [ui]
  > interactive = True
  > [extensions]
  > show =
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

  $ hg init test
  $ cd test
  $ echo foo > foo
  $ hg add foo
  $ hg ci -m "Added foo"
  $ hg phase -r . --public
  $ hg topic foo
  marked working directory as topic: foo
  $ echo a > a
  $ echo b > b
  $ hg ci -Aqm "Added a and b"
  $ echo c > c
  $ echo d > d
  $ hg ci -Aqm "Added c and d"
  $ echo e > e
  $ echo f > f
  $ hg ci -Aqm "Added e and f"
  $ hg show work
  @  f1d3 (foo) Added e and f
  o  8e82 (foo) Added c and d
  o  002b (foo) Added a and b
  o  f360 Added foo

Testing in case of split within the topic

  $ hg stack
  ### topic: foo
  ### target: default (branch)
  s3@ Added e and f (current)
  s2: Added c and d
  s1: Added a and b
  s0^ Added foo (base)
  $ hg prev
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  [s2] Added c and d

  $ echo 0 > num
  $ cat > editor.sh << '__EOF__'
  > NUM=$(cat num)
  > NUM=`expr "$NUM" + 1`
  > echo "$NUM" > num
  > echo "split$NUM" > "$1"
  > __EOF__
  $ export HGEDITOR="\"sh\" \"editor.sh\""

  $ hg split << EOF
  > y
  > y
  > n
  > c
  > EOF
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  adding c
  adding d
  diff --git a/c b/c
  new file mode 100644
  examine changes to 'c'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +c
  record change 1/2 to 'c'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/d b/d
  new file mode 100644
  examine changes to 'd'?
  (enter ? for help) [Ynesfdaq?] n
  
  continue splitting? [Ycdq?] c
  1 new orphan changesets

  $ hg stack
  ### topic: foo
  ### target: default (branch)
  s4$ Added e and f (orphan)
  s3@ split2 (current)
  s2: split1
  s1: Added a and b
  s0^ Added foo (base)

  $ hg show work
  @  5cce (foo) split2
  o  f26c (foo) split1
  | *  f1d3 (foo) Added e and f
  | x  8e82 (foo) Added c and d
  |/
  o  002b (foo) Added a and b
  o  f360 Added foo

  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [s2] split1
  $ echo foo > c
  $ hg diff
  diff -r f26c1b9addde c
  --- a/c	Thu Jan 01 00:00:00 1970 +0000
  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -c
  +foo

  $ hg amend
  1 new orphan changesets
  $ hg show work
  @  7d94 (foo) split1
  | *  5cce (foo) split2
  | x  f26c (foo) split1
  |/
  | *  f1d3 (foo) Added e and f
  | x  8e82 (foo) Added c and d
  |/
  o  002b (foo) Added a and b
  o  f360 Added foo

  $ hg stack
  ### topic: foo (2 heads)
  ### target: default (branch), 2 behind
  s4$ Added e and f (orphan)
  s3$ split2 (orphan)
  s2@ split1 (current)
  s1: Added a and b
  s0^ Added foo (base)

Test case with divergence
-------------------------

  $ hg evolve --all
  move:[s3] split2
  atop:[s2] split1
  move:[s4] Added e and f
  $ hg up s4
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg id -r .
  ec94a1ed1330 tip
  $ hg up --hidden 'min(predecessors(.))'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset f1d3649d6a8b
  (hidden revision 'f1d3649d6a8b' was rewritten as: ec94a1ed1330)
  working directory parent is obsolete! (f1d3649d6a8b)
  (use 'hg evolve' to update to its successor: ec94a1ed1330)
  $ hg amend -d '0 1'
  1 new orphan changesets
  2 new content-divergent changesets
  $ hg rebase -r . -d ec94a1ed1330~1
  rebasing 9:eb3b16fef8ea tip foo "Added e and f"
  $ hg stack
  ### topic: foo (2 heads)
  ### target: default (branch)
  s5$ Added e and f (content divergent)
  s3^ split2 (base)
  s4@ Added e and f (content divergent current)
  s3: split2
  s2: split1
  s1: Added a and b
  s0^ Added foo (base)

  $ hg evolve --content-divergent -r ec94a1ed1330
  merge:[s5] Added e and f
  with: [s4] Added e and f
  base: [3] Added e and f
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 692bc8b2aa4d

  $ hg log -r . -T '{date|hgdate}\n'
  0 1
