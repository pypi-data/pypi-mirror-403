"use strict";
(self["webpackChunkggblab"] = self["webpackChunkggblab"] || []).push([["lib_index_js"],{

/***/ "./lib/index.js"
/*!**********************!*\
  !*** ./lib/index.js ***!
  \**********************/
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _jupyterlab_application__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/application */ "webpack/sharing/consume/default/@jupyterlab/application");
/* harmony import */ var _jupyterlab_application__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_application__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _jupyterlab_launcher__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @jupyterlab/launcher */ "webpack/sharing/consume/default/@jupyterlab/launcher");
/* harmony import */ var _jupyterlab_launcher__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_launcher__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @jupyterlab/settingregistry */ "webpack/sharing/consume/default/@jupyterlab/settingregistry");
/* harmony import */ var _jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! @jupyterlab/ui-components */ "webpack/sharing/consume/default/@jupyterlab/ui-components");
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_4__);
/* harmony import */ var _widget__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./widget */ "./lib/widget.js");




//import { DockLayout } from '@lumino/widgets';


var CommandIDs;
(function (CommandIDs) {
    CommandIDs.create = 'ggblab:create';
})(CommandIDs || (CommandIDs = {}));
// const PANEL_CLASS = 'jp-ggblabPanel';
/**
 * Initialization data for the ggblab extension.
 */
const plugin = {
    id: 'ggblab:plugin',
    description: 'A JupyterLab extension.',
    autoStart: true,
    requires: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.ICommandPalette],
    optional: [_jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_3__.ISettingRegistry, _jupyterlab_application__WEBPACK_IMPORTED_MODULE_0__.ILayoutRestorer, _jupyterlab_launcher__WEBPACK_IMPORTED_MODULE_2__.ILauncher],
    activate: (app, palette, settingRegistry, restorer, launcher) => {
        console.log('JupyterLab extension ggblab-0.0.1 is activated!');
        if (settingRegistry) {
            settingRegistry
                .load(plugin.id)
                .then(settings => {
                console.log('ggblab settings loaded:', settings.composite);
            })
                .catch(reason => {
                console.error('Failed to load settings for ggblab.', reason);
            });
        }
        const { commands } = app;
        const command = CommandIDs.create;
        commands.addCommand(command, {
            caption: 'Create a new React Widget',
            label: 'React Widget',
            icon: args => (args['isPalette'] ? undefined : _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_4__.reactIcon),
            execute: (args) => {
                console.log('socketPath:', args['socketPath']);
                const content = new _widget__WEBPACK_IMPORTED_MODULE_5__.GeoGebraWidget({
                    kernelId: args['kernelId'] || '',
                    commTarget: args['commTarget'] || '',
                    insertMode: args['insertMode'] || 'split-right',
                    socketPath: args['socketPath'] || '',
                    wsPort: args['wsPort'] || 8888,
                });
                const widget = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.MainAreaWidget({ content });
                widget.title.label = 'GeoGebra (' + (args['kernelId'] || '').substring(0, 8) + ')';
                widget.title.icon = _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_4__.reactIcon;
                app.shell.add(widget, 'main', {
                    mode: args['insertMode'] || 'insert-right',
                });
            }
        });
        palette.addItem({
            command,
            category: "Tutorial",
        });
        let tracker = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.WidgetTracker({
            namespace: "ggblab",
        });
        if (restorer) {
            restorer.restore(tracker, {
                command,
                name: () => "ggblab",
            });
        }
        if (launcher) {
            launcher.add({
                command,
                category: "example",
                rank: 1,
            });
        }
    }
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (plugin);


/***/ },

/***/ "./lib/widget.js"
/*!***********************!*\
  !*** ./lib/widget.js ***!
  \***********************/
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   GeoGebraWidget: () => (/* binding */ GeoGebraWidget)
/* harmony export */ });
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/ui-components */ "webpack/sharing/consume/default/@jupyterlab/ui-components");
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! react */ "webpack/sharing/consume/default/react");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @jupyterlab/services */ "webpack/sharing/consume/default/@jupyterlab/services");
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @jupyterlab/coreutils */ "webpack/sharing/consume/default/@jupyterlab/coreutils");
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_3__);


//import MetaTags from 'react-meta-tags';


//import { Message } from '@lumino/messaging';
/**
 * React component for a GeoGebra.
 *
 * @returns The React component
 */
