#! /usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from contextlib import contextmanager

import pytest

from shuttle import flash
from shuttle.firmware import DEFAULT_BOARD


def test_list_available_boards_includes_default():
    assert DEFAULT_BOARD in flash.list_available_boards()


def test_load_firmware_manifest_returns_segments():
    manifest, package = flash.load_firmware_manifest("esp32c5")
    assert manifest["segments"]
    assert package.endswith("esp32c5")


def test_flash_firmware_invokes_esptool(monkeypatch):
    calls = []

    def fake_run(args):
        calls.append(args)

    monkeypatch.setattr(flash, "_run_esptool", fake_run)

    manifest = flash.flash_firmware(
        port="/dev/ttyUSB0",
        baudrate=921600,
        board="esp32c5",
        erase_first=True,
    )

    assert manifest["label"]
    assert len(calls) == 2  # erase + write
    erase_args, write_args = calls
    assert erase_args[:4] == ["--chip", manifest["chip"], "--port", "/dev/ttyUSB0"]
    assert "write-flash" in write_args
    assert any("devboard.ino.bin" in arg for arg in write_args)


def test_flash_firmware_unknown_board():
    with pytest.raises(flash.FirmwareFlashError):
        flash.flash_firmware(port="/dev/null", baudrate=921600, board="does-not-exist")


def test_load_firmware_manifest_missing_file(monkeypatch, tmp_path):
    board = "missing"
    pkg_dir = tmp_path / "shuttle.firmware" / board
    pkg_dir.mkdir(parents=True)

    original_files = flash.resources.files

    def fake_files(package):
        if package == f"shuttle.firmware.{board}":
            return pkg_dir
        return original_files(package)

    monkeypatch.setattr(flash.resources, "files", fake_files)

    with pytest.raises(flash.FirmwareFlashError, match="manifest missing"):
        flash.load_firmware_manifest(board)


def test_load_firmware_manifest_corrupt(monkeypatch, tmp_path):
    board = "corrupt"
    pkg_dir = tmp_path / "shuttle.firmware" / board
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "manifest.json").write_text("not-json", encoding="utf-8")

    original_files = flash.resources.files

    def fake_files(package):
        if package == f"shuttle.firmware.{board}":
            return pkg_dir
        return original_files(package)

    monkeypatch.setattr(flash.resources, "files", fake_files)

    with pytest.raises(flash.FirmwareFlashError, match="Invalid manifest"):
        flash.load_firmware_manifest(board)


def test_load_firmware_manifest_missing_segments(monkeypatch, tmp_path):
    board = "no-segments"
    pkg_dir = tmp_path / "shuttle.firmware" / board
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "manifest.json").write_text("{}", encoding="utf-8")

    original_files = flash.resources.files

    def fake_files(package):
        if package == f"shuttle.firmware.{board}":
            return pkg_dir
        return original_files(package)

    monkeypatch.setattr(flash.resources, "files", fake_files)

    with pytest.raises(flash.FirmwareFlashError, match="defines no segments"):
        flash.load_firmware_manifest(board)


@pytest.mark.parametrize("bad_segment", [{"file": "foo.bin"}, {"offset": "0x0"}])
def test_flash_firmware_segment_missing_fields(monkeypatch, bad_segment):
    manifest = {
        "chip": "esp32c5",
        "segments": [bad_segment],
    }

    monkeypatch.setattr(
        flash, "load_firmware_manifest", lambda _board: (manifest, "pkg")
    )

    with pytest.raises(
        flash.FirmwareFlashError,
        match="Manifest segment entries require 'offset' and 'file'",
    ):
        flash.flash_firmware(port="/dev/ttyUSB0", baudrate=921600, board="esp32c5")


def test_flash_firmware_missing_artifact(monkeypatch):
    manifest = {
        "chip": "esp32c5",
        "segments": [{"offset": "0x0", "file": "missing.bin"}],
    }
    calls = []
    tmp_pkg = Path("/nonexistent/pkg")

    monkeypatch.setattr(
        flash, "load_firmware_manifest", lambda _board: (manifest, "pkg")
    )
    monkeypatch.setattr(flash.resources, "files", lambda _pkg: tmp_pkg)
    monkeypatch.setattr(
        flash.resources,
        "as_file",
        lambda _traversable: (_ for _ in ()).throw(FileNotFoundError()),
    )
    monkeypatch.setattr(flash, "_run_esptool", lambda args: calls.append(args))

    with pytest.raises(
        flash.FirmwareFlashError, match="Missing firmware artifact: missing.bin"
    ):
        flash.flash_firmware(port="/dev/ttyUSB0", baudrate=921600, board="esp32c5")

    assert calls == []


