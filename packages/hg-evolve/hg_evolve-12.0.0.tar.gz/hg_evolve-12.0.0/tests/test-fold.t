  $ . $TESTDIR/testlib/common.sh

setup

  $ cat >> $HGRCPATH <<EOF
  > [extensions]
  > evolve=
  > [alias]
  > glog = log -GT "{rev}: {desc}"
  > glf = log -GT "{rev}: {desc} ({files})"
  > [ui]
  > logtemplate = '{rev} - {node|short} {desc|firstline} [{author}] ({phase}) {bookmarks}\n'
  > EOF

  $ hg init fold-tests
  $ cd fold-tests/
  $ hg debugbuilddag .+3:branchpoint+4*branchpoint+2
  $ hg up 'desc("r7")'
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg bookmark bm1
  $ hg log -G
  o  10 - a8407f9a3dc1 r10 [debugbuilddag] (draft)
  |
  o  9 - 529dfc5bb875 r9 [debugbuilddag] (draft)
  |
  o  8 - abf57d94268b r8 [debugbuilddag] (draft)
  |
  | @  7 - 4de32a90b66c r7 [debugbuilddag] (draft) bm1
  | |
  | o  6 - f69452c5b1af r6 [debugbuilddag] (draft)
  | |
  | o  5 - c8d03c1b5e94 r5 [debugbuilddag] (draft)
  | |
  | o  4 - bebd167eb94d r4 [debugbuilddag] (draft)
  |/
  o  3 - 2dc09a01254d r3 [debugbuilddag] (draft)
  |
  o  2 - 01241442b3c2 r2 [debugbuilddag] (draft)
  |
  o  1 - 66f7d451a68b r1 [debugbuilddag] (draft)
  |
  o  0 - 1ea73414a91b r0 [debugbuilddag] (draft)
  

Test various error case

  $ hg fold --exact null::
  abort: cannot fold the null revision
  (no changeset checked out)
  [10]
  $ hg fold
  abort: no revisions specified
  [255]
  $ hg fold --from
  abort: no revisions specified
  [255]
  $ hg fold .
  abort: must specify either --from or --exact
  [255]
  $ hg fold --from . --exact
  abort: cannot use both --from and --exact
  [255]
  $ hg fold --from .
  single revision specified, nothing to fold
  [1]
  $ hg fold '0::(7+10)' --exact
  abort: cannot fold non-linear revisions (multiple heads given)
  [255]
  $ hg fold -r 4 -r 6 --exact
  abort: cannot fold non-linear revisions (multiple roots given)
  [255]
  $ hg fold --from 10 1
  abort: cannot fold non-linear revisions
  (given revisions are unrelated to parent of working directory)
  [255]
  $ hg fold --exact -r "4 and not 4"
  abort: specified revisions evaluate to an empty set
  (use different revision arguments)
  [255]
  $ hg phase --public 0
  $ hg fold --from -r 0
  abort: cannot fold public changesets: 1ea73414a91b
  (see 'hg help phases' for details)
  [10]

