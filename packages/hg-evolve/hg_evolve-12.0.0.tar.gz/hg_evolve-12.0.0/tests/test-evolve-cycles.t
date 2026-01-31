Test that evolve related algorithms don't crash on obs markers cycles

Global setup
============

  $ . $TESTDIR/testlib/common.sh
  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > interactive = true
  > [phases]
  > publish=False
  > [extensions]
  > evolve =
  > EOF

Test with cycle
===============

Test setup
----------

  $ hg init $TESTTMP/cycle
  $ cd $TESTTMP/cycle
  $ mkcommit ROOT
  $ mkcommit A
  $ mkcommit B
  $ mkcommit C
  $ hg log -G
  @  changeset:   3:a8df460dbbfe
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     C
  |
  o  changeset:   2:c473644ee0e9
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     B
  |
  o  changeset:   1:2a34000d3544
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
Create a cycle
  $ hg prune -s "desc(B)" "desc(A)"
  1 changesets pruned
  2 new orphan changesets
  $ hg prune -s "desc(C)" "desc(B)"
  1 changesets pruned
  $ hg prune -s "desc(A)" "desc(C)"
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  working directory is now at 2a34000d3544
  1 changesets pruned
  $ hg log --hidden -G
  x  changeset:   3:a8df460dbbfe
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  obsolete:    rewritten using prune as 1:2a34000d3544
  |  summary:     C
  |
  x  changeset:   2:c473644ee0e9
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  obsolete:    rewritten using prune as 3:a8df460dbbfe
  |  summary:     B
  |
  @  changeset:   1:2a34000d3544
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  obsolete:    rewritten using prune as 2:c473644ee0e9
  |  summary:     A
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
Actual test
-----------

Check that obslog never crashes on a cycle

  $ hg obslog "desc(A)" --hidden
  @  2a34000d3544 (1) A
  |    rewritten(description, parent, content) from a8df460dbbfe using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  a8df460dbbfe (3) C
  |    rewritten(description, parent, content) from c473644ee0e9 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  c473644ee0e9 (2) B
  |    rewritten(description, parent, content) from 2a34000d3544 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |

  $ hg obslog "desc(B)" --hidden
  @  2a34000d3544 (1) A
  |    rewritten(description, parent, content) from a8df460dbbfe using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  a8df460dbbfe (3) C
  |    rewritten(description, parent, content) from c473644ee0e9 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  c473644ee0e9 (2) B
  |    rewritten(description, parent, content) from 2a34000d3544 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |

  $ hg obslog "desc(C)" --hidden
  @  2a34000d3544 (1) A
  |    rewritten(description, parent, content) from a8df460dbbfe using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  a8df460dbbfe (3) C
  |    rewritten(description, parent, content) from c473644ee0e9 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  c473644ee0e9 (2) B
  |    rewritten(description, parent, content) from 2a34000d3544 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |

  $ hg obslog "desc(C)" --hidden --no-origin
  @  2a34000d3544 (1) A
  |    rewritten(description, parent, content) as c473644ee0e9 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  a8df460dbbfe (3) C
  |    rewritten(description, parent, content) as 2a34000d3544 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  c473644ee0e9 (2) B
  |    rewritten(description, parent, content) as a8df460dbbfe using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |

Check that all option doesn't crash on a cycle either

  $ hg obslog "desc(C)" --hidden --all
  @  2a34000d3544 (1) A
  |    rewritten(description, parent, content) from a8df460dbbfe using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  a8df460dbbfe (3) C
  |    rewritten(description, parent, content) from c473644ee0e9 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  c473644ee0e9 (2) B
  |    rewritten(description, parent, content) from 2a34000d3544 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |

  $ hg obslog "desc(C)" --hidden --all --no-origin
  @  2a34000d3544 (1) A
  |    rewritten(description, parent, content) as c473644ee0e9 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  a8df460dbbfe (3) C
  |    rewritten(description, parent, content) as 2a34000d3544 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  c473644ee0e9 (2) B
  |    rewritten(description, parent, content) as a8df460dbbfe using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |

Test with multiple cyles
========================

