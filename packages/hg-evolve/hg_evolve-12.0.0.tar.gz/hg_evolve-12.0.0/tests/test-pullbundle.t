  $ . "$TESTDIR/testlib/pythonpath.sh"

  $ cat << EOF >> $HGRCPATH
  > [extensions]
  > # evolve is providing the stable range code
  > evolve=
  > pullbundle=
  > [experimental]
  > obshashrange.warm-cache=yes
  > EOF

basic setup

  $ hg init server
  $ hg -R server debugbuilddag '.+898:branchpoint+352:mergepoint+267<branchpoint+145/mergepoint+467'
  $ hg init client
  $ hg init client2
  $ hg init client3
  $ hg init client4

simple initial pull
-------------------

  $ hg -R server log -G -T '{rev}:{node}\n' -r '0+1234+(::1234 and (merge() or branchpoint()))'
  o  1234:f864bc82f6a2f2ecb49b83722e0895f9d657b0dd
  :
  o  898:1388f909cd2b0685efd4e2ce076d198bce20922c
  :
  o  0:1ea73414a91b0920940797d8fc6a11e447f8ea1e
  

  $ hg -R client pull server -r 1234 --debug --config devel.bundle2.debug=yes | grep -v 'add changeset'
  pulling from server
  listing keys for "bookmarks"
  query 1; heads
  pullbundle-cache: "missing" set sliced into 6 subranges in *.* seconds (glob)
  1024 changesets found
  128 changesets found
  64 changesets found
  16 changesets found
  2 changesets found
  1 changesets found
  bundle2-output-bundle: "HG20", 7 parts total
  bundle2-output: start emission of HG20 stream
  bundle2-output: bundle parameter: 
  bundle2-output: start of parts
  bundle2-output: bundle part: "changegroup"
  bundle2-output-part: "changegroup" (params: 1 mandatory 1 advisory) streamed payload
  bundle2-output: part 0: "CHANGEGROUP"
  bundle2-output: header chunk size: 44
  bundle2-output: payload chunk size: 32768
  bundle2-output: payload chunk size: 32768
  bundle2-output: payload chunk size: 32768
  bundle2-output: payload chunk size: 32768
  bundle2-output: payload chunk size: 32768
  bundle2-output: payload chunk size: 24420
  bundle2-output: closing payload chunk
  bundle2-output: bundle part: "changegroup"
  bundle2-output-part: "changegroup" (params: 1 mandatory 1 advisory) streamed payload
  bundle2-output: part 1: "CHANGEGROUP"
  bundle2-output: header chunk size: 43
  bundle2-output: payload chunk size: 23824
  bundle2-output: closing payload chunk
  bundle2-output: bundle part: "changegroup"
  bundle2-output-part: "changegroup" (params: 1 mandatory 1 advisory) streamed payload
  bundle2-output: part 2: "CHANGEGROUP"
  bundle2-output: header chunk size: 42
  bundle2-output: payload chunk size: 11920
  bundle2-output: closing payload chunk
  bundle2-output: bundle part: "changegroup"
  bundle2-output-part: "changegroup" (params: 1 mandatory 1 advisory) streamed payload
  bundle2-output: part 3: "CHANGEGROUP"
  bundle2-output: header chunk size: 42
  bundle2-output: payload chunk size: 2992
  bundle2-output: closing payload chunk
  bundle2-output: bundle part: "changegroup"
  bundle2-output-part: "changegroup" (params: 1 mandatory 1 advisory) streamed payload
  bundle2-output: part 4: "CHANGEGROUP"
  bundle2-output: header chunk size: 41
  bundle2-output: payload chunk size: 388
  bundle2-output: closing payload chunk
  bundle2-output: bundle part: "changegroup"
  bundle2-output-part: "changegroup" (params: 1 mandatory 1 advisory) streamed payload
  bundle2-output: part 5: "CHANGEGROUP"
  bundle2-output: header chunk size: 41
  bundle2-output: payload chunk size: 202
  bundle2-output: closing payload chunk
  bundle2-output: bundle part: "phase-heads"
  bundle2-output-part: "phase-heads" 24 bytes payload
  bundle2-output: part 6: "PHASE-HEADS"
  bundle2-output: header chunk size: 18
  bundle2-output: payload chunk size: 24
  bundle2-output: closing payload chunk
  bundle2-output: end of bundle
  bundle2-input: start processing of HG20 stream
  bundle2-input: reading bundle2 stream parameters
  bundle2-input-bundle: with-transaction
  bundle2-input: start extraction of bundle2 parts
  bundle2-input: part header size: 44
  bundle2-input: part type: "CHANGEGROUP"
  bundle2-input: part id: "0"
  bundle2-input: part parameters: 2
  bundle2-input: found a handler for part changegroup
  bundle2-input-part: "changegroup" (params: 1 mandatory 1 advisory) supported
  adding changesets
  bundle2-input: payload chunk size: 32768
  bundle2-input: payload chunk size: 32768
  bundle2-input: payload chunk size: 32768
  bundle2-input: payload chunk size: 32768
  bundle2-input: payload chunk size: 32768
  bundle2-input: payload chunk size: 24420
  bundle2-input: payload chunk size: 0
  adding manifests
  adding file changes
  bundle2-input-part: total payload size 188260
  bundle2-input: part header size: 43
  bundle2-input: part type: "CHANGEGROUP"
  bundle2-input: part id: "1"
  bundle2-input: part parameters: 2
  bundle2-input: found a handler for part changegroup
  bundle2-input-part: "changegroup" (params: 1 mandatory 1 advisory) supported
  adding changesets
  bundle2-input: payload chunk size: 23824
  bundle2-input: payload chunk size: 0
  adding manifests
  adding file changes
  bundle2-input-part: total payload size 23824
  bundle2-input: part header size: 42
  bundle2-input: part type: "CHANGEGROUP"
  bundle2-input: part id: "2"
  bundle2-input: part parameters: 2
  bundle2-input: found a handler for part changegroup
  bundle2-input-part: "changegroup" (params: 1 mandatory 1 advisory) supported
  adding changesets
  bundle2-input: payload chunk size: 11920
  bundle2-input: payload chunk size: 0
  adding manifests
  adding file changes
  bundle2-input-part: total payload size 11920
  bundle2-input: part header size: 42
  bundle2-input: part type: "CHANGEGROUP"
  bundle2-input: part id: "3"
  bundle2-input: part parameters: 2
  bundle2-input: found a handler for part changegroup
  bundle2-input-part: "changegroup" (params: 1 mandatory 1 advisory) supported
  adding changesets
  bundle2-input: payload chunk size: 2992
  bundle2-input: payload chunk size: 0
  adding manifests
  adding file changes
  bundle2-input-part: total payload size 2992
  bundle2-input: part header size: 41
  bundle2-input: part type: "CHANGEGROUP"
  bundle2-input: part id: "4"
  bundle2-input: part parameters: 2
  bundle2-input: found a handler for part changegroup
  bundle2-input-part: "changegroup" (params: 1 mandatory 1 advisory) supported
  adding changesets
  bundle2-input: payload chunk size: 388
  bundle2-input: payload chunk size: 0
  adding manifests
  adding file changes
  bundle2-input-part: total payload size 388
  bundle2-input: part header size: 41
  bundle2-input: part type: "CHANGEGROUP"
  bundle2-input: part id: "5"
  bundle2-input: part parameters: 2
  bundle2-input: found a handler for part changegroup
  bundle2-input-part: "changegroup" (params: 1 mandatory 1 advisory) supported
  adding changesets
  bundle2-input: payload chunk size: 202
  bundle2-input: payload chunk size: 0
  adding manifests
  adding file changes
  bundle2-input-part: total payload size 202
  bundle2-input: part header size: 18
  bundle2-input: part type: "PHASE-HEADS"
  bundle2-input: part id: "6"
  bundle2-input: part parameters: 0
  bundle2-input: found a handler for part phase-heads
  bundle2-input-part: "phase-heads" supported
  bundle2-input: payload chunk size: 24
  bundle2-input: payload chunk size: 0
  bundle2-input-part: total payload size 24
  bundle2-input: part header size: 0
  bundle2-input: end of bundle2 stream
  bundle2-input-bundle: 7 parts total
  checking for updated bookmarks
  stable-range cache: unable to load, regenerating
  obshashrange cache: unable to load, regenerating
  updating the branch cache
  added 1235 changesets with 0 changes to 0 files
  new changesets 1ea73414a91b:f864bc82f6a2
  (run 'hg update' to get a working copy)

  $ touch oldbundles
  $ ls -1 server/.hg/cache/pullbundles > newbundles
  $ diff -u oldbundles newbundles
  --- oldbundles	* (glob)
  +++ newbundles	* (glob)
  @@ -0,0 +1,6 @@
  +0?-467b6e370e816747e27de0d0b9237f4090a33656-0000001152skip-0000000064size.hg (glob)
  +0?-540f762640ee62ca597ece26af725e6357e82805-0000000000skip-0000001024size.hg (glob)
  +0?-63ded94ceab180ac2fa13e1f0beeb4d2265998a3-0000001232skip-0000000002size.hg (glob)
  +0?-7f3a79522d6e904d52aea07c71e6cb612667e8f4-0000001216skip-0000000016size.hg (glob)
  +0?-ee2deecf044fa5583f66188c9177b0f13332adc2-0000001024skip-0000000128size.hg (glob)
  +0?-f864bc82f6a2f2ecb49b83722e0895f9d657b0dd-0000001234skip-0000000001size.hg (glob)
  [1]

