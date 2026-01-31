.. Copyright 2011 Pierre-Yves David <pierre-yves.david@ens-lyon.org>
..                Logilab SA        <contact@logilab.fr>

-----------------------------------
From MQ To Evolve, The Refugee Book
-----------------------------------

Cheat sheet
-----------

==============================  ============================================
mq command                       new equivalent
==============================  ============================================
qseries                         ``log``
qnew                            ``commit``
qrefresh                        ``amend``
qrefresh --exclude              ``uncommit``
qpop                            ``update`` or ``previous``
qpush                           ``update`` or ``next`` sometimes ``evolve`` or ``pick``
qrm                             ``prune``
qfold                           ``fold``
qdiff                           ``pdiff``
qrecord                         ``record``
qimport                         ``import``

qfinish                         --
qcommit                         --
==============================  ============================================


Replacement details
-------------------

hg qseries
``````````

All your work in progress is now in real changesets all the time.

You can use the standard ``log`` command to display them. You can use the
``draft()`` (or ``secret()``) revset to display unfinished work only, and
use templates to have the same kind of compact that the output of
``qseries`` has.

This will result in something like

.. code-block:: ini

  [alias]
  wip = log -r 'not public()' --template='{rev}:{node|short} {desc|firstline}\n'

Using the topic extension provides another way of looking at your
work in progress. Topic branches are lightweight branches which
fade out when changes are finalized. Although the underlying
mechanics are different, both queues and topics help users
organize and share their unfinished work. The topic extension
provides the ``stack`` command. Similar to ``qseries``, ``stack``
lists all changesets in a topic as well as other related
information.

.. code-block:: console

  $ hg stack

Installing the evolve extension also installs the topic extension. To enable
it, add the following to your `hgrc` config:

.. code-block:: ini

  [extensions]
  topic =

hg qnew
```````

With evolve you handle standard changesets without an additional overlay.

Standard changeset are created using ``hg commit`` as usual

.. code-block:: console

  $ hg commit

If you want to keep the "WIP is not pushed" behavior, you want to
set your changeset in the secret phase using the ``phase`` command.

Note that you only need it for the first commit you want to be secret. Later
commits will inherit their parent's phase.

If you always want your new commit to be in the secret phase, your should
consider updating your configuration

.. code-block:: ini

  [phases]
  new-commit = secret

hg qref
```````

A new command from evolution will allow you to rewrite the changeset you are
currently on. Just call

.. code-block:: console

  $ hg amend

This command takes the same options as ``commit``, plus the switch ``-e`` (``--edit``)
to edit the commit message in an editor.


.. -c is very confusig
..
.. The amend command also has a -c switch which allows you to make an
.. explicit amending commit before rewriting a changeset.::
..
..   $ hg record -m 'feature A'
..   # oups, I forgot some stuff
..   $ hg record babar.py
..   $ hg amend -c .^ # .^ refer to "working directory parent, here 'feature A'

.. note: refresh is an alias for amend

hg qref --exclude
`````````````````

To remove changes from your current commit use

.. code-block:: console

  $ hg uncommit not-ready.txt


hg qpop
```````

To emulate the behavior of ``qpop`` use

.. code-block:: console

  $ hg previous

If you need to go back to an arbitrary commit you can use

.. code-block:: console

  $ hg update

.. note:: previous and update allow movement with working directory
          changes applied, and gracefully merge them.

.. note:: Previous versions of the documentation recommended
          the deprecated gdown command

hg qpush
````````

The following command emulates the behavior of ``hg qpush``

.. code-block:: console

  $ hg next

When you rewrite changesets, descendants of rewritten changesets are marked as
"orphan". You need to rewrite them on top of the new version of their
ancestor.

The evolution extension adds a command to rewrite "orphan" changesets

.. code-block:: console

  $ hg evolve

You can also reorder a changeset using

.. code-block:: console

  $ hg pick OLD_VERSION

or

.. code-block:: console

  $ hg rebase -r REVSET_FOR_OLD_VERSION -d .

note: using ``pick`` allows you to choose the changeset you want next as the ``--move``
option of ``qpush`` does.


hg qrm
``````

evolution introduces a new command to mark a changeset as "not wanted anymore".

.. code-block:: console

  $ hg prune REVSET

hg qfold
````````

The following command emulates the behavior of ``qfold``

.. code-block:: console

  $ hg fold FIRST::LAST

hg qdiff
````````

``pdiff`` is an alias for ``hg diff -r .^`` It works like ``qdiff``, but outside MQ.


hg qimport
``````````

To import a new patch, use

.. code-block:: console

  $ hg import NEW_CHANGES.patch

hg qfinish
``````````

This is not necessary anymore. If you want to control the
mutability of changesets, see the ``phase`` feature.

hg qcommit
``````````

If you really need to send patches through versioned mq patches, you should
look at the qsync extension.
