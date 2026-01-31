Testing obslog and other commands accessing obsolete revisions.

Global setup
============

  $ . $TESTDIR/testlib/obshistory_setup.sh

Test output with folded commit
==============================

Test setup
----------

  $ hg init $TESTTMP/local-fold
  $ hg init $TESTTMP/server
  $ cd $TESTTMP/local-fold
  $ mkcommit ROOT
  $ mkcommit A0
  $ sync
  $ mkcommit B0
  $ hg log --hidden -G
  @  changeset:   2:0dec01379d3b
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     B0
  |
  o  changeset:   1:471f378eab4c
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
  $ hg fold --exact -r 'desc(A0) + desc(B0)' --date "0 0" -m "C0"
  2 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg log --hidden -G
  @  changeset:   3:eb5a0daa2192
  |  tag:         tip
  |  parent:      0:ea207398892e
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     C0
  |
  | x  changeset:   2:0dec01379d3b
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  obsolete:    folded using fold as 3:eb5a0daa2192
  | |  summary:     B0
  | |
  | x  changeset:   1:471f378eab4c
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    folded using fold as 3:eb5a0daa2192
  |    summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  

  $ sync
Check output of the client
--------------------------

Check that obslog on the first folded revision shows only the revision with the
target
  $ hg obslog --hidden 471f378eab4c --patch --no-origin
  x  471f378eab4c (1) A0
       folded(description, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r eb5a0daa2192 changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +C0
  
         diff -r 471f378eab4c -r eb5a0daa2192 B0
         --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
         +++ b/B0	Thu Jan 01 00:00:00 1970 +0000
         @@ -0,0 +1,1 @@
         +B0
  
  
Check that with all option, all changesets are shown
  $ hg obslog --hidden --all 471f378eab4c --patch --no-origin
  @    eb5a0daa2192 (3) C0
  |\
  x |  0dec01379d3b (2) B0
   /     folded(description, parent, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r 0dec01379d3b -r eb5a0daa2192+ changeset-description
  |        --- a/changeset-description
  |        +++ b/changeset-description
  |        @@ -1,1 +1,1 @@
  |        -B0
  |        +C0
  |
  |
  x  471f378eab4c (1) A0
       folded(description, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r eb5a0daa2192 changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +C0
  
         diff -r 471f378eab4c -r eb5a0daa2192 B0
         --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
         +++ b/B0	Thu Jan 01 00:00:00 1970 +0000
         @@ -0,0 +1,1 @@
         +B0
  
  
Check that obslog on the second folded revision shows only the revision with
the target
  $ hg obslog --hidden 0dec01379d3b --patch --no-origin
  x  0dec01379d3b (2) B0
       folded(description, parent, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 0dec01379d3b -r eb5a0daa2192+ changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -B0
         +C0
  
  
Check that with all option, all changesets are shown
  $ hg obslog --hidden --all 0dec01379d3b --patch --no-origin
  @    eb5a0daa2192 (3) C0
  |\
  x |  0dec01379d3b (2) B0
   /     folded(description, parent, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r 0dec01379d3b -r eb5a0daa2192+ changeset-description
  |        --- a/changeset-description
  |        +++ b/changeset-description
  |        @@ -1,1 +1,1 @@
  |        -B0
  |        +C0
  |
  |
  x  471f378eab4c (1) A0
       folded(description, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r eb5a0daa2192 changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +C0
  
         diff -r 471f378eab4c -r eb5a0daa2192 B0
         --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
         +++ b/B0	Thu Jan 01 00:00:00 1970 +0000
         @@ -0,0 +1,1 @@
         +B0
  
  
Check that obslog on the successor revision shows a coherent graph
  $ hg obslog eb5a0daa2192 --patch --no-origin
  @    eb5a0daa2192 (3) C0
  |\
  x |  0dec01379d3b (2) B0
   /     folded(description, parent, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r 0dec01379d3b -r eb5a0daa2192+ changeset-description
  |        --- a/changeset-description
  |        +++ b/changeset-description
  |        @@ -1,1 +1,1 @@
  |        -B0
  |        +C0
  |
  |
  x  471f378eab4c (1) A0
       folded(description, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r eb5a0daa2192 changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +C0
  
         diff -r 471f378eab4c -r eb5a0daa2192 B0
         --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
         +++ b/B0	Thu Jan 01 00:00:00 1970 +0000
         @@ -0,0 +1,1 @@
         +B0
  
  
  $ hg obslog eb5a0daa2192 --no-graph --no-origin -Tjson | "$PYTHON" -m json.tool
  [
      {
          "markers": [],
          "node": "eb5a0daa21923bbf8caeb2c42085b9e463861fd0",
          "shortdescription": "C0"
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
                      "description",
                      "content"
                  ],
                  "operations": [
                      "fold"
                  ],
                  "succnodes": [
                      "eb5a0daa21923bbf8caeb2c42085b9e463861fd0"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "folded"
              }
          ],
          "node": "471f378eab4c5e25f6c77f785b27c936efb22874",
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
                      "description",
                      "parent",
                      "content"
                  ],
                  "operations": [
                      "fold"
                  ],
                  "succnodes": [
                      "eb5a0daa21923bbf8caeb2c42085b9e463861fd0"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "folded"
              }
          ],
          "node": "0dec01379d3be6318c470ead31b1fe7ae7cb53d5",
          "shortdescription": "B0"
      }
  ]

  $ hg obslog eb5a0daa2192 --patch
  @    eb5a0daa2192 (3) C0
  |\     folded(description, parent, content) from 0dec01379d3b, 471f378eab4c using fold by test (Thu Jan 01 00:00:00 1970 +0000)
  | |      (No patch available, too many predecessors (2))
  | |
  x |  0dec01379d3b (2) B0
   /
  x  471f378eab4c (1) A0
  
  $ hg obslog eb5a0daa2192 --no-graph -Tjson | "$PYTHON" -m json.tool
  [
      {
          "markers": [
              {
                  "dates": [
                      [
                          *, (glob)
                          0
                      ],
                      [
                          *, (glob)
                          0
                      ]
                  ],
                  "effects": [
                      "description",
                      "parent",
                      "content"
                  ],
                  "operations": [
                      "fold"
                  ],
                  "prednodes": [
                      "0dec01379d3be6318c470ead31b1fe7ae7cb53d5",
                      "471f378eab4c5e25f6c77f785b27c936efb22874"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "folded"
              }
          ],
          "node": "eb5a0daa21923bbf8caeb2c42085b9e463861fd0",
          "shortdescription": "C0"
      },
      {
          "markers": [],
          "node": "471f378eab4c5e25f6c77f785b27c936efb22874",
          "shortdescription": "A0"
      },
      {
          "markers": [],
          "node": "0dec01379d3be6318c470ead31b1fe7ae7cb53d5",
          "shortdescription": "B0"
      }
  ]
  $ hg update 471f378eab4c
  abort: hidden revision '471f378eab4c' was rewritten as: eb5a0daa2192
  (use --hidden to access hidden revisions)
  [10]
  $ hg update --hidden 'desc(A0)'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  updated to hidden changeset 471f378eab4c
  (hidden revision '471f378eab4c' was rewritten as: eb5a0daa2192)
  working directory parent is obsolete! (471f378eab4c)
  (use 'hg evolve' to update to its successor: eb5a0daa2192)
  $ hg update 0dec01379d3b
  abort: hidden revision '0dec01379d3b' was rewritten as: eb5a0daa2192
  (use --hidden to access hidden revisions)
  [10]
  $ hg update --hidden 'desc(B0)'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 0dec01379d3b
  (hidden revision '0dec01379d3b' was rewritten as: eb5a0daa2192)
  working directory parent is obsolete! (0dec01379d3b)
  (use 'hg evolve' to update to its successor: eb5a0daa2192)

Check output of the server
--------------------------

  $ hg obslog -R $TESTTMP/server --all --patch tip --no-origin
  o    eb5a0daa2192 (2) C0
  |\
  x |  0dec01379d3b
   /     folded(description, parent, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
  |        (No patch available, context is not local)
  |
  x  471f378eab4c (1) A0
       folded(description, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r eb5a0daa2192 changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +C0
  
         diff -r 471f378eab4c -r eb5a0daa2192 B0
         --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
         +++ b/B0	Thu Jan 01 00:00:00 1970 +0000
         @@ -0,0 +1,1 @@
         +B0
  
  
  $ hg obslog -R $TESTTMP/server -f --all --patch tip --no-origin
  o  eb5a0daa2192 (2) C0
  |
  x  471f378eab4c (1) A0
       folded(description, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r eb5a0daa2192 changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +C0
  
         diff -r 471f378eab4c -r eb5a0daa2192 B0
         --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
         +++ b/B0	Thu Jan 01 00:00:00 1970 +0000
         @@ -0,0 +1,1 @@
         +B0
  
  

  $ hg obslog -R $TESTTMP/server --all --patch 471f378eab4c --no-origin --hidden
  o    eb5a0daa2192 (2) C0
  |\
  x |  0dec01379d3b
   /     folded(description, parent, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
  |        (No patch available, context is not local)
  |
  x  471f378eab4c (1) A0
       folded(description, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r eb5a0daa2192 changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +C0
  
         diff -r 471f378eab4c -r eb5a0daa2192 B0
         --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
         +++ b/B0	Thu Jan 01 00:00:00 1970 +0000
         @@ -0,0 +1,1 @@
         +B0
  
  
  $ hg obslog -R $TESTTMP/server -f --all --patch 471f378eab4c --no-origin --hidden
  o  eb5a0daa2192 (2) C0
  |
  x  471f378eab4c (1) A0
       folded(description, content) as eb5a0daa2192 using fold by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r eb5a0daa2192 changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +C0
  
         diff -r 471f378eab4c -r eb5a0daa2192 B0
         --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
         +++ b/B0	Thu Jan 01 00:00:00 1970 +0000
         @@ -0,0 +1,1 @@
         +B0
  
  
