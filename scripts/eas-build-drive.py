#!/usr/bin/env python3
"""Drive the interactive `eas build` credential prompts under a real pty.
Apple auth comes from EXPO_APPLE_ID / EXPO_APPLE_APP_SPECIFIC_PASSWORD in the env.
We answer the 'log in to your Apple account' and any reuse/generate prompts
by accepting the default (Enter), which is the desired choice in each case."""
import os, pty, select, sys, time, re

cmd = ["npx", "eas-cli", "build", "--platform", "ios",
       "--profile", "production", "--auto-submit"]

ansi = re.compile(rb"\x1b\[[0-9;?]*[a-zA-Z]")
prompt_re = re.compile(rb"\?\s.*(\(Y/n\)|\(y/N\)|\xe2\x80\xba|>)", re.I)

pid, fd = pty.fork()
if pid == 0:
    os.execvp(cmd[0], cmd)

buf = b""
last_answer = 0.0
deadline = time.time() + 1500
try:
    while True:
        if time.time() > deadline:
            sys.stdout.write("\n[driver] overall timeout reached\n")
            break
        r, _, _ = select.select([fd], [], [], 1.0)
        if fd in r:
            try:
                data = os.read(fd, 4096)
            except OSError:
                break
            if not data:
                break
            sys.stdout.buffer.write(data)
            sys.stdout.flush()
            buf += data
            clean = ansi.sub(b"", buf)
            # When the tail looks like a waiting prompt, answer the default.
            tail = clean[-200:]
            if prompt_re.search(tail) and (time.time() - last_answer) > 1.5:
                time.sleep(0.4)
                os.write(fd, b"\r")
                last_answer = time.time()
                buf = b""
        else:
            # idle; check if child exited
            try:
                wpid, status = os.waitpid(pid, os.WNOHANG)
                if wpid == pid:
                    break
            except ChildProcessError:
                break
finally:
    try:
        _, status = os.waitpid(pid, 0)
        code = os.waitstatus_to_exitcode(status)
    except Exception:
        code = -1
sys.stdout.write(f"\n[driver] eas exited with code {code}\n")
sys.exit(0 if code in (0, None) else 1)
