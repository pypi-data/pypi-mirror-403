import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';
import { IStatusBar } from '@jupyterlab/statusbar';
import { Widget } from '@lumino/widgets';

enum MESSAGE_TYPE {
  READY = 'JCJY_AUTHING_READY',
  DATA = 'JCJY_AUTHING_DATA'
}
const NOTEBOOK_DATA_KEY = 'JCJY_AUTHING_DATA';
let currentData: any = {};
const injectedKernels = new Set<string>();

/**
 * 状态栏小部件
 */
class JcjyStatusWidget extends Widget {
  constructor() {
    super();
    this.addClass('jcjy-status-item');
    this.updateStatus(false);
  }

  updateStatus(active: boolean) {
    this.node.textContent = `JCJY: ${active ? 'LOGINED' : 'STANDBY'}`;
    this.node.style.color = active ? '#4caf50' : '#888888';
    this.node.style.fontWeight = 'bold';
    this.node.style.padding = '0 5px';
    this.node.style.lineHeight = '24px';
  }
}

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jcjy-authing:plugin',
  description: '预植入 JCJY_AUTHING_DATA ,内含token 和用户信息',
  autoStart: true,
  requires: [INotebookTracker, IStatusBar], // 注入状态栏服务
  activate: (
    app: JupyterFrontEnd,
    notebookTracker: INotebookTracker,
    statusBar: IStatusBar
  ) => {
    console.log('jcjy-authing 插件已激活！');
    // 监听消息更新
    window.addEventListener('message', event => {
      const { type, data } = event.data || {};
      console.log('jupyterlab 监听到消息:  ', event.data);
      if (type === MESSAGE_TYPE.DATA) {
        currentData = data;
        notebookTracker.forEach(notebook => injectDataToNotebook(notebook));
      }
    });
    // 通知外部获取数据
    window.parent.postMessage(
      {
        type: MESSAGE_TYPE.READY
      },
      '*'
    );
    // 创建并添加状态栏小部件
    const statusWidget = new JcjyStatusWidget();
    statusBar.registerStatusItem('jcjy-status', {
      item: statusWidget,
      align: 'left',
      rank: 900
    });

    const injectDataToNotebook = async (
      notebook: NotebookPanel,
      data: any = currentData
    ) => {
      const sessionContext = notebook.context.sessionContext;
      if (!sessionContext.session?.kernel) {
        return;
      }

      const code = `${NOTEBOOK_DATA_KEY} = ${JSON.stringify(data)}`;
      try {
        await sessionContext.session.kernel.requestExecute({ code }).done;
        statusWidget.updateStatus(true); // 注入成功，更新状态
      } catch (err) {
        console.error('❌ 注入失败:', err);
        statusWidget.updateStatus(false);
      }
    };

    // 核心逻辑：监听 Notebook 状态
    notebookTracker.widgetAdded.connect((sender, notebook) => {
      const sessionContext = notebook.context.sessionContext;

      // 每次内核变动或重启
      sessionContext.statusChanged.connect((_, status) => {
        const kernelId = sessionContext.session?.kernel?.id;

        if (status === 'idle' && kernelId) {
          // 检查当前内核 ID 是否已经注入过
          if (!injectedKernels.has(kernelId)) {
            console.log(`🚀 内核 ${kernelId} 就绪，执行单次注入`);
            injectDataToNotebook(notebook).then(() => {
              injectedKernels.add(kernelId); // 标记该内核已注入
            });
          }
        } else if (status === 'restarting' || status === 'starting') {
          // 内核重启时，旧 ID 会失效，这里其实不需要手动清理，
          // 因为新内核会有新 ID，但为了内存整洁，可以在这里处理
          if (kernelId) {
            injectedKernels.delete(kernelId);
          }
          statusWidget.updateStatus(false);
        }
      });
    });
  }
};

export default plugin;
