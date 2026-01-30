import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { showDialog, Dialog, ICommandPalette } from '@jupyterlab/apputils';
import { PageConfig } from '@jupyterlab/coreutils';
import { Widget } from '@lumino/widgets';

/**
 * Command ID for the proxy launcher
 */
const COMMAND_ID = 'proxy-launcher:open';

/**
 * Plugin ID
 */
const PLUGIN_ID = 'jupyterlab_proxy_launcher_command_extension:plugin';

/**
 * Interface for dialog form values
 */
interface IProxyLauncherFormValue {
  port: number;
  path: string;
  newBrowserTab: boolean;
}

/**
 * Interface for command arguments
 */
interface IProxyLauncherArgs {
  default_port?: number;
  default_path?: string;
  default_newBrowserTab?: boolean;
  title?: string;
}

/**
 * Custom dialog body widget for proxy launcher configuration
 */
class ProxyLauncherDialogBody extends Widget {
  private _portInput: HTMLInputElement;
  private _pathInput: HTMLInputElement;
  private _newBrowserTabCheckbox: HTMLInputElement;

  constructor(
    defaultPort?: number,
    defaultPath?: string,
    defaultNewBrowserTab?: boolean
  ) {
    super();
    this.addClass('jp-ProxyLauncher-dialog');

    const container = document.createElement('div');
    container.style.padding = '10px';

    // Port input
    const portLabel = document.createElement('label');
    portLabel.textContent = 'Port:';
    portLabel.style.display = 'block';
    portLabel.style.marginBottom = '5px';
    portLabel.style.fontWeight = 'bold';

    this._portInput = document.createElement('input');
    this._portInput.type = 'number';
    this._portInput.min = '1';
    this._portInput.max = '65535';
    this._portInput.value = defaultPort?.toString() ?? '';
    this._portInput.style.width = '100%';
    this._portInput.style.padding = '8px';
    this._portInput.style.marginBottom = '4px';
    this._portInput.style.boxSizing = 'border-box';
    this._portInput.style.border = '1px solid var(--jp-border-color1)';
    this._portInput.style.borderRadius = '4px';
    this._portInput.style.backgroundColor = 'var(--jp-layout-color1)';
    this._portInput.style.color = 'var(--jp-ui-font-color1)';

    const portHelper = document.createElement('div');
    portHelper.textContent = 'e.g., 8501';
    portHelper.style.fontSize = '12px';
    portHelper.style.color = 'var(--jp-ui-font-color2)';
    portHelper.style.marginBottom = '15px';

    // Path input
    const pathLabel = document.createElement('label');
    pathLabel.textContent = 'Path suffix (optional):';
    pathLabel.style.display = 'block';
    pathLabel.style.marginBottom = '5px';
    pathLabel.style.fontWeight = 'bold';

    this._pathInput = document.createElement('input');
    this._pathInput.type = 'text';
    this._pathInput.value = defaultPath ?? '';
    this._pathInput.style.width = '100%';
    this._pathInput.style.padding = '8px';
    this._pathInput.style.marginBottom = '4px';
    this._pathInput.style.boxSizing = 'border-box';
    this._pathInput.style.border = '1px solid var(--jp-border-color1)';
    this._pathInput.style.borderRadius = '4px';
    this._pathInput.style.backgroundColor = 'var(--jp-layout-color1)';
    this._pathInput.style.color = 'var(--jp-ui-font-color1)';

    const pathHelper = document.createElement('div');
    pathHelper.textContent = 'e.g., /api/docs';
    pathHelper.style.fontSize = '12px';
    pathHelper.style.color = 'var(--jp-ui-font-color2)';
    pathHelper.style.marginBottom = '15px';

    // New browser tab checkbox
    const checkboxContainer = document.createElement('div');
    checkboxContainer.style.display = 'flex';
    checkboxContainer.style.alignItems = 'center';
    checkboxContainer.style.gap = '8px';

    this._newBrowserTabCheckbox = document.createElement('input');
    this._newBrowserTabCheckbox.type = 'checkbox';
    this._newBrowserTabCheckbox.id = 'proxy-launcher-browser-checkbox';
    this._newBrowserTabCheckbox.checked = defaultNewBrowserTab ?? false;

    const checkboxLabel = document.createElement('label');
    checkboxLabel.htmlFor = 'proxy-launcher-browser-checkbox';
    checkboxLabel.textContent = 'Open in new browser tab';

    checkboxContainer.appendChild(this._newBrowserTabCheckbox);
    checkboxContainer.appendChild(checkboxLabel);

    // Description text
    const descriptionText = document.createElement('div');
    descriptionText.textContent =
      'Connect to a service running on the specified port via jupyter-server-proxy.';
    descriptionText.style.fontSize = '12px';
    descriptionText.style.color = 'var(--jp-ui-font-color2)';
    descriptionText.style.marginTop = '15px';
    descriptionText.style.paddingTop = '10px';
    descriptionText.style.borderTop = '1px solid var(--jp-border-color2)';

    // Assemble container
    container.appendChild(portLabel);
    container.appendChild(this._portInput);
    container.appendChild(portHelper);
    container.appendChild(pathLabel);
    container.appendChild(this._pathInput);
    container.appendChild(pathHelper);
    container.appendChild(checkboxContainer);
    container.appendChild(descriptionText);

    this.node.appendChild(container);
  }

