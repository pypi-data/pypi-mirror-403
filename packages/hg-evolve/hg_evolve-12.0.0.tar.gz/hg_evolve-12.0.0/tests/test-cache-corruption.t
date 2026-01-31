Testing cache corruption and recovery
https://bz.mercurial-scm.org/show_bug.cgi?id=6354

  $ . $TESTDIR/testlib/pythonpath.sh

  $ cat << EOF >> $HGRCPATH
  > [extensions]
  > evolve =
  > [experimental]
  > obshashrange = 1
  > obshashrange.warm-cache = yes
  > [ui]
  > logtemplate = "{rev} {node|short} {desc} {tags}\n"
  > EOF

  $ cat >> repack.py << EOF
  > import struct
  > import sys
  > # imitating array.array().tobytes() with a platform-dependent item size
  > sixtyfour = struct.Struct('<q') # as seen on 64-bit platforms
  > thirtytwo = struct.Struct('<l') # as seen on 32-bit platforms
  > iss = struct.Struct('<I') # for rewriting indexsize of stablesortcache
  > data = []
  > with open(sys.argv[1], 'rb') as f:
  >     header = f.read(24)
  >     if '--index' in sys.argv:
  >         indexsize = iss.unpack(f.read(iss.size))[0]
  >     while True:
  >         buf = f.read(sixtyfour.size)
  >         if not buf: break
  >         data.append(sixtyfour.unpack(buf)[0])
  > with open(sys.argv[1], 'wb') as f:
  >     f.write(header)
  >     if '--index' in sys.argv:
  >         indexsize = int(indexsize * thirtytwo.size / sixtyfour.size)
  >         f.write(iss.pack(indexsize))
  >     for item in data:
  >         f.write(thirtytwo.pack(item))
  > EOF

  $ cat >> truncate.py << EOF
  > import os
  > import sys
  > with open(sys.argv[1], 'ab') as fp:
  >     fp.seek(int(sys.argv[2]), os.SEEK_END)
  >     fp.truncate()
  > EOF

Simple linear setup

  $ hg init linear
  $ cd linear

  $ hg debugbuilddag '+3'
  $ hg log -G
  o  2 01241442b3c2 r2 tip
  |
  o  1 66f7d451a68b r1
  |
  o  0 1ea73414a91b r0
  
  $ f -s .hg/cache/evoext-*
  .hg/cache/evoext-depthcache-00: size=48
  .hg/cache/evoext-firstmerge-00: size=48
  .hg/cache/evoext-obscache-00: size=67
  .hg/cache/evoext-stablesortcache-00: size=52

testing depthcache

  $ f -H .hg/cache/evoext-depthcache-00
  .hg/cache/evoext-depthcache-00:
  0000: 00 00 00 02 01 24 14 42 b3 c2 bf 32 11 e5 93 b5 |.....$.B...2....|
  0010: 49 c6 55 ea 65 b2 95 e3 01 00 00 00 00 00 00 00 |I.U.e...........|
  0020: 02 00 00 00 00 00 00 00 03 00 00 00 00 00 00 00 |................|

  $ hg debugdepth --rev 'all()' --method compare --debug
  1ea73414a91b 1
  66f7d451a68b 2
  01241442b3c2 3

  $ "$PYTHON" ../repack.py .hg/cache/evoext-depthcache-00
  $ f -H .hg/cache/evoext-depthcache-00
  .hg/cache/evoext-depthcache-00:
  0000: 00 00 00 02 01 24 14 42 b3 c2 bf 32 11 e5 93 b5 |.....$.B...2....|
  0010: 49 c6 55 ea 65 b2 95 e3 01 00 00 00 02 00 00 00 |I.U.e...........|
  0020: 03 00 00 00                                     |....|

  $ hg debugdepth --rev 'all()' --method compare --debug
  depthcache file seems to be corrupted, it will be rebuilt from scratch
  1ea73414a91b 1
  66f7d451a68b 2
  01241442b3c2 3

  $ "$PYTHON" ../truncate.py .hg/cache/evoext-depthcache-00 -4
  $ f -H .hg/cache/evoext-depthcache-00
  .hg/cache/evoext-depthcache-00:
  0000: 00 00 00 02 01 24 14 42 b3 c2 bf 32 11 e5 93 b5 |.....$.B...2....|
  0010: 49 c6 55 ea 65 b2 95 e3 01 00 00 00 00 00 00 00 |I.U.e...........|
  0020: 02 00 00 00 00 00 00 00 03 00 00 00             |............|

  $ hg debugdepth --rev 'all()' --method compare --debug
  depthcache file seems to be corrupted, it will be rebuilt from scratch
  1ea73414a91b 1
  66f7d451a68b 2
  01241442b3c2 3