pull the other missing entries (multiple heads pulled)
------------------------------------------------------

  $ hg -R server log -G -T '{rev}:{node}\n' -r '1234+head()+(only(head(), 1234) and (merge() or branchpoint()))'
  o  2130:0f376356904fc8c1c6ceaac27990f2fd79b1f8c1
  :
  o    1663:1710092b3ab17a6d2ecad664580991a608537749
  |\
  | ~
  | o  1517:1dded5aafa0f8d548f6357cc2f8882dcc4489fbf
  |/
  o  1250:d83212ecaa436c80d6113cf915ba35e2db787e79
  :
  o  1234:f864bc82f6a2f2ecb49b83722e0895f9d657b0dd
  |
  ~
  $ hg -R client pull server --verbose
  pulling from server
  searching for changes
  all local changesets known remotely
  pullbundle-cache: "missing" set sliced into 18 subranges in *.* seconds (glob)
  1 changesets found
  4 changesets found
  8 changesets found
  32 changesets found
  128 changesets found
  64 changesets found
  32 changesets found
  8 changesets found
  4 changesets found
  2 changesets found
  1 changesets found
  4 changesets found
  8 changesets found
  16 changesets found
  256 changesets found
  256 changesets found
  64 changesets found
  8 changesets found
  uncompressed size of bundle content:
       190 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
       748 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      1492 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      5956 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
     23812 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
     11908 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      5956 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      1492 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
       748 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
       376 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
       190 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
       748 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      1492 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      2980 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
     47620 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
     47620 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
     11908 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      1492 (changelog)
         4 (manifests)
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  added 896 changesets with 0 changes to 0 files (+1 heads)
  new changesets 17185c1c22f1:0f376356904f
  (run 'hg heads' to see heads, 'hg merge' to merge)

  $ mv newbundles oldbundles
  $ ls -1 server/.hg/cache/pullbundles > newbundles
  $ diff -u oldbundles newbundles
  --- oldbundles	* (glob)
  +++ newbundles	* (glob)
  @@ -1,6 +1,24 @@
  +0?-0f376356904fc8c1c6ceaac27990f2fd79b1f8c1-0000001856skip-0000000008size.hg (glob)
  +0?-17185c1c22f1266b084daf7cfb07b6ebbfbc65ab-0000001235skip-0000000001size.hg (glob)
  +0?-1dded5aafa0f8d548f6357cc2f8882dcc4489fbf-0000001516skip-0000000002size.hg (glob)
  +0?-2dc4f1ab9029719714b8e0dde8e3725a5bb28472-0000001408skip-0000000064size.hg (glob)
  +0?-2f0e261a08964bc1c607c0eda4978364c22a9b94-0000001504skip-0000000008size.hg (glob)
   0?-467b6e370e816747e27de0d0b9237f4090a33656-0000001152skip-0000000064size.hg (glob)
  +0?-484c46df3e41f371efd0ff74fa5221657527213f-0000001240skip-0000000008size.hg (glob)
  +0?-4a6d0f7d07d060b026d9fc690cd89cd26af96e42-0000001248skip-0000000032size.hg (glob)
   0?-540f762640ee62ca597ece26af725e6357e82805-0000000000skip-0000001024size.hg (glob)
   0?-63ded94ceab180ac2fa13e1f0beeb4d2265998a3-0000001232skip-0000000002size.hg (glob)
  +0?-694ef7e5b2984f1ec66c3d960799f4ff2459672c-0000001236skip-0000000004size.hg (glob)
   0?-7f3a79522d6e904d52aea07c71e6cb612667e8f4-0000001216skip-0000000016size.hg (glob)
  +0?-89fab188d2ce3c4cde6be031f2fc5b9b4ff248e3-0000000900skip-0000000004size.hg (glob)
  +0?-97ede4832194ed56894374f2a1cc7a0022b486da-0000000904skip-0000000008size.hg (glob)
  +0?-b2d350c94c26edbb783aaa21fc24f1fc65c30e74-0000001536skip-0000000256size.hg (glob)
  +0?-bbd293bd171fd5b711d428db46940a72eca7a40f-0000001280skip-0000000128size.hg (glob)
  +0?-c72277ff25807eb444fa48a60afb434d78c21f2f-0000000899skip-0000000001size.hg (glob)
  +0?-da87a81c5310760f414a933e6550b7e8e60cf241-0000001792skip-0000000064size.hg (glob)
  +0?-dba2fddbf3c28198659046674a512afd616a1519-0000001472skip-0000000032size.hg (glob)
  +0?-e469a7aa5cce57653b6b02ff46c80b2d94d62629-0000000912skip-0000000016size.hg (glob)
  +0?-e74670ea99533967c5d90da3ddbc0318cc1fd502-0000001280skip-0000000256size.hg (glob)
   0?-ee2deecf044fa5583f66188c9177b0f13332adc2-0000001024skip-0000000128size.hg (glob)
   0?-f864bc82f6a2f2ecb49b83722e0895f9d657b0dd-0000001234skip-0000000001size.hg (glob)
  +0?-fb6c210a224903e81e5a8d2ee099cb0c9526ba8c-0000001512skip-0000000004size.hg (glob)
  [1]

