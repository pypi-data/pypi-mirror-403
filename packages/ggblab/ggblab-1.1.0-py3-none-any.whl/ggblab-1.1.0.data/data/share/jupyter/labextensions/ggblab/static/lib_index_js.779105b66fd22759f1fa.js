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
/* harmony import */ var _jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @jupyterlab/settingregistry */ "webpack/sharing/consume/default/@jupyterlab/settingregistry");
/* harmony import */ var _jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @jupyterlab/ui-components */ "webpack/sharing/consume/default/@jupyterlab/ui-components");
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _widget__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./widget */ "./lib/widget.js");
/* harmony import */ var _package_json__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ../package.json */ "./package.json");


// ILauncher removed: launcher integration is not used in this build

//import { DockLayout } from '@lumino/widgets';


// Import package.json to reflect the package version in the UI log.

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
    optional: [_jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_2__.ISettingRegistry, _jupyterlab_application__WEBPACK_IMPORTED_MODULE_0__.ILayoutRestorer],
    activate: (app, settingRegistry, restorer) => {
        console.log(`JupyterLab extension ggblab-${_package_json__WEBPACK_IMPORTED_MODULE_5__.version} is activated!`);
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
        // Tracker for created GeoGebra widgets so they can be restored after reload
        const tracker = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.WidgetTracker({
            namespace: 'ggblab-tracker'
        });
        const command = CommandIDs.create;
        commands.addCommand(command, {
            caption: 'Create a new React Widget',
            label: 'React Widget',
            icon: args => (args['isPalette'] ? undefined : _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3__.reactIcon),
            execute: async (args) => {
                console.log('socketPath:', args['socketPath']);
                // Precompute widget id so we can detect and remove any existing panel
                const idPart = (args['kernelId'] || '').substring(0, 8);
                const widgetId = `ggblab-${idPart}`;
                // If a widget with the same id exists, close and remove it first.
                try {
                    const existing = tracker.find((w) => w.id === widgetId);
                    if (existing) {
                        try {
                            existing.close();
                        }
                        catch (e) {
                            console.warn('Failed to close existing widget:', e);
                        }
                        try {
                            // tracker.remove may return a Promise
                            await tracker.remove(existing);
                        }
                        catch (e) {
                            // non-fatal
                            console.warn('Failed to remove existing widget from tracker:', e);
                        }
                    }
                }
                catch (e) {
                    // If tracker API differs, ignore and continue
                }
                const content = new _widget__WEBPACK_IMPORTED_MODULE_4__.GeoGebraWidget({
                    kernelId: args['kernelId'] || '',
                    commTarget: args['commTarget'] || '',
                    insertMode: args['insertMode'] || 'split-right',
                    socketPath: args['socketPath'] || '',
                    wsPort: args['wsPort'] || 8888
                });
                const widget = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.MainAreaWidget({ content });
                // make widget id unique so restorer can identify it later
                widget.id = widgetId;
                widget.title.label = `GeoGebra (${idPart})`;
                widget.title.icon = _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3__.reactIcon;
                // register with tracker so state will be saved for restoration
                try {
                    await tracker.add(widget);
                }
                catch (e) {
                    console.warn('Failed to add widget to tracker:', e);
                }
                app.shell.add(widget, 'main', {
                    mode: args['insertMode'] || 'split-right'
                });
            }
        });
        // palette.addItem({
        //   command,
        //   category: "Tutorial",
        // });
        if (restorer) {
            // Note: we may in future support restoring the applet's internal
            // state from an autosave (e.g. localStorage or a persistent store).
            // That would involve fetching a saved XML/Base64 snapshot and
            // passing it through `args` or a dedicated `initialXml` prop so the
            // recreated widget can rehydrate the GeoGebra applet.
            restorer.restore(tracker, {
                command,
                // use widget.id as the saved name so it is unique per widget
                name: widget => widget.id,
                // reconstruct args (kernelId) from the saved widget id so the
                // command can recreate the widget with the same kernel association
                args: widget => {
                    // Prefer to read the original creation props from the widget content
                    const content = (widget && widget.content) || {};
                    const p = content.props || {};
                    // Fallback to reconstructing kernelId from the widget id if not present
                    const id = widget.id || '';
                    const kernelId = p.kernelId ||
                        (id.startsWith('ggblab-') ? id.slice('ggblab-'.length) : '');
                    return {
                        kernelId,
                        commTarget: p.commTarget || '',
                        socketPath: p.socketPath || '',
                        wsPort: p.wsPort || 8888,
                        insertMode: p.insertMode || 'split-right'
                    };
                }
            });
        }
        // Launcher integration removed: no launcher item will be added.
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
/* eslint-disable */


//import MetaTags from 'react-meta-tags';


// Global typings are provided in src/declarations.d.ts; avoid duplicate declarations here.
/**
 * React component for a GeoGebra.
 *
 * @returns The React component
 */
const GGAComponent = (props) => {
    // const [kernels, setKernels] = React.useState<any[]>([]);
    const widgetRef = (0,react__WEBPACK_IMPORTED_MODULE_1__.useRef)(null);
    // const [size, setSize] = useState<{width: number; height: number}>({width: 800, height: 600});
    // // Listen to resize events to update size state
    // // but not working as expected in Lumino
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
    console.log("Component props: ", props.kernelId, props.commTarget, props.socketPath, props.wsPort);
    // window.dispatchEvent(new Event('resize'));
    const elementId = "ggb-element-" + ((props === null || props === void 0 ? void 0 : props.kernelId) || '').substring(0, 8);
    console.log("Element ID:", elementId);
    let applet = null;
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
    // Serialize outgoing socket sends to avoid kernel-side requestExecute jams.
    // `sendChain` is a promise chain that ensures each send completes before
    // the next begins. We also add a small inter-send delay to give the
    // remote helper kernel time to tear down connections.
    let sendChain = Promise.resolve();
    async function callRemoteSocketSend(kernel2, message, socketPath, wsUrl) {
        try {
            console.log("callRemoteSocketSend: sending message", { socketPath, wsUrl, messagePreview: message.slice(0, 200) });
            // Queue the actual send work on the chain so sends are serialized.
            const doSend = async () => {
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
                // small delay to give the helper kernel a moment to tear down
                // and to avoid immediate back-to-back requestExecute calls.
                await new Promise(resolve => setTimeout(resolve, 40));
            };
            // Append to chain and ensure errors don't break future sends.
            const next = sendChain.then(() => doSend());
            // swallow errors on chain so chain remains healthy
            sendChain = next.catch(() => { });
            await next;
            try {
                console.log("callRemoteSocketSend: sent", { idPreview: message.slice(0, 40) });
            }
            catch (e) { /* ignore */ }
        }
        catch (err) {
            try {
                console.error("callRemoteSocketSend: error sending message", err);
            }
            catch (e) { /* ignore */ }
            throw err;
        }
    }
    (0,react__WEBPACK_IMPORTED_MODULE_1__.useEffect)(() => {
        // Track resources created during effect so we can clean them up precisely
        let kernel2 = null;
        let kernelManager = null;
        let kernelConn = null;
        let comm = null;
        let observer = null;
        let resizeHandler = null;
        let closeHandler = null;
        let metaViewport = null;
        let scriptTag = null;
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
            kernelManager = new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__.KernelManager({ serverSettings: settings });
            kernel2 = await kernelManager.startNew({ name: 'python3' });
            console.log("Started new kernel:", kernel2, props.kernelId);
            await kernel2.requestExecute({ code: `from websockets.sync.client import unix_connect, connect` }).done;
            const wsUrl = `ws://localhost:${props.wsPort}/`;
            const socketPath = props.socketPath || null;
            kernelConn = new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__.KernelConnection({
                model: { name: 'python3', id: props.kernelId || kernels[0]['id'] },
                serverSettings: settings,
            });
            console.log("Connected to kernel:", kernelConn);
            async function ggbOnLoad(api) {
                console.log("GeoGebra applet loaded:", api);
                (async function () {
                    var msg = {
                        "type": "start",
                        "payload": {}
                    };
                    await callRemoteSocketSend(kernel2, JSON.stringify(msg), socketPath, wsUrl);
                })();
                resizeHandler = function () {
                    const wrapperDiv = document.getElementById(elementId);
                    const parentDiv = wrapperDiv === null || wrapperDiv === void 0 ? void 0 : wrapperDiv.parentElement;
                    const width = parseInt((parentDiv === null || parentDiv === void 0 ? void 0 : parentDiv.style.width) || "800");
                    const height = parseInt((parentDiv === null || parentDiv === void 0 ? void 0 : parentDiv.style.height) || "600");
                    api.recalculateEnvironments();
                    api.setSize(width, height);
                };
                window.addEventListener('resize', resizeHandler);
                resizeHandler();
                // // Observe size changes of the widget's DOM element
                // // but not working as expected in Lumino
                // const widgetElemnt = window.document.querySelector('div.lm-DockPanel-widget');
                // const widgetElemnt = window.document.querySelector('div.lm-SplitPanel-child');
                // const widgetElemnt = window.document.querySelector('div[class*="Panel"]');
                // if (widgetElemnt) {
                // if (widgetRef.current) {
                //     const resizeObserver = new ResizeObserver(() => {
                //         console.log("Panel resized.");
                //         resize();
                //     });
                //     resizeObserver.observe(widgetRef.current); //widgetElemnt);
                // }
                comm = kernelConn.createComm(props.commTarget || 'test');
                comm.open('HELO from GGB').done;
                // comm.send('HELO2').done
                // kernel.registerCommTarget('test', (comm, commMsg) => {
                // console.log("Comm opened from kernel with message:", commMsg['content']['data']);
                closeHandler = () => {
                    var _a;
                    // Attempt to close comm and shutdown helper kernel
                    try {
                        (_a = comm === null || comm === void 0 ? void 0 : comm.close) === null || _a === void 0 ? void 0 : _a.call(comm);
                    }
                    catch (e) {
                        console.error(e);
                    }
                    kernel2 === null || kernel2 === void 0 ? void 0 : kernel2.shutdown().catch((err) => console.error(err));
                    console.log("Kernel and comm closed.");
                    if (resizeHandler)
                        window.removeEventListener('resize', resizeHandler);
                };
                window.addEventListener('close', closeHandler);
                comm.onMsg = async (msg) => {
                    console.log("Message received from server:", msg['content']['data']);
                    const command = JSON.parse(msg.content.data);
                    console.log("Parsed command:", command.type, command.payload);
                    var rmsg = null;
                    if (command.type === "command") {
                        var label = api.evalCommandGetLabels(command.payload);
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
                var addListener = async function (data) {
                    // console.log("Add listener triggered for:", data);
                    var msg = {
                        "type": "add",
                        "payload": data,
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
                // // nothing triggered?
                // var clientListener = async function(data: any) {
                // // console.log("Add listener triggered for:", data);
                //     var msg = {
                //         "type": "client",
                //         "payload": data
                //     }
                //     console.log("Client detected:", JSON.stringify(msg));
                //     await callRemoteSocketSend(kernel2, JSON.stringify(msg), socketPath, wsUrl);
                // }
                // api.registerClearListener(clientListener);
                observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        mutation.addedNodes.forEach((node) => {
                            try {
                                node.querySelectorAll('div.dialogMainPanel > div.dialogTitle').forEach((n) => {
                                    // console.log(n.textContent); detect titles like 'Error'
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
            // Avoid duplicate meta/script inserts: reuse if already present
            const existingMeta = document.getElementById('ggblab-viewport-meta');
            if (existingMeta) {
                metaViewport = existingMeta;
            }
            else {
                metaViewport = document.createElement('meta');
                metaViewport.id = 'ggblab-viewport-meta';
                metaViewport.name = "viewport";
                metaViewport.content = "width=device-width, initial-scale=1";
                document.head.appendChild(metaViewport);
            }
            const existingScript = document.getElementById('ggblab-deployggb-script');
            const createApplet = () => {
                const params = {
                    id: "ggbApplet" + ((props === null || props === void 0 ? void 0 : props.kernelId) || '').substring(0, 8), // applet ID
                    appName: "suite", // specify GeoGebra Classic smart applet
                    width: 800, // applet width
                    height: 600, // applet height
                    showToolBar: true, // show the toolbar
                    showAlgebraInput: false, // show algebra input field
                    showMenuBar: true, // show the menu bar
                    autoHeight: true,
                    scaleContainerClass: "lm-Panel", // "lm-DockPanel-widget",
                    // autoWidth: false,
                    // scale: 2,
                    allowUpscale: false,
                    appletOnLoad: ggbOnLoad
                };
                applet = new window.GGBApplet(params, true);
                applet.inject(elementId);
            };
            if (existingScript) {
                scriptTag = existingScript;
                // If script already loaded and GGBApplet is available, instantiate immediately
                if (window.GGBApplet) {
                    createApplet();
                }
                else {
                    // Otherwise ensure we call createApplet once it loads
                    scriptTag.addEventListener('load', createApplet, { once: true });
                }
            }
            else {
                scriptTag = document.createElement('script');
                scriptTag.id = 'ggblab-deployggb-script';
                scriptTag.src = 'https://cdn.geogebra.org/apps/deployggb.js';
                scriptTag.async = true;
                scriptTag.onload = createApplet;
                document.body.appendChild(scriptTag);
            }
        });
        return () => {
            // Remove resize listener
            if (resizeHandler) {
                window.removeEventListener('resize', resizeHandler);
                resizeHandler = null;
            }
            // Remove close listener
            if (closeHandler) {
                window.removeEventListener('close', closeHandler);
                closeHandler = null;
            }
            // Disconnect mutation observer
            if (observer) {
                try {
                    observer.disconnect();
                }
                catch (e) {
                    console.error(e);
                }
                observer = null;
            }
            // Remove injected meta tag
            if (metaViewport && metaViewport.parentNode) {
                metaViewport.parentNode.removeChild(metaViewport);
                metaViewport = null;
            }
            // Remove injected script tag
            if (scriptTag && scriptTag.parentNode) {
                scriptTag.parentNode.removeChild(scriptTag);
                scriptTag = null;
            }
            // Clean up GeoGebra applet
            if (applet) {
                try {
                    console.log("Cleaning up GeoGebra applet.");
                    window.ggbApplet.remove();
                }
                catch (e) {
                    console.error(e);
                }
                applet = null;
                try {
                    delete window.GGBApplet;
                }
                catch (_a) { }
            }
            // Close comm and shutdown helper kernel asynchronously
            (async () => {
                var _a, _b;
                try {
                    if (comm) {
                        try {
                            (_a = comm.close) === null || _a === void 0 ? void 0 : _a.call(comm);
                        }
                        catch (e) {
                            console.error(e);
                        }
                        comm = null;
                    }
                    if (kernel2) {
                        await kernel2.shutdown();
                        kernel2 = null;
                    }
                    if (kernelManager) {
                        try {
                            await ((_b = kernelManager.shutdown) === null || _b === void 0 ? void 0 : _b.call(kernelManager));
                        }
                        catch (e) { /* ignore */ }
                        kernelManager = null;
                    }
                }
                catch (e) {
                    console.error('Error during cleanup:', e);
                }
            })();
        };
    }, []);
    return (react__WEBPACK_IMPORTED_MODULE_1___default().createElement("div", { id: elementId, ref: widgetRef, style: { width: "100%", height: "100%" } }));
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
    }
    render() {
        var _a, _b, _c, _d;
        return react__WEBPACK_IMPORTED_MODULE_1___default().createElement(GGAComponent, { kernelId: (_a = this.props) === null || _a === void 0 ? void 0 : _a.kernelId, commTarget: (_b = this.props) === null || _b === void 0 ? void 0 : _b.commTarget, wsPort: (_c = this.props) === null || _c === void 0 ? void 0 : _c.wsPort, socketPath: (_d = this.props) === null || _d === void 0 ? void 0 : _d.socketPath });
    }
    // only onResize is responsible for size changes in Lumino,
    // but onAfterAttach and onAfterShow and onFitRequest may also be relevant in some cases.
    onResize(msg) {
        // console.log("GeoGebraWidget resized:", msg.width, msg.height);
        window.dispatchEvent(new Event('resize'));
        super.onResize(msg);
    }
    // Only perform cleanup when the widget is explicitly closed by the user.
    // Use onCloseRequest to trigger cleanup so that transient disposals
    // during layout/restore operations do not tear down the internal state.
    onCloseRequest(msg) {
        console.log('GeoGebraWidget onCloseRequest — performing cleanup.');
        window.dispatchEvent(new Event('close'));
        super.onCloseRequest(msg);
    }
    // dispose should not trigger cleanup again; allow normal disposal to proceed
    // without duplicating shutdown logic.
    dispose() {
        console.log('GeoGebraWidget disposed.');
        super.dispose();
    }
}
// // Example of attaching the GeoGebraWidget to a DockPanel
// // but commented out to avoid automatic execution.
// const dock = new DockPanel();
// ReactWidget.attach(dock, document.body);
// // window.addEventListener('resize', () => { dock.update(); });
// dock.layoutModified.connect(() => { 
//     console.log("Dock layout modified.");
//     dock.update(); 
// });


/***/ },

/***/ "./package.json"
/*!**********************!*\
  !*** ./package.json ***!
  \**********************/
(module) {

module.exports = /*#__PURE__*/JSON.parse('{"name":"ggblab","version":"1.1.0","description":"A JupyterLab extension for learning geometry and Python programming side-by-side with GeoGebra.","keywords":["jupyter","jupyterlab","jupyterlab-extension"],"homepage":"https://github.com/moyhig-ecs/ggblab#readme","bugs":{"url":"https://github.com/moyhig-ecs/ggblab/issues"},"license":"BSD-3-Clause","author":{"name":"Manabu Higashida","email":"manabu@higashida.net"},"files":["lib/**/*.{d.ts,eot,gif,html,jpg,js,js.map,json,png,svg,woff2,ttf}","style/**/*.{css,js,eot,gif,html,jpg,json,png,svg,woff2,ttf}","src/**/*.{ts,tsx}","schema/*.json"],"main":"lib/index.js","types":"lib/index.d.ts","style":"style/index.css","repository":{"type":"git","url":"https://github.com/moyhig-ecs/ggblab"},"scripts":{"build":"jlpm build:lib && jlpm build:labextension:dev","build:prod":"jlpm clean && jlpm build:lib:prod && jlpm build:labextension","build:labextension":"jupyter labextension build .","build:labextension:dev":"jupyter labextension build --development True .","build:lib":"tsc --sourceMap","build:lib:prod":"tsc","clean":"jlpm clean:lib","clean:lib":"rimraf lib tsconfig.tsbuildinfo","clean:lintcache":"rimraf .eslintcache .stylelintcache","clean:labextension":"rimraf ggblab/labextension ggblab/_version.py","clean:all":"jlpm clean:lib && jlpm clean:labextension && jlpm clean:lintcache","eslint":"jlpm eslint:check --fix","eslint:check":"eslint . --cache --ext .ts,.tsx","install:extension":"jlpm build","lint":"jlpm stylelint && jlpm prettier && jlpm eslint","lint:check":"jlpm stylelint:check && jlpm prettier:check && jlpm eslint:check","prettier":"jlpm prettier:base --write --list-different","prettier:base":"prettier \\"**/*{.ts,.tsx,.js,.jsx,.css,.json,.md}\\"","prettier:check":"jlpm prettier:base --check","stylelint":"jlpm stylelint:check --fix","stylelint:check":"stylelint --cache \\"style/**/*.css\\"","test":"jest --coverage","watch":"run-p watch:src watch:labextension","watch:src":"tsc -w --sourceMap","watch:labextension":"jupyter labextension watch ."},"dependencies":{"@jupyterlab/application":"^4.0.0","@jupyterlab/apputils":"^4.6.1","@jupyterlab/launcher":"^4.5.1","@jupyterlab/settingregistry":"^4.0.0","@lumino/widgets":"^2.7.2","@marshallku/react-postscribe":"^0.2.0","react-meta-tags":"^1.0.1"},"devDependencies":{"@jupyterlab/builder":"^4.0.0","@jupyterlab/testutils":"^4.0.0","@types/jest":"^29.2.0","@types/json-schema":"^7.0.11","@types/react":"^18.0.26","@types/react-addons-linked-state-mixin":"^0.14.22","@typescript-eslint/eslint-plugin":"^6.1.0","@typescript-eslint/parser":"^6.1.0","css-loader":"^6.7.1","eslint":"^8.36.0","eslint-config-prettier":"^8.8.0","eslint-plugin-prettier":"^5.0.0","jest":"^29.2.0","npm-run-all2":"^7.0.1","prettier":"^3.0.0","rimraf":"^5.0.1","source-map-loader":"^1.0.2","style-loader":"^3.3.1","stylelint":"^15.10.1","stylelint-config-recommended":"^13.0.0","stylelint-config-standard":"^34.0.0","stylelint-csstree-validator":"^3.0.0","stylelint-prettier":"^4.0.0","typescript":"~5.5.4","yjs":"^13.5.0"},"resolutions":{"lib0":"0.2.111"},"sideEffects":["style/*.css","style/index.js"],"styleModule":"style/index.js","publishConfig":{"access":"public"},"jupyterlab":{"extension":true,"outputDir":"ggblab/labextension","schemaDir":"schema"},"eslintIgnore":["node_modules","dist","coverage","**/*.d.ts","tests","**/__tests__","ui-tests"],"eslintConfig":{"extends":["eslint:recommended","plugin:@typescript-eslint/eslint-recommended","plugin:@typescript-eslint/recommended","plugin:prettier/recommended"],"parser":"@typescript-eslint/parser","parserOptions":{"project":"tsconfig.json","sourceType":"module"},"plugins":["@typescript-eslint"],"rules":{"@typescript-eslint/naming-convention":["error",{"selector":"interface","format":["PascalCase"],"custom":{"regex":"^I[A-Z]","match":true}}],"@typescript-eslint/no-unused-vars":["warn",{"args":"none"}],"@typescript-eslint/no-explicit-any":"off","@typescript-eslint/no-namespace":"off","@typescript-eslint/no-use-before-define":"off","@typescript-eslint/quotes":["error","single",{"avoidEscape":true,"allowTemplateLiterals":false}],"curly":["error","all"],"eqeqeq":"error","prefer-arrow-callback":"error"}},"prettier":{"singleQuote":true,"trailingComma":"none","arrowParens":"avoid","endOfLine":"auto","overrides":[{"files":"package.json","options":{"tabWidth":4}}]},"stylelint":{"extends":["stylelint-config-recommended","stylelint-config-standard","stylelint-prettier/recommended"],"plugins":["stylelint-csstree-validator"],"rules":{"csstree/validator":true,"property-no-vendor-prefix":null,"selector-class-pattern":"^([a-z][A-z\\\\d]*)(-[A-z\\\\d]+)*$","selector-no-vendor-prefix":null,"value-no-vendor-prefix":null}}}');

/***/ }

}]);
//# sourceMappingURL=lib_index_js.779105b66fd22759f1fa.js.map