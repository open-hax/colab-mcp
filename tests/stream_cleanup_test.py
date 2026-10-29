# OpenHAX modification notice (2026-10-29): compatibility adaptation.
# OpenHAX-authored changes: LGPL-3.0-or-later; upstream portions retain Apache-2.0.
# See NOTICE and LICENSING.md for provenance and the modification boundary.
import gc

import pytest

from colab_mcp.websocket_server import ColabWebSocketServer


def endpoints(server):
    return [
        server.read_stream,
        server.write_stream,
        server._read_stream_writer,
        server._write_stream_reader,
    ]


@pytest.mark.asyncio
async def test_actual_websocket_context_closes_all_four_owned_endpoints():
    server = ColabWebSocketServer(host="127.0.0.1")
    streams = endpoints(server)
    assert not any(s._closed for s in streams)
    async with server:
        assert server.port > 0
    assert all(s._closed for s in streams)
    gc.collect()


@pytest.mark.asyncio
async def test_unstarted_server_cleanup_still_closes_all_four_endpoints():
    server = ColabWebSocketServer(host="127.0.0.1")
    streams = endpoints(server)
    assert server._server is None
    await server.__aexit__(None, None, None)
    assert all(s._closed for s in streams)


@pytest.mark.asyncio
async def test_native_shutdown_wait_failure_does_not_leave_stream_endpoints_open():
    server = ColabWebSocketServer(host="127.0.0.1")
    streams = endpoints(server)

    class FailedWait:
        def close(self):
            pass

        async def wait_closed(self):
            raise RuntimeError("fixture shutdown wait failed")

    server._server = FailedWait()
    with pytest.raises(RuntimeError, match="shutdown wait failed"):
        await server.__aexit__(None, None, None)
    assert all(s._closed for s in streams)
