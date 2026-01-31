Testing obslog and other commands accessing obsolete revisions.

Global setup
============

  $ . $TESTDIR/testlib/obshistory_setup.sh

Test output with split commit
=============================

Test setup
----------

  $ hg init $TESTTMP/local-split
  $ hg init $TESTTMP/server
  $ cd $TESTTMP/local-split
  $ mkcommit ROOT
  $ sync
  $ echo 42 >> a
  $ echo 43 >> b
  $ hg commit -A -m "A0"
  adding a
  adding b
  $ hg log --hidden -G
  @  changeset:   1:471597cad322
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
  $ hg split -r 'desc(A0)' -n "testing split" -d "0 0" << EOF
  > y
  > y
  > n
  > y
  > y
  > y
  > EOF
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  adding a
  adding b
  diff --git a/a b/a
  new file mode 100644
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +42
  record change 1/2 to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/b b/b
  new file mode 100644
  examine changes to 'b'?
  (enter ? for help) [Ynesfdaq?] n
  
  created new head
  continue splitting? [Ycdq?] y
  diff --git a/b b/b
  new file mode 100644
  examine changes to 'b'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +43
  record this change to 'b'?
  (enter ? for help) [Ynesfdaq?] y
  
  no more changes to split

  $ sync

  $ hg log --hidden -G
  @  changeset:   3:f257fde29c7a
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A0
  |
  o  changeset:   2:337fec4d2edc
  |  parent:      0:ea207398892e
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A0
  |
  | x  changeset:   1:471597cad322
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    split using split as 2:337fec4d2edc, 3:f257fde29c7a
  |    summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
Check output on the client side
-------------------------------

