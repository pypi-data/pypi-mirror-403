Testing obslog and other commands accessing obsolete revisions.

Global setup
============

  $ . $TESTDIR/testlib/obshistory_setup.sh

Test output with phase-divergence
=================================

Test setup
----------

  $ hg init $TESTTMP/phase-divergence
  $ cd $TESTTMP/phase-divergence
  $ mkcommit ROOT
  $ mkcommit A0
  $ hg amend -m "A1"
  $ hg log --hidden -G
  @  changeset:   2:fdf9bde5129a
  |  tag:         tip
  |  parent:      0:ea207398892e
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A1
  |
  | x  changeset:   1:471f378eab4c
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    reworded using amend as 2:fdf9bde5129a
  |    summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
  $ hg update --hidden 'desc(A0)'
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 471f378eab4c
  (hidden revision '471f378eab4c' was rewritten as: fdf9bde5129a)
  working directory parent is obsolete! (471f378eab4c)
  (use 'hg evolve' to update to its successor: fdf9bde5129a)
  $ hg phase -p .
  1 new phase-divergent changesets
  $ hg log --hidden -G
  *  changeset:   2:fdf9bde5129a
  |  tag:         tip
  |  parent:      0:ea207398892e
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: phase-divergent
  |  summary:     A1
  |
  | @  changeset:   1:471f378eab4c
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
Actual test
-----------

Check that obslog on the public revision shows both public (diverged) and draft (divergent) revisions
  $ hg obslog --hidden 471f378eab4c --patch --no-origin
  @  471f378eab4c (1) A0
       reworded(description) as fdf9bde5129a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r fdf9bde5129a changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +A1
  
  

Check that with all option, every changeset is shown
  $ hg obslog --hidden --all 471f378eab4c --patch --no-origin
  *  fdf9bde5129a (2) A1
  |
  @  471f378eab4c (1) A0
       reworded(description) as fdf9bde5129a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r fdf9bde5129a changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +A1
  
  
  $ hg obslog --hidden --all 471f378eab4c --patch
  *  fdf9bde5129a (2) A1
  |    reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 471f378eab4c -r fdf9bde5129a changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -A0
  |      +A1
  |
  |
  @  471f378eab4c (1) A0
  
  $ hg obslog --hidden 471f378eab4c --no-graph --no-origin -Tjson | "$PYTHON" -m json.tool
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
                      "description"
                  ],
                  "operations": [
                      "amend"
                  ],
                  "succnodes": [
                      "fdf9bde5129a28d4548fadd3f62b265cdd3b7a2e"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "reworded"
              }
          ],
          "node": "471f378eab4c5e25f6c77f785b27c936efb22874",
          "shortdescription": "A0"
      }
  ]
  $ hg obslog --hidden 471f378eab4c --no-graph -Tjson | "$PYTHON" -m json.tool
  [
      {
          "markers": [],
          "node": "471f378eab4c5e25f6c77f785b27c936efb22874",
          "shortdescription": "A0"
      }
  ]
Check that obslog on the draft (divergent) revision also shows public (diverged) revision
  $ hg obslog fdf9bde5129a --patch
  *  fdf9bde5129a (2) A1
  |    reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 471f378eab4c -r fdf9bde5129a changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -A0
  |      +A1
  |
  |
  @  471f378eab4c (1) A0
  

Check that all option shows all of them
  $ hg obslog fdf9bde5129a -a --patch
  *  fdf9bde5129a (2) A1
  |    reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 471f378eab4c -r fdf9bde5129a changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -A0
  |      +A1
  |
  |
  @  471f378eab4c (1) A0
  
Check that obslog on the both draft (divergent) and public (diverged) revisions shows a coherent graph
  $ hg obslog 'fdf9bde5129a+471f378eab4c' --patch
  *  fdf9bde5129a (2) A1
  |    reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 471f378eab4c -r fdf9bde5129a changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -A0
  |      +A1
  |
  |
  @  471f378eab4c (1) A0
  
  $ hg obslog 'fdf9bde5129a+471f378eab4c' --no-graph --no-origin -Tjson | "$PYTHON" -m json.tool
  [
      {
          "markers": [],
          "node": "fdf9bde5129a28d4548fadd3f62b265cdd3b7a2e",
          "shortdescription": "A1"
      },
      {
          "markers": [
              {
                  "dates": [
                      [
                          0.0,
                          0
                      ]
                  ],
                  "effects": [
                      "description"
                  ],
                  "operations": [
                      "amend"
                  ],
                  "succnodes": [
                      "fdf9bde5129a28d4548fadd3f62b265cdd3b7a2e"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "reworded"
              }
          ],
          "node": "471f378eab4c5e25f6c77f785b27c936efb22874",
          "shortdescription": "A0"
      }
  ]
  $ hg obslog 'fdf9bde5129a+471f378eab4c' --no-graph -Tjson | "$PYTHON" -m json.tool
  [
      {
          "markers": [
              {
                  "dates": [
                      [
                          0.0,
                          0
                      ]
                  ],
                  "effects": [
                      "description"
                  ],
                  "operations": [
                      "amend"
                  ],
                  "prednodes": [
                      "471f378eab4c5e25f6c77f785b27c936efb22874"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "reworded"
              }
          ],
          "node": "fdf9bde5129a28d4548fadd3f62b265cdd3b7a2e",
          "shortdescription": "A1"
      },
      {
          "markers": [],
          "node": "471f378eab4c5e25f6c77f785b27c936efb22874",
          "shortdescription": "A0"
      }
  ]
  $ hg update 471f378eab4c
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg update --hidden 'desc(A0)'
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