Test actual folding

  $ hg fold --from -r 'desc("r5")'
  3 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg debugobsolete -r 'desc("r5")' --exclusive
  4de32a90b66cd083ebf3c00b41277aa7abca51dd 198b5c405d01a50c41a81a00fc61677b81981a5f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '37', 'fold-id': '25cb328e', 'fold-idx': '3', 'fold-size': '3', 'operation': 'fold', 'user': 'test'}
  c8d03c1b5e94af74b772900c58259d2e08917735 198b5c405d01a50c41a81a00fc61677b81981a5f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '33', 'fold-id': '25cb328e', 'fold-idx': '1', 'fold-size': '3', 'operation': 'fold', 'user': 'test'}
  f69452c5b1af6cbaaa56ef50cf94fff5bcc6ca23 198b5c405d01a50c41a81a00fc61677b81981a5f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '37', 'fold-id': '25cb328e', 'fold-idx': '2', 'fold-size': '3', 'operation': 'fold', 'user': 'test'}

  $ hg obslog --no-origin
  @    198b5c405d01 (11) r5
  |\
  | \
  | |\
  x | |  4de32a90b66c (7) r7
   / /     folded(description, date, parent) as 198b5c405d01 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  c8d03c1b5e94 (5) r5
   /     folded(description, date) as 198b5c405d01 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  f69452c5b1af (6) r6
       folded(description, date, parent) as 198b5c405d01 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
  
  $ hg obslog
  @    198b5c405d01 (11) r5
  |\     folded(description, date, parent) from 4de32a90b66c, c8d03c1b5e94, f69452c5b1af using fold by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | \
  | |\
  x | |  4de32a90b66c (7) r7
   / /
  x /  c8d03c1b5e94 (5) r5
   /
  x  f69452c5b1af (6) r6
  

Checking whether the bookmarks are moved or not

  $ hg log -G
  @  11 - 198b5c405d01 r5 [debugbuilddag] (draft) bm1
  |
  | o  10 - a8407f9a3dc1 r10 [debugbuilddag] (draft)
  | |
  | o  9 - 529dfc5bb875 r9 [debugbuilddag] (draft)
  | |
  | o  8 - abf57d94268b r8 [debugbuilddag] (draft)
  | |
  o |  4 - bebd167eb94d r4 [debugbuilddag] (draft)
  |/
  o  3 - 2dc09a01254d r3 [debugbuilddag] (draft)
  |
  o  2 - 01241442b3c2 r2 [debugbuilddag] (draft)
  |
  o  1 - 66f7d451a68b r1 [debugbuilddag] (draft)
  |
  o  0 - 1ea73414a91b r0 [debugbuilddag] (public)
  
(test inherited from test-evolve.t)

  $ hg fold --from 6 # want to run hg fold 6
  abort: hidden revision '6' was rewritten as: 198b5c405d01
  (use --hidden to access hidden revisions)
  [10]

  $ hg log -G
  @  11 - 198b5c405d01 r5 [debugbuilddag] (draft) bm1
  |
  | o  10 - a8407f9a3dc1 r10 [debugbuilddag] (draft)
  | |
  | o  9 - 529dfc5bb875 r9 [debugbuilddag] (draft)
  | |
  | o  8 - abf57d94268b r8 [debugbuilddag] (draft)
  | |
  o |  4 - bebd167eb94d r4 [debugbuilddag] (draft)
  |/
  o  3 - 2dc09a01254d r3 [debugbuilddag] (draft)
  |
  o  2 - 01241442b3c2 r2 [debugbuilddag] (draft)
  |
  o  1 - 66f7d451a68b r1 [debugbuilddag] (draft)
  |
  o  0 - 1ea73414a91b r0 [debugbuilddag] (public)
  

test fold --exact

  $ hg fold --exact 'desc("r8") + desc("r10")'
  abort: cannot fold non-linear revisions (multiple roots given)
  [255]
  $ hg fold --exact 'desc("r8")::desc("r10")'
  3 changesets folded
  $ hg log -G
  o  12 - b568edbee6e0 r8 [debugbuilddag] (draft)
  |
  | @  11 - 198b5c405d01 r5 [debugbuilddag] (draft) bm1
  | |
  | o  4 - bebd167eb94d r4 [debugbuilddag] (draft)
  |/
  o  3 - 2dc09a01254d r3 [debugbuilddag] (draft)
  |
  o  2 - 01241442b3c2 r2 [debugbuilddag] (draft)
  |
  o  1 - 66f7d451a68b r1 [debugbuilddag] (draft)
  |
  o  0 - 1ea73414a91b r0 [debugbuilddag] (public)
  