testing firstmergecache

  $ f -H .hg/cache/evoext-firstmerge-00
  .hg/cache/evoext-firstmerge-00:
  0000: 00 00 00 02 01 24 14 42 b3 c2 bf 32 11 e5 93 b5 |.....$.B...2....|
  0010: 49 c6 55 ea 65 b2 95 e3 ff ff ff ff ff ff ff ff |I.U.e...........|
  0020: ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff |................|

  $ hg debugfirstmergecache --debug
  1ea73414a91b -1
  66f7d451a68b -1
  01241442b3c2 -1

  $ "$PYTHON" ../repack.py .hg/cache/evoext-firstmerge-00
  $ f -H .hg/cache/evoext-firstmerge-00
  .hg/cache/evoext-firstmerge-00:
  0000: 00 00 00 02 01 24 14 42 b3 c2 bf 32 11 e5 93 b5 |.....$.B...2....|
  0010: 49 c6 55 ea 65 b2 95 e3 ff ff ff ff ff ff ff ff |I.U.e...........|
  0020: ff ff ff ff                                     |....|

  $ hg debugfirstmergecache --debug
  firstmergecache file seems to be corrupted, it will be rebuilt from scratch
  1ea73414a91b -1
  66f7d451a68b -1
  01241442b3c2 -1

  $ "$PYTHON" ../truncate.py .hg/cache/evoext-firstmerge-00 -4
  $ f -H .hg/cache/evoext-firstmerge-00
  .hg/cache/evoext-firstmerge-00:
  0000: 00 00 00 02 01 24 14 42 b3 c2 bf 32 11 e5 93 b5 |.....$.B...2....|
  0010: 49 c6 55 ea 65 b2 95 e3 ff ff ff ff ff ff ff ff |I.U.e...........|
  0020: ff ff ff ff ff ff ff ff ff ff ff ff             |............|

  $ hg debugfirstmergecache --debug
  firstmergecache file seems to be corrupted, it will be rebuilt from scratch
  1ea73414a91b -1
  66f7d451a68b -1
  01241442b3c2 -1

testing stablesortcache

  $ f -H .hg/cache/evoext-stablesortcache-00
  .hg/cache/evoext-stablesortcache-00:
  0000: 00 00 00 02 01 24 14 42 b3 c2 bf 32 11 e5 93 b5 |.....$.B...2....|
  0010: 49 c6 55 ea 65 b2 95 e3 00 00 00 18 00 00 00 00 |I.U.e...........|
  0020: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|
  0030: 00 00 00 00                                     |....|

  $ hg debug::evo-ext-stable-sort-cache --debug
  number of revisions:            3
  number of merge:                0
  number of jumps:                0

  $ "$PYTHON" ../repack.py .hg/cache/evoext-stablesortcache-00 --index
  $ f -H .hg/cache/evoext-stablesortcache-00
  .hg/cache/evoext-stablesortcache-00:
  0000: 00 00 00 02 01 24 14 42 b3 c2 bf 32 11 e5 93 b5 |.....$.B...2....|
  0010: 49 c6 55 ea 65 b2 95 e3 00 00 00 0c 00 00 00 00 |I.U.e...........|
  0020: 00 00 00 00 00 00 00 00                         |........|

  $ hg debug::evo-ext-stable-sort-cache --debug
  number of revisions:            3
  stablesortcache file seems to be corrupted, it will be rebuilt from scratch
  number of merge:                0
  number of jumps:                0

  $ "$PYTHON" ../truncate.py .hg/cache/evoext-stablesortcache-00 -4
  $ f -H .hg/cache/evoext-stablesortcache-00
  .hg/cache/evoext-stablesortcache-00:
  0000: 00 00 00 02 01 24 14 42 b3 c2 bf 32 11 e5 93 b5 |.....$.B...2....|
  0010: 49 c6 55 ea 65 b2 95 e3 00 00 00 18 00 00 00 00 |I.U.e...........|
  0020: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|

  $ hg debug::evo-ext-stable-sort-cache --debug
  number of revisions:            3
  stablesortcache file seems to be corrupted, it will be rebuilt from scratch
  number of merge:                0
  number of jumps:                0

  $ cd ..