Same Pullin with a different client
-----------------------------------
  $ hg -R server log -G -T '{rev}:{node}\n' -r '0+1234+(::1234 and (merge() or branchpoint()))'
  o  1234:f864bc82f6a2f2ecb49b83722e0895f9d657b0dd
  :
  o  898:1388f909cd2b0685efd4e2ce076d198bce20922c
  :
  o  0:1ea73414a91b0920940797d8fc6a11e447f8ea1e
  

  $ hg -R client2 pull server -r 1234 --verbose
  pulling from server
  pullbundle-cache: "missing" set sliced into 6 subranges in *.* seconds (glob)
  1024 changesets found in caches
  128 changesets found in caches
  64 changesets found in caches
  16 changesets found in caches
  2 changesets found in caches
  1 changesets found in caches
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  added 1235 changesets with 0 changes to 0 files
  new changesets 1ea73414a91b:f864bc82f6a2
  (run 'hg update' to get a working copy)

  $ mv newbundles oldbundles
  $ ls -1 server/.hg/cache/pullbundles > newbundles
  $ diff -u oldbundles newbundles

  $ hg -R server log -G -T '{rev}:{node}\n' -r '1234+head()+(only(head(), 1234) and (merge() or branchpoint()))'
  o  2130:0f376356904fc8c1c6ceaac27990f2fd79b1f8c1
  :
  o    1663:1710092b3ab17a6d2ecad664580991a608537749
  |\
  | ~
  | o  1517:1dded5aafa0f8d548f6357cc2f8882dcc4489fbf
  |/
  o  1250:d83212ecaa436c80d6113cf915ba35e2db787e79
  :
  o  1234:f864bc82f6a2f2ecb49b83722e0895f9d657b0dd
  |
  ~

  $ hg -R client2 pull server --verbose
  pulling from server
  searching for changes
  all local changesets known remotely
  pullbundle-cache: "missing" set sliced into 18 subranges in *.* seconds (glob)
  1 changesets found in caches
  4 changesets found in caches
  8 changesets found in caches
  32 changesets found in caches
  128 changesets found in caches
  64 changesets found in caches
  32 changesets found in caches
  8 changesets found in caches
  4 changesets found in caches
  2 changesets found in caches
  1 changesets found in caches
  4 changesets found in caches
  8 changesets found in caches
  16 changesets found in caches
  256 changesets found in caches
  256 changesets found in caches
  64 changesets found in caches
  8 changesets found in caches
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  added 896 changesets with 0 changes to 0 files (+1 heads)
  new changesets 17185c1c22f1:0f376356904f
  (run 'hg heads' to see heads, 'hg merge' to merge)

  $ mv newbundles oldbundles
  $ ls -1 server/.hg/cache/pullbundles > newbundles
  $ diff -u oldbundles newbundles

