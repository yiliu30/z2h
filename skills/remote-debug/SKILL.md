---
name: remote-debug
description: "Drive Claude Code to debug an issue on a remote node over SSH — connect, set up an environment, copy scripts/probes across, run repros, and capture findings. Use when the user says we're 'on a remote node', hands you ssh credentials, or asks to reproduce / debug / set up on a remote host. Covers pexpect-based ssh/scp when sshpass is unavailable, minimal standalone repros, and isolating a root cause by comparing machines."
license: MIT
---

# Remote Debugging with Claude Code

A general workflow for using Claude Code to debug an issue on a **remote node** over
SSH: connect, provision an environment, copy minimal scripts/probes across, run
reproductions, and (when relevant) compare a working node against a failing one to
isolate the variable.

## When to use

- The prompt starts with `ssh ...`, or the user says "we are on a remote node".
- The user hands you a host + credentials and asks to reproduce / debug / set up there.
- A bug only reproduces in a remote environment you can't run locally (specific
  hardware, OS, driver, network, or data).
- You need to A/B two machines to find which layer is the deciding variable.

## Golden rules

1. **Assume the remote is SHARED.** Treat installs, upgrades, service restarts,
   reboots, and `rm -rf` as destructive — get explicit user go-ahead before any of
   them. Read-only inspection (listing packages, reading files, running a probe) is
   fine to do directly.
2. **Back up before patching anything in place.** `cp x x.bak` first, tell the user
   the backup path, and offer to revert at the end.
3. **Change one variable at a time.** When comparing a PASS vs FAIL node, keep
   everything identical except the one thing under test (same binary, same inputs).
4. **Prefer a minimal standalone repro over the full app.** A small script that
   exercises only the suspect behavior removes the rest of the app from the equation
   and makes the result attributable to one thing.
5. **Record findings as you go**, in a file, not just in chat — long sessions get
   compacted and chat context is lost. A short `*_finding.md` with the evidence table
   survives.

## Step 1 — Establish the connection

First check whether non-interactive SSH already works (key-based):

```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 USER@HOST 'echo ok' 2>&1
```

If it needs a password and `sshpass` is **not** installed (common), don't try to pipe
the password. Use a small `pexpect` helper instead. Use `python3` (bare `python` is
often absent).

`/tmp/ssh_run.py`:

```python
#!/usr/bin/env python3
import sys, pexpect
host, password, cmd = sys.argv[1], sys.argv[2], sys.argv[3]
child = pexpect.spawn(f"ssh -o StrictHostKeyChecking=no {host} {cmd!r}",
                      encoding="utf-8", timeout=600)
i = child.expect([r"[Pp]assword:", pexpect.EOF])
if i == 0:
    child.sendline(password); child.expect(pexpect.EOF)
print(child.before)
```

Run: `python3 /tmp/ssh_run.py USER@HOST 'secret' 'whoami'`

A matching `/tmp/scp_run.py` (swap the spawn line for `scp LOCAL host:REMOTE`) copies
files across. If `pexpect` is missing: `python3 -m pip install --user pexpect`.

Once connected, prefer setting up an SSH key (`ssh-copy-id`) so later commands are
non-interactive — ask the user before modifying `authorized_keys` on a shared box.

### Quoting trap (learned the hard way)

Nested SSH + inline scripts break on quote/backslash escaping (e.g. a `\t` inside a
Python one-liner becomes a literal tab over the wire → `SyntaxError`). **Don't** send
multi-line scripts through `ssh '...'`. Instead: write the script to a local file,
`scp` it over, then `ssh host 'python3 /remote/path/script.py'`.

## Step 2 — Survey the remote environment (read-only)

Before changing anything, capture the state relevant to the bug. Tailor to the issue,
but typically: OS/kernel (`uname -a`, `/etc/os-release`), installed package versions
of the suspect components, library/binary versions actually loaded (`ldd`,
`readlink -f`), env vars, and how the framework/app reports the resource. Write the
output into the finding doc. When comparing two nodes, lay it out as a table so the
**single differing column** is obvious.

## Step 3 — Set up an environment (if needed)

Follow the user's global conventions (e.g. `uv` for Python envs, a short name, a
standard venvs dir). If the network is flaky, apply the project's proxy settings. When
A/B-ing nodes, mirror the same toolchain versions as the known-good node so the
environment itself isn't an accidental confound.


## Step 4 — Patch / verify a fix (carefully)

- Testing a code patch on the remote? **Back up first** (`cp f f.bak`), make the
  change reversible (env-driven and default-off when possible), and tell the user
  exactly what changed and how to revert.
- If the fix is an install/upgrade/restart on a shared node, **stop and ask** —
  describe the exact action and that it touches shared state. Don't run it unprompted.
- Re-run the repro to confirm. A fix that removes error A but exposes error B is not
  done — report the new blocker rather than calling it fixed.


## Cleanup checklist

- Revert in-place patches you weren't told to keep (restore the `.bak`).
- Remove throwaway probes/scripts from `/tmp` if asked; leave reusable checkers in the repo.
- Summarize for the user: root cause, fix applied, and anything still pending a
  decision (especially actions on shared state that need their go-ahead).
