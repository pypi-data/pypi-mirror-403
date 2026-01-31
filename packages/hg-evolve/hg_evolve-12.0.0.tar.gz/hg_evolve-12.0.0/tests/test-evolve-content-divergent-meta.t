+====================================================
+Tests the resolution of content divergence: metadata
+====================================================

This file intend to cover cases focused around meta data merging.

Setup
-----

  $ cat >> $HGRCPATH <<EOF
  > [alias]
  > glog = log -GT "{rev}:{node|short} {desc|firstline}\n {phase} {instabilities}\n\n"
  > [phases]
  > publish = False
  > [experimental]
  > evolution.allowdivergence = True
  > [extensions]
  > rebase =
  > strip =
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

Check we preserve the author properly
-------------------------------------

Testing issue6113 to make sure that content-divergence resolution don't
replace initial author with the user running the resolution command:

  $ hg init userfoo
  $ cd userfoo
  $ unset HGUSER
  $ echo "[ui]" >> ./.hg/hgrc
  $ echo "username = foo <foo@test.com>" >> ./.hg/hgrc
  $ for ch in a b c; do
  > echo $ch > $ch;
  > hg add $ch;
  > hg ci -m "added "$ch;
  > done;

  $ cd ..
  $ hg init userbar
  $ cd userbar
  $ unset HGUSER
  $ echo "[ui]" >> ./.hg/hgrc
  $ echo "username = bar <bar@test.com>" >> ./.hg/hgrc
  $ hg pull ./../userfoo -q

  $ cd ../userfoo
  $ hg up -r "desc('added b')"
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo c > c
  $ echo e > e
  $ hg add c e
  $ hg ci -m "added c e"
  created new head

  $ hg up -r "desc('added b')"
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo cc > c
  $ hg add c
  $ hg ci -m "added c"
  created new head

  $ hg prune -r "min(desc('added c'))" -s "desc('added c e')"
  1 changesets pruned
  $ hg prune -r "min(desc('added c'))" -s "max(desc('added c'))" --hidden
  1 changesets pruned
  2 new content-divergent changesets

  $ hg glog
  @  4:6c06cda6dc99 added c
  |   draft content-divergent
  |
  | *  3:0c9267e23c9d added c e
  |/    draft content-divergent
  |
  o  1:1740ad2a1eda added b
  |   draft
  |
  o  0:f863f39764c4 added a
      draft
  

  $ cd ../userbar
  $ hg pull ./../userfoo -q
  2 new content-divergent changesets

  $ hg evolve --content-divergent --any
  merge:[3] added c e
  with: [4] added c
  base: [2] added c
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

Make sure resultant cset don't replace the initial user with user running the command:
  $ hg log -r tip
  changeset:   5:8cabe7248d20
  tag:         tip
  parent:      1:1740ad2a1eda
  user:        foo <foo@test.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added c e
  
  $ cd ..

Testing the three way merge logic for user of content divergent changesets
--------------------------------------------------------------------------

  $ hg init mergeusers
  $ cd mergeusers
  $ for ch in a b c; do
  > touch $ch
  > hg add $ch
  > hg ci -m "added "$ch
  > done;

  $ hg amend -m "updated c"
  $ hg up -r 'desc("added c")' --hidden -q
  updated to hidden changeset 2b3c31fe982d
  (hidden revision '2b3c31fe982d' was rewritten as: 464e35020fd0)
  working directory parent is obsolete! (2b3c31fe982d)
  $ echo coco > c

1) when one user is different wrt base
--------------------------------------

Insert a diverging author name:
  $ hg amend -u 'foouser'
  2 new content-divergent changesets

Run automatic evolution:
  $ hg evolve --content-divergent
  merge:[3] updated c
  with: [4] added c
  base: [2] added c
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 2300a271820b

  $ hg log -r tip | grep "^user"
  user:        foouser

  $ hg strip . -q --config extensions.strip=
  2 new content-divergent changesets

2) when both the user are different wrt base
--------------------------------------------

  $ hg up -r 'max(desc("updated c"))'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg amend -u 'baruser'

Run automatic evolution:
  $ hg evolve --content-divergent
  merge:[4] added c
  with: [5] updated c
  base: [2] added c
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 3d7ae55fbfe4

  $ hg log -r tip | grep "^user"
  user:        baruser, foouser

  $ cd ..