different pull with a different client
--------------------------------------

  $ hg -R server log -G -T '{rev}:{node}\n' -r '87232049c8d1+0+1789+(::1789 and (merge() or branchpoint()))'
  o  2085:87232049c8d1f413105bf813b6bfc21da3e26a4f
  :
  o  1789:44e80141ad530a2aa085e9bd9b5311b57eff72ff
  :
  o    1663:1710092b3ab17a6d2ecad664580991a608537749
  |\
  o :  1250:d83212ecaa436c80d6113cf915ba35e2db787e79
  :/
  o  898:1388f909cd2b0685efd4e2ce076d198bce20922c
  :
  o  0:1ea73414a91b0920940797d8fc6a11e447f8ea1e
  

  $ hg -R client3 pull server -r 1789 --verbose
  pulling from server
  pullbundle-cache: "missing" set sliced into 9 subranges in *.* seconds (glob)
  1024 changesets found in caches
  227 changesets found
  29 changesets found
  128 changesets found
  64 changesets found
  32 changesets found
  16 changesets found
  2 changesets found
  1 changesets found
  uncompressed size of bundle content:
     42226 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      5398 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
     23812 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
     11908 (changelog)
         4 (manifests)
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  uncompressed size of bundle content:
      5956 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      2980 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
       376 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
       190 (changelog)
         4 (manifests)
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  added 1523 changesets with 0 changes to 0 files
  new changesets 1ea73414a91b:44e80141ad53
  (run 'hg update' to get a working copy)

  $ mv newbundles oldbundles
  $ ls -1 server/.hg/cache/pullbundles > newbundles
  $ diff -u oldbundles newbundles
  --- oldbundles	* (glob)
  +++ newbundles	* (glob)
  @@ -3,20 +3,28 @@
   0?-1dded5aafa0f8d548f6357cc2f8882dcc4489fbf-0000001516skip-0000000002size.hg (glob)
   0?-2dc4f1ab9029719714b8e0dde8e3725a5bb28472-0000001408skip-0000000064size.hg (glob)
   0?-2f0e261a08964bc1c607c0eda4978364c22a9b94-0000001504skip-0000000008size.hg (glob)
  +0?-44e80141ad530a2aa085e9bd9b5311b57eff72ff-0000001522skip-0000000001size.hg (glob)
   0?-467b6e370e816747e27de0d0b9237f4090a33656-0000001152skip-0000000064size.hg (glob)
   0?-484c46df3e41f371efd0ff74fa5221657527213f-0000001240skip-0000000008size.hg (glob)
   0?-4a6d0f7d07d060b026d9fc690cd89cd26af96e42-0000001248skip-0000000032size.hg (glob)
   0?-540f762640ee62ca597ece26af725e6357e82805-0000000000skip-0000001024size.hg (glob)
  +0?-59e60b258b18cde1e931cf30ce4ae62b49e37abd-0000001520skip-0000000002size.hg (glob)
   0?-63ded94ceab180ac2fa13e1f0beeb4d2265998a3-0000001232skip-0000000002size.hg (glob)
   0?-694ef7e5b2984f1ec66c3d960799f4ff2459672c-0000001236skip-0000000004size.hg (glob)
  +0?-7a55a4d5ce324910842c893b56173cf2a847cb9d-0000001472skip-0000000032size.hg (glob)
   0?-7f3a79522d6e904d52aea07c71e6cb612667e8f4-0000001216skip-0000000016size.hg (glob)
   0?-89fab188d2ce3c4cde6be031f2fc5b9b4ff248e3-0000000900skip-0000000004size.hg (glob)
   0?-97ede4832194ed56894374f2a1cc7a0022b486da-0000000904skip-0000000008size.hg (glob)
  +0?-a4ab7df9d74053fb819c8a1c6a48ad605cc05f8a-0000001504skip-0000000016size.hg (glob)
   0?-b2d350c94c26edbb783aaa21fc24f1fc65c30e74-0000001536skip-0000000256size.hg (glob)
   0?-bbd293bd171fd5b711d428db46940a72eca7a40f-0000001280skip-0000000128size.hg (glob)
  +0?-c12927fef661d2463043347101b90067c2961333-0000001280skip-0000000128size.hg (glob)
   0?-c72277ff25807eb444fa48a60afb434d78c21f2f-0000000899skip-0000000001size.hg (glob)
  +0?-d83212ecaa436c80d6113cf915ba35e2db787e79-0000001024skip-0000000227size.hg (glob)
   0?-da87a81c5310760f414a933e6550b7e8e60cf241-0000001792skip-0000000064size.hg (glob)
   0?-dba2fddbf3c28198659046674a512afd616a1519-0000001472skip-0000000032size.hg (glob)
  +0?-dc714c3a5d080165292ba99b097567d0b95e5756-0000001408skip-0000000064size.hg (glob)
  +0?-e469a7aa5cce57653b6b02ff46c80b2d94d62629-0000000899skip-0000000029size.hg (glob)
   0?-e469a7aa5cce57653b6b02ff46c80b2d94d62629-0000000912skip-0000000016size.hg (glob)
   0?-e74670ea99533967c5d90da3ddbc0318cc1fd502-0000001280skip-0000000256size.hg (glob)
   0?-ee2deecf044fa5583f66188c9177b0f13332adc2-0000001024skip-0000000128size.hg (glob)
  [1]

  $ hg -R server log -G -T '{rev}:{node}\n' -r '1789+head()+parents(roots(only(head(), 1789)))+(only(head(), 1789) and (merge() or branchpoint()))'
  o  2130:0f376356904fc8c1c6ceaac27990f2fd79b1f8c1
  :
  o  1789:44e80141ad530a2aa085e9bd9b5311b57eff72ff
  :
  : o  1517:1dded5aafa0f8d548f6357cc2f8882dcc4489fbf
  :/
  o  1250:d83212ecaa436c80d6113cf915ba35e2db787e79
  |
  ~

  $ hg -R client3 pull server --verbose
  pulling from server
  searching for changes
  all local changesets known remotely
  pullbundle-cache: "missing" set sliced into 16 subranges in *.* seconds (glob)
  1 changesets found
  4 changesets found
  8 changesets found
  16 changesets found
  128 changesets found in caches
  64 changesets found in caches
  32 changesets found in caches
  8 changesets found in caches
  4 changesets found in caches
  2 changesets found in caches
  1 changesets found
  4 changesets found
  8 changesets found
  256 changesets found in caches
  64 changesets found in caches
  8 changesets found in caches
  uncompressed size of bundle content:
       190 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
       748 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      1492 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      2980 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
       190 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
       748 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      1492 (changelog)
         4 (manifests)
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  added 608 changesets with 0 changes to 0 files (+1 heads)
  new changesets d1807e351389:0f376356904f
  (run 'hg heads' to see heads, 'hg merge' to merge)

  $ mv newbundles oldbundles
  $ ls -1 server/.hg/cache/pullbundles > newbundles
  $ diff -u oldbundles newbundles
  --- oldbundles	* (glob)
  +++ newbundles	* (glob)
  @@ -1,14 +1,17 @@
   0?-0f376356904fc8c1c6ceaac27990f2fd79b1f8c1-0000001856skip-0000000008size.hg (glob)
   0?-17185c1c22f1266b084daf7cfb07b6ebbfbc65ab-0000001235skip-0000000001size.hg (glob)
   0?-1dded5aafa0f8d548f6357cc2f8882dcc4489fbf-0000001516skip-0000000002size.hg (glob)
  +0?-1ed78f99f705cb819a02f1227c217728d008e461-0000001524skip-0000000004size.hg (glob)
   0?-2dc4f1ab9029719714b8e0dde8e3725a5bb28472-0000001408skip-0000000064size.hg (glob)
   0?-2f0e261a08964bc1c607c0eda4978364c22a9b94-0000001504skip-0000000008size.hg (glob)
   0?-44e80141ad530a2aa085e9bd9b5311b57eff72ff-0000001522skip-0000000001size.hg (glob)
   0?-467b6e370e816747e27de0d0b9237f4090a33656-0000001152skip-0000000064size.hg (glob)
   0?-484c46df3e41f371efd0ff74fa5221657527213f-0000001240skip-0000000008size.hg (glob)
   0?-4a6d0f7d07d060b026d9fc690cd89cd26af96e42-0000001248skip-0000000032size.hg (glob)
  +0?-4a6d0f7d07d060b026d9fc690cd89cd26af96e42-0000001264skip-0000000016size.hg (glob)
   0?-540f762640ee62ca597ece26af725e6357e82805-0000000000skip-0000001024size.hg (glob)
   0?-59e60b258b18cde1e931cf30ce4ae62b49e37abd-0000001520skip-0000000002size.hg (glob)
  +0?-5eaa75df73c454c1afff722301a4c73e897de94d-0000001256skip-0000000008size.hg (glob)
   0?-63ded94ceab180ac2fa13e1f0beeb4d2265998a3-0000001232skip-0000000002size.hg (glob)
   0?-694ef7e5b2984f1ec66c3d960799f4ff2459672c-0000001236skip-0000000004size.hg (glob)
   0?-7a55a4d5ce324910842c893b56173cf2a847cb9d-0000001472skip-0000000032size.hg (glob)
  @@ -19,7 +22,10 @@
   0?-b2d350c94c26edbb783aaa21fc24f1fc65c30e74-0000001536skip-0000000256size.hg (glob)
   0?-bbd293bd171fd5b711d428db46940a72eca7a40f-0000001280skip-0000000128size.hg (glob)
   0?-c12927fef661d2463043347101b90067c2961333-0000001280skip-0000000128size.hg (glob)
  +0?-c232505f58fdf70bcf5f6ab6a555f23ffc74f761-0000001523skip-0000000001size.hg (glob)
   0?-c72277ff25807eb444fa48a60afb434d78c21f2f-0000000899skip-0000000001size.hg (glob)
  +0?-ca970a853ea24846035ccb324cc8de49ef768748-0000001252skip-0000000004size.hg (glob)
  +0?-d1807e3513890ac71c2e8d10e9dc9a5b58b15d4b-0000001251skip-0000000001size.hg (glob)
   0?-d83212ecaa436c80d6113cf915ba35e2db787e79-0000001024skip-0000000227size.hg (glob)
   0?-da87a81c5310760f414a933e6550b7e8e60cf241-0000001792skip-0000000064size.hg (glob)
   0?-dba2fddbf3c28198659046674a512afd616a1519-0000001472skip-0000000032size.hg (glob)
  @@ -27,6 +33,7 @@
   0?-e469a7aa5cce57653b6b02ff46c80b2d94d62629-0000000899skip-0000000029size.hg (glob)
   0?-e469a7aa5cce57653b6b02ff46c80b2d94d62629-0000000912skip-0000000016size.hg (glob)
   0?-e74670ea99533967c5d90da3ddbc0318cc1fd502-0000001280skip-0000000256size.hg (glob)
  +0?-e74670ea99533967c5d90da3ddbc0318cc1fd502-0000001528skip-0000000008size.hg (glob)
   0?-ee2deecf044fa5583f66188c9177b0f13332adc2-0000001024skip-0000000128size.hg (glob)
   0?-f864bc82f6a2f2ecb49b83722e0895f9d657b0dd-0000001234skip-0000000001size.hg (glob)
   0?-fb6c210a224903e81e5a8d2ee099cb0c9526ba8c-0000001512skip-0000000004size.hg (glob)
  [1]