Check that obslog on split commit shows both targets
  $ hg obslog 471597cad322 --hidden --patch --no-origin
  x  471597cad322 (1) A0
       split(parent, content) as 337fec4d2edc, f257fde29c7a using split by test (Thu Jan 01 00:00:00 1970 +0000)
         note: testing split
         (No patch available, too many successors (2))
  
  $ hg obslog 471597cad322 --hidden --no-graph --no-origin -Tjson | "$PYTHON" -m json.tool
  [
      {
          "markers": [
              {
                  "dates": [
                      [
                          *, (glob)
                          0
                      ]
                  ],
                  "effects": [
                      "parent",
                      "content"
                  ],
                  "notes": [
                      "testing split"
                  ],
                  "operations": [
                      "split"
                  ],
                  "succnodes": [
                      "337fec4d2edcf0e7a467e35f818234bc620068b5",
                      "f257fde29c7a847c9b607f6e958656d0df0fb15c"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "split"
              }
          ],
          "node": "471597cad322d1f659bb169751be9133dad92ef3",
          "shortdescription": "A0"
      }
  ]
  $ hg obslog 471597cad322 --hidden --no-graph -Tjson | "$PYTHON" -m json.tool
  [
      {
          "markers": [],
          "node": "471597cad322d1f659bb169751be9133dad92ef3",
          "shortdescription": "A0"
      }
  ]
Check that obslog on the first successor after split shows the revision plus
the split one
  $ hg obslog 337fec4d2edc --patch
  o  337fec4d2edc (2) A0
  |    split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |      note: testing split
  |      diff -r 471597cad322 -r 337fec4d2edc b
  |      --- a/b	Thu Jan 01 00:00:00 1970 +0000
  |      +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,1 +0,0 @@
  |      -43
  |
  |
  x  471597cad322 (1) A0
  
With the all option, it should show all three changesets
  $ hg obslog --all 337fec4d2edc --patch
  o  337fec4d2edc (2) A0
  |    split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |      note: testing split
  |      diff -r 471597cad322 -r 337fec4d2edc b
  |      --- a/b	Thu Jan 01 00:00:00 1970 +0000
  |      +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,1 +0,0 @@
  |      -43
  |
  |
  | @  f257fde29c7a (3) A0
  |/     split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |        note: testing split
  |
  x  471597cad322 (1) A0
  
Check that obslog on the second successor after split shows the revision plus
the split one
  $ hg obslog f257fde29c7a --patch
  @  f257fde29c7a (3) A0
  |    split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |      note: testing split
  |
  x  471597cad322 (1) A0
  
With the all option, it should show all three changesets
  $ hg obslog f257fde29c7a --all --patch
  o  337fec4d2edc (2) A0
  |    split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |      note: testing split
  |      diff -r 471597cad322 -r 337fec4d2edc b
  |      --- a/b	Thu Jan 01 00:00:00 1970 +0000
  |      +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,1 +0,0 @@
  |      -43
  |
  |
  | @  f257fde29c7a (3) A0
  |/     split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |        note: testing split
  |
  x  471597cad322 (1) A0
  
Obslog with all option should also works on the split commit
  $ hg obslog -a 471597cad322 --hidden --patch --no-origin
  o  337fec4d2edc (2) A0
  |
  | @  f257fde29c7a (3) A0
  |/
  x  471597cad322 (1) A0
       split(parent, content) as 337fec4d2edc, f257fde29c7a using split by test (Thu Jan 01 00:00:00 1970 +0000)
         note: testing split
         (No patch available, too many successors (2))
  
Check that obslog on both successors after split shows a coherent graph
  $ hg obslog 'f257fde29c7a+337fec4d2edc' --patch --no-origin
  o  337fec4d2edc (2) A0
  |
  | @  f257fde29c7a (3) A0
  |/
  x  471597cad322 (1) A0
       split(parent, content) as 337fec4d2edc, f257fde29c7a using split by test (Thu Jan 01 00:00:00 1970 +0000)
         note: testing split
         (No patch available, too many successors (2))
  
  $ hg obslog 'f257fde29c7a+337fec4d2edc' --patch
  o  337fec4d2edc (2) A0
  |    split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |      note: testing split
  |      diff -r 471597cad322 -r 337fec4d2edc b
  |      --- a/b	Thu Jan 01 00:00:00 1970 +0000
  |      +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,1 +0,0 @@
  |      -43
  |
  |
  | @  f257fde29c7a (3) A0
  |/     split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |        note: testing split
  |
  x  471597cad322 (1) A0
  
  $ hg update 471597cad322
  abort: hidden revision '471597cad322' was split as: 337fec4d2edc, f257fde29c7a
  (use --hidden to access hidden revisions)
  [10]
  $ hg update --hidden 'min(desc(A0))'
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 471597cad322
  (hidden revision '471597cad322' was split as: 337fec4d2edc, f257fde29c7a)
  working directory parent is obsolete! (471597cad322)
  (use 'hg evolve' to update to its tipmost successor: 337fec4d2edc, f257fde29c7a)

Check output on the server side
-------------------------------

  $ hg obslog -R $TESTTMP/server --patch tip --no-origin
  o  f257fde29c7a (2) A0
  |
  x  471597cad322
       split(parent, content) as 337fec4d2edc, f257fde29c7a using split by test (Thu Jan 01 00:00:00 1970 +0000)
         note: testing split
         (No patch available, context is not local)
  
  $ hg obslog -R $TESTTMP/server -f --patch tip --no-origin
  o  f257fde29c7a (2) A0
  
  $ hg obslog -R $TESTTMP/server --all --patch tip --no-origin
  o  337fec4d2edc (1) A0
  |
  | o  f257fde29c7a (2) A0
  |/
  x  471597cad322
       split(parent, content) as 337fec4d2edc, f257fde29c7a using split by test (Thu Jan 01 00:00:00 1970 +0000)
         note: testing split
         (No patch available, context is not local)
  
  $ hg obslog -R $TESTTMP/server --all -f --patch tip --no-origin
  o  337fec4d2edc (1) A0
  
  o  f257fde29c7a (2) A0
  
  $ hg obslog -R $TESTTMP/server --no-graph --all --patch tip --no-origin
  f257fde29c7a (2) A0
  
  471597cad322
    split(parent, content) as 337fec4d2edc, f257fde29c7a using split by test (Thu Jan 01 00:00:00 1970 +0000)
      note: testing split
      (No patch available, context is not local)
  
  337fec4d2edc (1) A0
  
  $ hg obslog -R $TESTTMP/server --no-graph -f --all --patch tip --no-origin
  f257fde29c7a (2) A0
  
  337fec4d2edc (1) A0
  

  $ hg obslog -R $TESTTMP/server --patch tip
  o  f257fde29c7a (2) A0
  |    split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |      note: testing split
  |      (No patch available, predecessor is unknown locally)
  |
  x  471597cad322
  
  $ hg obslog -R $TESTTMP/server -f --patch tip
  o  f257fde29c7a (2) A0
  
  $ hg obslog -R $TESTTMP/server --all --patch tip
  o  337fec4d2edc (1) A0
  |    split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |      note: testing split
  |      (No patch available, predecessor is unknown locally)
  |
  | o  f257fde29c7a (2) A0
  |/     split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |        note: testing split
  |        (No patch available, predecessor is unknown locally)
  |
  x  471597cad322
  
  $ hg obslog -R $TESTTMP/server --all -f --patch tip
  o  337fec4d2edc (1) A0
  
  o  f257fde29c7a (2) A0
  
  $ hg obslog -R $TESTTMP/server --no-graph --all --patch tip
  f257fde29c7a (2) A0
    split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
      note: testing split
      (No patch available, predecessor is unknown locally)
  
  471597cad322
  
  337fec4d2edc (1) A0
    split(parent, content) from 471597cad322 using split by test (Thu Jan 01 00:00:00 1970 +0000)
      note: testing split
      (No patch available, predecessor is unknown locally)
  
  $ hg obslog -R $TESTTMP/server --no-graph -f --all --patch tip
  f257fde29c7a (2) A0
  
  337fec4d2edc (1) A0
  