A "diamond" setup with a merge

  $ hg init with-a-merge
  $ cd with-a-merge

  $ hg debugbuilddag '+2 *2 /2'
  $ hg log -G
  o    3 2b6d669947cd r3 tip
  |\
  | o  2 fa942426a6fd r2
  | |
  o |  1 66f7d451a68b r1
  |/
  o  0 1ea73414a91b r0
  
  $ f -s .hg/cache/evoext-*
  .hg/cache/evoext-depthcache-00: size=56
  .hg/cache/evoext-firstmerge-00: size=56
  .hg/cache/evoext-obscache-00: size=68
  .hg/cache/evoext-stablesortcache-00: size=84

testing depthcache

  $ f -H .hg/cache/evoext-depthcache-00
  .hg/cache/evoext-depthcache-00:
  0000: 00 00 00 03 2b 6d 66 99 47 cd 52 4d 74 f4 3c 1b |....+mf.G.RMt.<.|
  0010: 11 c7 84 85 89 70 7e ef 01 00 00 00 00 00 00 00 |.....p~.........|
  0020: 02 00 00 00 00 00 00 00 02 00 00 00 00 00 00 00 |................|
  0030: 04 00 00 00 00 00 00 00                         |........|

  $ hg debugdepth --rev 'all()' --method compare --debug
  1ea73414a91b 1
  66f7d451a68b 2
  fa942426a6fd 2
  2b6d669947cd 4

  $ "$PYTHON" ../repack.py .hg/cache/evoext-depthcache-00
  $ f -H .hg/cache/evoext-depthcache-00
  .hg/cache/evoext-depthcache-00:
  0000: 00 00 00 03 2b 6d 66 99 47 cd 52 4d 74 f4 3c 1b |....+mf.G.RMt.<.|
  0010: 11 c7 84 85 89 70 7e ef 01 00 00 00 02 00 00 00 |.....p~.........|
  0020: 02 00 00 00 04 00 00 00                         |........|

  $ hg debugdepth --rev 'all()' --method compare --debug
  depthcache file seems to be corrupted, it will be rebuilt from scratch
  1ea73414a91b 1
  66f7d451a68b 2
  fa942426a6fd 2
  2b6d669947cd 4

  $ "$PYTHON" ../truncate.py .hg/cache/evoext-depthcache-00 -4
  $ f -H .hg/cache/evoext-depthcache-00
  .hg/cache/evoext-depthcache-00:
  0000: 00 00 00 03 2b 6d 66 99 47 cd 52 4d 74 f4 3c 1b |....+mf.G.RMt.<.|
  0010: 11 c7 84 85 89 70 7e ef 01 00 00 00 00 00 00 00 |.....p~.........|
  0020: 02 00 00 00 00 00 00 00 02 00 00 00 00 00 00 00 |................|
  0030: 04 00 00 00                                     |....|

  $ hg debugdepth --rev 'all()' --method compare --debug
  depthcache file seems to be corrupted, it will be rebuilt from scratch
  1ea73414a91b 1
  66f7d451a68b 2
  fa942426a6fd 2
  2b6d669947cd 4