Single pull coming after various cache warming
----------------------------------------------

  $ hg -R client4 pull --verbose server | grep -v 'add changeset'
  pulling from server
  requesting all changes
  pullbundle-cache: "missing" set sliced into 16 subranges in *.* seconds (glob)
  1024 changesets found in caches
  256 changesets found
  128 changesets found in caches
  64 changesets found in caches
  32 changesets found in caches
  8 changesets found in caches
  4 changesets found in caches
  2 changesets found in caches
  1 changesets found in caches
  4 changesets found in caches
  8 changesets found in caches
  16 changesets found in caches
  256 changesets found in caches
  256 changesets found in caches
  64 changesets found in caches
  8 changesets found in caches
  uncompressed size of bundle content:
     47620 (changelog)
         4 (manifests)
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  added 2131 changesets with 0 changes to 0 files (+1 heads)
  new changesets 1ea73414a91b:0f376356904f
  (run 'hg heads' to see heads, 'hg merge' to merge)

  $ mv newbundles oldbundles
  $ ls -1 server/.hg/cache/pullbundles > newbundles
  $ diff -u oldbundles newbundles
  --- oldbundles	* (glob)
  +++ newbundles	* (glob)
  @@ -7,6 +7,7 @@
   0?-44e80141ad530a2aa085e9bd9b5311b57eff72ff-0000001522skip-0000000001size.hg (glob)
   0?-467b6e370e816747e27de0d0b9237f4090a33656-0000001152skip-0000000064size.hg (glob)
   0?-484c46df3e41f371efd0ff74fa5221657527213f-0000001240skip-0000000008size.hg (glob)
  +0?-4a6d0f7d07d060b026d9fc690cd89cd26af96e42-0000001024skip-0000000256size.hg (glob)
   0?-4a6d0f7d07d060b026d9fc690cd89cd26af96e42-0000001248skip-0000000032size.hg (glob)
   0?-4a6d0f7d07d060b026d9fc690cd89cd26af96e42-0000001264skip-0000000016size.hg (glob)
   0?-540f762640ee62ca597ece26af725e6357e82805-0000000000skip-0000001024size.hg (glob)
  [1]

