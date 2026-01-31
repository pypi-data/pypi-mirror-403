import queue
import pytest
import shuttle.serial_client as serial_client


class DummySerial:
    def __init__(self, data=b"", fail=False):
        self._data = data
        self._fail = fail
        self.read_calls = 0
        self.in_waiting = len(data)
        self.is_open = True

    def read(self, n):
        self.read_calls += 1
        if self._fail:
            raise Exception("fail")
        d, self._data = self._data[:n], self._data[n:]
        self.in_waiting = len(self._data)
        return d

    def close(self):
        self.is_open = False


class DummyLogger:
    def __init__(self):
        self.logged = []

    def log(self, direction, data):
        self.logged.append((direction, data))


def test_flush_input_and_log_reads_and_logs(monkeypatch):
    client = serial_client.NDJSONSerialClient.__new__(serial_client.NDJSONSerialClient)
    logger = DummyLogger()
    # Data in buffer
    client._serial = DummySerial(b"abc123")
    client._logger = logger
    client.flush_input_and_log()
    assert logger.logged == [("RX", b"abc123")]
    # No data in buffer
    client._serial = DummySerial(b"")
    logger.logged.clear()
    client.flush_input_and_log()
    assert logger.logged == []
    # Exception in read is handled
    client._serial = DummySerial(b"abc", fail=True)
    client.flush_input_and_log()  # Should not raise


def test_flush_input_and_log_no_serial():
    client = serial_client.NDJSONSerialClient.__new__(serial_client.NDJSONSerialClient)
    client._logger = DummyLogger()
    client.flush_input_and_log()  # Should not raise
