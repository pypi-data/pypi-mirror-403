/**
 * NotebookSettingsContainer
 *
 * A JupyterLab ReactWidget container for the settings panel.
 * Wraps the SettingsWidget and manages its lifecycle.
 */

import * as React from 'react';
import { Widget } from '@lumino/widgets';
import { ReactWidget } from '@jupyterlab/ui-components';
import { SettingsWidget } from './SettingsWidget';
import { ToolService } from '@/LLM/ToolService';

/**
 * React component that mounts the SettingsWidget into the DOM
 */
function SettingsContainerContent({
  settingsWidget
}: {
  settingsWidget: SettingsWidget;
}): JSX.Element {
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (containerRef.current && settingsWidget && !settingsWidget.isDisposed) {
      Widget.attach(settingsWidget, containerRef.current);
    }
    return () => {
      if (settingsWidget && !settingsWidget.isDisposed) {
        Widget.detach(settingsWidget);
      }
    };
  }, [settingsWidget]);

  return (
    <div ref={containerRef} className="sage-ai-settings-container-inner" />
  );
}

/**
 * Container widget that holds the settings panel in the JupyterLab shell.
 */
export class NotebookSettingsContainer extends ReactWidget {
  private settingsWidget: SettingsWidget;

  constructor(toolService: ToolService) {
    super();

    this.id = 'sage-ai-settings-container';
    this.title.label = 'SignalPilot Settings';
    this.title.closable = true;
    this.addClass('sage-ai-settings-container');

    this.settingsWidget = new SettingsWidget(toolService);
  }

  render(): JSX.Element {
    return <SettingsContainerContent settingsWidget={this.settingsWidget} />;
  }

  /**
   * Get the settings widget instance
   */
  public getSettingsWidget(): SettingsWidget {
    return this.settingsWidget;
  }
}
