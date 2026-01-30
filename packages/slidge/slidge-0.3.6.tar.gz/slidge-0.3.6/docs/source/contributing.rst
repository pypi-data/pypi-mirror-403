Contributing
============

Development setup
-----------------

With docker compose
*******************

The easiest way to develop using slidge is by using docker-compose.
Clone the repo, run `docker-compose up` and you should have:

- an XMPP server (prosody) exposed on port 5222 with a registered user
  <test@localhost> (password: password)
- an XMPP component, the "super duper" gateway, a fake component that can be
  used to try stuff directly in an XMPP client, with code hot-reload.

You can login with the JID ``test@localhost`` and ``password`` as the password.

With uv
*******

Alternatively, use `uv <https://docs.astral.sh/uv/>`_ to set up a virtual environment
with ``uv sync``.
Launch our preconfigured prosody instance for development with
``podman run --network host codeberg.org/slidge/prosody-slidge-dev``, then launch
slidge with ``python -m superduper --jid slidge.localhost --secret secret --home-dir ./persistent --debug``.

Guidelines
----------

Tests should be written with the `pytest <https://pytest.org>`_ framework.
For complex tests involving mocking data through the XMPP stream, the
:class:`slidge.util.test.SlidgeTest` class can come in handy.

The code should pass
`mypy <https://mypy-lang.org/>`_ and
`ruff <https://ruff.rs>`_
with the settings defined in ``pyproject.toml``.

About XMPP clients
------------------

`Gajim <https://gajim.org>`_
is also a good choice to test stuff during development, since it implement a lot
of XEPs, especially when it comes to components.
You can launch it with ``--user-profile slidge`` to use a
clean profile and not mess up your usual gajim config, db, cache, etc.

Unlike gajim, some clients will not accept self signed certificates, a possible
workaround using debian and docker is

.. code-block::

   docker cp slidge_prosody_1:/etc/prosody/certs/localhost.crt \
      /tmp/localhost.crt
   sudo /tmp/localhost.crt /usr/local/share/ca-certificates
   sudo update-ca-certificates