Pull with piece "not linear from head"
--------------------------------------

  $ hg -R server log -G -T '{rev}:{node}\n' -r 'branchpoint() + merge() + head() + children(branchpoint())'
  o  2130:0f376356904fc8c1c6ceaac27990f2fd79b1f8c1
  :
  o    1663:1710092b3ab17a6d2ecad664580991a608537749
  |\
  | o  1518:c72277ff25807eb444fa48a60afb434d78c21f2f
  | |
  | | o  1517:1dded5aafa0f8d548f6357cc2f8882dcc4489fbf
  | | :
  +---o  1251:d1807e3513890ac71c2e8d10e9dc9a5b58b15d4b
  | |
  o |  1250:d83212ecaa436c80d6113cf915ba35e2db787e79
  : |
  o |  899:c31a4e0cc28d677b8020e46aa3bb2fd5ee5b1a06
  |/
  o  898:1388f909cd2b0685efd4e2ce076d198bce20922c
  |
  ~

  $ hg init test-local-missing
  $ hg -R test-local-missing pull server --rev 899 --rev 1518 --verbose
  pulling from server
  pullbundle-cache: "missing" set sliced into 5 subranges in *.* seconds (glob)
  512 changesets found
  256 changesets found
  128 changesets found
  4 changesets found
  1 changesets found
  uncompressed size of bundle content:
     93992 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
     47108 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
     23556 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
       742 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
       188 (changelog)
         4 (manifests)
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  added 901 changesets with 0 changes to 0 files (+1 heads)
  new changesets 1ea73414a91b:c31a4e0cc28d
  (run 'hg heads' to see heads, 'hg merge' to merge)
  $ hg -R test-local-missing pull server --verbose
  pulling from server
  searching for changes
  all local changesets known remotely
  pullbundle-cache: "missing" set sliced into 19 subranges in *.* seconds (glob)
  4 changesets found
  8 changesets found
  16 changesets found
  32 changesets found
  64 changesets found
  256 changesets found in caches
  128 changesets found in caches
  64 changesets found in caches
  32 changesets found in caches
  8 changesets found in caches
  4 changesets found in caches
  2 changesets found in caches
  4 changesets found in caches
  8 changesets found in caches
  16 changesets found in caches
  256 changesets found in caches
  256 changesets found in caches
  64 changesets found in caches
  8 changesets found in caches
  uncompressed size of bundle content:
       740 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      1476 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      2948 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
      5892 (changelog)
         4 (manifests)
  uncompressed size of bundle content:
     11828 (changelog)
         4 (manifests)
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  added 1230 changesets with 0 changes to 0 files
  new changesets e600b80a2fc8:0f376356904f
  (run 'hg update' to get a working copy)

