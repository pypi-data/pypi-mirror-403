# Inhibit.py

Systemd Inhibitor - Prevent system shutdowns and sleep states via stdin ON/OFF
commands.

This script creates a systemd inhibitor that can be controlled via stdin.
It reads ON/OFF commands from standard input and toggles the inhibition
accordingly. This is useful for preventing system shutdowns and sleep states
when controlled by external processes through pipes.

Basic Usage:
```bash
    # Just an example of valid input values.
    echo "ON" | inhibit
    echo "OFF" | inhibit

    # In practice, an external process emits these values.
    some_process |inhibit

    # Common arguments
    inhibit --what sleep --who "my-app" --why "processing data"
```
The script uses systemd's logind interface to create inhibitors for:
- sleep: Prevent system sleep/suspend
- idle: Prevent automatic idle detection

For detailed command-line options, use --help.

## Requirements

### System requirements

These must be available and installed

- dbus-python
- systemd

## Installing

Important: tool assumes that system provides `dbus-python` package.

Alternatively you can install `dbus-python` manually.

```bash
$ python -m venv --system-site-packages venv
$ source venv/bin/activate
$ python -m pip install inhibit
$ inhibit --version
inhibit 0.1.0
```

To install the package, it's recommended to use the Linux distribution default package manager.

## Development

### Requirements

- uv
- just
- reuse
- tox

### Build

- `just check`
- `just build`

See [Justfile](Justfile).