def test_flash_firmware_adds_flash_options(monkeypatch, tmp_path):
    artifact = tmp_path / "fw.bin"
    artifact.write_bytes(b"fw")
    manifest = {
        "chip": "esp32c5",
        "segments": [{"offset": "0x1000", "file": artifact.name}],
        "flash-mode": "dout",
        "flash-freq": "80m",
        "flash-size": "2MB",
    }
    calls = []

    monkeypatch.setattr(
        flash, "load_firmware_manifest", lambda _board: (manifest, "pkg")
    )
    monkeypatch.setattr(flash.resources, "files", lambda _pkg: tmp_path)

    @contextmanager
    def fake_as_file(traversable):
        yield traversable

    monkeypatch.setattr(flash.resources, "as_file", fake_as_file)
    monkeypatch.setattr(flash, "_run_esptool", lambda args: calls.append(args))

    flash.flash_firmware(port="/dev/ttyUSB0", baudrate=921600, board="esp32c5")

    assert len(calls) == 1
    write_args = calls[0]
    assert ["--flash-mode", "dout"] in [
        write_args[i : i + 2] for i in range(len(write_args) - 1)
    ]
    assert ["--flash-freq", "80m"] in [
        write_args[i : i + 2] for i in range(len(write_args) - 1)
    ]
    assert ["--flash-size", "2MB"] in [
        write_args[i : i + 2] for i in range(len(write_args) - 1)
    ]
    assert str(artifact) in write_args


def test_flash_firmware_skips_missing_flash_options(monkeypatch, tmp_path):
    artifact = tmp_path / "fw.bin"
    artifact.write_bytes(b"fw")
    manifest = {
        "chip": "esp32c5",
        "segments": [{"offset": "0x1000", "file": artifact.name}],
        # no flash-mode/freq/size keys -> exercise falsy branch
    }
    calls = []

    monkeypatch.setattr(
        flash, "load_firmware_manifest", lambda _board: (manifest, "pkg")
    )
    monkeypatch.setattr(flash.resources, "files", lambda _pkg: tmp_path)

    @contextmanager
    def fake_as_file(traversable):
        yield traversable

    monkeypatch.setattr(flash.resources, "as_file", fake_as_file)
    monkeypatch.setattr(flash, "_run_esptool", lambda args: calls.append(args))

    flash.flash_firmware(port="/dev/ttyUSB0", baudrate=921600, board="esp32c5")

    assert len(calls) == 1
    write_args = calls[0]
    assert all(
        flag not in write_args
        for flag in ("--flash-mode", "--flash-freq", "--flash-size")
    )
    assert str(artifact) in write_args


def test_flash_firmware_handles_no_compress(monkeypatch):
    calls = []

    def fake_run(args):
        calls.append(args)

    manifest, package = flash.load_firmware_manifest("esp32c5")
    custom_manifest = dict(manifest)
    custom_manifest["compress"] = False

    monkeypatch.setattr(flash, "_run_esptool", fake_run)
    monkeypatch.setattr(
        flash,
        "load_firmware_manifest",
        lambda _board: (custom_manifest, package),
    )

    flash.flash_firmware(port="/dev/ttyUSB0", baudrate=921600)

    assert len(calls) == 1
    assert "--no-compress" in calls[0]


def test_run_esptool_success_with_exit_zero(monkeypatch):
    recorded = []

    def fake_main(args):
        recorded.append(list(args))
        raise SystemExit(0)

    monkeypatch.setattr(flash.esptool, "main", fake_main)

    flash._run_esptool(["ping"])

    assert recorded[0] == ["ping"]


def test_run_esptool_failure(monkeypatch):
    def fake_main(_args):
        raise SystemExit(2)

    monkeypatch.setattr(flash.esptool, "main", fake_main)

    with pytest.raises(flash.FirmwareFlashError):
        flash._run_esptool(["bad"])
