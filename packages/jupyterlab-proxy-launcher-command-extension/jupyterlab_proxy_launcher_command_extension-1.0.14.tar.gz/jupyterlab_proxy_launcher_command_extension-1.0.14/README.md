# jupyterlab_proxy_launcher_command_extension

[![GitHub Actions](https://github.com/stellarshenson/jupyterlab_proxy_launcher_command_extension/actions/workflows/build.yml/badge.svg)](https://github.com/stellarshenson/jupyterlab_proxy_launcher_command_extension/actions/workflows/build.yml)
[![npm version](https://img.shields.io/npm/v/jupyterlab_proxy_launcher_command_extension.svg)](https://www.npmjs.com/package/jupyterlab_proxy_launcher_command_extension)
[![PyPI version](https://img.shields.io/pypi/v/jupyterlab-proxy-launcher-command-extension.svg)](https://pypi.org/project/jupyterlab-proxy-launcher-command-extension/)
[![Total PyPI downloads](https://static.pepy.tech/badge/jupyterlab-proxy-launcher-command-extension)](https://pepy.tech/project/jupyterlab-proxy-launcher-command-extension)
[![JupyterLab 4](https://img.shields.io/badge/JupyterLab-4-orange.svg)](https://jupyterlab.readthedocs.io/en/stable/)
[![Brought To You By KOLOMOLO](https://img.shields.io/badge/Brought%20To%20You%20By-KOLOMOLO-00ffff?style=flat)](https://kolomolo.com)

JupyterLab extension providing a command to launch jupyter-server-proxy connections via modal dialog, opening proxied services in either a JupyterLab tab or new browser window.

## Features

- **Modal dialog** - Configure port, path suffix, and target (JupyterLab tab or browser window)
- **JupyterLab tab** - Embed proxied service in an IFrame within JupyterLab
- **Browser tab** - Open proxied service in a new browser window
- **Command palette** - Access via "Open Proxy Launcher" in the Proxy category
- **Keyboard shortcut** - `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
- **Programmatic API** - Call with arguments to pre-fill dialog values

## Usage

1. Open command palette (`Ctrl+Shift+C` / `Cmd+Shift+C`)
2. Search for "Open Proxy Launcher"
3. Enter port number and optional path suffix
4. Choose whether to open in new browser tab
5. Click "Open"

## Command Arguments

When calling the command programmatically, the following arguments are supported:

| Argument                | Type    | Description                         |
| ----------------------- | ------- | ----------------------------------- |
| `default_port`          | number  | Pre-fill port input                 |
| `default_path`          | string  | Pre-fill path suffix input          |
| `default_newBrowserTab` | boolean | Pre-check the browser tab checkbox  |
| `title`                 | string  | Custom title for the JupyterLab tab |

Example:

```typescript
app.commands.execute('proxy-launcher:open', {
  default_port: 8501,
  default_path: '/api/docs',
  title: 'Streamlit App'
});
```

## Requirements

- JupyterLab >= 4.0.0
- jupyter-server-proxy

## Install

```bash
pip install jupyterlab_proxy_launcher_command_extension
```

## Uninstall

```bash
pip uninstall jupyterlab_proxy_launcher_command_extension
```
