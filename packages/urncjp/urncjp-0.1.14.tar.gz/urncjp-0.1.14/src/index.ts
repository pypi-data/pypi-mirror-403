import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
} from "@jupyterlab/application";

import { ISettingRegistry } from "@jupyterlab/settingregistry";
import { ICommandPalette, DOMUtils } from "@jupyterlab/apputils";
import { INotebookTracker } from "@jupyterlab/notebook";
import { Widget } from "@lumino/widgets";
import fnv1a from "@sindresorhus/fnv1a";

import { submitNotebook, userInfo } from "./handler";

const plugin: JupyterFrontEndPlugin<void> = {
  id: "urncjp:plugin",
  description: "A JupyterLab extension to collect exam files",
  autoStart: true,
  requires: [ICommandPalette, INotebookTracker],
  optional: [ISettingRegistry],
  activate: (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    nbtracker: INotebookTracker,
    settingRegistry: ISettingRegistry | null,
  ) => {
    console.log("JupyterLab extension urncjp is activated!");

    const { commands } = app;

    const nbHashes: { [key: string]: string } = {};

    const userWidget = addTopDiv(app, "jp-UserWidget");
    const submitWidget = addTopDiv(app, "jp-SubmitWidget");

    commands.addCommand("urncjp:submit", {
      label: "Submit Exam",
      caption: "Submit the exam to the server",
      execute: () => {
        const current = nbtracker.currentWidget;
        if (!current) {
          console.error("No notebook is active");
          return;
        }
        const panel = current.content;
        const nbData = panel.model?.toJSON();
        if (!nbData) {
          console.error("Failed to get notebook data");
          return;
        }
        const data = nbData as { metadata: { exam?: string } };
        if (!data.metadata || !data.metadata.exam) {
          console.log("Not an exam notebook. Skipping submission.");
          return;
        }
        const examId = data.metadata.exam;
        const dataString = JSON.stringify(nbData);
        const hash = fnv1a(dataString, { size: 128 }).toString(16);
        console.log("hash:", hash);

        if (nbHashes[examId] === hash) {
          console.log("Notebook is unchanged. Skipping submission.");
          return;
        }
        nbHashes[examId] = hash;

        submitNotebook(JSON.stringify(nbData))
          .then((data) => {
            const { submission } = data;
            const { createdAt, valid } = submission;
            const date = new Date(createdAt).toLocaleString("de-DE");
            if (!valid) {
              submitWidget.node.textContent = "Exam submissions are closed";
              submitWidget.node.style.backgroundColor = "#1d293d";
            } else {
              submitWidget.node.textContent = `Submitted at ${date}`;
              submitWidget.node.style.backgroundColor = "#006045";
            }
          })
          .catch((error) => {
            console.error("Failed to submit notebook:", error);
          });
      },
    });
    commands.addCommand("urncjp:status", {
      label: "Check Status",
      caption: "Check the status of the exam",
      execute: () => {
        userInfo().then((data) => {
          const { sub } = data;
          userWidget.node.textContent = `Jupyter Exam: ${sub}`;
        });
      },
    });

    palette.addItem({
      command: "urncjp:status",
      category: "Notebook Operations",
    });

    palette.addItem({
      command: "urncjp:submit",
      category: "Notebook Operations",
    });

    nbtracker.currentChanged.connect((_, nbPanel) => {
      if (!nbPanel) {
        return;
      }
      commands.execute("urncjp:status");

      nbPanel.context.saveState.connect((_, state) => {
        if (state === "completed") {
          commands.execute("urncjp:submit");
        }
      });
    });

    if (settingRegistry) {
      settingRegistry
        .load(plugin.id)
        .then((settings) => {
          console.log("urncjp settings loaded:", settings.composite);
        })
        .catch((reason) => {
          console.error("Failed to load settings for urncjp.", reason);
        });
    }
  },
};

function addTopDiv(app: JupyterFrontEnd, className: string) {
  const node = document.createElement("div");
  node.textContent = "";
  const widget = new Widget({ node });
  widget.id = DOMUtils.createDomID();
  widget.addClass(className);
  app.shell.add(widget, "top", { rank: 1000 });
  return widget;
}

export default plugin;