testing firstmergecache

  $ f -H .hg/cache/evoext-firstmerge-00
  .hg/cache/evoext-firstmerge-00:
  0000: 00 00 00 03 2b 6d 66 99 47 cd 52 4d 74 f4 3c 1b |....+mf.G.RMt.<.|
  0010: 11 c7 84 85 89 70 7e ef ff ff ff ff ff ff ff ff |.....p~.........|
  0020: ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff |................|
  0030: 03 00 00 00 00 00 00 00                         |........|

  $ hg debugfirstmergecache --debug
  1ea73414a91b -1
  66f7d451a68b -1
  fa942426a6fd -1
  2b6d669947cd 3

  $ "$PYTHON" ../repack.py .hg/cache/evoext-firstmerge-00
  $ f -H .hg/cache/evoext-firstmerge-00
  .hg/cache/evoext-firstmerge-00:
  0000: 00 00 00 03 2b 6d 66 99 47 cd 52 4d 74 f4 3c 1b |....+mf.G.RMt.<.|
  0010: 11 c7 84 85 89 70 7e ef ff ff ff ff ff ff ff ff |.....p~.........|
  0020: ff ff ff ff 03 00 00 00                         |........|

  $ hg debugfirstmergecache --debug
  firstmergecache file seems to be corrupted, it will be rebuilt from scratch
  1ea73414a91b -1
  66f7d451a68b -1
  fa942426a6fd -1
  2b6d669947cd 3

  $ "$PYTHON" ../truncate.py .hg/cache/evoext-firstmerge-00 -4
  $ f -H .hg/cache/evoext-firstmerge-00
  .hg/cache/evoext-firstmerge-00:
  0000: 00 00 00 03 2b 6d 66 99 47 cd 52 4d 74 f4 3c 1b |....+mf.G.RMt.<.|
  0010: 11 c7 84 85 89 70 7e ef ff ff ff ff ff ff ff ff |.....p~.........|
  0020: ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff |................|
  0030: 03 00 00 00                                     |....|

  $ hg debugfirstmergecache --debug
  firstmergecache file seems to be corrupted, it will be rebuilt from scratch
  1ea73414a91b -1
  66f7d451a68b -1
  fa942426a6fd -1
  2b6d669947cd 3

testing stablesortcache

  $ f -H .hg/cache/evoext-stablesortcache-00
  .hg/cache/evoext-stablesortcache-00:
  0000: 00 00 00 03 2b 6d 66 99 47 cd 52 4d 74 f4 3c 1b |....+mf.G.RMt.<.|
  0010: 11 c7 84 85 89 70 7e ef 00 00 00 20 00 00 00 00 |.....p~.... ....|
  0020: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|
  0030: 00 00 00 00 01 00 00 00 00 00 00 00 02 00 00 00 |................|
  0040: 00 00 00 00 01 00 00 00 00 00 00 00 02 00 00 00 |................|
  0050: 00 00 00 00                                     |....|

  $ hg debug::evo-ext-stable-sort-cache --debug
  number of revisions:            4
  number of merge:                1
  number of jumps:                1
  average jumps:                  1.000
  median jumps:                   1
  90% jumps:                      1
  99% jumps:                      1
  max jumps:                      1
  jump cache size:               12 bytes

  $ "$PYTHON" ../repack.py .hg/cache/evoext-stablesortcache-00 --index
  $ f -H .hg/cache/evoext-stablesortcache-00
  .hg/cache/evoext-stablesortcache-00:
  0000: 00 00 00 03 2b 6d 66 99 47 cd 52 4d 74 f4 3c 1b |....+mf.G.RMt.<.|
  0010: 11 c7 84 85 89 70 7e ef 00 00 00 10 00 00 00 00 |.....p~.........|
  0020: 00 00 00 00 00 00 00 00 01 00 00 00 02 00 00 00 |................|
  0030: 01 00 00 00 02 00 00 00                         |........|

  $ hg debug::evo-ext-stable-sort-cache --debug
  number of revisions:            4
  stablesortcache file seems to be corrupted, it will be rebuilt from scratch
  number of merge:                1
  number of jumps:                1
  average jumps:                  1.000
  median jumps:                   1
  90% jumps:                      1
  99% jumps:                      1
  max jumps:                      1
  jump cache size:               12 bytes

  $ "$PYTHON" ../truncate.py .hg/cache/evoext-stablesortcache-00 -4
  $ f -H .hg/cache/evoext-stablesortcache-00
  .hg/cache/evoext-stablesortcache-00:
  0000: 00 00 00 03 2b 6d 66 99 47 cd 52 4d 74 f4 3c 1b |....+mf.G.RMt.<.|
  0010: 11 c7 84 85 89 70 7e ef 00 00 00 20 00 00 00 00 |.....p~.... ....|
  0020: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 |................|
  0030: 00 00 00 00 01 00 00 00 00 00 00 00 02 00 00 00 |................|
  0040: 00 00 00 00 01 00 00 00 00 00 00 00 02 00 00 00 |................|

  $ hg debug::evo-ext-stable-sort-cache --debug
  number of revisions:            4
  stablesortcache file seems to be corrupted, it will be rebuilt from scratch
  number of merge:                1
  number of jumps:                1
  average jumps:                  1.000
  median jumps:                   1
  90% jumps:                      1
  99% jumps:                      1
  max jumps:                      1
  jump cache size:               12 bytes

  $ cd ..