Test allow unstable

  $ echo a > a
  $ hg add a
  $ hg commit '-m r11'
  $ hg up '.^'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  (leaving bookmark bm1)
  $ hg log -G
  o  13 - 14d0e0da8e91 r11 [test] (draft) bm1
  |
  | o  12 - b568edbee6e0 r8 [debugbuilddag] (draft)
  | |
  @ |  11 - 198b5c405d01 r5 [debugbuilddag] (draft)
  | |
  o |  4 - bebd167eb94d r4 [debugbuilddag] (draft)
  |/
  o  3 - 2dc09a01254d r3 [debugbuilddag] (draft)
  |
  o  2 - 01241442b3c2 r2 [debugbuilddag] (draft)
  |
  o  1 - 66f7d451a68b r1 [debugbuilddag] (draft)
  |
  o  0 - 1ea73414a91b r0 [debugbuilddag] (public)
  

  $ cat << EOF >> .hg/hgrc
  > [experimental]
  > evolution = createmarkers, allnewcommands
  > EOF
  $ hg fold --from 'desc("r4")'
  abort: cannot fold changeset, as that will orphan 1 descendants
  (see 'hg help evolution.instability')
  [10]
  $ hg fold --from 'desc("r3")::desc("r11")'
  abort: cannot fold changeset, as that will orphan 1 descendants
  (see 'hg help evolution.instability')
  [10]

test --user variant

  $ cat << EOF >> .hg/hgrc
  > [experimental]
  > evolution = createmarkers, allnewcommands
  > EOF
  $ cat << EOF >> .hg/hgrc
  > [experimental]
  > evolution = all
  > EOF

  $ hg fold --exact 'desc("r5") + desc("r11")' --user 'Victor Rataxes <victor@rhino.savannah>'
  2 changesets folded
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg log -G
  @  14 - 29b470a33594 r5 [Victor Rataxes <victor@rhino.savannah>] (draft) bm1
  |
  | o  12 - b568edbee6e0 r8 [debugbuilddag] (draft)
  | |
  o |  4 - bebd167eb94d r4 [debugbuilddag] (draft)
  |/
  o  3 - 2dc09a01254d r3 [debugbuilddag] (draft)
  |
  o  2 - 01241442b3c2 r2 [debugbuilddag] (draft)
  |
  o  1 - 66f7d451a68b r1 [debugbuilddag] (draft)
  |
  o  0 - 1ea73414a91b r0 [debugbuilddag] (public)
  

  $ hg fold --from 'desc("r4")' -U
  2 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg log -G
  @  15 - 91880abed0f2 r4 [test] (draft) bm1
  |
  | o  12 - b568edbee6e0 r8 [debugbuilddag] (draft)
  |/
  o  3 - 2dc09a01254d r3 [debugbuilddag] (draft)
  |
  o  2 - 01241442b3c2 r2 [debugbuilddag] (draft)
  |
  o  1 - 66f7d451a68b r1 [debugbuilddag] (draft)
  |
  o  0 - 1ea73414a91b r0 [debugbuilddag] (public)
  
Test order of proposed commit message

  $ hg fold --exact --hidden -r 4 -r 5 -r 6 \
  >         --config experimental.evolution.allowdivergence=yes
  2 new content-divergent changesets
  3 changesets folded
  $ hg log -r tip -T '{desc}'
  r4
  
  
  r5
  
  
  r6 (no-eol)
  $ hg fold --exact --hidden -r 6 -r 4 -r 5 \
  >         --config experimental.evolution.allowdivergence=yes
  3 changesets folded
  $ hg log -r tip -T '{desc}'
  r4
  
  
  r5
  
  
  r6 (no-eol)

  $ cd ..

One merge commit

  $ hg init fold-a-merge
  $ cd fold-a-merge

  $ mkcommit zebra

  $ hg up null
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ mkcommit apple
  created new head
  $ mkcommit banana

  $ hg merge
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m merge

  $ mkcommit coconut

  $ hg glf
  @  4: coconut (coconut)
  |
  o    3: merge ()
  |\
  | o  2: banana (banana)
  | |
  | o  1: apple (apple)
  |
  o  0: zebra (zebra)
  

