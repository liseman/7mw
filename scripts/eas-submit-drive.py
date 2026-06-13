#!/usr/bin/env python3
"""Drive `eas submit` under a pty for a first-time App Store Connect submission.

The submit profile in eas.json pre-fills language/sku/companyName, so the only
interactive step should be confirming creation of the App Store Connect app
(a Y/n prompt). We accept defaults with Enter. If we hit a required free-text
prompt that loops (same value re-requested), we bail instead of hammering it.

Usage: BUILD_ID=<id> python3 scripts/eas-submit-drive.py
"""
import os, pty, select, sys, time, re

LOG = os.environ.get("EAS_DRIVE_LOG", "/tmp/eas-submit.log")
build_id = os.environ["BUILD_ID"]
cmd = ["npx", "eas-cli", "submit", "--platform", "ios",
       "--profile", "production", "--id", build_id]

ansi = re.compile(rb"\x1b\[[0-9;?]*[a-zA-Z]")
prompt_markers = [b"(Y/n)", b"(y/N)", b"\xe2\x80\xba", b"\xe2\x9d\xaf"]  # › ❯
fatal_markers = [b"please enter a valid value", b"password:", b"verification code",
                 b"two-factor", b"security code"]

logf = open(LOG, "wb", buffering=0)
def log(m): logf.write(m if isinstance(m, bytes) else m.encode()); logf.flush()
log(f"[driver] submit starting at {time.ctime()} build={build_id}\n")

pid, fd = pty.fork()
if pid == 0:
    os.execvp(cmd[0], cmd)

clean_all = b""
last_output = time.time()
last_answer = 0.0
answered = 0
loop_guard = 0
deadline = time.time() + 1200
exit_reason = "child exited"
try:
    while True:
        if time.time() > deadline:
            exit_reason = "overall timeout"; break
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
            clean_all = clean_all[-8000:]
            tail = clean_all[-300:].lower()
            if any(m in tail for m in fatal_markers):
                exit_reason = "FATAL: required free-text/auth prompt - cannot proceed unattended"
                log(f"\n[driver] {exit_reason}\n"); break
        else:
            idle = now - last_output
            tail = clean_all[-300:]
            looks_prompt = (b"?" in tail) and any(m in tail for m in prompt_markers)
            if looks_prompt and idle > 2.0 and (now - last_answer) > 2.0:
                loop_guard += 1
                if loop_guard > 12:
                    exit_reason = "FATAL: prompt loop (answered 12x with no progress)"
                    log(f"\n[driver] {exit_reason}\n"); break
                log(f"\n[driver] answering prompt with <Enter> (#{answered+1})\n")
                os.write(fd, b"\r"); answered += 1; last_answer = now
            try:
                wpid, _ = os.waitpid(pid, os.WNOHANG)
                if wpid == pid: break
            except ChildProcessError:
                break
finally:
    try:
        _, status = os.waitpid(pid, 0)
        code = os.waitstatus_to_exitcode(status)
    except Exception:
        code = None
log(f"\n[driver] done: {exit_reason}; eas exit = {code}; answered = {answered}\n")
sys.exit(0 if code in (0, None) else 2)