Test the content-divergence resolution involving date update
------------------------------------------------------------

  $ hg init divergingdate
  $ cd divergingdate
  $ unset HGUSER
  $ echo "[ui]" >> ./.hg/hgrc
  $ echo "username = test" >> ./.hg/hgrc

  $ echo hi > r0
  $ hg ci -qAm 'add r0'
  $ echo hi > foo.txt
  $ hg ci -qAm 'add foo.txt'
  $ hg metaedit -r . -d '0 2'
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

date: updated on both side to the same value

  $ echo hi > bar.txt
  $ hg add -q bar.txt
  $ hg amend -q
  $ hg metaedit -r 1 -d '0 1' --hidden
  2 new content-divergent changesets
  $ hg log -G
  *  changeset:   4:c17bf400a278
  |  tag:         tip
  |  parent:      0:a24ed8ad918c
  |  user:        test
  |  date:        Wed Dec 31 23:59:59 1969 -0000
  |  instability: content-divergent
  |  summary:     add foo.txt
  |
  | @  changeset:   3:a25dd7af6cf6
  |/   parent:      0:a24ed8ad918c
  |    user:        test
  |    date:        Wed Dec 31 23:59:58 1969 -0000
  |    instability: content-divergent
  |    summary:     add foo.txt
  |
  o  changeset:   0:a24ed8ad918c
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     add r0
  
  $ hg evolve --list --rev .
  a25dd7af6cf6: add foo.txt
    content-divergent: c17bf400a278 (draft) (precursor cc71ffbc7c00)
  
  $ hg log --hidden -r cc71ffbc7c00 -T '{rev} {node|short} {date|isodate}: {join(obsfate, "; ")}\n'
  1 cc71ffbc7c00 1970-01-01 00:00 +0000: date-changed using metaedit as 4:c17bf400a278; date-changed using metaedit as 2:0065551bd38f
  $ hg log -r 'desc("add foo.txt")' -T '{rev} {node|short} {date|isodate}: {join(obsfate, "; ")}\n'
  3 a25dd7af6cf6 1969-12-31 23:59 -0000: 
  4 c17bf400a278 1969-12-31 23:59 -0000: 
  $ hg evolve --content-divergent
  merge:[3] add foo.txt
  with: [4] add foo.txt
  base: [1] add foo.txt
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at bbcfcd9b9e21
  $ hg log -r 'desc("add foo.txt")' -T '{rev} {node|short} {date|isodate}: {join(obsfate, "; ")}\n'
  5 bbcfcd9b9e21 1969-12-31 23:59 -0000: 

date: updated one one side to an older value

  $ hg strip .
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/divergingdate/.hg/strip-backup/bbcfcd9b9e21-567273f3-backup.hg
  2 new content-divergent changesets
  $ hg up tip
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg amend --date "0 3"
  $ hg log -G
  @  changeset:   5:6189a9adfff0
  |  tag:         tip
  |  parent:      0:a24ed8ad918c
  |  user:        test
  |  date:        Wed Dec 31 23:59:57 1969 -0000
  |  instability: content-divergent
  |  summary:     add foo.txt
  |
  | *  changeset:   3:a25dd7af6cf6
  |/   parent:      0:a24ed8ad918c
  |    user:        test
  |    date:        Wed Dec 31 23:59:58 1969 -0000
  |    instability: content-divergent
  |    summary:     add foo.txt
  |
  o  changeset:   0:a24ed8ad918c
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     add r0
  
  $ hg evolve --list -r .
  6189a9adfff0: add foo.txt
    content-divergent: a25dd7af6cf6 (draft) (precursor cc71ffbc7c00)
  
  $ hg log -r cc71ffbc7c00+6189a9adfff0+a25dd7af6cf6 --hidden -T '{rev} {node|short} {date|isodate}: {join(obsfate, "; ")}\n'
  1 cc71ffbc7c00 1970-01-01 00:00 +0000: date-changed using metaedit as 4:c17bf400a278; date-changed using metaedit as 2:0065551bd38f
  5 6189a9adfff0 1969-12-31 23:59 -0000: 
  3 a25dd7af6cf6 1969-12-31 23:59 -0000: 
  $ hg evolve --content-divergent
  merge:[3] add foo.txt
  with: [5] add foo.txt
  base: [1] add foo.txt
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 4708538fed7d
  $ hg log -r . --hidden -T '{rev} {node|short} {date|isodate}: {join(obsfate, "; ")}\n'
  6 4708538fed7d 1969-12-31 23:59 -0000: 

