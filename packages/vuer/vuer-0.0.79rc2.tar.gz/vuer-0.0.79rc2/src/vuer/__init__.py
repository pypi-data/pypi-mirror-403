from vuer._compat import try_import_server

Vuer, VuerSession = try_import_server()

from vuer.client import VuerClient


def entrypoint():
    """CLI entrypoint for vuer command."""
    app = Vuer()
    app.run()


__all__ = ["Vuer", "VuerSession", "VuerClient", "entrypoint"]