Test setup
----------

  $ hg init $TESTTMP/multiple-cycle
  $ cd $TESTTMP/multiple-cycle
  $ mkcommit ROOT
  $ mkcommit A
  $ mkcommit B
  $ mkcommit C
  $ mkcommit D
  $ mkcommit E
  $ mkcommit F
  $ hg log -G
  @  changeset:   6:d9f908fde1a1
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     F
  |
  o  changeset:   5:0da815c333f6
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     E
  |
  o  changeset:   4:868d2e0eb19c
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     D
  |
  o  changeset:   3:a8df460dbbfe
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     C
  |
  o  changeset:   2:c473644ee0e9
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     B
  |
  o  changeset:   1:2a34000d3544
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     A
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
Create a first cycle
  $ hg prune -s "desc(B)" "desc(A)"
  1 changesets pruned
  5 new orphan changesets
  $ hg prune -s "desc(C)" "desc(B)"
  1 changesets pruned
  $ hg prune --split -s "desc(A)" -s "desc(D)" "desc(C)"
  1 changesets pruned
And create a second one
  $ hg prune -s "desc(E)" "desc(D)"
  1 changesets pruned
  $ hg prune -s "desc(F)" "desc(E)"
  1 changesets pruned
  $ hg prune -s "desc(D)" "desc(F)"
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  working directory is now at 868d2e0eb19c
  1 changesets pruned
  $ hg log --hidden -G
  x  changeset:   6:d9f908fde1a1
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  obsolete:    rewritten using prune as 4:868d2e0eb19c
  |  summary:     F
  |
  x  changeset:   5:0da815c333f6
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  obsolete:    rewritten using prune as 6:d9f908fde1a1
  |  summary:     E
  |
  @  changeset:   4:868d2e0eb19c
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  obsolete:    rewritten using prune as 5:0da815c333f6
  |  summary:     D
  |
  x  changeset:   3:a8df460dbbfe
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  obsolete:    split using prune as 1:2a34000d3544, 4:868d2e0eb19c
  |  summary:     C
  |
  x  changeset:   2:c473644ee0e9
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  obsolete:    rewritten using prune as 3:a8df460dbbfe
  |  summary:     B
  |
  x  changeset:   1:2a34000d3544
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  obsolete:    rewritten using prune as 2:c473644ee0e9
  |  summary:     A
  |
  o  changeset:   0:ea207398892e
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     ROOT
  
Actual test
-----------

Check that obslog never crashes on a cycle

  $ hg obslog "desc(D)" --hidden
  x  0da815c333f6 (5) E
  |    rewritten(description, parent, content) from 868d2e0eb19c using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  @    868d2e0eb19c (4) D
  |\     split(description, parent, content) from a8df460dbbfe using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    rewritten(description, parent, content) from d9f908fde1a1 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  d9f908fde1a1 (6) F
  | |    rewritten(description, parent, content) from 0da815c333f6 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  +---x  2a34000d3544 (1) A
  | |      split(description, parent, content) from a8df460dbbfe using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  a8df460dbbfe (3) C
  | |    rewritten(description, parent, content) from c473644ee0e9 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  c473644ee0e9 (2) B
  | |    rewritten(description, parent, content) from 2a34000d3544 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |

  $ hg obslog "desc(D)" --hidden --no-origin
  x  0da815c333f6 (5) E
  |    rewritten(description, parent, content) as d9f908fde1a1 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  @    868d2e0eb19c (4) D
  |\     rewritten(description, parent, content) as 0da815c333f6 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  d9f908fde1a1 (6) F
  | |    rewritten(description, parent, content) as 868d2e0eb19c using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  +---x  2a34000d3544 (1) A
  | |      rewritten(description, parent, content) as c473644ee0e9 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  a8df460dbbfe (3) C
  | |    split(description, parent, content) as 2a34000d3544, 868d2e0eb19c using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  c473644ee0e9 (2) B
  | |    rewritten(description, parent, content) as a8df460dbbfe using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |

Check that all option doesn't crash on a cycle either

  $ hg obslog --all --hidden "desc(F)"
  x  0da815c333f6 (5) E
  |    rewritten(description, parent, content) from 868d2e0eb19c using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  @    868d2e0eb19c (4) D
  |\     split(description, parent, content) from a8df460dbbfe using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    rewritten(description, parent, content) from d9f908fde1a1 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  d9f908fde1a1 (6) F
  | |    rewritten(description, parent, content) from 0da815c333f6 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  +---x  2a34000d3544 (1) A
  | |      split(description, parent, content) from a8df460dbbfe using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  a8df460dbbfe (3) C
  | |    rewritten(description, parent, content) from c473644ee0e9 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  c473644ee0e9 (2) B
  | |    rewritten(description, parent, content) from 2a34000d3544 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |

  $ hg obslog --all --hidden --no-origin "desc(F)"
  x  0da815c333f6 (5) E
  |    rewritten(description, parent, content) as d9f908fde1a1 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  @    868d2e0eb19c (4) D
  |\     rewritten(description, parent, content) as 0da815c333f6 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  d9f908fde1a1 (6) F
  | |    rewritten(description, parent, content) as 868d2e0eb19c using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  +---x  2a34000d3544 (1) A
  | |      rewritten(description, parent, content) as c473644ee0e9 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  a8df460dbbfe (3) C
  | |    split(description, parent, content) as 2a34000d3544, 868d2e0eb19c using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  c473644ee0e9 (2) B
  | |    rewritten(description, parent, content) as a8df460dbbfe using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |

