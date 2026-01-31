Test that share-clones use the cache in the original repository.

  $ . $TESTDIR/testlib/common.sh

  $ hg init share-base
  $ cd share-base/
  $ cat >> .hg/hgrc <<EOF
  > [extensions]
  > evolve=
  > share=
  > EOF
  $ hg debugbuilddag .+3:branchpoint+4*branchpoint+2
  $ cd ..
  $ hg --config extensions.share= share -U share-base share-client
  $ cd share-client
  $ hg debugupdatecache
  $ test -d .hg/cache
  [1]
  $ test -d ../share-base/.hg/cache

