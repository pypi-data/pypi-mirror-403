Testing obslog and other commands accessing obsolete revisions.

Global setup
============

  $ . $TESTDIR/testlib/obshistory_setup.sh

Test output with lots of split commit
=====================================

Test setup
----------

  $ hg init $TESTTMP/local-lots-split
  $ cd $TESTTMP/local-lots-split
  $ mkcommit ROOT
  $ echo 42 >> a
  $ echo 43 >> b
  $ echo 44 >> c
  $ echo 45 >> d
  $ hg commit -A -m "A0"
  adding a
  adding b
  adding c
  adding d
  $ hg log --hidden -G
  @  changeset:   1:de7290d8b885
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  

  $ hg split -r 'desc(A0)' -d "0 0" << EOF
  > y
  > y
  > n
  > n
  > n
  > y
  > y
  > y
  > n
  > n
  > y
  > y
  > y
  > n
  > y
  > y
  > y
  > EOF
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  adding a
  adding b
  adding c
  adding d
  diff --git a/a b/a
  new file mode 100644
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +42
  record change 1/4 to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/b b/b
  new file mode 100644
  examine changes to 'b'?
  (enter ? for help) [Ynesfdaq?] n
  
  diff --git a/c b/c
  new file mode 100644
  examine changes to 'c'?
  (enter ? for help) [Ynesfdaq?] n
  
  diff --git a/d b/d
  new file mode 100644
  examine changes to 'd'?
  (enter ? for help) [Ynesfdaq?] n
  
  created new head
  continue splitting? [Ycdq?] y
  diff --git a/b b/b
  new file mode 100644
  examine changes to 'b'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +43
  record change 1/3 to 'b'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/c b/c
  new file mode 100644
  examine changes to 'c'?
  (enter ? for help) [Ynesfdaq?] n
  
  diff --git a/d b/d
  new file mode 100644
  examine changes to 'd'?
  (enter ? for help) [Ynesfdaq?] n
  
  continue splitting? [Ycdq?] y
  diff --git a/c b/c
  new file mode 100644
  examine changes to 'c'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +44
  record change 1/2 to 'c'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/d b/d
  new file mode 100644
  examine changes to 'd'?
  (enter ? for help) [Ynesfdaq?] n
  
  continue splitting? [Ycdq?] y
  diff --git a/d b/d
  new file mode 100644
  examine changes to 'd'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +45
  record this change to 'd'?
  (enter ? for help) [Ynesfdaq?] y
  
  no more changes to split

  $ hg log --hidden -G
  @  changeset:   5:c7f044602e9b
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A0
  |
  o  changeset:   4:1ae8bc733a14
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A0
  |
  o  changeset:   3:f257fde29c7a
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
  | x  changeset:   1:de7290d8b885
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    split using split as 2:337fec4d2edc, 3:f257fde29c7a, 4:1ae8bc733a14, 5:c7f044602e9b
  |    summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
Actual test
-----------

  $ hg obslog de7290d8b885 --hidden --patch --no-origin
  x  de7290d8b885 (1) A0
       split(parent, content) as 1ae8bc733a14, 337fec4d2edc, c7f044602e9b, f257fde29c7a using split by test (Thu Jan 01 00:00:00 1970 +0000)
         (No patch available, too many successors (4))
  
  $ hg obslog de7290d8b885 --hidden --all --patch --no-origin
  o  1ae8bc733a14 (4) A0
  |
  | o  337fec4d2edc (2) A0
  |/
  | @  c7f044602e9b (5) A0
  |/
  | o  f257fde29c7a (3) A0
  |/
  x  de7290d8b885 (1) A0
       split(parent, content) as 1ae8bc733a14, 337fec4d2edc, c7f044602e9b, f257fde29c7a using split by test (Thu Jan 01 00:00:00 1970 +0000)
         (No patch available, too many successors (4))
  
  $ hg obslog de7290d8b885 --hidden --all --patch
  o  1ae8bc733a14 (4) A0
  |    split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 1ae8bc733a14 d
  |      --- a/d	Thu Jan 01 00:00:00 1970 +0000
  |      +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,1 +0,0 @@
  |      -45
  |
  |
  | o  337fec4d2edc (2) A0
  |/     split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r de7290d8b885 -r 337fec4d2edc b
  |        --- a/b	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -43
  |        diff -r de7290d8b885 -r 337fec4d2edc c
  |        --- a/c	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -44
  |        diff -r de7290d8b885 -r 337fec4d2edc d
  |        --- a/d	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -45
  |
  |
  | @  c7f044602e9b (5) A0
  |/     split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  | o  f257fde29c7a (3) A0
  |/     split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r f257fde29c7a c
  |        --- a/c	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -44
  |        diff -r f257fde29c7a d
  |        --- a/d	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -45
  |
  |
  x  de7290d8b885 (1) A0
  
  $ hg obslog de7290d8b885 --hidden --no-graph --no-origin -Tjson | "$PYTHON" -m json.tool
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
                  "operations": [
                      "split"
                  ],
                  "succnodes": [
                      "1ae8bc733a14e374f11767d2ad128d4c891dc43f",
                      "337fec4d2edcf0e7a467e35f818234bc620068b5",
                      "c7f044602e9bd5dec6528b33114df3d0221e6359",
                      "f257fde29c7a847c9b607f6e958656d0df0fb15c"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "split"
              }
          ],
          "node": "de7290d8b885925115bb9e88887252dfc20ef2a8",
          "shortdescription": "A0"
      }
  ]
  $ hg obslog c7f044602e9b --patch --no-origin
  @  c7f044602e9b (5) A0
  |
  x  de7290d8b885 (1) A0
       split(parent, content) as 1ae8bc733a14, 337fec4d2edc, c7f044602e9b, f257fde29c7a using split by test (Thu Jan 01 00:00:00 1970 +0000)
         (No patch available, too many successors (4))
  
  $ hg obslog c7f044602e9b --patch
  @  c7f044602e9b (5) A0
  |    split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  de7290d8b885 (1) A0
  
  $ hg obslog c7f044602e9b --no-graph --no-origin -Tjson | "$PYTHON" -m json.tool
  [
      {
          "markers": [],
          "node": "c7f044602e9bd5dec6528b33114df3d0221e6359",
          "shortdescription": "A0"
      },
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
                  "operations": [
                      "split"
                  ],
                  "succnodes": [
                      "1ae8bc733a14e374f11767d2ad128d4c891dc43f",
                      "337fec4d2edcf0e7a467e35f818234bc620068b5",
                      "c7f044602e9bd5dec6528b33114df3d0221e6359",
                      "f257fde29c7a847c9b607f6e958656d0df0fb15c"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "split"
              }
          ],
          "node": "de7290d8b885925115bb9e88887252dfc20ef2a8",
          "shortdescription": "A0"
      }
  ]
  $ hg obslog c7f044602e9b --no-graph -Tjson | "$PYTHON" -m json.tool
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
                  "operations": [
                      "split"
                  ],
                  "prednodes": [
                      "de7290d8b885925115bb9e88887252dfc20ef2a8"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "split"
              }
          ],
          "node": "c7f044602e9bd5dec6528b33114df3d0221e6359",
          "shortdescription": "A0"
      },
      {
          "markers": [],
          "node": "de7290d8b885925115bb9e88887252dfc20ef2a8",
          "shortdescription": "A0"
      }
  ]