const GGAComponent = (props) => {
    // const [kernels, setKernels] = React.useState<any[]>([]);
    const widgetRef = (0,react__WEBPACK_IMPORTED_MODULE_1__.useRef)(null);
    // const [size, setSize] = useState<{width: number; height: number}>({width: 800, height: 600});
    //   useEffect(() => {
    //     window.addEventListener('resize', () => {
    //     if (widgetRef.current) {
    //         setSize({
    //             width: widgetRef.current.offsetWidth,
    //             height: widgetRef.current.offsetHeight,
    //         });
    //         console.log("Resized to:", size.width, size.height);
    //     }
    //     });
    //   }, []);
    console.log(props.kernelId, props.commTarget, props.socketPath, props.wsPort);
    var applet = null;
    function isArrayOfArrays(value) {
        return Array.isArray(value) && value.every(subArray => Array.isArray(subArray));
    }
    /**
     * Calls a remote procedure on kernel2 to send a message via remote socket between kernel2 to kernel.
     * Executes Python code on kernel2 that sends the message through either a unix socket or websocket.
     *
     * Note on WebSocket Connection Handling:
     * Previous attempts to maintain persistent websocket connections using ping/pong (keep-alive)
     * were unsuccessful. Websocket connections established via kernel2.requestExecute() execute
     * within isolated contexts that are torn down immediately after the code execution completes.
     * Even with ping/pong mechanisms, connections would be disconnected once the kernel's
     * requestExecute() context ended. Therefore, the implementation creates new socket connections
     * for each message send operation, which is more reliable than attempting to maintain
     * persistent but fragile connections.
     *
     * @param kernel2 - The kernel to execute the remote procedure on
     * @param message - The message to send (as a JSON string)
     * @param socketPath - Optional unix socket path (if provided, uses unix socket; otherwise uses websocket)
     * @param wsUrl - WebSocket URL (used if socketPath is not provided)
     */
    async function callRemoteSocketSend(kernel2, message, socketPath, wsUrl) {
        if (socketPath) {
            await kernel2.requestExecute({ code: `
with unix_connect("${socketPath}") as ws:
    ws.send(r"""${message}""")
`
            }).done;
        }
        else {
            await kernel2.requestExecute({ code: `
with connect("${wsUrl}") as ws:
    ws.send(r"""${message}""")
`
            }).done;
        }
    }
    (0,react__WEBPACK_IMPORTED_MODULE_1__.useEffect)(() => {
        (async () => {
            return await _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__.KernelAPI.listRunning();
        })().then(async (kernels) => {
            // setKernels(kernels);
            console.log("Running kernels:", kernels);
            const baseUrl = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_3__.PageConfig.getBaseUrl();
            const token = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_3__.PageConfig.getToken();
            console.log(`Base URL: ${baseUrl}`);
            console.log(`Token: ${token}`);
            const settings = _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__.ServerConnection.makeSettings({
                baseUrl: baseUrl, //'http://localhost:8889/',
                token: token, //'7e89be30eb93ee7c149a839d4c7577e08c2c25b3c7f14647',
                appendToken: true,
            });
            const kernelManager = new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__.KernelManager({ serverSettings: settings });
            const kernel2 = await kernelManager.startNew({ name: 'python3' });
            console.log("Started new kernel:", kernel2, props.kernelId);
            await kernel2.requestExecute({ code: `from websockets.sync.client import unix_connect, connect` }).done;
            const wsUrl = `ws://localhost:${props.wsPort}/`;
            const socketPath = props.socketPath || null;
            const kernel = new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__.KernelConnection({
                model: { name: 'python3', id: props.kernelId || kernels[0]['id'] },
                serverSettings: settings,
            });
            console.log("Connected to kernel:", kernel);
            async function ggbOnLoad(api) {
                console.log("GeoGebra applet loaded:", api);
                var resize = function () {
                    const wrapperDiv = document.getElementById('ggb-element');
                    const parentDiv = wrapperDiv === null || wrapperDiv === void 0 ? void 0 : wrapperDiv.parentElement;
                    const width = parseInt((parentDiv === null || parentDiv === void 0 ? void 0 : parentDiv.style.width) || "800");
                    const height = parseInt((parentDiv === null || parentDiv === void 0 ? void 0 : parentDiv.style.height) || "600");
                    // console.log("Window resized:", width, height);
                    api.recalculateEnvironments();
                    api.setSize(width, height);
                };
                window.addEventListener('resize', resize);
                resize();
                const comm = kernel.createComm(props.commTarget || 'test');
                comm.open('HELO from GGB').done;
                // comm.send('HELO2').done
                // kernel.registerCommTarget('test', (comm, commMsg) => {
                // console.log("Comm opened from kernel with message:", commMsg['content']['data']);
                addEventListener('close', () => {
                    // comm.close().done;
                    // kernel.shutdown().catch(err => console.error(err));
                    kernel2.shutdown().catch(err => console.error(err));
                    console.log("Kernel and comm closed.");
                    window.removeEventListener('resize', resize);
                });
                comm.onMsg = async (msg) => {
                    console.log("Message received from server:", msg['content']['data']);
                    const command = JSON.parse(msg.content.data);
                    console.log("Parsed command:", command.type, command.payload);
                    var rmsg = null;
                    if (command.type === "command") {
                        var label = api.evalCommandGetLabels(command.payload); // GeoGebraにコマンドを適用
                        rmsg = JSON.stringify({
                            "type": "created",
                            "id": command.id,
                            "payload": label
                        }); // .replace(/'/g, "\\'");
                    }
                    else if (command.type === "function") {
                        var apiName = command.payload.name;
                        console.log(apiName);
                        var value = [];
                        // if (command.payload.args == null) {
                        //     value = api[apiName]();
                        // } else 
                        {
                            var args = command.payload.args;
                            value = [];
                            (Array.isArray(apiName) ? apiName : [apiName]).forEach((f) => {
                                console.log(f, args);
                                if (isArrayOfArrays(args)) {
                                    var value2 = [];
                                    args.forEach((arg2) => {
                                        if (args) {
                                            value2.push(api[f](...arg2) || null);
                                        }
                                        else {
                                            value2.push(api[f]() || null);
                                        }
                                    });
                                    value.push(value2);
                                }
                                else {
                                    if (args) {
                                        value.push(api[f](...args) || null);
                                    }
                                    else {
                                        value.push(api[f]() || null);
                                    }
                                }
                            });
                            value = (Array.isArray(apiName) ? value : value[0]);
                            console.log("Function value:", value);
                        }
                        rmsg = JSON.stringify({
                            "type": "value",
                            "id": command.id,
                            "payload": {
                                //"label": command.payload,
                                "value": value
                            }
                        }); // .replace(/'/g, "\\'");
                    }
                    comm.send(rmsg);
                    await callRemoteSocketSend(kernel2, rmsg, socketPath, wsUrl);
                };
                // var clientListener = function(data: any) {
                //  // console.log("Add listener triggered for:", data);
                //     var msg = {
                //         "type": "add",
                //         "payload": data,
                //     }
                //     console.log("Add detected:", JSON.stringify(msg));
                //     comm.send(JSON.stringify(msg));
                // }
                // api.registerClientListener(clientListener);
                var addListener = async function (data) {
                    // console.log("Add listener triggered for:", data);
                    var msg = {
                        "type": "add",
                        "payload": data, // {
                        // "label": data, 
                        // "details": {
                        //     "type": api.getObjectType(data),
                        //     "commandString": api.getCommandString(data, false),
                        //     "visible": api.getVisible(data),
                        //     "layer": api.getLayer(data),
                        // }
                        // }
                    };
                    // console.log("Add detected:", JSON.stringify(msg));
                    await callRemoteSocketSend(kernel2, JSON.stringify(msg), socketPath, wsUrl);
                };
                api.registerAddListener(addListener);
                var removeListener = async function (data) {
                    // console.log("Add listener triggered for:", data);
                    var msg = {
                        "type": "remove",
                        "payload": data,
                    };
                    // console.log("Remove detected:", JSON.stringify(msg));
                    await callRemoteSocketSend(kernel2, JSON.stringify(msg), socketPath, wsUrl);
                };
                api.registerRemoveListener(removeListener);
                var renameListener = async function (data) {
                    // console.log("Add listener triggered for:", data);
                    var msg = {
                        "type": "rename",
                        "payload": data,
                    };
                    // console.log("Rename detected:", JSON.stringify(msg));
                    await callRemoteSocketSend(kernel2, JSON.stringify(msg), socketPath, wsUrl);
                };
                api.registerRenameListener(renameListener);
                var clearListener = async function (data) {
                    // console.log("Add listener triggered for:", data);
                    var msg = {
                        "type": "clear",
                        "payload": data
                    };
                    // console.log("Rename detected:", JSON.stringify(msg));
                    await callRemoteSocketSend(kernel2, JSON.stringify(msg), socketPath, wsUrl);
                };
                api.registerClearListener(clearListener);
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        mutation.addedNodes.forEach((node) => {
                            try {
                                node.querySelectorAll('div.dialogMainPanel > div.dialogTitle').forEach((n) => {
                                    // console.log(n.textContent); 'Error'などのタイトルを検出
                                    node.querySelector('div.dialogContent')
                                        .querySelectorAll(`[class$='Label']`).forEach(async (n2) => {
                                        // console.log(n2.textContent);
                                        const msg = JSON.stringify({
                                            "type": n.textContent,
                                            "payload": n2.textContent
                                        });
                                        // comm.send(msg);
                                        await callRemoteSocketSend(kernel2, msg, socketPath, wsUrl);
                                    });
                                });
                            }
                            catch (e) {
                                // console.log(e, node);
                            }
                        });
                    });
                });
                observer.observe(document.body, { childList: true, subtree: true });
            }
            const metaViewport = document.createElement('meta');
            metaViewport.name = "viewport";
            metaViewport.content = "width=device-width, initial-scale=1";
            document.head.appendChild(metaViewport);
            const scriptTag = document.createElement('script');
            scriptTag.src = 'https://cdn.geogebra.org/apps/deployggb.js';
            scriptTag.async = true;
            scriptTag.onload = () => {
                const params = {
                    id: "ggbApplet", // アプレットのID
                    appName: "suite", // GeoGebra Classicスマートアプレットを指定
                    width: 800, // アプレットの横幅
                    height: 600, // アプレットの高さ
                    showToolBar: true, // ツールバーを表示
                    showAlgebraInput: false, // 入力フィールドを表示
                    showMenuBar: true, // メニューバーを表示
                    autoHeight: true,
                    // autoWidth: false,
                    // scale: 2,
                    allowUpscale: false,
                    appletOnLoad: ggbOnLoad
                };
                applet = new window.GGBApplet(params, true);
                applet.inject("ggb-element");
            };
            document.body.appendChild(scriptTag);
        });
        return () => {
            // コンポーネントのアンマウント時にスクリプトとアプレットをクリーンアップ
            // document.head.removeChild(scriptTag);
            if (applet) {
                console.log("Cleaning up GeoGebra applet.");
                // delete (window as any).applet;
                window.ggbApplet.remove();
                applet = null;
                delete window.GGBApplet;
            }
        };
    }, []);
    return (react__WEBPACK_IMPORTED_MODULE_1___default().createElement("div", { id: "ggb-element", ref: widgetRef, style: { width: "100%", height: "100%" } }));
};
/**
 * A GeoGebra Lumino Widget that wraps a GeoGebraComponent.
 */