now we merge some of the fruits

  $ hg fold --exact -r 'desc("banana")::desc("coconut")' -m 'banana+coconut in a merge with zebra'
  3 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg glf
  @    5: banana+coconut in a merge with zebra (banana coconut)
  |\
  | o  1: apple (apple)
  |
  o  0: zebra (zebra)
  

let's go even further: zebra becomes a parent of the squashed fruit commit

  $ hg fold --from -r 'desc("apple")' -m 'apple+banana+coconut is a child of zebra'
  2 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg glf
  @  6: apple+banana+coconut is a child of zebra (apple banana coconut)
  |
  o  0: zebra (zebra)
  

make sure zebra exists at tip and has expected contents

  $ hg cat -r tip zebra
  zebra

  $ cd ..

Multiple merge commits

  $ hg init fold-many-merges
  $ cd fold-many-merges

  $ hg debugbuilddag '+3 *3 /3 /4 /4'
  $ hg glog
  o    6: r6
  |\
  | o    5: r5
  | |\
  | | o  4: r4
  | |/|
  | | o  3: r3
  | | |
  o | |  2: r2
  |/ /
  o /  1: r1
  |/
  o  0: r0
  

cannot fold 5 and 6 because they have 3 external parents in total: 1, 2, 4

  $ hg fold --exact -r 5:6 -m r5+r6
  abort: cannot fold revisions that merge with more than one external changeset (not in revisions)
  [255]

now many of the parents are included in the revisions to fold, only 0 and 3 are external

  $ hg fold --exact -r 1+2+4+5+6 -m r1+r2+r4+r5+r6
  5 changesets folded

  $ hg glog
  o    7: r1+r2+r4+r5+r6
  |\
  | o  3: r3
  |/
  o  0: r0
  
  $ cd ..

Fold should respect experimental.evolution.allowdivergence option
https://bz.mercurial-scm.org/show_bug.cgi?id=5817

  $ hg init issue5817
  $ cd issue5817

  $ echo A > foo
  $ hg ci -qAm A
  $ echo B > foo
  $ hg ci -m B
  $ echo C > foo
  $ hg ci -m C

  $ hg fold --exact -r 'desc("A")::desc("B")' -m 'first fold'
  1 new orphan changesets
  2 changesets folded

fold aborts here because divergence is not allowed

  $ hg fold --exact -r 'desc("A")::desc("B")' -m 'second fold' \
  >         --config experimental.evolution.allowdivergence=no
  abort: cannot fold 4b34ecfb0d56, as that creates content-divergence with fcfd42a7fa46
  (add --verbose for details or see 'hg help evolution.instability')
  [10]

but if we allow divergence, this should work and should create new content-divergent changesets

  $ hg fold --exact -r 'desc("A")::desc("B")' -m 'second fold' \
  >         --config experimental.evolution.allowdivergence=yes
  2 new content-divergent changesets
  2 changesets folded

  $ cd ..

Saving the last user-edited message in last-message.txt
https://bz.mercurial-scm.org/show_bug.cgi?id=6549

  $ hg init issue6549
  $ cd issue6549

  $ echo A > foo
  $ hg ci -qAm A
  $ echo B > foo
  $ hg ci -m B

  $ cat > editor.sh << 'EOF'
  > echo 'Big commit message that was crafted with care.' > "$1"
  > echo '' >> "$1"
  > echo 'It would be a shame if something happened to it.' >> "$1"
  > EOF
  $ HGEDITOR="sh ./editor.sh" hg fold --exact --rev 'all()'
  2 changesets folded
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ hg glog
  @  2: Big commit message that was crafted with care.
  
     It would be a shame if something happened to it.
  $ cat .hg/last-message.txt
  Big commit message that was crafted with care.
  
  It would be a shame if something happened to it.

  $ cd ..