  /**
   * Get the form values
   */
  getValue(): IProxyLauncherFormValue {
    const port = parseInt(this._portInput.value, 10);
    let path = this._pathInput.value.trim();

    // Ensure path starts with / if not empty
    if (path && !path.startsWith('/')) {
      path = '/' + path;
    }

    return {
      port: isNaN(port) ? 0 : port,
      path: path,
      newBrowserTab: this._newBrowserTabCheckbox.checked
    };
  }

  /**
   * Validate the port input
   */
  isValid(): boolean {
    const port = parseInt(this._portInput.value, 10);
    return !isNaN(port) && port >= 1 && port <= 65535;
  }

  /**
   * Focus the port input on dialog open
   */
  onAfterAttach(): void {
    this._portInput.focus();
  }
}

/**
 * IFrame widget for embedding proxy content in JupyterLab
 */
class ProxyIFrameWidget extends Widget {
  constructor(url: string, title: string) {
    super();
    this.addClass('jp-ProxyLauncher-iframe');
    this.id = `proxy-iframe-${Date.now()}`;
    this.title.label = title;
    this.title.closable = true;
    this.title.caption = url;

    const iframe = document.createElement('iframe');
    iframe.src = url;
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = 'none';
    this.node.appendChild(iframe);
  }
}

/**
 * Initialization data for the jupyterlab_proxy_launcher_command_extension extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  description:
    'JupyterLab commands to launch jupyter-server-proxy to a given port via modal window, opening in either a new JupyterLab tab or new browser tab',
  autoStart: true,
  optional: [ICommandPalette],
  activate: (app: JupyterFrontEnd, palette: ICommandPalette | null) => {
    console.log(
      'JupyterLab extension jupyterlab_proxy_launcher_command_extension is activated!'
    );

    const { commands, shell } = app;

    commands.addCommand(COMMAND_ID, {
      label: 'Open Proxy Launcher',
      caption:
        'Open dialog to launch jupyter-server-proxy connection to a port',
      describedBy: () =>
        Promise.resolve({
          args: {
            type: 'object',
            properties: {
              default_port: {
                type: 'number',
                description: 'Default port number to pre-fill in the dialog'
              },
              default_path: {
                type: 'string',
                description: 'Default path suffix to pre-fill in the dialog'
              },
              default_newBrowserTab: {
                type: 'boolean',
                description: 'Default state of the new browser tab checkbox'
              },
              title: {
                type: 'string',
                description: 'Custom title for the JupyterLab tab'
              }
            }
          }
        }),
      execute: async (args: IProxyLauncherArgs) => {
        const dialogBody = new ProxyLauncherDialogBody(
          args.default_port,
          args.default_path,
          args.default_newBrowserTab
        );

        const result = await showDialog({
          title: 'Proxy Launcher',
          body: dialogBody,
          buttons: [Dialog.cancelButton(), Dialog.okButton({ label: 'Open' })]
        });

        if (!result.button.accept) {
          return;
        }

        const formValue = dialogBody.getValue();

        // Validate port
        if (!formValue.port || formValue.port < 1 || formValue.port > 65535) {
          await showDialog({
            title: 'Invalid Port',
            body: 'Please enter a valid port number between 1 and 65535.',
            buttons: [Dialog.okButton()]
          });
          return;
        }

        // Construct proxy URL
        const baseUrl = PageConfig.getBaseUrl();
        const proxyUrl = `${baseUrl}proxy/${formValue.port}/${formValue.path.replace(/^\//, '')}`;

        if (formValue.newBrowserTab) {
          // Open in new browser tab
          window.open(proxyUrl, '_blank');
        } else {
          // Open in JupyterLab IFrame tab
          const tabTitle =
            args.title || `Proxy :${formValue.port}${formValue.path || ''}`;
          const widget = new ProxyIFrameWidget(proxyUrl, tabTitle);
          shell.add(widget, 'main');
          shell.activateById(widget.id);
        }
      }
    });

    // Add command to command palette
    if (palette) {
      palette.addItem({
        command: COMMAND_ID,
        category: 'Proxy'
      });
    }

    // Add keyboard shortcut
    app.commands.addKeyBinding({
      command: COMMAND_ID,
      keys: ['Accel Shift P'],
      selector: 'body'
    });

    console.log(`Command ${COMMAND_ID} registered`);
  }
};

export default plugin;
