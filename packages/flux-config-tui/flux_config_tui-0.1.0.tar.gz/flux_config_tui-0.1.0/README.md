# flux-config-tui

Terminal UI client for Flux Node Configuration.

This package provides an interactive TUI for managing Flux Node configuration via the flux-configd daemon.

## Features

- Interactive terminal interface
- Real-time system monitoring
- Service management
- Installation wizard
- Configuration management
- Log viewing

## Requirements

- flux-configd daemon must be running
- Access to Unix socket at `/run/flux-configd/daemon.sock`
- User must be in `flux-daemon-access` group