Check that obslog on all heads shows a coherent graph
  $ hg obslog 2::5 --patch --no-origin
  o  1ae8bc733a14 (4) A0
  |
  | o  337fec4d2edc (2) A0
  |/
  | @  c7f044602e9b (5) A0
  |/
  | o  f257fde29c7a (3) A0
  |/
  x  de7290d8b885 (1) A0
       split(parent, content) as 1ae8bc733a14, 337fec4d2edc, c7f044602e9b, f257fde29c7a using split by test (Thu Jan 01 00:00:00 1970 +0000)
         (No patch available, too many successors (4))
  
  $ hg obslog 2::5 --patch
  o  1ae8bc733a14 (4) A0
  |    split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 1ae8bc733a14 d
  |      --- a/d	Thu Jan 01 00:00:00 1970 +0000
  |      +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,1 +0,0 @@
  |      -45
  |
  |
  | o  337fec4d2edc (2) A0
  |/     split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r de7290d8b885 -r 337fec4d2edc b
  |        --- a/b	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -43
  |        diff -r de7290d8b885 -r 337fec4d2edc c
  |        --- a/c	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -44
  |        diff -r de7290d8b885 -r 337fec4d2edc d
  |        --- a/d	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -45
  |
  |
  | @  c7f044602e9b (5) A0
  |/     split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  | o  f257fde29c7a (3) A0
  |/     split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r f257fde29c7a c
  |        --- a/c	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -44
  |        diff -r f257fde29c7a d
  |        --- a/d	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -45
  |
  |
  x  de7290d8b885 (1) A0
  
  $ hg obslog 5 --all --patch --no-origin
  o  1ae8bc733a14 (4) A0
  |
  | o  337fec4d2edc (2) A0
  |/
  | @  c7f044602e9b (5) A0
  |/
  | o  f257fde29c7a (3) A0
  |/
  x  de7290d8b885 (1) A0
       split(parent, content) as 1ae8bc733a14, 337fec4d2edc, c7f044602e9b, f257fde29c7a using split by test (Thu Jan 01 00:00:00 1970 +0000)
         (No patch available, too many successors (4))
  
  $ hg obslog 5 --all --patch
  o  1ae8bc733a14 (4) A0
  |    split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 1ae8bc733a14 d
  |      --- a/d	Thu Jan 01 00:00:00 1970 +0000
  |      +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,1 +0,0 @@
  |      -45
  |
  |
  | o  337fec4d2edc (2) A0
  |/     split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r de7290d8b885 -r 337fec4d2edc b
  |        --- a/b	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -43
  |        diff -r de7290d8b885 -r 337fec4d2edc c
  |        --- a/c	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -44
  |        diff -r de7290d8b885 -r 337fec4d2edc d
  |        --- a/d	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -45
  |
  |
  | @  c7f044602e9b (5) A0
  |/     split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  | o  f257fde29c7a (3) A0
  |/     split(parent, content) from de7290d8b885 using split by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r f257fde29c7a c
  |        --- a/c	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -44
  |        diff -r f257fde29c7a d
  |        --- a/d	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -45
  |
  |
  x  de7290d8b885 (1) A0
  
  $ hg update de7290d8b885
  abort: hidden revision 'de7290d8b885' was split as: 337fec4d2edc, f257fde29c7a and 2 more
  (use --hidden to access hidden revisions)
  [10]
  $ hg update --hidden 'min(desc(A0))'
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset de7290d8b885
  (hidden revision 'de7290d8b885' was split as: 337fec4d2edc, f257fde29c7a and 2 more)
  working directory parent is obsolete! (de7290d8b885)
  (use 'hg evolve' to update to its tipmost successor: 337fec4d2edc, f257fde29c7a and 2 more)
