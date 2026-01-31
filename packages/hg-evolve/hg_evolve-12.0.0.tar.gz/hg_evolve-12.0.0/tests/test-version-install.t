  $ cat >> $HGRCPATH <<EOF
  > [extensions]
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

Test outputting version number

  $ hg version -v
  Mercurial Distributed SCM (version *) (glob)
  (see https://mercurial-scm.org for more information)
  
  Copyright (C) 2005-* (glob)
  This is free software; see the source for copying conditions. There is NO
  warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
  
  Enabled extensions:
  
    evolve  external  * (glob)

Test install
(pip on python2 doesn't have --root-user-action flag, so we ignore the warning manually)

  $ "$PYTHON" -m pip install "$TESTDIR/.." --root="$TESTTMP/installtest" --quiet --disable-pip-version-check
  WARNING: Running pip as the 'root' user * (glob) (?)

Test that evolve can be loaded from the above path

  $ echo "evolve=$(find $TESTTMP -path '*/hgext3rd/evolve')" >> $HGRCPATH
  $ hg debugconfig extensions.evolve
  */installtest/*/python*/hgext3rd/evolve (glob)
  $ hg help evolve | head -1
  hg evolve [OPTIONS]...
