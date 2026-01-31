test for range based discovery
==============================

  $ . $TESTDIR/testlib/pythonpath.sh

  $ cat << EOF >> $HGRCPATH
  > [extensions]
  > evolve =
  > blackbox =
  > [defaults]
  > blackbox = -l 100
  > [blackbox]
  > track = backupbundle, cache, command, commandalias, commandfinish, debug,
  >         discovery, evoext-cache, evoext-obsdiscovery, incoming, tagscache
  > [experimental]
  > obshashrange=1
  > verbose-obsolescence-exchange=1
  > [ui]
  > logtemplate = "{rev} {node|short} {desc} {tags}\n"
  > ssh = "$PYTHON" "$RUNTESTDIR/dummyssh"
  > EOF

  $ getid() {
  >     hg log --hidden --template '{node}\n' --rev "$1" --config 'extensions.blackbox=!'
  > }

  $ hg init server
  $ hg clone ssh://user@dummy/server client
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd server
  $ hg debugbuilddag '.+7'
  $ hg blackbox
  * @0000000000000000000000000000000000000000 (*)> init server exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> -R server serve --stdio (glob)
  * @0000000000000000000000000000000000000000 (*)> -R server serve --stdio exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> debugbuilddag .+7 (glob) (no-windows !)
  * @0000000000000000000000000000000000000000 (*)> debugbuilddag ".+7" (glob) (windows !)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obscache in *.???? seconds (8r, 0o) (glob)
  * @0000000000000000000000000000000000000000 (*)> debugbuilddag .+7 exited 0 after *.?? seconds (glob) (no-windows !)
  * @0000000000000000000000000000000000000000 (*)> debugbuilddag ".+7" exited 0 after *.?? seconds (glob) (windows !)
  * @0000000000000000000000000000000000000000 (*)> blackbox (glob)
  $ rm .hg/blackbox.log
  $ hg log -G
  o  7 4de32a90b66c r7 tip
  |
  o  6 f69452c5b1af r6
  |
  o  5 c8d03c1b5e94 r5
  |
  o  4 bebd167eb94d r4
  |
  o  3 2dc09a01254d r3
  |
  o  2 01241442b3c2 r2
  |
  o  1 66f7d451a68b r1
  |
  o  0 1ea73414a91b r0
  

  $ hg debugobsolete aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa `getid 'desc(r1)'`
  1 new obsolescence markers
  $ hg debugobsolete bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb `getid 'desc(r2)'` --config experimental.obshashrange.max-revs=1
  1 new obsolescence markers
  $ hg debugobsolete cccccccccccccccccccccccccccccccccccccccc `getid 'desc(r4)'`
  1 new obsolescence markers
  $ hg debugobsolete dddddddddddddddddddddddddddddddddddddddd `getid 'desc(r5)'` --config experimental.obshashrange.warm-cache=0
  1 new obsolescence markers
  $ hg debugobsolete eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee `getid 'desc(r7)'`
  1 new obsolescence markers
  $ hg debugobsolete
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb 01241442b3c2bf3211e593b549c655ea65b295e3 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  cccccccccccccccccccccccccccccccccccccccc bebd167eb94d257ace0e814aeb98e6972ed2970d 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  dddddddddddddddddddddddddddddddddddddddd c8d03c1b5e94af74b772900c58259d2e08917735 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee 4de32a90b66cd083ebf3c00b41277aa7abca51dd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}

  $ hg blackbox
  * @0000000000000000000000000000000000000000 (*)> log -G (glob)
  * @0000000000000000000000000000000000000000 (*)> writing .hg/cache/tags2-visible with 0 tags (glob)
  * @0000000000000000000000000000000000000000 (*)> log -G exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 66f7d451a68b85ed82ff5fcc254daf50c74144bd (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 66f7d451a68b85ed82ff5fcc254daf50c74144bd exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb 01241442b3c2bf3211e593b549c655ea65b295e3 --config *experimental.obshashrange.max-revs=1* (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb 01241442b3c2bf3211e593b549c655ea65b295e3 --config *experimental.obshashrange.max-revs=1* exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete cccccccccccccccccccccccccccccccccccccccc bebd167eb94d257ace0e814aeb98e6972ed2970d (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete cccccccccccccccccccccccccccccccccccccccc bebd167eb94d257ace0e814aeb98e6972ed2970d exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete dddddddddddddddddddddddddddddddddddddddd c8d03c1b5e94af74b772900c58259d2e08917735 --config *experimental.obshashrange.warm-cache=0* (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete dddddddddddddddddddddddddddddddddddddddd c8d03c1b5e94af74b772900c58259d2e08917735 --config *experimental.obshashrange.warm-cache=0* exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee 4de32a90b66cd083ebf3c00b41277aa7abca51dd (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee 4de32a90b66cd083ebf3c00b41277aa7abca51dd exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> blackbox (glob)
  $ rm .hg/blackbox.log
  $ hg debugobshashrange --subranges --rev tip
           rev         node        index         size        depth      obshash
             7 4de32a90b66c            0            8            8 38d1e7ad86ea
             3 2dc09a01254d            0            4            4 000000000000
             7 4de32a90b66c            4            4            8 38d1e7ad86ea
             3 2dc09a01254d            2            2            4 000000000000
             7 4de32a90b66c            6            2            8 033544c939f0
             1 66f7d451a68b            0            2            2 17ff8dd63509
             5 c8d03c1b5e94            4            2            6 57f6cf3757a2
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 000000000000
             7 4de32a90b66c            7            1            8 033544c939f0
             1 66f7d451a68b            1            1            2 17ff8dd63509
             4 bebd167eb94d            4            1            5 bbe4d7fe27a8
             5 c8d03c1b5e94            5            1            6 446c2dc3bce5
             6 f69452c5b1af            6            1            7 000000000000
  $ cd .. 

testing simple pull
===================

  $ cd client
  $ hg pull --rev 4
  pulling from ssh://user@dummy/server
  adding changesets
  adding manifests
  adding file changes
  added 5 changesets with 0 changes to 0 files
  3 new obsolescence markers
  new changesets 1ea73414a91b:bebd167eb94d
  (run 'hg update' to get a working copy)
  $ hg -R ../server blackbox
  * @0000000000000000000000000000000000000000 (*)> debugobshashrange --subranges --rev tip (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-depthcache in *.???? seconds (8r) (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-stablerange-mergepoint in *.???? seconds (8r) (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obshashrange in *.???? seconds (8r, 5o) (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-stablesort in *.???? seconds (8r) (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-firstmerge in *.???? seconds (8r) (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobshashrange --subranges --rev tip exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> -R server serve --stdio (glob)
  * @0000000000000000000000000000000000000000 (*)> -R server serve --stdio exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> -R ../server blackbox (glob)
  $ rm ../server/.hg/blackbox.log
  $ hg -R ../server/ debugobsolete --rev ::4 | sort
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb 01241442b3c2bf3211e593b549c655ea65b295e3 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  cccccccccccccccccccccccccccccccccccccccc bebd167eb94d257ace0e814aeb98e6972ed2970d 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  $ rm ../server/.hg/blackbox.log
  $ hg blackbox
  * @0000000000000000000000000000000000000000 (*)> clone *ssh://user@dummy/server* client exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> pull --rev 4 (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obscache in *.???? seconds (5r, 3o) (glob)
  * @0000000000000000000000000000000000000000 (*)> 5 incoming changes - new heads: bebd167eb94d (glob)
  * @0000000000000000000000000000000000000000 (*)> pull --rev 4 exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> blackbox (glob)
  $ rm .hg/blackbox.log
  $ hg debugobsolete | sort
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb 01241442b3c2bf3211e593b549c655ea65b295e3 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  cccccccccccccccccccccccccccccccccccccccc bebd167eb94d257ace0e814aeb98e6972ed2970d 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}

testing simple push
===================

  $ hg up
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo foo > foo
  $ hg add foo
  $ hg commit -m foo
  $ hg debugobsolete ffffffffffffffffffffffffffffffffffffffff `getid '.'`
  1 new obsolescence markers
  $ hg push -f --debug
  could not import hgext.hgext3rd.evolve (No module named hgext3rd.evolve): trying hgext3rd.hgext3rd.evolve (?)
  could not import hgext3rd.hgext3rd.evolve (No module named hgext3rd.evolve): trying hgext3rd.evolve (?)
  pushing to ssh://user@dummy/server
  running "*python*" "*/dummyssh" *user@dummy* *hg -R server serve --stdio* (glob)
  sending hello command
  sending between command
  remote: * (glob)
  remote: capabilities: _evoext_getbundle_obscommon _evoext_obshashrange_v1 batch * (glob)
  remote: 1
  sending protocaps command
  query 1; heads
  sending batch command
  searching for changes
  taking quick initial sample
  query 2; still undecided: 5, sample size is: 5
  sending known command
  2 total queries in *.????s (glob)
  preparing listkeys for "phases"
  sending listkeys command
  received listkey for "phases": 58 bytes
  preparing listkeys for "namespaces"
  sending listkeys command
  received listkey for "namespaces": 40 bytes
  OBSEXC: computing relevant nodes
  OBSEXC: looking for common markers in 6 nodes
  stable-range cache: unable to load, regenerating
  obshashrange cache: unable to load, regenerating
  query 0; add more sample (target 100, current 1)
  query 0; sample size is 9, largest range 5
  sending evoext_obshashrange_v1 command
  obsdiscovery, 0/5 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  OBSEXC: computing markers relevant to 1 nodes
  checking for updated bookmarks
  preparing listkeys for "bookmarks"
  sending listkeys command
  received listkey for "bookmarks": 0 bytes
  1 changesets found
  list of changesets:
  45f8b879de922f6a6e620ba04205730335b6fc7e
  sending unbundle command
  bundle2-output-bundle: "HG20", 4 parts total
  bundle2-output-part: "replycaps" * bytes payload (glob)
  bundle2-output-part: "changegroup" (params: 1 mandatory) streamed payload
  bundle2-output-part: "phase-heads" 24 bytes payload
  bundle2-output-part: "obsmarkers" streamed payload
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: 1 new obsolescence markers
  bundle2-input-bundle: no-transaction
  bundle2-input-part: "reply:changegroup" (advisory) (params: 0 advisory) supported
  bundle2-input-part: "reply:obsmarkers" (params: 0 advisory) supported
  bundle2-input-bundle: 2 parts total
  preparing listkeys for "phases"
  sending listkeys command
  received listkey for "phases": 58 bytes
  $ hg -R ../server blackbox
  * @0000000000000000000000000000000000000000 (*)> -R server serve --stdio (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-firstmerge in *.???? seconds (1r) (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-depthcache in *.???? seconds (1r) (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-stablesort in *.???? seconds (1r) (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-stablerange-mergepoint in *.???? seconds (1r) (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obshashrange in *.???? seconds (1r, 1o) (glob)
  * @0000000000000000000000000000000000000000 (*)> obscache is out of date, falling back to slower obsstore version (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obscache in *.???? seconds (1r, 1o) (glob)
  * @0000000000000000000000000000000000000000 (*)> 1 incoming changes - new heads: 45f8b879de92 (glob)
  * @0000000000000000000000000000000000000000 (*)> -R server serve --stdio exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> -R ../server blackbox (glob)
  $ rm ../server/.hg/blackbox.log

testing push with extra local markers
=====================================

  $ hg log -G
  @  5 45f8b879de92 foo tip
  |
  o  4 bebd167eb94d r4
  |
  o  3 2dc09a01254d r3
  |
  o  2 01241442b3c2 r2
  |
  o  1 66f7d451a68b r1
  |
  o  0 1ea73414a91b r0
  
  $ hg debugobsolete 111111111111111aaaaaaaaa1111111111111111 `getid 'desc(r1)'`
  1 new obsolescence markers
  $ hg debugobsolete 22222222222222222bbbbbbbbbbbbb2222222222 `getid 'desc(r3)'`
  1 new obsolescence markers
  $ hg push
  pushing to ssh://user@dummy/server
  searching for changes
  OBSEXC: computing relevant nodes
  OBSEXC: looking for common markers in 6 nodes
  OBSEXC: computing markers relevant to 2 nodes
  no changes found
  remote: 2 new obsolescence markers
  [1]
  $ hg -R ../server blackbox
  * @0000000000000000000000000000000000000000 (*)> -R server serve --stdio (glob)
  * @0000000000000000000000000000000000000000 (*)> obshashcache clean - new markers affect 2 changeset and cached ranges (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obshashrange in *.???? seconds (0r, 2o) (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obscache in *.???? seconds (0r, 2o) (glob)
  * @0000000000000000000000000000000000000000 (*)> -R server serve --stdio exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> -R ../server blackbox (glob)
  $ rm ../server/.hg/blackbox.log
  $ hg -R ../server/ debugobsolete --rev ::tip | sort
  111111111111111aaaaaaaaa1111111111111111 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  22222222222222222bbbbbbbbbbbbb2222222222 2dc09a01254db841290af0538aa52f6f52c776e3 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb 01241442b3c2bf3211e593b549c655ea65b295e3 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  cccccccccccccccccccccccccccccccccccccccc bebd167eb94d257ace0e814aeb98e6972ed2970d 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  ffffffffffffffffffffffffffffffffffffffff 45f8b879de922f6a6e620ba04205730335b6fc7e 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  $ hg blackbox
  * @0000000000000000000000000000000000000000 (*)> debugobsolete (glob)
  * @0000000000000000000000000000000000000000 (*)> debugobsolete exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> up (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> up exited 0 after *.?? seconds (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> add foo (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> add foo exited 0 after *.?? seconds (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> commit -m foo (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obscache is out of date, falling back to slower obsstore version (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (1r, 0o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> commit -m foo exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobsolete ffffffffffffffffffffffffffffffffffffffff 45f8b879de922f6a6e620ba04205730335b6fc7e (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobsolete ffffffffffffffffffffffffffffffffffffffff 45f8b879de922f6a6e620ba04205730335b6fc7e exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> push -f --debug (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> running "*python*" "*/dummyssh" *user@dummy* *hg -R server serve --stdio* (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> sending hello command (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> sending between command (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> remote: * (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> remote: capabilities: _evoext_getbundle_obscommon _evoext_obshashrange_v1 batch * (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> remote: 1 (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> sending protocaps command (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> query 1; heads (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> sending batch command (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> taking quick initial sample (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> query 2; still undecided: 5, sample size is: 5 (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> sending known command (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> 2 total queries in *.????s (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> found 1 common and 1 unknown server heads, 2 roundtrips in *.????s (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> preparing listkeys for "phases" (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> sending listkeys command (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> received listkey for "phases": 58 bytes (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> preparing listkeys for "namespaces" (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> sending listkeys command (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> received listkey for "namespaces": 40 bytes (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> stable-range cache: unable to load, regenerating (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-depthcache in *.???? seconds (6r) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-stablerange-mergepoint in *.???? seconds (6r) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obshashrange cache: unable to load, regenerating (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obshashrange in *.???? seconds (6r, 4o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> query 0; add more sample (target 100, current 1) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> query 0; sample size is 9, largest range 5 (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> sending evoext_obshashrange_v1 command (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-stablesort in *.???? seconds (6r) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-firstmerge in *.???? seconds (6r) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obsdiscovery, 0/5 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obsdiscovery, 0/5 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> checking for updated bookmarks (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> preparing listkeys for "bookmarks" (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> sending listkeys command (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> received listkey for "bookmarks": 0 bytes (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> list of changesets: (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> 45f8b879de922f6a6e620ba04205730335b6fc7e (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> sending unbundle command (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> bundle2-output-bundle: "HG20", 4 parts total (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> bundle2-output-part: "replycaps" * bytes payload (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> bundle2-output-part: "changegroup" (params: 1 mandatory) streamed payload (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> bundle2-output-part: "phase-heads" 24 bytes payload (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> bundle2-output-part: "obsmarkers" streamed payload (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> bundle2-input-bundle: no-transaction (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> bundle2-input-part: "reply:changegroup" (advisory) (params: 0 advisory) supported (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> bundle2-input-part: "reply:obsmarkers" (params: 0 advisory) supported (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> bundle2-input-bundle: 2 parts total (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> preparing listkeys for "phases" (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> sending listkeys command (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> received listkey for "phases": 58 bytes (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> push -f --debug exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> log -G (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> writing .hg/cache/tags2-visible with 0 tags (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> log -G exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobsolete 111111111111111aaaaaaaaa1111111111111111 66f7d451a68b85ed82ff5fcc254daf50c74144bd (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobsolete 111111111111111aaaaaaaaa1111111111111111 66f7d451a68b85ed82ff5fcc254daf50c74144bd exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobsolete 22222222222222222bbbbbbbbbbbbb2222222222 2dc09a01254db841290af0538aa52f6f52c776e3 (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobsolete 22222222222222222bbbbbbbbbbbbb2222222222 2dc09a01254db841290af0538aa52f6f52c776e3 exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> push (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obshashcache clean - new markers affect 2 changeset and cached ranges (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obshashrange in *.???? seconds (0r, 2o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obsdiscovery, 2/6 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> push exited 1 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> blackbox (glob)
  $ rm .hg/blackbox.log
  $ hg debugobsolete | sort
  111111111111111aaaaaaaaa1111111111111111 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  22222222222222222bbbbbbbbbbbbb2222222222 2dc09a01254db841290af0538aa52f6f52c776e3 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb 01241442b3c2bf3211e593b549c655ea65b295e3 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  cccccccccccccccccccccccccccccccccccccccc bebd167eb94d257ace0e814aeb98e6972ed2970d 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  ffffffffffffffffffffffffffffffffffffffff 45f8b879de922f6a6e620ba04205730335b6fc7e 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}

testing pull with extra remote markers
=====================================

  $ hg log -G
  @  5 45f8b879de92 foo tip
  |
  o  4 bebd167eb94d r4
  |
  o  3 2dc09a01254d r3
  |
  o  2 01241442b3c2 r2
  |
  o  1 66f7d451a68b r1
  |
  o  0 1ea73414a91b r0
  
  $ hg -R ../server debugobsolete aaaaaaa11111111aaaaaaaaa1111111111111111 `getid 'desc(r1)'`
  1 new obsolescence markers
  $ hg -R ../server debugobsolete bbbbbbb2222222222bbbbbbbbbbbbb2222222222 `getid 'desc(r4)'`
  1 new obsolescence markers
  $ hg pull -r 6
  pulling from ssh://user@dummy/server
  searching for changes
  OBSEXC: looking for common markers in 6 nodes
  OBSEXC: request obsmarkers for 2 common nodes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 0 changes to 0 files (+1 heads)
  3 new obsolescence markers
  new changesets c8d03c1b5e94:f69452c5b1af
  (run 'hg heads' to see heads, 'hg merge' to merge)

  $ hg -R ../server blackbox
  * @0000000000000000000000000000000000000000 (*)> -R ../server/ debugobsolete --rev '::tip' (glob) (no-windows !)
  * @0000000000000000000000000000000000000000 (*)> -R ../server/ debugobsolete --rev ::tip (glob) (windows !)
  * @0000000000000000000000000000000000000000 (*)> writing .hg/cache/tags2-visible with 0 tags (glob)
  * @0000000000000000000000000000000000000000 (*)> -R ../server/ debugobsolete --rev '::tip' exited 0 after *.?? seconds (glob) (no-windows !)
  * @0000000000000000000000000000000000000000 (*)> -R ../server/ debugobsolete --rev ::tip exited 0 after *.?? seconds (glob) (windows !)
  * @0000000000000000000000000000000000000000 (*)> -R ../server debugobsolete aaaaaaa11111111aaaaaaaaa1111111111111111 66f7d451a68b85ed82ff5fcc254daf50c74144bd (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @0000000000000000000000000000000000000000 (*)> -R ../server debugobsolete aaaaaaa11111111aaaaaaaaa1111111111111111 66f7d451a68b85ed82ff5fcc254daf50c74144bd exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> -R ../server debugobsolete bbbbbbb2222222222bbbbbbbbbbbbb2222222222 bebd167eb94d257ace0e814aeb98e6972ed2970d (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @0000000000000000000000000000000000000000 (*)> -R ../server debugobsolete bbbbbbb2222222222bbbbbbbbbbbbb2222222222 bebd167eb94d257ace0e814aeb98e6972ed2970d exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> -R server serve --stdio (glob)
  * @0000000000000000000000000000000000000000 (*)> obshashcache clean - new markers affect 3 changeset and cached ranges (glob)
  * @0000000000000000000000000000000000000000 (*)> updated evo-ext-obshashrange in *.???? seconds (0r, 4o) (glob)
  * @0000000000000000000000000000000000000000 (*)> -R server serve --stdio exited 0 after *.?? seconds (glob)
  * @0000000000000000000000000000000000000000 (*)> -R ../server blackbox (glob)
  $ rm ../server/.hg/blackbox.log
  $ hg -R ../server/ debugobsolete --rev '::6' | sort
  111111111111111aaaaaaaaa1111111111111111 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  22222222222222222bbbbbbbbbbbbb2222222222 2dc09a01254db841290af0538aa52f6f52c776e3 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  aaaaaaa11111111aaaaaaaaa1111111111111111 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  bbbbbbb2222222222bbbbbbbbbbbbb2222222222 bebd167eb94d257ace0e814aeb98e6972ed2970d 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb 01241442b3c2bf3211e593b549c655ea65b295e3 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  cccccccccccccccccccccccccccccccccccccccc bebd167eb94d257ace0e814aeb98e6972ed2970d 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  dddddddddddddddddddddddddddddddddddddddd c8d03c1b5e94af74b772900c58259d2e08917735 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  $ hg blackbox
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobsolete (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobsolete exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> log -G (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> log -G exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull -r 6 (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obsdiscovery, 2/6 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (2r, 3o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> 2 incoming changes - new heads: f69452c5b1af (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull -r 6 exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> blackbox (glob)
  $ rm .hg/blackbox.log
  $ hg debugobsolete --rev '::6' | sort
  111111111111111aaaaaaaaa1111111111111111 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  22222222222222222bbbbbbbbbbbbb2222222222 2dc09a01254db841290af0538aa52f6f52c776e3 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  aaaaaaa11111111aaaaaaaaa1111111111111111 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 66f7d451a68b85ed82ff5fcc254daf50c74144bd 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  bbbbbbb2222222222bbbbbbbbbbbbb2222222222 bebd167eb94d257ace0e814aeb98e6972ed2970d 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb 01241442b3c2bf3211e593b549c655ea65b295e3 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  cccccccccccccccccccccccccccccccccccccccc bebd167eb94d257ace0e814aeb98e6972ed2970d 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}
  dddddddddddddddddddddddddddddddddddddddd c8d03c1b5e94af74b772900c58259d2e08917735 0 (Thu Jan 01 00:00:00 1970 +0000) {'user': 'test'}

Test cache behavior
===================

Adding markers affecting already used range:
--------------------------------------------

  $ hg debugobshashrange --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 f69452c5b1af            0            7            7 000000000000
             5 45f8b879de92            0            6            6 1643971dbe2d
             3 2dc09a01254d            0            4            4 6be48f31976a
             7 f69452c5b1af            4            3            7 000000000000
             3 2dc09a01254d            2            2            4 9522069ae085
             5 45f8b879de92            4            2            6 9c26c72819c0
             1 66f7d451a68b            0            2            2 853c77a32154
             6 c8d03c1b5e94            4            2            6 ec8a3e92c525
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 8a2acf8e1cde
             5 45f8b879de92            5            1            6 1a0c08180b65
             1 66f7d451a68b            1            1            2 853c77a32154
             4 bebd167eb94d            4            1            5 20a2cc572e4b
             6 c8d03c1b5e94            5            1            6 446c2dc3bce5
             7 f69452c5b1af            6            1            7 000000000000
  $ hg -R ../server debugobsolete aaaa333333333aaaaa333a3a3a3a3a3a3a3a3a3a `getid 'desc(r1)'`
  1 new obsolescence markers
  $ hg -R ../server debugobsolete bb4b4b4b4b4b4b4b44b4b4b4b4b4b4b4b4b4b4b4 `getid 'desc(r3)'`
  1 new obsolescence markers
  $ hg pull -r `getid 'desc(r6)'`
  pulling from ssh://user@dummy/server
  no changes found
  OBSEXC: looking for common markers in 7 nodes
  OBSEXC: request obsmarkers for 2 common nodes
  2 new obsolescence markers
  $ hg debugobshashrange --subranges --rev 'desc("r3")' -R ../server
           rev         node        index         size        depth      obshash
             3 2dc09a01254d            0            4            4 8932bf980bb4
             3 2dc09a01254d            2            2            4 ce1937ca1278
             1 66f7d451a68b            0            2            2 327c7dd73d29
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             1 66f7d451a68b            1            1            2 327c7dd73d29
  $ hg debugobshashrange --subranges --rev 'desc("r3")'
           rev         node        index         size        depth      obshash
             3 2dc09a01254d            0            4            4 8932bf980bb4
             3 2dc09a01254d            2            2            4 ce1937ca1278
             1 66f7d451a68b            0            2            2 327c7dd73d29
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             1 66f7d451a68b            1            1            2 327c7dd73d29
  $ hg blackbox
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobsolete --rev '::6' (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobsolete --rev ::6 (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> writing .hg/cache/tags2-visible with 0 tags (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobsolete --rev '::6' exited 0 after *.?? seconds (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobsolete --rev ::6 exited 0 after *.?? seconds (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-depthcache in *.???? seconds (2r) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-stablerange-mergepoint in *.???? seconds (2r) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obshashcache clean - new markers affect 2 changeset and cached ranges (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obshashrange in *.???? seconds (2r, 3o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-stablesort in *.???? seconds (2r) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-firstmerge in *.???? seconds (2r) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" exited 0 after *.?? seconds (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' exited 0 after *.?? seconds (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull -r f69452c5b1af6cbaaa56ef50cf94fff5bcc6ca23 (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obsdiscovery, 2/7 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (0r, 2o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull -r f69452c5b1af6cbaaa56ef50cf94fff5bcc6ca23 exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "desc(\"r3\")" (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'desc("r3")' (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obshashcache clean - new markers affect 2 changeset and cached ranges (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obshashrange in *.???? seconds (0r, 2o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "desc(\"r3\")" exited 0 after *.?? seconds (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'desc("r3")' exited 0 after *.?? seconds (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> blackbox (glob)
  $ rm .hg/blackbox.log

Adding markers affecting existing changeset
-------------------------------------------

Simple prune marker

  $ hg debugobshashrange -R ../server --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 4de32a90b66c            0            8            8 3e1f959425c6
             8 45f8b879de92            0            6            6 b405cb0bdc2b
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 4de32a90b66c            4            4            8 5a7179ca8e73
             3 2dc09a01254d            2            2            4 ce1937ca1278
             8 45f8b879de92            4            2            6 9c26c72819c0
             7 4de32a90b66c            6            2            8 033544c939f0
             1 66f7d451a68b            0            2            2 327c7dd73d29
             5 c8d03c1b5e94            4            2            6 ec8a3e92c525
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             8 45f8b879de92            5            1            6 1a0c08180b65
             7 4de32a90b66c            7            1            8 033544c939f0
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 20a2cc572e4b
             5 c8d03c1b5e94            5            1            6 446c2dc3bce5
             6 f69452c5b1af            6            1            7 000000000000
  $ hg -R ../server debugobsolete --record-parents `getid 'desc(foo)'`
  1 new obsolescence markers
  $ hg debugobshashrange -R ../server --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 4de32a90b66c            0            8            8 c7f1f7e9925b
             8 45f8b879de92            0            6            6 7c49a958a9ac
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 4de32a90b66c            4            4            8 c681c3e58c27
             3 2dc09a01254d            2            2            4 ce1937ca1278
             8 45f8b879de92            4            2            6 c6795525c540
             7 4de32a90b66c            6            2            8 033544c939f0
             1 66f7d451a68b            0            2            2 327c7dd73d29
             5 c8d03c1b5e94            4            2            6 89755fd39e6d
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             8 45f8b879de92            5            1            6 796507769034
             7 4de32a90b66c            7            1            8 033544c939f0
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 b21465ecb790
             5 c8d03c1b5e94            5            1            6 446c2dc3bce5
             6 f69452c5b1af            6            1            7 000000000000
  $ hg pull -r `getid 'desc(r4)'`
  pulling from ssh://user@dummy/server
  no changes found
  OBSEXC: looking for common markers in 5 nodes
  OBSEXC: request obsmarkers for 1 common nodes
  1 new obsolescence markers
  $ hg blackbox
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull -r bebd167eb94d257ace0e814aeb98e6972ed2970d (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obsdiscovery, 1/5 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull -r bebd167eb94d257ace0e814aeb98e6972ed2970d exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> blackbox (glob)
  $ rm .hg/blackbox.log
  $ hg debugobshashrange --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 f69452c5b1af            0            7            7 000000000000
             5 45f8b879de92            0            6            6 7c49a958a9ac
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 f69452c5b1af            4            3            7 000000000000
             3 2dc09a01254d            2            2            4 ce1937ca1278
             5 45f8b879de92            4            2            6 c6795525c540
             1 66f7d451a68b            0            2            2 327c7dd73d29
             6 c8d03c1b5e94            4            2            6 89755fd39e6d
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             5 45f8b879de92            5            1            6 796507769034
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 b21465ecb790
             6 c8d03c1b5e94            5            1            6 446c2dc3bce5
             7 f69452c5b1af            6            1            7 000000000000

Stacked prune markers

  $ hg -R ../server --hidden up 'desc(foo)'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo a > ../server/xhf
  $ hg -R ../server commit -Am "chain_prune"
  adding xhf
  $ hg -R ../server update null
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg debugobshashrange -R ../server --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 4de32a90b66c            0            8            8 c7f1f7e9925b
             9 09b2e73c5f20            0            7            7 000000000000
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 4de32a90b66c            4            4            8 c681c3e58c27
             9 09b2e73c5f20            4            3            7 000000000000
             3 2dc09a01254d            2            2            4 ce1937ca1278
             8 45f8b879de92            4            2            6 c6795525c540
             7 4de32a90b66c            6            2            8 033544c939f0
             1 66f7d451a68b            0            2            2 327c7dd73d29
             5 c8d03c1b5e94            4            2            6 89755fd39e6d
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             9 09b2e73c5f20            6            1            7 000000000000
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             8 45f8b879de92            5            1            6 796507769034
             7 4de32a90b66c            7            1            8 033544c939f0
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 b21465ecb790
             5 c8d03c1b5e94            5            1            6 446c2dc3bce5
             6 f69452c5b1af            6            1            7 000000000000
  $ hg -R ../server debugobsolete --record-parents `(cd ../server/; getid 'desc("chain_prune")')`
  1 new obsolescence markers
  obsoleted 1 changesets
  $ hg debugobshashrange -R ../server --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 4de32a90b66c            0            8            8 f966d46c2069
             8 45f8b879de92            0            6            6 c9ee11811914
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 4de32a90b66c            4            4            8 542cc6dd4c67
             3 2dc09a01254d            2            2            4 ce1937ca1278
             8 45f8b879de92            4            2            6 b5d53b723b2e
             7 4de32a90b66c            6            2            8 033544c939f0
             1 66f7d451a68b            0            2            2 327c7dd73d29
             5 c8d03c1b5e94            4            2            6 b0302c7614fb
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             8 45f8b879de92            5            1            6 78e8071e893a
             7 4de32a90b66c            7            1            8 033544c939f0
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 9b4a136d1137
             5 c8d03c1b5e94            5            1            6 446c2dc3bce5
             6 f69452c5b1af            6            1            7 000000000000
  $ hg debugobshashrange -R ../server --subranges --rev 'heads(all())' --hidden
           rev         node        index         size        depth      obshash
             7 4de32a90b66c            0            8            8 f966d46c2069
             9 09b2e73c5f20            0            7            7 be139f5b4d01
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 4de32a90b66c            4            4            8 542cc6dd4c67
             9 09b2e73c5f20            4            3            7 7a88eb008295
             3 2dc09a01254d            2            2            4 ce1937ca1278
             8 45f8b879de92            4            2            6 b5d53b723b2e
             7 4de32a90b66c            6            2            8 033544c939f0
             1 66f7d451a68b            0            2            2 327c7dd73d29
             5 c8d03c1b5e94            4            2            6 b0302c7614fb
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             9 09b2e73c5f20            6            1            7 3339d42d829e
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             8 45f8b879de92            5            1            6 78e8071e893a
             7 4de32a90b66c            7            1            8 033544c939f0
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 9b4a136d1137
             5 c8d03c1b5e94            5            1            6 446c2dc3bce5
             6 f69452c5b1af            6            1            7 000000000000
  $ hg pull -r `getid 'desc(r4)'`
  pulling from ssh://user@dummy/server
  no changes found
  OBSEXC: looking for common markers in 5 nodes
  OBSEXC: request obsmarkers for 1 common nodes
  1 new obsolescence markers
  $ hg blackbox
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obshashcache clean - new markers affect 2 changeset and cached ranges (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obshashrange in *.???? seconds (0r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" exited 0 after *.?? seconds (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' exited 0 after *.?? seconds (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull -r bebd167eb94d257ace0e814aeb98e6972ed2970d (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obsdiscovery, 1/5 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull -r bebd167eb94d257ace0e814aeb98e6972ed2970d exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> blackbox (glob)
  $ rm .hg/blackbox.log
  $ hg debugobshashrange --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 f69452c5b1af            0            7            7 000000000000
             5 45f8b879de92            0            6            6 c9ee11811914
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 f69452c5b1af            4            3            7 000000000000
             3 2dc09a01254d            2            2            4 ce1937ca1278
             5 45f8b879de92            4            2            6 b5d53b723b2e
             1 66f7d451a68b            0            2            2 327c7dd73d29
             6 c8d03c1b5e94            4            2            6 b0302c7614fb
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             5 45f8b879de92            5            1            6 78e8071e893a
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 9b4a136d1137
             6 c8d03c1b5e94            5            1            6 446c2dc3bce5
             7 f69452c5b1af            6            1            7 000000000000

New marker prefixed to another one

  $ hg -R ../server debugobsolete aaaa4444444444444444aaaaaaaaaaaaaaaaaaaa `(cd ../server/; getid 'desc("chain_prune")')`
  1 new obsolescence markers
  $ hg debugobshashrange -R ../server --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 4de32a90b66c            0            8            8 0ffc0013bda0
             8 45f8b879de92            0            6            6 0ffa86a0054f
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 4de32a90b66c            4            4            8 207792ae6aeb
             3 2dc09a01254d            2            2            4 ce1937ca1278
             8 45f8b879de92            4            2            6 a3de812028fa
             7 4de32a90b66c            6            2            8 033544c939f0
             1 66f7d451a68b            0            2            2 327c7dd73d29
             5 c8d03c1b5e94            4            2            6 e94b0f268773
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             8 45f8b879de92            5            1            6 e765ea1567b3
             7 4de32a90b66c            7            1            8 033544c939f0
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 8e945c34a0fd
             5 c8d03c1b5e94            5            1            6 446c2dc3bce5
             6 f69452c5b1af            6            1            7 000000000000

  $ hg pull -r `getid 'desc(r4)'`
  pulling from ssh://user@dummy/server
  no changes found
  OBSEXC: looking for common markers in 5 nodes
  OBSEXC: request obsmarkers for 1 common nodes
  1 new obsolescence markers
  $ hg blackbox
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obshashcache clean - new markers affect 2 changeset and cached ranges (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obshashrange in *.???? seconds (0r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" exited 0 after *.?? seconds (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' exited 0 after *.?? seconds (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull -r bebd167eb94d257ace0e814aeb98e6972ed2970d (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obsdiscovery, 1/5 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull -r bebd167eb94d257ace0e814aeb98e6972ed2970d exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> blackbox (glob)
  $ rm .hg/blackbox.log
  $ hg debugobshashrange --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 f69452c5b1af            0            7            7 000000000000
             5 45f8b879de92            0            6            6 0ffa86a0054f
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 f69452c5b1af            4            3            7 000000000000
             3 2dc09a01254d            2            2            4 ce1937ca1278
             5 45f8b879de92            4            2            6 a3de812028fa
             1 66f7d451a68b            0            2            2 327c7dd73d29
             6 c8d03c1b5e94            4            2            6 e94b0f268773
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             5 45f8b879de92            5            1            6 e765ea1567b3
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 8e945c34a0fd
             6 c8d03c1b5e94            5            1            6 446c2dc3bce5
             7 f69452c5b1af            6            1            7 000000000000

New prune marker prefixed to another one

  $ hg -R ../server debugobsolete aaaa4444444444444444aaaaaaaaaaaaaaaaaaaa
  1 new obsolescence markers
  $ hg debugobshashrange -R ../server --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 4de32a90b66c            0            8            8 87b2a11bd884
             8 45f8b879de92            0            6            6 fdbbaec33b20
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 4de32a90b66c            4            4            8 20745010e1d8
             3 2dc09a01254d            2            2            4 ce1937ca1278
             8 45f8b879de92            4            2            6 f45551c1cf4f
             7 4de32a90b66c            6            2            8 033544c939f0
             1 66f7d451a68b            0            2            2 327c7dd73d29
             5 c8d03c1b5e94            4            2            6 149be75f95c0
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             8 45f8b879de92            5            1            6 51df11ea9843
             7 4de32a90b66c            7            1            8 033544c939f0
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 42574a82229f
             5 c8d03c1b5e94            5            1            6 446c2dc3bce5
             6 f69452c5b1af            6            1            7 000000000000

  $ hg pull -r `getid 'desc(r4)'`
  pulling from ssh://user@dummy/server
  no changes found
  OBSEXC: looking for common markers in 5 nodes
  OBSEXC: request obsmarkers for 1 common nodes
  1 new obsolescence markers
  $ hg blackbox
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obshashcache clean - new markers affect 2 changeset and cached ranges (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obshashrange in *.???? seconds (0r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" exited 0 after *.?? seconds (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' exited 0 after *.?? seconds (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull -r bebd167eb94d257ace0e814aeb98e6972ed2970d (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obsdiscovery, 1/5 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (0r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull -r bebd167eb94d257ace0e814aeb98e6972ed2970d exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> blackbox (glob)
  $ rm .hg/blackbox.log
  $ hg debugobshashrange --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 f69452c5b1af            0            7            7 000000000000
             5 45f8b879de92            0            6            6 fdbbaec33b20
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 f69452c5b1af            4            3            7 000000000000
             3 2dc09a01254d            2            2            4 ce1937ca1278
             5 45f8b879de92            4            2            6 f45551c1cf4f
             1 66f7d451a68b            0            2            2 327c7dd73d29
             6 c8d03c1b5e94            4            2            6 149be75f95c0
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             5 45f8b879de92            5            1            6 51df11ea9843
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 42574a82229f
             6 c8d03c1b5e94            5            1            6 446c2dc3bce5
             7 f69452c5b1af            6            1            7 000000000000

Recover after rollback
----------------------

  $ hg pull
  pulling from ssh://user@dummy/server
  searching for changes
  OBSEXC: looking for common markers in 8 nodes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 0 files
  1 new obsolescence markers
  new changesets 4de32a90b66c
  (run 'hg update' to get a working copy)
  $ hg rollback
  repository tip rolled back to revision 7 (undo pull)
  $ hg blackbox
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obshashcache clean - new markers affect 2 changeset and cached ranges (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obshashrange in *.???? seconds (0r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' exited 0 after *.?? seconds (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" exited 0 after *.?? seconds (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obsdiscovery, 0/8 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (1r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> 1 incoming changes - new heads: 4de32a90b66c (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> rollback (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> strip detected, evo-ext-obscache cache reset (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (8r, 15o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> rollback exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> blackbox (glob)
  $ rm .hg/blackbox.log
  $ hg debugobshashrange --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 f69452c5b1af            0            7            7 000000000000
             5 45f8b879de92            0            6            6 fdbbaec33b20
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 f69452c5b1af            4            3            7 000000000000
             3 2dc09a01254d            2            2            4 ce1937ca1278
             5 45f8b879de92            4            2            6 f45551c1cf4f
             1 66f7d451a68b            0            2            2 327c7dd73d29
             6 c8d03c1b5e94            4            2            6 149be75f95c0
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             5 45f8b879de92            5            1            6 51df11ea9843
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 42574a82229f
             6 c8d03c1b5e94            5            1            6 446c2dc3bce5
             7 f69452c5b1af            6            1            7 000000000000
  $ hg pull
  pulling from ssh://user@dummy/server
  searching for changes
  OBSEXC: looking for common markers in 8 nodes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 0 files
  1 new obsolescence markers
  new changesets 4de32a90b66c
  (run 'hg update' to get a working copy)
  $ hg blackbox
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' exited 0 after *.?? seconds (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" exited 0 after *.?? seconds (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> obsdiscovery, 0/8 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obscache in *.???? seconds (1r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> 1 incoming changes - new heads: 4de32a90b66c (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> pull exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> blackbox (glob)
  $ rm .hg/blackbox.log
  $ hg debugobshashrange --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             8 4de32a90b66c            0            8            8 87b2a11bd884
             5 45f8b879de92            0            6            6 fdbbaec33b20
             3 2dc09a01254d            0            4            4 8932bf980bb4
             8 4de32a90b66c            4            4            8 20745010e1d8
             3 2dc09a01254d            2            2            4 ce1937ca1278
             5 45f8b879de92            4            2            6 f45551c1cf4f
             8 4de32a90b66c            6            2            8 033544c939f0
             1 66f7d451a68b            0            2            2 327c7dd73d29
             6 c8d03c1b5e94            4            2            6 149be75f95c0
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             5 45f8b879de92            5            1            6 51df11ea9843
             8 4de32a90b66c            7            1            8 033544c939f0
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 42574a82229f
             6 c8d03c1b5e94            5            1            6 446c2dc3bce5
             7 f69452c5b1af            6            1            7 000000000000

Recover after stripping (in the middle of the repo)

We strip a branch that is not the tip of the reporiosy so part of the affected
revision are reapplied after the target is stripped.

  $ hg log -G
  o  8 4de32a90b66c r7 tip
  |
  o  7 f69452c5b1af r6
  |
  o  6 c8d03c1b5e94 r5
  |
  | @  5 45f8b879de92 foo
  |/
  o  4 bebd167eb94d r4
  |
  o  3 2dc09a01254d r3
  |
  o  2 01241442b3c2 r2
  |
  o  1 66f7d451a68b r1
  |
  o  0 1ea73414a91b r0
  
  $ hg --config extensions.strip= strip -r 'desc("foo")'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/45f8b879de92-94c82517-backup.hg
  $ hg log -G
  o  7 4de32a90b66c r7 tip
  |
  o  6 f69452c5b1af r6
  |
  o  5 c8d03c1b5e94 r5
  |
  @  4 bebd167eb94d r4
  |
  o  3 2dc09a01254d r3
  |
  o  2 01241442b3c2 r2
  |
  o  1 66f7d451a68b r1
  |
  o  0 1ea73414a91b r0
  
  $ hg pull
  pulling from ssh://user@dummy/server
  searching for changes
  OBSEXC: looking for common markers in 8 nodes
  OBSEXC: request obsmarkers for 1 common nodes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  5 new obsolescence markers
  new changesets 45f8b879de92
  (run 'hg heads' to see heads, 'hg merge' to merge)
  $ hg log -G
  o  8 45f8b879de92 foo tip
  |
  | o  7 4de32a90b66c r7
  | |
  | o  6 f69452c5b1af r6
  | |
  | o  5 c8d03c1b5e94 r5
  |/
  @  4 bebd167eb94d r4
  |
  o  3 2dc09a01254d r3
  |
  o  2 01241442b3c2 r2
  |
  o  1 66f7d451a68b r1
  |
  o  0 1ea73414a91b r0
  
  $ hg blackbox
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> writing .hg/cache/tags2-visible with 0 tags (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-depthcache in *.???? seconds (1r) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-stablerange-mergepoint in *.???? seconds (1r) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-obshashrange in *.???? seconds (1r, 1o) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-stablesort in *.???? seconds (1r) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> updated evo-ext-firstmerge in *.???? seconds (1r) (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev "heads(all())" exited 0 after *.?? seconds (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> debugobshashrange --subranges --rev 'heads(all())' exited 0 after *.?? seconds (glob) (no-windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> log -G (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> log -G exited 0 after *.?? seconds (glob)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> --config "extensions.strip=" strip -r "desc(\"foo\")" (glob) (windows !)
  * @45f8b879de922f6a6e620ba04205730335b6fc7e (*)> --config 'extensions.strip=' strip -r 'desc("foo")' (glob) (no-windows !)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> saved backup bundle to $TESTTMP/client/.hg/strip-backup/45f8b879de92-94c82517-backup.hg (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> strip detected, evo-ext-obscache cache reset (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> updated evo-ext-obscache in *.???? seconds (5r, 11o) (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> updated evo-ext-obscache in *.???? seconds (3r, 0o) (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> 3 incoming changes - new heads: 4de32a90b66c (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> --config "extensions.strip=" strip -r "desc(\"foo\")" exited 0 after *.?? seconds (glob) (windows !)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> --config 'extensions.strip=' strip -r 'desc("foo")' exited 0 after *.?? seconds (glob) (no-windows !)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> log -G (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> writing .hg/cache/tags2-visible with 0 tags (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> log -G exited 0 after *.?? seconds (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> pull (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> strip detected, evo-ext-depthcache cache reset (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> updated evo-ext-depthcache in *.???? seconds (8r) (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> updated evo-ext-stablerange-mergepoint in *.???? seconds (8r) (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> strip detected, evo-ext-obshashrange cache reset (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> updated evo-ext-obshashrange in *.???? seconds (8r, 11o) (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> strip detected, evo-ext-stablesort cache reset (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> updated evo-ext-stablesort in *.???? seconds (8r) (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> strip detected, evo-ext-firstmerge cache reset (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> updated evo-ext-firstmerge in *.???? seconds (8r) (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> obsdiscovery, 1/8 mismatch - 1 obshashrange queries in *.???? seconds (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> updated evo-ext-obscache in *.???? seconds (1r, 5o) (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> 1 incoming changes - new heads: 45f8b879de92 (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> pull exited 0 after *.?? seconds (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> log -G (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> writing .hg/cache/tags2-visible with 0 tags (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> log -G exited 0 after *.?? seconds (glob)
  * @bebd167eb94d257ace0e814aeb98e6972ed2970d (*)> blackbox (glob)
  $ rm .hg/blackbox.log
  $ hg debugobshashrange --subranges --rev 'heads(all())'
           rev         node        index         size        depth      obshash
             7 4de32a90b66c            0            8            8 87b2a11bd884
             8 45f8b879de92            0            6            6 fdbbaec33b20
             3 2dc09a01254d            0            4            4 8932bf980bb4
             7 4de32a90b66c            4            4            8 20745010e1d8
             3 2dc09a01254d            2            2            4 ce1937ca1278
             8 45f8b879de92            4            2            6 f45551c1cf4f
             7 4de32a90b66c            6            2            8 033544c939f0
             1 66f7d451a68b            0            2            2 327c7dd73d29
             5 c8d03c1b5e94            4            2            6 149be75f95c0
             2 01241442b3c2            2            1            3 1ed3c61fb39a
             0 1ea73414a91b            0            1            1 000000000000
             3 2dc09a01254d            3            1            4 26f996446ecb
             8 45f8b879de92            5            1            6 51df11ea9843
             7 4de32a90b66c            7            1            8 033544c939f0
             1 66f7d451a68b            1            1            2 327c7dd73d29
             4 bebd167eb94d            4            1            5 42574a82229f
             5 c8d03c1b5e94            5            1            6 446c2dc3bce5
             6 f69452c5b1af            6            1            7 000000000000

Cache warming capabilities
--------------------------

  $ hg config experimental.obshashrange
  1
  $ hg config experimental.obshashrange.warm-cache
  [1]
  $ hg debugupdatecache
  $ ls -1 .hg/cache/evoext*
  .hg/cache/evoext-depthcache-00
  .hg/cache/evoext-firstmerge-00
  .hg/cache/evoext-obscache-00
  .hg/cache/evoext-stablesortcache-00
  .hg/cache/evoext_obshashrange_v2.sqlite
  .hg/cache/evoext_stablerange_v2.sqlite
  $ rm -f .hg/cache/evoext*
  $ ls -1 .hg/cache/ | grep evoext
  [1]
  $ hg debugupdatecache --debug
  stable-range cache: unable to load, regenerating
  obshashrange cache: unable to load, regenerating
  updating the branch cache
  $ f -s .hg/cache/evoext*
  .hg/cache/evoext-depthcache-00: size=96
  .hg/cache/evoext-firstmerge-00: size=96
  .hg/cache/evoext-obscache-00: size=73
  .hg/cache/evoext-stablesortcache-00: size=100
  .hg/cache/evoext_obshashrange_v2.sqlite: size=??* (glob)
  .hg/cache/evoext_stablerange_v2.sqlite: size=??* (glob)

  $ rm -f .hg/cache/evoext*
  $ ls -1 .hg/cache/ | grep evoext
  [1]
  $ hg strip -r 5 --config extensions.strip=
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/c8d03c1b5e94-b257442b-backup.hg
  $ f -s .hg/cache/evoext*
  .hg/cache/evoext-obscache-00: size=70
  $ cd ..

Check capabilities advertisement
================================

  $ hg init with-evolve
  $ cat << EOF >> with-evolve/.hg/hgrc
  > [experimental]
  > evolution.exchange=yes
  > EOF
  $ hg init without-evolve
  $ cat << EOF >> without-evolve/.hg/hgrc
  > [experimental]
  > evolution.exchange=no
  > EOF

  $ hg debugcapabilities ssh://user@dummy/with-evolve | grep _evoext
    _evoext_getbundle_obscommon
    _evoext_obshashrange_v1
  $ hg debugcapabilities ssh://user@dummy/without-evolve | grep _evoext
  [1]

Using http:

  $ cat > web.conf << EOF
  > [paths]
  > / = *
  > EOF

(evolve version first)

  $ hg serve --web-conf web.conf -p $HGPORT -d --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

  $ hg debugcapabilities http://localhost:$HGPORT/with-evolve| grep _evoext
    _evoext_getbundle_obscommon
    _evoext_obshashrange_v1
  $ hg debugcapabilities http://localhost:$HGPORT/without-evolve| grep _evoext
  [1]

  $ killdaemons.py


(evolve version second)

  $ hg serve --web-conf web.conf -p $HGPORT -d --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

  $ hg debugcapabilities http://localhost:$HGPORT/without-evolve| grep _evoext
  [1]
  $ hg debugcapabilities http://localhost:$HGPORT/with-evolve| grep _evoext
    _evoext_getbundle_obscommon
    _evoext_obshashrange_v1

  $ killdaemons.py