date: updated one side to an newer value

  $ hg strip .
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/divergingdate/.hg/strip-backup/4708538fed7d-ca550351-backup.hg
  2 new content-divergent changesets
  $ hg update a25dd7af6cf6 --hidden
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg amend --date "120 0"
  $ hg log -G
  @  changeset:   6:5199d0bc13d4
  |  tag:         tip
  |  parent:      0:a24ed8ad918c
  |  user:        test
  |  date:        Thu Jan 01 00:02:00 1970 +0000
  |  instability: content-divergent
  |  summary:     add foo.txt
  |
  | *  changeset:   5:6189a9adfff0
  |/   parent:      0:a24ed8ad918c
  |    user:        test
  |    date:        Wed Dec 31 23:59:57 1969 -0000
  |    instability: content-divergent
  |    summary:     add foo.txt
  |
  o  changeset:   0:a24ed8ad918c
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     add r0
  
  $ hg evolve --list -r .
  5199d0bc13d4: add foo.txt
    content-divergent: 6189a9adfff0 (draft) (precursor cc71ffbc7c00)
  
  $ hg up 6189a9adfff0
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg log -r cc71ffbc7c00+6189a9adfff0+5199d0bc13d4 --hidden -T '{rev} {node|short} {date|isodate}: {join(obsfate, "; ")}\n'
  1 cc71ffbc7c00 1970-01-01 00:00 +0000: date-changed using metaedit as 4:c17bf400a278; date-changed using metaedit as 2:0065551bd38f
  5 6189a9adfff0 1969-12-31 23:59 -0000: 
  6 5199d0bc13d4 1970-01-01 00:02 +0000: 
  $ hg evolve --content-divergent
  merge:[5] add foo.txt
  with: [6] add foo.txt
  base: [1] add foo.txt
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at dbea1c7e245d
  $ hg log -r . --hidden -T '{rev} {node|short} {date|isodate}: {join(obsfate, "; ")}\n'
  7 dbea1c7e245d 1970-01-01 00:02 +0000: 

date: updated each side to a different value, newer should win

  $ hg strip .
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/divergingdate/.hg/strip-backup/dbea1c7e245d-47ae3d98-backup.hg
  2 new content-divergent changesets
  $ hg up tip
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg amend --date "235 0"
  $ hg update 6189a9adfff0 --hidden
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg amend --date "784 0"
  $ hg log -G
  @  changeset:   8:75254fb3164b
  |  tag:         tip
  |  parent:      0:a24ed8ad918c
  |  user:        test
  |  date:        Thu Jan 01 00:13:04 1970 +0000
  |  instability: content-divergent
  |  summary:     add foo.txt
  |
  | *  changeset:   7:5421a7efcc6e
  |/   parent:      0:a24ed8ad918c
  |    user:        test
  |    date:        Thu Jan 01 00:03:55 1970 +0000
  |    instability: content-divergent
  |    summary:     add foo.txt
  |
  o  changeset:   0:a24ed8ad918c
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     add r0
  
  $ hg evolve --list -r .
  75254fb3164b: add foo.txt
    content-divergent: 5421a7efcc6e (draft) (precursor cc71ffbc7c00)
  
  $ hg log -r 6189a9adfff0+5421a7efcc6e+75254fb3164b --hidden -T '{rev} {node|short} {date|isodate}: {join(obsfate, "; ")}\n'
  5 6189a9adfff0 1969-12-31 23:59 -0000: date-changed using amend as 8:75254fb3164b
  7 5421a7efcc6e 1970-01-01 00:03 +0000: 
  8 75254fb3164b 1970-01-01 00:13 +0000: 
  $ hg evolve --content-divergent
  merge:[7] add foo.txt
  with: [8] add foo.txt
  base: [1] add foo.txt
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 10c950c7c11f
  $ hg log -r . --hidden -T '{rev} {node|short} {date|isodate}: {join(obsfate, "; ")}\n'
  9 10c950c7c11f 1970-01-01 00:13 +0000: 

  $ cd ..
