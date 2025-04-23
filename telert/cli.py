#!/usr/bin/env python3
"""
telert – Send Telegram alerts from shell commands.
Supports two modes:
  • **run** mode wraps a command, captures exit status & timing.
  • **filter** mode reads stdin so you can pipe long jobs.

Run `telert --help` or `telert help` for full usage.
"""
from __future__ import annotations
import argparse, json, pathlib, subprocess, sys, textwrap, time, requests, os

CFG_DIR = pathlib.Path(os.path.expanduser("~/.config/telert"))
CFG_FILE = CFG_DIR / "config.json"

# ───────────────────────────────── helpers ──────────────────────────────────

def _save(token: str, chat_id: str):
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    CFG_FILE.write_text(json.dumps({"token": token.strip(), "chat_id": str(chat_id).strip()}))
    print("✔ Configuration saved →", CFG_FILE)


def _load():
    if not CFG_FILE.exists():
        sys.exit("❌ telert is unconfigured – run `telert config …` first.")
    return json.loads(CFG_FILE.read_text())


def _send(msg: str):
    cfg = _load()
    url = f"https://api.telegram.org/bot{cfg['token']}/sendMessage"
    r = requests.post(url, json={"chat_id": cfg["chat_id"], "text": msg})
    if r.status_code != 200:
        sys.exit(f"❌ Telegram API error {r.status_code}: {r.text}")


def _human(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m} m {s} s" if m else f"{s} s"

# ────────────────────────────── sub‑commands ───────────────────────────────

def do_config(a):
    _save(a.token, a.chat_id)

def do_status(_):
    cfg = _load()
    print("token :", cfg['token'][:8] + "…")
    print("chat  :", cfg['chat_id'])
    _send("✅ telert status OK")
    print("sent  : test message")


def do_hook(a):
    t = a.longer_than
    print(textwrap.dedent(f"""
        telert_preexec() {{ TELERT_CMD=\"$BASH_COMMAND\"; TELERT_START=$EPOCHSECONDS; }}
        telert_precmd()  {{ local st=$?; local d=$((EPOCHSECONDS-TELERT_START));
          if (( d >= {t} )); then telert send \"$TELERT_CMD exited $st in $(printf '%dm%02ds' $((d/60)) $((d%60)))\"; fi; }}
        trap telert_preexec DEBUG
        PROMPT_COMMAND=telert_precmd:$PROMPT_COMMAND
    """).strip())


def do_send(a):
    _send(a.text)


def do_run(a):
    start = time.time()
    proc = subprocess.run(a.cmd, text=True, capture_output=True)
    dur = _human(time.time() - start)
    status = proc.returncode
    label = a.label or " ".join(a.cmd)
    if a.only_fail and status == 0:
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        sys.exit(status)

    msg = a.message or f"{label} finished with exit {status} in {dur}"
    if proc.stdout.strip():
        msg += "\n\n--- stdout ---\n" + "\n".join(proc.stdout.splitlines()[:20])[:3900]
    if proc.stderr.strip():
        msg += "\n\n--- stderr ---\n" + "\n".join(proc.stderr.splitlines()[:20])[:3900]
    _send(msg)

    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    sys.exit(status)

# ───────────────────────────── pipeline filter ─────────────────────────────

def piped_mode():
    data = sys.stdin.read()
    msg = sys.argv[1] if len(sys.argv) > 1 else "Pipeline finished"
    if len(sys.argv) > 2:
        msg += f" (exit {sys.argv[2]})"
    if data.strip():
        msg += "\n\n--- output ---\n" + "\n".join(data.splitlines()[:20])[:3900]
    _send(msg)

# ──────────────────────────────── entrypoint ───────────────────────────────

def main():
    if not sys.stdin.isatty():
        piped_mode()
        return

    p = argparse.ArgumentParser(
        prog="telert",
        description="Send Telegram alerts when commands finish (supports exit status).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", required=True)

    # config
    c = sp.add_parser("config", help="store bot token & chat‑id")
    c.add_argument("--token", required=True)
    c.add_argument("--chat-id", required=True)
    c.set_defaults(func=do_config)

    # status
    st = sp.add_parser("status", help="send test message & show config")
    st.set_defaults(func=do_status)

    # hook
    hk = sp.add_parser("hook", help="emit Bash hook for all commands")
    hk.add_argument("--longer-than", "-l", type=int, default=10)
    hk.set_defaults(func=do_hook)

    # send
    sd = sp.add_parser("send", help="send arbitrary text")
    sd.add_argument("text")
    sd.set_defaults(func=do_send)

    # run
    rn = sp.add_parser("run", help="run a command & notify when done")
    rn.add_argument("--label", "-L", help="friendly name")
    rn.add_argument("--message", "-m", help="override default text")
    rn.add_argument("--only-fail", action="store_true", help="notify only on non‑zero exit")
    rn.add_argument("cmd", nargs=argparse.REMAINDER, help="command to execute -- required")
    rn.set_defaults(func=do_run)

    # help alias
    hp = sp.add_parser("help", help="show global help")
    hp.set_defaults(func=lambda _a: p.print_help())

    args = p.parse_args()
    if getattr(args, "cmd", None) == [] and getattr(args, "func", None) is do_run:
        p.error("run: missing command – use telert run -- <cmd> …")
    args.func(args)

if __name__ == "__main__":
    main()