Check the json output is valid in this case

  $ hg obslog "desc(D)" --hidden --no-graph -Tjson | "$PYTHON" -m json.tool
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
                      "description",
                      "parent",
                      "content"
                  ],
                  "operations": [
                      "prune"
                  ],
                  "prednodes": [
                      "a8df460dbbfe9ef0c1e5ab4fff02e9514672e379"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "split"
              },
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
                      "prune"
                  ],
                  "prednodes": [
                      "d9f908fde1a10ad198a462a3ec8b440bb397fc9c"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "rewritten"
              }
          ],
          "node": "868d2e0eb19c2b55a2894d37e1c435c221384d48",
          "shortdescription": "D"
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
                      "prune"
                  ],
                  "prednodes": [
                      "0da815c333f6364b46c86b0a897c00eb617397b6"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "rewritten"
              }
          ],
          "node": "d9f908fde1a10ad198a462a3ec8b440bb397fc9c",
          "shortdescription": "F"
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
                      "prune"
                  ],
                  "prednodes": [
                      "868d2e0eb19c2b55a2894d37e1c435c221384d48"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "rewritten"
              }
          ],
          "node": "0da815c333f6364b46c86b0a897c00eb617397b6",
          "shortdescription": "E"
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
                      "prune"
                  ],
                  "prednodes": [
                      "c473644ee0e988d7f537e31423831bbc409f12f7"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "rewritten"
              }
          ],
          "node": "a8df460dbbfe9ef0c1e5ab4fff02e9514672e379",
          "shortdescription": "C"
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
                      "prune"
                  ],
                  "prednodes": [
                      "2a34000d35446022104f7a091c06fe21ff2b5912"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "rewritten"
              }
          ],
          "node": "c473644ee0e988d7f537e31423831bbc409f12f7",
          "shortdescription": "B"
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
                      "prune"
                  ],
                  "prednodes": [
                      "a8df460dbbfe9ef0c1e5ab4fff02e9514672e379"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "split"
              }
          ],
          "node": "2a34000d35446022104f7a091c06fe21ff2b5912",
          "shortdescription": "A"
      }
  ]

  $ hg obslog "desc(D)" --hidden --no-graph --no-origin -Tjson | "$PYTHON" -m json.tool
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
                      "description",
                      "parent",
                      "content"
                  ],
                  "operations": [
                      "prune"
                  ],
                  "succnodes": [
                      "0da815c333f6364b46c86b0a897c00eb617397b6"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "rewritten"
              }
          ],
          "node": "868d2e0eb19c2b55a2894d37e1c435c221384d48",
          "shortdescription": "D"
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
                      "prune"
                  ],
                  "succnodes": [
                      "868d2e0eb19c2b55a2894d37e1c435c221384d48"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "rewritten"
              }
          ],
          "node": "d9f908fde1a10ad198a462a3ec8b440bb397fc9c",
          "shortdescription": "F"
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
                      "prune"
                  ],
                  "succnodes": [
                      "d9f908fde1a10ad198a462a3ec8b440bb397fc9c"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "rewritten"
              }
          ],
          "node": "0da815c333f6364b46c86b0a897c00eb617397b6",
          "shortdescription": "E"
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
                      "prune"
                  ],
                  "succnodes": [
                      "2a34000d35446022104f7a091c06fe21ff2b5912",
                      "868d2e0eb19c2b55a2894d37e1c435c221384d48"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "split"
              }
          ],
          "node": "a8df460dbbfe9ef0c1e5ab4fff02e9514672e379",
          "shortdescription": "C"
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
                      "prune"
                  ],
                  "succnodes": [
                      "a8df460dbbfe9ef0c1e5ab4fff02e9514672e379"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "rewritten"
              }
          ],
          "node": "c473644ee0e988d7f537e31423831bbc409f12f7",
          "shortdescription": "B"
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
                      "prune"
                  ],
                  "succnodes": [
                      "c473644ee0e988d7f537e31423831bbc409f12f7"
                  ],
                  "users": [
                      "test"
                  ],
                  "verb": "rewritten"
              }
          ],
          "node": "2a34000d35446022104f7a091c06fe21ff2b5912",
          "shortdescription": "A"
      }
  ]
