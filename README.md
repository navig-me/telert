
# telert – Telegram Alerts for Your Terminal  

**Version 0.1.1**

Telert is a tiny command‑line utility that shoots you a Telegram message the moment a command (or an entire shell pipeline) finishes.  
It preserves **exit status**, captures **run‑time**, and can optionally include the first lines of _stdout_ / _stderr_.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mihirk)

---

## ✨ Features

| Mode           | What it does | Example |
|----------------|--------------|---------|
| **Run**        | Wraps a command, times it, sends notification with exit code. | `telert run --label "RSYNC" -- rsync -a /src /dst` |
| **Filter**     | Reads from stdin so you can _pipe_ output. | `long_job | telert "compile done"` |
| **Hook**       | Generates a Bash snippet so **every** command > *N* seconds notifies automatically. | `eval "$(telert hook -l 30)"` |
| **Send**       | Low‑level "send arbitrary text to myself" helper. | `telert send "server rebooted"` |

---

## 🚀 Quick install

```bash
# Any OS (PyPI)
pip install telert

# Fedora / RHEL / Alma / Rocky
sudo dnf install telert      # yum works too

# Debian / Ubuntu / Linux Mint
sudo apt install telert
```

RPM/DEB repositories are published by GitHub Actions on every release tag.  
If you prefer, you can also grab the single‑file wheel from Releases.

---

## 🤖 Bot set‑up (one‑time)

1. Chat with **@BotFather → /newbot →** copy the *API token*.
2. Send any throwaway message to the new bot **from the account/channel you want alerts in**.
3. Fetch the chat‑ID:
   ```bash
   curl -s "https://api.telegram.org/bot<token>/getUpdates" | jq .
   ```
   Copy the integer in `result[0].message.chat.id` (for channels it starts with `-100`).
4. Configure Telert:
   ```bash
   telert config --token <token> --chat-id <chat_id>
   telert status      # sends a ✅ test message
   ```

Telert stores creds in `~/.config/telert/config.json`.

---

## 🛠 Usage

### Run mode (recommended)
```bash
# Notify regardless of outcome
$ telert run --label " nightly backup " -- rsync -a /src /dst
# custom message & only if the command fails
telert run --only-fail -m "backup failed" -- rsync -a /src /dst
```

### Filter mode (legacy piping)
```bash
make big‑pdf | telert "LaTeX finished"
```
> ⚠️  Exit status is **unknown** here – a shell can’t pass `$?` inside a pipe.  
> If you need exit status, stick to **run** mode or explicit `; telert send "failed $?"`.

### Shell hook
```bash
echo 'eval "$(telert hook -l 20)"' >> ~/.bashrc  # any cmd >20 s notifies
```

### Help
```bash
telert --help       # global help
telert run --help   # sub‑command help
telert help         # alias to the same
```

---

## 🌿 Environment variables

| Variable            | Effect                                      |
|---------------------|---------------------------------------------|
| `TELERT_LONG`       | Default threshold (seconds) for `hook`.     |
| `TELERT_SILENT=1`   | Suppress stdout/stderr echo in `run`.       |

---

## 👩‍💻 Development
```bash
git clone https://github.com/navig-me/telert
cd telert
python -m pip install -e .[dev]
```

### Releasing to PyPI

The project is automatically published to PyPI when a new GitHub release is created:

1. Update version in both `pyproject.toml` and `telert/__init__.py`
2. Commit the changes and push to main
3. Create a new GitHub release with a tag like `v0.1.1`
4. The GitHub Actions workflow will automatically build and publish to PyPI

To manually publish to PyPI if needed:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Upload to PyPI
twine upload dist/*
```

---

## 🤝 Contributing / License

PRs & issues welcome!  
Licensed under the MIT License – see `LICENSE`.
