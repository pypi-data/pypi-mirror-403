#require no-rhg no-chg

XXX-RHG this test hangs if `hg` is really `rhg`. This was hidden by the use of
`alias hg=rhg` by run-tests.py. With such alias removed, this test is revealed
buggy. This need to be resolved sooner than later.

XXX-CHG this test hangs if `hg` is really `chg`. This was hidden by the use of
`alias hg=chg` by run-tests.py. With such alias removed, this test is revealed
buggy. This need to be resolved sooner than later.

  $ . "$TESTDIR/testlib/topic_setup.sh"

#if windows
  $ PYTHONPATH="$RUNTESTDIR/../contrib;$PYTHONPATH"
#else
  $ PYTHONPATH="$RUNTESTDIR/../contrib:$PYTHONPATH"
#endif
  $ export PYTHONPATH

typical client does not want echo-back messages, so test without it:

  $ grep -v '^promptecho ' < $HGRCPATH >> $HGRCPATH.new
  $ mv $HGRCPATH.new $HGRCPATH

  $ hg init repo
  $ cd repo

  $ touch a
  $ hg ci -Am 'a'
  adding a
  $ touch b
  $ hg ci -Am 'b'
  adding b
  $ touch c
  $ hg ci -Am 'c'
  adding c
  $ touch d
  $ hg ci -Am 'd'
  adding d

Ensure that topics are not left around for stale revisions.

  >>> from hgclient import check, readchannel, runcommand
  >>> @check
  ... def checkruncommand(server):
  ...     # hello block
  ...     readchannel(server)
  ... 
  ...     # Initial case
  ...     runcommand(server, [b'log', b'-T', b'{rev} {desc} ({topic})\n'])
  ... 
  ...     # first topic
  ...     runcommand(server, [b'topic', b'topic1', b'-r', b'.'])
  ... 
  ...     # Current state
  ...     runcommand(server, [b'log', b'-T', b'{rev} {desc} ({topic})\n'])
  ... 
  ...     # status quo ante
  ...     runcommand(server, [b'rollback', b'--config', b'ui.rollback=True'])
  ... 
  ...     # Current state
  ...     runcommand(server, [b'log', b'-T', b'{rev} {desc} ({topic})\n'])
  ... 
  ...     # second topic
  ...     runcommand(server, [b'topic', b'topic2', b'-r', b'(.^^)::'])
  ... 
  ...     # Current state
  ...     runcommand(server, [b'log', b'-T', b'{rev} {desc} ({topic})\n'])
  ... 
  ...     # status quo ante
  ...     runcommand(server, [b'rollback', b'--config', b'ui.rollback=True'])
  ... 
  ...     # Current state
  ...     runcommand(server, [b'log', b'-T', b'{rev} {desc} ({topic})\n'])
  *** runcommand log -T {rev} {desc} ({topic})
  
  3 d ()
  2 c ()
  1 b ()
  0 a ()
  *** runcommand topic topic1 -r .
  switching to topic topic1
  changed topic on 1 changesets to "topic1"
  *** runcommand log -T {rev} {desc} ({topic})
  
  4 d (topic1)
  2 c ()
  1 b ()
  0 a ()
  *** runcommand rollback --config ui.rollback=True
  repository tip rolled back to revision 3 (undo rewrite-topics)
  working directory now based on revision 3
  *** runcommand log -T {rev} {desc} ({topic})
  
  3 d ()
  2 c ()
  1 b ()
  0 a ()
  *** runcommand topic topic2 -r (.^^)::
  switching to topic topic2
  changed topic on 3 changesets to "topic2"
  *** runcommand log -T {rev} {desc} ({topic})
  
  6 d (topic2)
  5 c (topic2)
  4 b (topic2)
  0 a ()
  *** runcommand rollback --config ui.rollback=True
  repository tip rolled back to revision 3 (undo rewrite-topics)
  working directory now based on revision 3
  *** runcommand log -T {rev} {desc} ({topic})
  
  3 d ()
  2 c ()
  1 b ()
  0 a ()
