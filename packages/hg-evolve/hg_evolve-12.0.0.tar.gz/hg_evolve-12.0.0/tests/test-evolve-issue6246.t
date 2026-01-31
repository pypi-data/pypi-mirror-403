Failure to open evoext_stablerange_v2.sqlite shouldn't affect operations (issue6246)
https://bz.mercurial-scm.org/show_bug.cgi?id=6246

  $ . $TESTDIR/testlib/common.sh

  $ cat << EOF >> $HGRCPATH
  > [extensions]
  > evolve =
  > EOF

  $ hg init issue6246
  $ cd issue6246
  $ hg debugbuilddag '.+6'

making a cache file that sqlite cannot open shouldn't break stablerange cache

  $ touch .hg/cache/evoext_stablerange_v2.sqlite
  $ chmod 0000 .hg/cache/evoext_stablerange_v2.sqlite

  $ hg debug::evo-ext-stable-range --method default --verify --subranges --rev 1 --debug
  stable-range cache: unable to load, regenerating
  66f7d451a68b-0 (1, 2, 2) [complete] - 1ea73414a91b-0 (0, 1, 1), 66f7d451a68b-1 (1, 2, 1)
  1ea73414a91b-0 (0, 1, 1) [leaf] - 
  66f7d451a68b-1 (1, 2, 1) [leaf] - 

  $ hg debugobshashrange --rev tip --debug
  stable-range cache: unable to load, regenerating
           rev         node        index         size        depth      obshash
  obshashrange cache: unable to load, regenerating
             6 f69452c5b1af            0            7            7 000000000000

  $ cd ..
