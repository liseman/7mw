#!/usr/bin/env python3
"""Drive the interactive `eas build` credential prompts under a real pty.

Apple auth comes from EXPO_APPLE_ID / EXPO_APPLE_APP_SPECIFIC_PASSWORD in the env,
so we should never be asked for the Apple ID, password, or a 2FA code. For any
yes/no or selection prompt that appears we accept the default (Enter), which is
the desired choice for credential generation.

Strategy: stream the pty output to a live log file (unbuffered). When output
goes idle for a moment and the recent buffer looks like a waiting prompt, press
Enter. If a 2FA / verification-code prompt appears, log a clear marker and exit
so the caller can intervene instead of hanging forever.
"""
import os, pty, select, sys, time, re

LOG = os.environ.get("EAS_DRIVE_LOG", "/tmp/eas-build.log")
cmd = ["npx", "eas-cli", "build", "--platform", "ios",
       "--profile", "production", "--auto-submit"]

ansi = re.compile(rb"\x1b\[[0-9;?]*[a-zA-Z]")
spin = re.compile(rb"[\xe2\xa0\x80-\xff\xe2\xa3\xbf]")  # braille spinner bytes (best effort)

# Markers that indicate the CLI is blocked waiting for a y/n or list selection.
prompt_markers = [b"(Y/n)", b"(y/N)", b"\xe2\x80\xba", b"\xe2\x9d\xaf"]  # › ❯
# Markers that mean we are stuck and CANNOT proceed unattended.
fatal_markers = [b"verification code", b"two-factor", b"2fa", b"security code",
                 b"enter the code", b"password:"]

logf = open(LOG, "wb", buffering=0)

def log(msg):
    logf.write(msg if isinstance(msg, bytes) else msg.encode())
    logf.flush()

log(f"[driver] starting at {time.ctime()}\n")

pid, fd = pty.fork()
if pid == 0:
    os.execvp(cmd[0], cmd)

clean_all = b""
last_output = time.time()
last_answer = 0.0
answered = 0
deadline = time.time() + 1500
exit_reason = "child exited"

try:
    while True:
        if time.time() > deadline:
            exit_reason = "overall timeout (1500s)"
            break
        r, _, _ = select.select([fd], [], [], 0.5)
        now = time.time()
        if fd in r:
            try:
                data = os.read(fd, 4096)
            except OSError:
                break
            if not data:
                break
            logf.write(data); logf.flush()
            last_output = now
            clean_all += ansi.sub(b"", data)
            if len(clean_all) > 8000:
                clean_all = clean_all[-8000:]
            tail = clean_all[-300:].lower()
            if any(m in tail for m in fatal_markers):
                exit_reason = "FATAL: hit interactive auth prompt (2FA/password) - cannot proceed unattended"
                log(f"\n[driver] {exit_reason}\n")
                break
        else:
            # No output this tick. If it has been idle and the tail looks like a
            # waiting prompt, accept the default.
            idle = now - last_output
            tail = clean_all[-300:]
            looks_prompt = (b"?" in tail) and any(m in tail for m in prompt_markers)
            if looks_prompt and idle > 2.0 and (now - last_answer) > 2.0:
                log(f"\n[driver] answering prompt with <Enter> (#{answered+1})\n")
                os.write(fd, b"\r")
                answered += 1
                last_answer = now
            # detect child exit
            try:
                wpid, _ = os.waitpid(pid, os.WNOHANG)
                if wpid == pid:
                    break
            except ChildProcessError:
                break
finally:
    try:
        _, status = os.waitpid(pid, 0)
        code = os.waitstatus_to_exitcode(status)
    except Exception:
        code = None
log(f"\n[driver] done: {exit_reason}; eas exit code = {code}; prompts answered = {answered}\n")
# Mirror the exit code (non-zero if eas failed).
sys.exit(0 if code in (0, None) else 2)