Test cache setting
==================

cache directory
---------------

  $ mkdir bundle-cache
  $ cat << EOF >> $HGRCPATH
  > [pullbundle]
  > cache-directory=$TESTTMP/bundle-cache
  > EOF

  $ hg clone --pull server other-cache-directory
  requesting all changes
  pullbundle-cache: "missing" set sliced into 16 subranges in *.* seconds (glob)
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  adding changesets
  adding manifests
  adding file changes
  added 2131 changesets with 0 changes to 0 files (+1 heads)
  new changesets 1ea73414a91b:0f376356904f
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ ls -1 bundle-cache
  0?-0f376356904fc8c1c6ceaac27990f2fd79b1f8c1-0000001856skip-0000000008size.hg (glob)
  0?-1dded5aafa0f8d548f6357cc2f8882dcc4489fbf-0000001516skip-0000000002size.hg (glob)
  0?-2dc4f1ab9029719714b8e0dde8e3725a5bb28472-0000001408skip-0000000064size.hg (glob)
  0?-2f0e261a08964bc1c607c0eda4978364c22a9b94-0000001504skip-0000000008size.hg (glob)
  0?-4a6d0f7d07d060b026d9fc690cd89cd26af96e42-0000001024skip-0000000256size.hg (glob)
  0?-540f762640ee62ca597ece26af725e6357e82805-0000000000skip-0000001024size.hg (glob)
  0?-89fab188d2ce3c4cde6be031f2fc5b9b4ff248e3-0000000900skip-0000000004size.hg (glob)
  0?-97ede4832194ed56894374f2a1cc7a0022b486da-0000000904skip-0000000008size.hg (glob)
  0?-b2d350c94c26edbb783aaa21fc24f1fc65c30e74-0000001536skip-0000000256size.hg (glob)
  0?-bbd293bd171fd5b711d428db46940a72eca7a40f-0000001280skip-0000000128size.hg (glob)
  0?-c72277ff25807eb444fa48a60afb434d78c21f2f-0000000899skip-0000000001size.hg (glob)
  0?-da87a81c5310760f414a933e6550b7e8e60cf241-0000001792skip-0000000064size.hg (glob)
  0?-dba2fddbf3c28198659046674a512afd616a1519-0000001472skip-0000000032size.hg (glob)
  0?-e469a7aa5cce57653b6b02ff46c80b2d94d62629-0000000912skip-0000000016size.hg (glob)
  0?-e74670ea99533967c5d90da3ddbc0318cc1fd502-0000001280skip-0000000256size.hg (glob)
  0?-fb6c210a224903e81e5a8d2ee099cb0c9526ba8c-0000001512skip-0000000004size.hg (glob)

  $ hg debugpullbundlecacheoverlap -R server 'all()' | grep -v '^  '
  gathering 100 sample pulls within 2131 revisions
  pull size:
  non-cached changesets:
  ratio of cached changesets:
  bundle count:
  ratio of cached bundles:
  changesets served:
  size of cached bundles:
  hit on cached bundles:
