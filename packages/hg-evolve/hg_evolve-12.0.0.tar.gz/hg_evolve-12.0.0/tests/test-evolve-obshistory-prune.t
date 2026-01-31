Testing obslog and other commands accessing obsolete revisions.

Global setup
============

  $ . $TESTDIR/testlib/obshistory_setup.sh

Test output with pruned commit
==============================

Check output on the client side
-------------------------------

  $ hg init $TESTTMP/local-prune
  $ hg init $TESTTMP/server
  $ cd $TESTTMP/local-prune
  $ mkcommit ROOT
  $ mkcommit A0 # 0
  $ mkcommit B0 # 1
  $ sync
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
  
  $ hg prune -r 'desc(B0)'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at 471f378eab4c
  1 changesets pruned
  $ sync
  $ hg log --hidden -G
  x  changeset:   2:0dec01379d3b
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  obsolete:    pruned using prune
  |  summary:     B0
  |
  @  changeset:   1:471f378eab4c
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A0
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  

Actual test
-----------

  $ hg obslog 'desc(B0)' --hidden --patch
  x  0dec01379d3b (2) B0
       pruned using prune by test (Thu Jan 01 00:00:00 1970 +0000)
         (No patch available, no predecessors)
  
  $ hg obslog 'desc(B0)' --hidden --no-graph -Tjson | "$PYTHON" -m json.tool
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
                  "operations": [
                      "prune"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "pruned"
              }
          ],
          "node": "0dec01379d3be6318c470ead31b1fe7ae7cb53d5",
          "shortdescription": "B0"
      }
  ]
  $ hg obslog 'desc(A0)' --patch
  @  471f378eab4c (1) A0
  
  $ hg obslog 'desc(A0)' --no-graph -Tjson | "$PYTHON" -m json.tool
  [
      {
          "markers": [],
          "node": "471f378eab4c5e25f6c77f785b27c936efb22874",
          "shortdescription": "A0"
      }
  ]
  $ hg up 1
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg up 0dec01379d3b
  abort: hidden revision '0dec01379d3b' is pruned
  (use --hidden to access hidden revisions)
  [10]
  $ hg up --hidden -r 'desc(B0)'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 0dec01379d3b
  (hidden revision '0dec01379d3b' is pruned)
  working directory parent is obsolete! (0dec01379d3b)
  (use 'hg evolve' to update to its parent successor)

Check output on the server side
-------------------------------

  $ hg obslog -f -R $TESTTMP/server --patch 0dec01379d3b --hidden
  x  0dec01379d3b (2) B0
       pruned using prune by test (Thu Jan 01 00:00:00 1970 +0000)
         (No patch available, no predecessors)
  
# TODO ADD amend + prune
