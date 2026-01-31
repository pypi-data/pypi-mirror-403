"""Tests for gateway_client reconnect race condition.

Verifies that when a reconnect happens, the old generator cannot steal
messages from the new connection's queue. This was a bug where the first
streaming chunk after a reconnect would be consumed by the old (dead)
generator and silently dropped.
"""

import queue
import threading
import time
from unittest.mock import Mock, MagicMock, patch

import pytest

from march_agent.gateway_client import GatewayClient


class FakeProtoMessage:
    """Minimal fake protobuf ClientMessage for testing."""

    def __init__(self, body: bytes = b'{}', key: str = 'conv-1'):
        self.produce = Mock()
        self.produce.body = body
        self.produce.key = key

    def HasField(self, field):
        return field == 'produce'


@pytest.fixture
def client():
    """Create a GatewayClient without connecting."""
    c = GatewayClient(gateway_url='localhost:8080', api_key='test')
    c._running = True
    c._send_queue = queue.Queue()
    return c


class TestGeneratorQueueIsolation:
    """Test that old generators stop consuming after reconnect."""

    def test_old_generator_stops_when_queue_replaced(self, client):
        """After _send_queue is replaced, the old generator should exit its loop."""
        old_queue = client._send_queue

        # Start the old generator (skip auth message)
        gen = client._generate_requests(first_message=None)

        # Put a message on the old queue
        msg1 = FakeProtoMessage(b'{"content": "first"}', 'conv-1')
        old_queue.put(msg1)

        # The generator should yield it
        result = next(gen)
        assert result is msg1

        # Now simulate reconnect: replace the queue
        client._send_queue = queue.Queue()

        # Put a message on the NEW queue
        msg2 = FakeProtoMessage(b'{"content": "second"}', 'conv-1')
        client._send_queue.put(msg2)

        # The old generator should NOT yield msg2 — it should stop
        # because my_queue is no longer self._send_queue.
        # Give it enough time to notice (> 0.1s poll timeout)
        items_from_old_gen = []
        deadline = time.time() + 0.5
        try:
            while time.time() < deadline:
                items_from_old_gen.append(next(gen))
        except StopIteration:
            pass

        assert msg2 not in items_from_old_gen, (
            "Old generator stole a message from the new queue!"
        )

        # msg2 should still be in the new queue (not consumed)
        assert not client._send_queue.empty()
        assert client._send_queue.get_nowait() is msg2

    def test_new_generator_gets_all_messages(self, client):
        """After reconnect, the new generator should get all messages from the new queue."""
        # Simulate reconnect
        client._send_queue = queue.Queue()

        new_gen = client._generate_requests(first_message=None)

        # Put messages on the new queue
        messages = []
        for i in range(5):
            msg = FakeProtoMessage(f'{{"content": "chunk-{i}"}}'.encode(), 'conv-1')
            messages.append(msg)
            client._send_queue.put(msg)

        # Generator should yield all of them
        received = []
        for _ in range(5):
            received.append(next(new_gen))

        assert received == messages

    def test_concurrent_reconnect_no_message_loss(self, client):
        """Simulate the exact race condition: old generator running while
        reconnect happens and new messages are produced."""
        old_queue = client._send_queue

        # Start old generator in a thread (simulates gRPC consuming it)
        old_gen = client._generate_requests(first_message=None)
        stolen_messages = []
        old_gen_done = threading.Event()

        def drain_old_gen():
            try:
                while True:
                    msg = next(old_gen)
                    stolen_messages.append(msg)
            except StopIteration:
                pass
            old_gen_done.set()

        old_thread = threading.Thread(target=drain_old_gen, daemon=True)
        old_thread.start()

        # Let the old generator start polling
        time.sleep(0.05)

        # Simulate reconnect: replace queue
        client._send_queue = queue.Queue()

        # Immediately produce messages on the new queue (like agent handler does)
        new_messages = []
        for i in range(13):
            msg = FakeProtoMessage(f'{{"content": "chunk-{i}"}}'.encode(), 'conv-1')
            new_messages.append(msg)
            client._send_queue.put(msg)

        # Wait for old generator to notice and stop
        old_gen_done.wait(timeout=2.0)

        # None of the new messages should have been stolen by the old generator
        for msg in new_messages:
            assert msg not in stolen_messages, (
                f"Old generator stole message from new queue!"
            )

        # All new messages should still be available in the new queue
        remaining = []
        while not client._send_queue.empty():
            remaining.append(client._send_queue.get_nowait())

        assert remaining == new_messages

    def test_running_false_stops_generator(self, client):
        """Generator should stop when _running is set to False."""
        gen = client._generate_requests(first_message=None)

        client._running = False

        items = []
        try:
            # Should exit quickly (within one poll cycle)
            deadline = time.time() + 0.5
            while time.time() < deadline:
                items.append(next(gen))
        except StopIteration:
            pass

        assert items == []