class GeoGebraWidget extends _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.ReactWidget {
    /**
     * Constructs a new GeoGebraWidget.
     */
    constructor(props) {
        super();
        this.addClass('jp-ggblabWidget');
        this.props = props;
        // this.kernelId = props?.kernelId || '';
        // this.commTarget = props?.commTarget || '';
        // this.wsPort = props?.wsPort || 0;
        // this.socketPath = props?.socketPath || '';
    }
    render() {
        var _a, _b, _c, _d;
        return react__WEBPACK_IMPORTED_MODULE_1___default().createElement(GGAComponent, { kernelId: (_a = this.props) === null || _a === void 0 ? void 0 : _a.kernelId, commTarget: (_b = this.props) === null || _b === void 0 ? void 0 : _b.commTarget, wsPort: (_c = this.props) === null || _c === void 0 ? void 0 : _c.wsPort, socketPath: (_d = this.props) === null || _d === void 0 ? void 0 : _d.socketPath });
    }
    //   protected onCloseRequest(msg: Message): void {
    //     console.log("GeoGebraWidget is being closed.");
    //     super.onCloseRequest(msg);
    //     // this.dispose();
    //   }
    dispose() {
        console.log("GeoGebraWidget is being disposed.");
        window.dispatchEvent(new Event('close'));
        // delete(window.ggbApplet);
        super.dispose();
    }
}


/***/ }

}]);
//# sourceMappingURL=lib_index_js.bbfa36bc62ee08eb62b2.js.map