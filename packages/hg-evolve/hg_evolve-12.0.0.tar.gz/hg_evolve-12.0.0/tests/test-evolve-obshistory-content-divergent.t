Testing obslog and other commands accessing obsolete revisions.

Global setup
============

  $ . $TESTDIR/testlib/obshistory_setup.sh
  $ cat >> $HGRCPATH << EOF
  > [experimental]
  > evolution.allowdivergence = True
  > EOF

Test output with content-divergence
===================================

Test setup
----------

  $ hg init $TESTTMP/local-divergence
  $ cd $TESTTMP/local-divergence
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
  $ hg amend -m "A2"
  2 new content-divergent changesets
  $ hg log --hidden -G
  @  changeset:   3:65b757b745b9
  |  tag:         tip
  |  parent:      0:ea207398892e
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: content-divergent
  |  summary:     A2
  |
  | *  changeset:   2:fdf9bde5129a
  |/   parent:      0:ea207398892e
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    instability: content-divergent
  |    summary:     A1
  |
  | x  changeset:   1:471f378eab4c
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    reworded using amend as 2:fdf9bde5129a
  |    obsolete:    reworded using amend as 3:65b757b745b9
  |    summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
Actual test
-----------

Check that obslog on the divergent revision shows both destinations
  $ hg obslog --hidden 471f378eab4c --patch --no-origin
  x  471f378eab4c (1) A0
       reworded(description) as 65b757b745b9 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r 65b757b745b9 changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +A2
  
       reworded(description) as fdf9bde5129a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r fdf9bde5129a changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +A1
  
  
  $ hg obslog --hidden 'desc(A0)' --no-origin -f
  x  471f378eab4c (1) A0
       reworded(description) as 65b757b745b9 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
       reworded(description) as fdf9bde5129a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  

Check that with all option, every changeset is shown
  $ hg obslog --hidden --all 471f378eab4c --patch
  @  65b757b745b9 (3) A2
  |    reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 471f378eab4c -r 65b757b745b9 changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -A0
  |      +A2
  |
  |
  | *  fdf9bde5129a (2) A1
  |/     reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r 471f378eab4c -r fdf9bde5129a changeset-description
  |        --- a/changeset-description
  |        +++ b/changeset-description
  |        @@ -1,1 +1,1 @@
  |        -A0
  |        +A1
  |
  |
  x  471f378eab4c (1) A0
  
  $ hg obslog --hidden --all 'desc(A0)' --no-origin -f
  @  65b757b745b9 (3) A2
  |
  | *  fdf9bde5129a (2) A1
  |/
  x  471f378eab4c (1) A0
       reworded(description) as 65b757b745b9 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
       reworded(description) as fdf9bde5129a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  
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
                      "65b757b745b935093c87a2bccd877521cccffcbd"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "reworded"
              },
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
Check that obslog on the first diverged revision shows the revision and the
divergent one
  $ hg obslog fdf9bde5129a --patch --no-origin
  *  fdf9bde5129a (2) A1
  |
  x  471f378eab4c (1) A0
       reworded(description) as 65b757b745b9 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r 65b757b745b9 changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +A2
  
       reworded(description) as fdf9bde5129a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r fdf9bde5129a changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +A1
  
  

Check that all option shows all of them
  $ hg obslog fdf9bde5129a -a --patch
  @  65b757b745b9 (3) A2
  |    reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 471f378eab4c -r 65b757b745b9 changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -A0
  |      +A2
  |
  |
  | *  fdf9bde5129a (2) A1
  |/     reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r 471f378eab4c -r fdf9bde5129a changeset-description
  |        --- a/changeset-description
  |        +++ b/changeset-description
  |        @@ -1,1 +1,1 @@
  |        -A0
  |        +A1
  |
  |
  x  471f378eab4c (1) A0
  
Check that obslog on the second diverged revision shows the revision and the
divergent one
  $ hg obslog 65b757b745b9 --patch --no-origin
  @  65b757b745b9 (3) A2
  |
  x  471f378eab4c (1) A0
       reworded(description) as 65b757b745b9 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r 65b757b745b9 changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +A2
  
       reworded(description) as fdf9bde5129a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
         diff -r 471f378eab4c -r fdf9bde5129a changeset-description
         --- a/changeset-description
         +++ b/changeset-description
         @@ -1,1 +1,1 @@
         -A0
         +A1
  
  
Check that all option shows all of them
  $ hg obslog 65b757b745b9 -a --patch
  @  65b757b745b9 (3) A2
  |    reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 471f378eab4c -r 65b757b745b9 changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -A0
  |      +A2
  |
  |
  | *  fdf9bde5129a (2) A1
  |/     reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r 471f378eab4c -r fdf9bde5129a changeset-description
  |        --- a/changeset-description
  |        +++ b/changeset-description
  |        @@ -1,1 +1,1 @@
  |        -A0
  |        +A1
  |
  |
  x  471f378eab4c (1) A0
  
Check that obslog on the both diverged revision shows a coherent graph
  $ hg obslog '65b757b745b9+fdf9bde5129a' --patch
  @  65b757b745b9 (3) A2
  |    reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 471f378eab4c -r 65b757b745b9 changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -A0
  |      +A2
  |
  |
  | *  fdf9bde5129a (2) A1
  |/     reworded(description) from 471f378eab4c using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r 471f378eab4c -r fdf9bde5129a changeset-description
  |        --- a/changeset-description
  |        +++ b/changeset-description
  |        @@ -1,1 +1,1 @@
  |        -A0
  |        +A1
  |
  |
  x  471f378eab4c (1) A0
  
  $ hg obslog '65b757b745b9+fdf9bde5129a' --no-graph --no-origin -Tjson | "$PYTHON" -m json.tool
  [
      {
          "markers": [],
          "node": "65b757b745b935093c87a2bccd877521cccffcbd",
          "shortdescription": "A2"
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
                      "description"
                  ],
                  "operations": [
                      "amend"
                  ],
                  "succnodes": [
                      "65b757b745b935093c87a2bccd877521cccffcbd"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "reworded"
              },
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
      },
      {
          "markers": [],
          "node": "fdf9bde5129a28d4548fadd3f62b265cdd3b7a2e",
          "shortdescription": "A1"
      }
  ]
  $ hg obslog '65b757b745b9+fdf9bde5129a' --no-graph -Tjson | "$PYTHON" -m json.tool
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
          "node": "65b757b745b935093c87a2bccd877521cccffcbd",
          "shortdescription": "A2"
      },
      {
          "markers": [],
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
      }
  ]
  $ hg update 471f378eab4c
  abort: hidden revision '471f378eab4c' has diverged
  (use --hidden to access hidden revisions)
  [10]
  $ hg update --hidden 'desc(A0)'
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 471f378eab4c
  (hidden revision '471f378eab4c' has diverged)
  working directory parent is obsolete! (471f378eab4c)
  (471f378eab4c has diverged, use 'hg evolve --list --content-divergent' to resolve the issue)
