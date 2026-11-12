#!/usr/bin/env python3
"""Restore the Model 100 Fun-layer actions formerly supplied by Karabiner.

Run without flags to inspect the patch; use --apply to write and verify it,
or --restore-fkeys to put only these slots back on their original F keys.
"""

import argparse
import glob
import os
import select
import subprocess
import termios
import time
import tty


KEYS_PER_LAYER = 64
FUNCTION_LAYER = 2
CONSUMER = 0x4800
SYSTEM = 0x4100
# Keys left as F3/F4 are handled globally by Codex Hotkey.
ACTIONS = {
    58: (CONSUMER | 0x70, "F1: brightness down"),
    59: (CONSUMER | 0x6F, "F2: brightness up"),
    62: (CONSUMER | 0xCF, "F5: dictation"),
    63: (SYSTEM | 0x9B, "F6: Do Not Disturb"),
    64: (CONSUMER | 0xB4, "F7: rewind/previous"),
    65: (CONSUMER | 0xCD, "F8: play/pause"),
    66: (CONSUMER | 0xB3, "F9: fast-forward/next"),
    67: (CONSUMER | 0xE2, "F10: mute"),
    68: (CONSUMER | 0xEA, "F11: volume down"),
    69: (CONSUMER | 0xE9, "F12: volume up"),
}


def query(fd, command):
    """Send one Focus command and return its reply, excluding the terminator.

    For example, query(fd, "keymap.custom") reads the stored map. Replies
    must complete within five seconds; partial writes and replies are errors.
    """
    deadline = time.monotonic() + 5
    pending = (command + "\n").encode()
    while pending:
        _, writable, _ = select.select([], [fd], [], 0.1)
        if writable:
            pending = pending[os.write(fd, pending):]
        if time.monotonic() >= deadline:
            raise RuntimeError("Keyboard command write timed out")
    response = b""
    terminator = b"\r\n.\r\n"
    while time.monotonic() < deadline:
        readable, _, _ = select.select([fd], [], [], 0.1)
        if readable:
            response += os.read(fd, 32768)
            if terminator in response:
                return response.split(terminator, 1)[0].decode().strip()
    raise RuntimeError(f"Keyboard reply timed out for {command.split()[0]}")


def patch_map(current, compiled, restore):
    """Return a patched copy and its changed indices; preserve custom slots.

    A compiled F8 slot becomes play/pause only when its current value is
    still F8 or the expected media key. A custom Home key stays Home.
    """
    start = FUNCTION_LAYER * KEYS_PER_LAYER
    if len(compiled) < start + KEYS_PER_LAYER or len(current) < len(compiled):
        raise RuntimeError("Expected a Model 100 map with a 64-key function layer")
    if len(current) % KEYS_PER_LAYER:
        raise RuntimeError("Stored keymap length is not a multiple of 64")
    if [compiled[start + i] for i in range(1, 6)] != [58, 59, 60, 61, 62]:
        raise RuntimeError("Compiled function layer does not match the Model 100 layout")
    result = current.copy()
    changes = []
    for index in range(start, start + KEYS_PER_LAYER):
        original = compiled[index]
        if original not in ACTIONS:
            continue
        native, name = ACTIONS[original]
        if current[index] not in (original, native):
            print(f"Preserve custom slot {index}: {current[index]} ({name})")
            continue
        target = original if restore else native
        print(f"{name}: {current[index]} -> {target}")
        if current[index] != target:
            result[index] = target
            changes.append(index)
    return result, changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", help="Model 100 Focus serial port")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--restore-fkeys", action="store_true")
    args = parser.parse_args()
    ports = [args.port] if args.port else glob.glob("/dev/cu.usbmodem*")
    if len(ports) != 1:
        parser.error("Connect one Model 100, or select it with --port")
    port = ports[0]
    in_use = subprocess.run(["/usr/sbin/lsof", "-t", port], capture_output=True)
    if in_use.returncode == 0:
        parser.error("The configuration port is in use; close Chrysalis first")
    if in_use.returncode != 1:
        raise RuntimeError(in_use.stderr.decode().strip() or "Could not check the serial port")
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        raw = termios.tcgetattr(fd)
        raw[4] = raw[5] = termios.B115200
        termios.tcsetattr(fd, termios.TCSANOW, raw)
        print(f"Keyboard firmware: {query(fd, 'version')}")
        if query(fd, "keymap.onlyCustom") != "1":
            raise RuntimeError("Expected the keyboard to use its stored custom keymap")
        current = [int(value) for value in query(fd, "keymap.custom").split()]
        compiled = [int(value) for value in query(fd, "keymap.default").split()]
        updated, changes = patch_map(current, compiled, args.restore_fkeys)
        print(f"Changed slots: {len(changes)}; all other {len(current) - len(changes)} slots preserved")
        if not args.apply and not args.restore_fkeys:
            print("Inspection only. Use --apply to save this patch.")
            return
        if not changes:
            print("Already configured; no write needed.")
            return
        try:
            query(fd, "keymap.custom " + " ".join(map(str, updated)))
            verified = [int(value) for value in query(fd, "keymap.custom").split()]
            if verified != updated:
                raise RuntimeError("Stored keymap did not match the requested patch")
        except Exception as error:
            try:
                query(fd, "keymap.custom " + " ".join(map(str, current)))
                rollback = [int(value) for value in query(fd, "keymap.custom").split()]
                if rollback != current:
                    raise RuntimeError("Restored map does not match the original")
            except Exception as rollback_error:
                raise RuntimeError(
                    f"Keymap update failed ({error}); rollback failed ({rollback_error})"
                ) from rollback_error
            print("Restored the original keymap after an error")
            raise
        print("Saved and verified the complete keymap.")
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, settings)
        os.close(fd)


if __name__ == "__main__":
    main()
