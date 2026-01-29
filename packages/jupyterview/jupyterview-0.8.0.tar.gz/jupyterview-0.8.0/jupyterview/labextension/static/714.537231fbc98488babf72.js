(self["webpackChunkjupyterview"] = self["webpackChunkjupyterview"] || []).push([[714],{

/***/ 1234
() {

/* (ignored) */

/***/ },

/***/ 3996
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
// ESM COMPAT FLAG
__webpack_require__.r(__webpack_exports__);

// EXPORTS
__webpack_require__.d(__webpack_exports__, {
  "default": () => (/* binding */ lib)
});

// EXTERNAL MODULE: consume shared module (default) @jupyterlab/application@^4.5.3 (singleton)
var application_4_5_singleton_ = __webpack_require__(9986);
// EXTERNAL MODULE: consume shared module (default) @jupyterlab/apputils@^4.6.3 (singleton)
var apputils_4_6_singleton_ = __webpack_require__(5285);
// EXTERNAL MODULE: consume shared module (default) @lumino/algorithm@^2.0.0 (singleton)
var algorithm_2_0_singleton_ = __webpack_require__(4053);
// EXTERNAL MODULE: consume shared module (default) @lumino/coreutils@^2.0.0 (singleton)
var coreutils_2_0_singleton_ = __webpack_require__(7262);
;// ./lib/kernel.js


const KERNEL_NAME = 'JupyterView Kernel';
class KernelExecutor {
    constructor(options) {
        this.options = options;
        this._kernelStarted = false;
    }
    async startKernel() {
        var _a;
        if (this._kernelStarted) {
            return;
        }
        const sessionManager = this.options.manager.sessions;
        await sessionManager.ready;
        await sessionManager.refreshRunning();
        const model = (0,algorithm_2_0_singleton_.find)(sessionManager.running(), item => {
            return item.name === KERNEL_NAME;
        });
        if (model) {
            this._sessionConnection = sessionManager.connectTo({ model });
        }
        else {
            await this.options.manager.kernelspecs.ready;
            const specs = this.options.manager.kernelspecs.specs;
            this._sessionConnection = await sessionManager.startNew({
                name: KERNEL_NAME,
                path: coreutils_2_0_singleton_.UUID.uuid4(),
                kernel: {
                    name: specs.default
                },
                type: 'notebook'
            });
            const kernelModel = {
                name: specs.kernelspecs[specs.default].name
            };
            await this._sessionConnection.changeKernel(kernelModel);
        }
        (_a = this._sessionConnection.kernel) === null || _a === void 0 ? void 0 : _a.disposed.connect(() => (this._kernelStarted = false));
        this._kernelStarted = true;
    }
    codeGenerator(filePath) {
        if (filePath.startsWith('RTC:')) {
            filePath = filePath.split(':')[1];
        }
        const writeFile = `
      try:
        import piplite
        await piplite.install('meshio')
      except:
        pass
      import base64,  meshio, tempfile 
      mesh = meshio.read("${filePath}")
      c = tempfile.NamedTemporaryFile(delete=False)
      try:
        ext = 0
        mesh.write(c.name,'vtu')
      except:
        ext = 1
        mesh.write(c.name,'vtk')
      with open(c.name,'rb') as f:
          content = f.read()
      c.close()
      try:
        os.remove("${filePath}")
        os.remove(c.name)
      except:
        pass
      base64_bytes = base64.b64encode(content)
      {ext: base64_bytes}
      `;
        return writeFile;
    }
    fileGenerator(filePath, content) {
        const ext = filePath.split('.').pop();
        const code = `
    import base64, tempfile
    tempPath = tempfile.NamedTemporaryFile(suffix=".${ext}",delete=False)
    message = """${content}"""
    base64_bytes = message.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    with open(tempPath.name, 'wb') as f:
      f.write(message_bytes)
    tempPath.name
    `;
        return { ext, code };
    }
    async executeCode(code) {
        var _a;
        const kernel = (_a = this._sessionConnection) === null || _a === void 0 ? void 0 : _a.kernel;
        if (!kernel) {
            throw new Error('Session has no kernel.');
        }
        return new Promise((resolve, reject) => {
            const future = kernel.requestExecute(code, false, undefined);
            future.onIOPub = (msg) => {
                const msgType = msg.header.msg_type;
                if (msgType === 'execute_result') {
                    const content = msg.content.data['text/plain'];
                    resolve(content);
                }
                else if (msgType === 'error') {
                    console.error('Kernel operation failed', msg.content);
                    reject(msg.content);
                }
            };
        });
    }
    async convertFile(filePath, fileContent) {
        var _a;
        const stopOnError = true;
        let path = filePath;
        const kernel = (_a = this._sessionConnection) === null || _a === void 0 ? void 0 : _a.kernel;
        if (!kernel) {
            throw new Error('Session has no kernel.');
        }
        if (this.options.jupyterLite) {
            const fileGeneratorCode = this.fileGenerator(filePath, fileContent);
            const tempPath = await this.executeCode({ code: fileGeneratorCode.code });
            path = tempPath.slice(1, -1);
        }
        const code = this.codeGenerator(path);
        const content = {
            code,
            stop_on_error: stopOnError
        };
        const promise = this.executeCode(content).then(content => {
            const type = content[1] === '0' ? 'vtu' : 'vtk';
            const binary = content.slice(6, -2);
            return { type, binary };
        });
        return promise;
    }
    dispose() {
        this._sessionConnection.dispose();
    }
}

// EXTERNAL MODULE: consume shared module (default) @jupyterlab/docregistry@^4.5.3
var docregistry_4_5 = __webpack_require__(3638);
// EXTERNAL MODULE: consume shared module (default) @lumino/signaling@^2.0.0 (singleton)
var signaling_2_0_singleton_ = __webpack_require__(4602);
// EXTERNAL MODULE: consume shared module (default) @jupyter/ydoc@^3.0.0-a3 (singleton)
var ydoc_3_0_0_a3_singleton_ = __webpack_require__(8000);
;// ./lib/mainview/model.js


class JupyterViewModel {
    constructor(options) {
        this.collaborative = false;
        this._onCameraChanged = () => {
            const clients = this.sharedModel.awareness.getStates();
            this._cameraChanged.emit(clients);
        };
        this.defaultKernelName = '';
        this.defaultKernelLanguage = '';
        this._dirty = false;
        this._readOnly = true;
        this._isDisposed = false;
        this._contentChanged = new signaling_2_0_singleton_.Signal(this);
        this._stateChanged = new signaling_2_0_singleton_.Signal(this);
        this._themeChanged = new signaling_2_0_singleton_.Signal(this);
        this._cameraChanged = new signaling_2_0_singleton_.Signal(this);
        const { sharedModel } = options;
        if (sharedModel) {
            this._sharedModel = sharedModel;
        }
        else {
            this._sharedModel = JupyterViewDoc.create();
        }
        this._sharedModel.awareness.on('change', this._onCameraChanged);
    }
    get sharedModel() {
        return this._sharedModel;
    }
    get isDisposed() {
        return this._isDisposed;
    }
    get contentChanged() {
        return this._contentChanged;
    }
    get stateChanged() {
        return this._stateChanged;
    }
    get themeChanged() {
        return this._themeChanged;
    }
    dispose() {
        if (this._isDisposed) {
            return;
        }
        this._isDisposed = true;
        signaling_2_0_singleton_.Signal.clearData(this);
    }
    get dirty() {
        return this._dirty;
    }
    set dirty(value) {
        this._dirty = value;
    }
    get readOnly() {
        return this._readOnly;
    }
    set readOnly(value) {
        this._readOnly = true;
    }
    toString() {
        const content = this.sharedModel.getContent('content');
        if (content && content.length > 0) {
            return content;
        }
        else {
            throw Error('Content not found');
        }
    }
    fromString(data) {
        this.sharedModel.transact(() => {
            this.sharedModel.setContent('content', data);
        });
    }
    toJSON() {
        return {};
    }
    fromJSON(data) {
        /** */
    }
    initialize() {
        this.sharedModel.setContent('backup', this.sharedModel.getContent('content'));
    }
    syncCamera(pos) {
        this.sharedModel.awareness.setLocalStateField('mouse', pos);
    }
    getClientId() {
        return this.sharedModel.awareness.clientID;
    }
    get cameraChanged() {
        return this._cameraChanged;
    }
    getKernel() {
        return JupyterViewModel.kernel;
    }
}
class JupyterViewDoc extends ydoc_3_0_0_a3_singleton_.YDocument {
    constructor() {
        super();
        /**
         * Document version
         */
        this.version = '1.0.0';
        this._mainViewStateObserver = (event) => {
            const changes = {};
            event.keysChanged.forEach(key => {
                changes[key] = this.getMainViewStateByKey(key);
            });
            this._mainViewStateChanged.emit(changes);
        };
        this._controlViewStateObserver = (event) => {
            const changes = {};
            event.keysChanged.forEach(key => {
                changes[key] = this.getControlViewStateByKey(key);
            });
            this._controlViewStateChanged.emit(changes);
        };
        this._mainViewStateChanged = new signaling_2_0_singleton_.Signal(this);
        this._controlViewStateChanged = new signaling_2_0_singleton_.Signal(this);
        this._content = this.ydoc.getMap('content');
        this._mainViewState = this.ydoc.getMap('mainViewState');
        this._mainViewState.observe(this._mainViewStateObserver);
        this._controlViewState = this.ydoc.getMap('controlViewState');
        this._controlViewState.observe(this._controlViewStateObserver);
    }
    dispose() {
        this._mainViewState.unobserve(this._mainViewStateObserver);
        this._controlViewState.unobserve(this._controlViewStateObserver);
    }
    getSource() {
        return this._content.toJSON();
    }
    setSource(source) {
        let value;
        if (!source) {
            return;
        }
        if (typeof source === 'string') {
            value = JSON.parse(source);
        }
        else {
            value = source;
        }
        this.transact(() => {
            Object.entries(value).forEach(([key, value]) => {
                this._content.set(key, value);
            });
        });
    }
    static create() {
        return new JupyterViewDoc();
    }
    get mainViewStateChanged() {
        return this._mainViewStateChanged;
    }
    get controlViewStateChanged() {
        return this._controlViewStateChanged;
    }
    getContent(key) {
        return this._content.get(key);
    }
    setContent(key, value) {
        this._content.set(key, value);
    }
    getMainViewState() {
        const ret = {};
        for (const key of this._mainViewState.keys()) {
            ret[key] = this._mainViewState.get(key);
        }
        return ret;
    }
    getMainViewStateByKey(key) {
        return this._mainViewState.get(key);
    }
    setMainViewState(payload) {
        this.transact(() => {
            for (const key in payload) {
                this._mainViewState.set(key, payload[key]);
            }
        });
    }
    getControlViewState() {
        const ret = {};
        for (const key of this._controlViewState.keys()) {
            ret[key] = this._controlViewState.get(key);
        }
        return ret;
    }
    getControlViewStateByKey(key) {
        return this._controlViewState.get(key);
    }
    setControlViewState(payload) {
        this.transact(() => {
            for (const key in payload) {
                this._controlViewState.set(key, payload[key]);
            }
        });
    }
}

// EXTERNAL MODULE: consume shared module (default) react@^18.2.0 (singleton)
var consume_shared_module_default_react_18_2_singleton_ = __webpack_require__(3345);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Rendering/OpenGL/Profiles/All.js + 56 modules
var All = __webpack_require__(4678);
// EXTERNAL MODULE: ./node_modules/itk/readPolyDataArrayBuffer.js + 1 modules
var readPolyDataArrayBuffer = __webpack_require__(7392);
// EXTERNAL MODULE: consume shared module (default) uuid@^8.3.2 (strict) (fallback: ./node_modules/uuid/dist/esm-browser/index.js)
var index_js_ = __webpack_require__(1422);
// EXTERNAL MODULE: consume shared module (default) @jupyterlab/services@^7.5.3 (singleton)
var services_7_5_singleton_ = __webpack_require__(1125);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Common/Core/Math.js
var Core_Math = __webpack_require__(2973);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Common/Core/MatrixBuilder.js
var MatrixBuilder = __webpack_require__(2871);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Filters/General/WarpScalar.js
var WarpScalar = __webpack_require__(1638);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Interaction/Widgets/OrientationMarkerWidget.js + 1 modules
var OrientationMarkerWidget = __webpack_require__(9718);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Rendering/Core/Actor.js + 1 modules
var Actor = __webpack_require__(2526);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Rendering/Core/AxesActor.js + 4 modules
var AxesActor = __webpack_require__(1280);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Rendering/Core/ColorTransferFunction.js + 1 modules
var ColorTransferFunction = __webpack_require__(547);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Rendering/Core/ColorTransferFunction/ColorMaps.js + 1 modules
var ColorMaps = __webpack_require__(4995);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Rendering/Core/Mapper.js + 4 modules
var Mapper = __webpack_require__(948);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Rendering/Core/Mapper/Constants.js
var Constants = __webpack_require__(8689);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Rendering/Core/ScalarBarActor.js
var ScalarBarActor = __webpack_require__(8924);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Rendering/Misc/RenderWindowWithControlBar.js + 13 modules
var RenderWindowWithControlBar = __webpack_require__(7137);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/vtk.js
var vtk = __webpack_require__(4594);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Widgets/Core/WidgetManager.js + 3 modules
var WidgetManager = __webpack_require__(3317);
// EXTERNAL MODULE: ./node_modules/@kitware/vtk.js/Widgets/Widgets3D/InteractiveOrientationWidget.js + 22 modules
var InteractiveOrientationWidget = __webpack_require__(8845);
// EXTERNAL MODULE: consume shared module (default) @jupyterlab/ui-components@^4.5.3 (singleton)
var ui_components_4_5_singleton_ = __webpack_require__(3391);
;// ./style/icons/jvc-light.svg
const jvc_light_namespaceObject = "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"256\" height=\"256\" viewBox=\"0 0 100 100\"><rect width=\"100\" height=\"100\" rx=\"50\" fill=\"#242454\"></rect><path fill=\"#fff\" d=\"M29.71 26.55L29.71 26.55Q30.10 26.40 30.90 26.21Q31.71 26.01 32.56 26.01L32.56 26.01Q35.95 26.01 35.95 28.86L35.95 28.86L35.95 61.82Q35.95 65.28 34.95 67.63Q33.95 69.98 32.21 71.41Q30.48 72.83 28.21 73.45Q25.94 74.06 23.47 74.06L23.47 74.06Q19.08 74.06 17.08 73.02Q15.08 71.98 15.08 70.29L15.08 70.29Q15.08 69.21 15.54 68.44Q16.00 67.67 16.39 67.29L16.39 67.29Q17.54 67.83 19.16 68.29Q20.78 68.75 22.55 68.75L22.55 68.75Q26.01 68.75 27.86 67.09Q29.71 65.44 29.71 61.51L29.71 61.51L29.71 26.55ZM69.52 72.60L69.52 72.60Q69.13 72.98 68.06 73.29Q66.98 73.60 65.67 73.60L65.67 73.60Q64.21 73.60 63.05 73.18Q61.90 72.75 61.51 71.91L61.51 71.91Q60.51 69.90 59.16 66.75Q57.82 63.59 56.31 59.70Q54.81 55.81 53.23 51.50Q51.66 47.19 50.19 42.95Q48.73 38.72 47.42 34.75Q46.11 30.79 45.19 27.63L45.19 27.63Q45.65 27.02 46.57 26.48Q47.50 25.94 48.65 25.94L48.65 25.94Q50.12 25.94 50.81 26.63Q51.50 27.32 51.96 28.71L51.96 28.71Q55.43 38.80 58.59 48.19Q61.74 57.58 65.52 67.29L65.52 67.29L65.82 67.29Q67.52 62.90 69.33 57.93Q71.14 52.96 72.87 47.69Q74.60 42.42 76.26 37.03Q77.91 31.64 79.22 26.48L79.22 26.48Q80.22 25.94 81.84 25.94L81.84 25.94Q83.23 25.94 84.07 26.63Q84.92 27.32 84.92 28.71L84.92 28.71Q84.92 29.86 84.03 33.06Q83.15 36.26 81.76 40.49Q80.38 44.73 78.64 49.58Q76.91 54.43 75.22 58.89Q73.52 63.36 71.98 67.06Q70.44 70.75 69.52 72.60Z\"></path></svg>";
;// ./style/icons/rotate_right_white_24dp.svg
const rotate_right_white_24dp_namespaceObject = "<svg xmlns=\"http://www.w3.org/2000/svg\" height=\"18px\" viewBox=\"0 0 24 24\" width=\"18px\" fill=\"#BBBBBB\"><path d=\"M0 0h24v24H0V0z\" fill=\"none\"/><path d=\"M15.55 5.55L11 1v3.07C7.06 4.56 4 7.92 4 12s3.05 7.44 7 7.93v-2.02c-2.84-.48-5-2.94-5-5.91s2.16-5.43 5-5.91V10l4.55-4.45zM19.93 11c-.17-1.39-.72-2.73-1.62-3.89l-1.42 1.42c.54.75.88 1.6 1.02 2.47h2.02zM13 17.9v2.02c1.39-.17 2.74-.71 3.9-1.61l-1.44-1.44c-.75.54-1.59.89-2.46 1.03zm3.89-2.42l1.42 1.41c.9-1.16 1.45-2.5 1.62-3.89h-2.02c-.14.87-.48 1.72-1.02 2.48z\"/></svg>";
;// ./style/icons/rotate_left_white_24dp.svg
const rotate_left_white_24dp_namespaceObject = "<svg xmlns=\"http://www.w3.org/2000/svg\" height=\"18px\" viewBox=\"0 0 24 24\" width=\"18px\" fill=\"#BBBBBB\"><path d=\"M0 0h24v24H0V0z\" fill=\"none\"/><path d=\"M7.11 8.53L5.7 7.11C4.8 8.27 4.24 9.61 4.07 11h2.02c.14-.87.49-1.72 1.02-2.47zM6.09 13H4.07c.17 1.39.72 2.73 1.62 3.89l1.41-1.42c-.52-.75-.87-1.59-1.01-2.47zm1.01 5.32c1.16.9 2.51 1.44 3.9 1.61V17.9c-.87-.15-1.71-.49-2.46-1.03L7.1 18.32zM13 4.07V1L8.45 5.55 13 10V6.09c2.84.48 5 2.94 5 5.91s-2.16 5.43-5 5.91v2.02c3.95-.49 7-3.85 7-7.93s-3.05-7.44-7-7.93z\"/></svg>";
;// ./style/icons/center_focus_weak_white_24dp.svg
const center_focus_weak_white_24dp_namespaceObject = "<svg xmlns=\"http://www.w3.org/2000/svg\" height=\"18px\" viewBox=\"0 0 24 24\" width=\"18px\" fill=\"#BBBBBB\"><path d=\"M0 0h24v24H0V0z\" fill=\"none\"/><path d=\"M5 15H3v4c0 1.1.9 2 2 2h4v-2H5v-4zM5 5h4V3H5c-1.1 0-2 .9-2 2v4h2V5zm7 3c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm0 6c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm7-11h-4v2h4v4h2V5c0-1.1-.9-2-2-2zm0 16h-4v2h4c1.1 0 2-.9 2-2v-4h-2v4z\"/></svg>";
;// ./lib/tools.js






const jvcLightIcon = new ui_components_4_5_singleton_.LabIcon({
    name: 'jupyterview:control-light',
    svgstr: jvc_light_namespaceObject
});
const rotateRightIcon = new ui_components_4_5_singleton_.LabIcon({
    name: 'jupyterview:rotate-right',
    svgstr: rotate_right_white_24dp_namespaceObject
});
const rotateLeftIcon = new ui_components_4_5_singleton_.LabIcon({
    name: 'jupyterview:rotate-left',
    svgstr: rotate_left_white_24dp_namespaceObject
});
const focusViewIcon = new ui_components_4_5_singleton_.LabIcon({
    name: 'jupyterview:focus-view',
    svgstr: center_focus_weak_white_24dp_namespaceObject
});
function majorAxis(vec3, idxA, idxB) {
    const axis = [0, 0, 0];
    const idx = Math.abs(vec3[idxA]) > Math.abs(vec3[idxB]) ? idxA : idxB;
    const value = vec3[idx] > 0 ? 1 : -1;
    axis[idx] = value;
    return axis;
}
function moveCamera(camera, renderer, interactor, focalPoint, position, viewUp, animateSteps = 0) {
    const EPSILON = 0.000001;
    const originalFocalPoint = camera.getFocalPoint();
    const originalPosition = camera.getPosition();
    const originalViewUp = camera.getViewUp();
    const animationStack = [
        {
            focalPoint,
            position,
            viewUp
        }
    ];
    if (animateSteps) {
        const deltaFocalPoint = [
            (originalFocalPoint[0] - focalPoint[0]) / animateSteps,
            (originalFocalPoint[1] - focalPoint[1]) / animateSteps,
            (originalFocalPoint[2] - focalPoint[2]) / animateSteps
        ];
        const deltaPosition = [
            (originalPosition[0] - position[0]) / animateSteps,
            (originalPosition[1] - position[1]) / animateSteps,
            (originalPosition[2] - position[2]) / animateSteps
        ];
        const deltaViewUp = [
            (originalViewUp[0] - viewUp[0]) / animateSteps,
            (originalViewUp[1] - viewUp[1]) / animateSteps,
            (originalViewUp[2] - viewUp[2]) / animateSteps
        ];
        const needSteps = deltaFocalPoint[0] ||
            deltaFocalPoint[1] ||
            deltaFocalPoint[2] ||
            deltaPosition[0] ||
            deltaPosition[1] ||
            deltaPosition[2] ||
            deltaViewUp[0] ||
            deltaViewUp[1] ||
            deltaViewUp[2];
        const focalPointDeltaAxisCount = deltaFocalPoint
            .map(i => (Math.abs(i) < EPSILON ? 0 : 1))
            .reduce((a, b) => (a + b), 0);
        const positionDeltaAxisCount = deltaPosition
            .map(i => (Math.abs(i) < EPSILON ? 0 : 1))
            .reduce((a, b) => (a + b), 0);
        const viewUpDeltaAxisCount = deltaViewUp
            .map(i => (Math.abs(i) < EPSILON ? 0 : 1))
            .reduce((a, b) => (a + b), 0);
        const rotation180Only = viewUpDeltaAxisCount === 1 &&
            positionDeltaAxisCount === 0 &&
            focalPointDeltaAxisCount === 0;
        if (needSteps) {
            if (rotation180Only) {
                const availableAxes = originalFocalPoint
                    .map((fp, i) => Math.abs(originalPosition[i] - fp) < EPSILON ? i : null)
                    .filter(i => i !== null);
                const axisCorrectionIndex = availableAxes.find(v => Math.abs(deltaViewUp[v]) < EPSILON);
                for (let i = 0; i < animateSteps; i++) {
                    const newViewUp = [
                        viewUp[0] + (i + 1) * deltaViewUp[0],
                        viewUp[1] + (i + 1) * deltaViewUp[1],
                        viewUp[2] + (i + 1) * deltaViewUp[2]
                    ];
                    newViewUp[axisCorrectionIndex] = Math.sin((Math.PI * i) / (animateSteps - 1));
                    animationStack.push({
                        focalPoint,
                        position,
                        viewUp: newViewUp
                    });
                }
            }
            else {
                for (let i = 0; i < animateSteps; i++) {
                    animationStack.push({
                        focalPoint: [
                            focalPoint[0] + (i + 1) * deltaFocalPoint[0],
                            focalPoint[1] + (i + 1) * deltaFocalPoint[1],
                            focalPoint[2] + (i + 1) * deltaFocalPoint[2]
                        ],
                        position: [
                            position[0] + (i + 1) * deltaPosition[0],
                            position[1] + (i + 1) * deltaPosition[1],
                            position[2] + (i + 1) * deltaPosition[2]
                        ],
                        viewUp: [
                            viewUp[0] + (i + 1) * deltaViewUp[0],
                            viewUp[1] + (i + 1) * deltaViewUp[1],
                            viewUp[2] + (i + 1) * deltaViewUp[2]
                        ]
                    });
                }
            }
        }
    }
    if (animationStack.length === 1) {
        // update camera directly
        camera.set(animationStack.pop());
        renderer.resetCameraClippingRange();
        if (interactor.getLightFollowCamera()) {
            renderer.updateLightsGeometryToFollowCamera();
        }
        return Promise.resolve();
    }
    return new Promise((resolve, reject) => {
        const now = performance.now().toString();
        const animationRequester = `moveCamera.${now}`;
        interactor.requestAnimation(animationRequester);
        let intervalId = undefined;
        const consumeAnimationStack = () => {
            if (animationStack.length) {
                const { focalPoint: cameraFocalPoint, position: cameraPosition, viewUp: cameraViewUp } = animationStack.pop();
                camera.setFocalPoint(cameraFocalPoint[0], cameraFocalPoint[1], cameraFocalPoint[2]);
                camera.setPosition(cameraPosition[0], cameraPosition[1], cameraPosition[2]);
                camera.setViewUp(cameraViewUp[0], cameraViewUp[1], cameraViewUp[2]);
                renderer.resetCameraClippingRange();
                if (interactor.getLightFollowCamera()) {
                    renderer.updateLightsGeometryToFollowCamera();
                }
            }
            else {
                clearInterval(intervalId);
                interactor.cancelAnimation(animationRequester);
                resolve();
            }
        };
        intervalId = setInterval(consumeAnimationStack, 1);
    });
}
const VIEW_ORIENTATIONS = {
    default: {
        axis: 1,
        orientation: -1,
        viewUp: [0, 0, 1]
    },
    x: {
        axis: 0,
        orientation: 1,
        viewUp: [0, 0, 1]
    },
    y: {
        axis: 1,
        orientation: 1,
        viewUp: [0, 0, 1]
    },
    z: {
        axis: 2,
        orientation: 1,
        viewUp: [0, 1, 0]
    }
};
function selectorFactory(props) {
    return (consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: "lm-Widget p-Widget jp-Dialog-body", style: { margin: '2px 2px 5px 2px' } },
        consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: "jp-select-wrapper", style: { height: '32px' } },
            props.label ? consume_shared_module_default_react_18_2_singleton_.createElement("label", null, props.label) : consume_shared_module_default_react_18_2_singleton_.createElement("div", null),
            consume_shared_module_default_react_18_2_singleton_.createElement("select", { value: props.defaultValue, onChange: props.onChange, className: "jp-mod-styled", style: { marginTop: '2px' } }, props.options.map(option => (consume_shared_module_default_react_18_2_singleton_.createElement("option", { value: option.value }, option.label)))))));
}
const debounce = (func, timeout = 100) => {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            func(...args);
        }, timeout);
    };
};
function convertPath(windowsPath) {
    return windowsPath
        .replace(/^\\\\\?\\/, '')
        .replace(/\\/g, '/')
        .replace(/\/\/+/g, '/');
}
function b64_to_utf8(str) {
    return decodeURIComponent(atob(str));
}

;// ./lib/mainview/cameraToolbar.js


class CameraToolbar extends consume_shared_module_default_react_18_2_singleton_.Component {
    render() {
        return (consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: "jpview-view-toolbar" },
            consume_shared_module_default_react_18_2_singleton_.createElement("button", { className: "jp-Button jpview-toolbar-button dark", title: "Reset zoom level", onClick: this.props.resetCamera },
                consume_shared_module_default_react_18_2_singleton_.createElement("span", null,
                    consume_shared_module_default_react_18_2_singleton_.createElement(focusViewIcon.react, null))),
            consume_shared_module_default_react_18_2_singleton_.createElement("span", null),
            " ",
            consume_shared_module_default_react_18_2_singleton_.createElement("span", null),
            consume_shared_module_default_react_18_2_singleton_.createElement("button", { className: "jp-Button jpview-toolbar-button dark", title: "Rotate camera left 90\u00B0", onClick: this.props.rotateHandler('left') },
                consume_shared_module_default_react_18_2_singleton_.createElement("span", null,
                    consume_shared_module_default_react_18_2_singleton_.createElement(rotateLeftIcon.react, null))),
            ' ',
            consume_shared_module_default_react_18_2_singleton_.createElement("span", null),
            consume_shared_module_default_react_18_2_singleton_.createElement("button", { className: "jp-Button jpview-toolbar-button dark", title: "Rotate camera right 90\u00B0", onClick: this.props.rotateHandler('right') },
                consume_shared_module_default_react_18_2_singleton_.createElement("span", null,
                    consume_shared_module_default_react_18_2_singleton_.createElement(rotateRightIcon.react, null))),
            ' ',
            consume_shared_module_default_react_18_2_singleton_.createElement("span", null),
            consume_shared_module_default_react_18_2_singleton_.createElement("button", { className: "jp-Button jpview-toolbar-button dark", title: "Move camera to X-Direction", onClick: () => this.props.updateOrientation('x') },
                consume_shared_module_default_react_18_2_singleton_.createElement("span", null, "X")),
            ' ',
            consume_shared_module_default_react_18_2_singleton_.createElement("span", null),
            consume_shared_module_default_react_18_2_singleton_.createElement("button", { className: "jp-Button jpview-toolbar-button dark", title: "Move camera to Y-Direction", onClick: () => this.props.updateOrientation('y') },
                consume_shared_module_default_react_18_2_singleton_.createElement("span", null, "Y")),
            ' ',
            consume_shared_module_default_react_18_2_singleton_.createElement("span", null),
            consume_shared_module_default_react_18_2_singleton_.createElement("button", { className: "jp-Button jpview-toolbar-button dark", title: "Move camera to Z-Direction", onClick: () => this.props.updateOrientation('z') },
                consume_shared_module_default_react_18_2_singleton_.createElement("span", null, "Z"))));
    }
}

;// ./lib/mainview/utils.js
const DARK_THEME = 'JupyterLab Dark';
const LIGHT_THEME = 'JupyterLab Light';
//linear-gradient(rgb(0, 0, 42), rgb(82, 87, 110))
const DARK_BG = 'linear-gradient(var(--jp-layout-color2), var(--jp-layout-color4))';
const LIGHT_BG = 'linear-gradient(var(--jp-layout-color4), var(--jp-layout-color2))';
const BG_COLOR = {
    [DARK_THEME]: DARK_BG,
    [LIGHT_THEME]: LIGHT_BG //'linear-gradient(#000028, #ffffff)'
};
const OBJECT_COLOR = {
    [DARK_THEME]: [0.9, 0.9, 0.9],
    [LIGHT_THEME]: [0.8, 0.8, 0.8] //'linear-gradient(#000028, #ffffff)'
};
const ROTATION_STEP = 2;
const JUPYTER_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'";

// EXTERNAL MODULE: consume shared module (default) @jupyterlab/coreutils@^6.5.3 (singleton)
var coreutils_6_5_singleton_ = __webpack_require__(4526);
;// ./lib/mainview/mainview.js
























class MainView extends consume_shared_module_default_react_18_2_singleton_.Component {
    constructor(props) {
        super(props);
        this.handleThemeChange = (newTheme) => {
            this.setState(old => ({ ...old, theme: newTheme }), () => {
                const style = this.state.theme === LIGHT_THEME
                    ? { fontColor: 'rgba(0, 0, 0, 0.87)' }
                    : { fontColor: 'rgba(255, 255, 255, 0.87)' };
                this._scalarBarActor.setTickTextStyle(style);
                this._scalarBarActor.setAxisTextStyle(style);
                this._actor.getProperty().setColor(...OBJECT_COLOR[this.state.theme]);
            });
        };
        this.mainViewStateChanged = (_, changed) => {
            if (changed.camera) {
                if (!this._mouseDown) {
                    const camera = changed.camera;
                    this._camera.set(camera);
                    this._renderer.resetCameraClippingRange();
                    this._renderWindow.render();
                }
            }
        };
        this.controlStateChanged = (_, changed) => {
            let needRerender = false;
            if (changed.selectedColor) {
                this.updateColorBy(changed.selectedColor);
            }
            if (changed.colorSchema) {
                this.applyPreset({ colorSchema: changed.colorSchema });
            }
            if (changed.modifiedDataRange) {
                this.applyPreset({
                    colorSchema: this._sharedModel.getControlViewStateByKey('colorSchema'),
                    dataRange: changed.modifiedDataRange
                });
            }
            if (changed.displayMode) {
                const [visibility, representation, edgeVisibility] = changed.displayMode
                    .split(':')
                    .map(Number);
                this._actor.getProperty().set({ representation, edgeVisibility });
                this._actor.setVisibility(!!visibility);
                needRerender = true;
            }
            if (changed.opacity) {
                this._actor.getProperty().setOpacity(changed.opacity);
                needRerender = true;
            }
            if (changed.warpFactor || changed.warpFactor === 0) {
                const value = Number(changed.warpFactor);
                this._warpScalar.setScaleFactor(value);
                this._mapper.setInputData(this._warpScalar.getOutputData());
                needRerender = true;
            }
            if (changed.selectedWarp) {
                const [location, colorByArrayName] = changed.selectedWarp.split(':');
                if (location === '') {
                    this._warpScalar.setScaleFactor(0);
                }
                else {
                    this._warpScalar.setInputArrayToProcess(0, colorByArrayName, location);
                }
                this._mapper.setInputData(this._warpScalar.getOutputData());
                needRerender = true;
            }
            if (changed.warpNormalAxis) {
                this._warpScalar.setNormal(changed.warpNormalAxis);
                this._warpScalar.update();
                this._mapper.setInputData(this._warpScalar.getOutputData());
                needRerender = true;
            }
            if (changed.selectedDataset) {
                this._source = this._fileData[changed.selectedDataset];
                this._warpScalar.setInputData(this._source);
                this._mapper.setInputData(this._warpScalar.getOutputData());
                needRerender = true;
            }
            if (needRerender) {
                setTimeout(() => this._renderWindow.render(), 50);
            }
        };
        this.updateColorBy = (color) => {
            const [location, colorByArrayName, indexValue] = color.split(':');
            const interpolateScalarsBeforeMapping = location === 'PointData';
            let colorMode = Constants/* ColorMode */.lH.DEFAULT;
            let scalarMode = Constants/* ScalarMode */.i5.DEFAULT;
            const scalarVisibility = location.length > 0;
            if (scalarVisibility) {
                const newArray = this._source[`get${location}`]().getArrayByName(colorByArrayName);
                const selectedComp = parseInt(indexValue);
                this._activeArray = newArray;
                const newDataRange = this._activeArray.getRange(selectedComp);
                this._dataRange[0] = newDataRange[0];
                this._dataRange[1] = newDataRange[1];
                if (this._dataRange[0] === this._dataRange[1]) {
                    this._dataRange[1] = this._dataRange[0] + 0.0000000001;
                }
                this._sharedModel.transact(() => {
                    this._sharedModel.setMainViewState({ dataRange: [...this._dataRange] });
                });
                colorMode = Constants/* ColorMode */.lH.MAP_SCALARS;
                scalarMode =
                    location === 'PointData'
                        ? Constants/* ScalarMode */.i5.USE_POINT_FIELD_DATA
                        : Constants/* ScalarMode */.i5.USE_CELL_FIELD_DATA;
                if (this._mapper.getLookupTable()) {
                    const lut = this._mapper.getLookupTable();
                    if (selectedComp === -1) {
                        lut.setVectorModeToMagnitude();
                    }
                    else {
                        lut.setVectorModeToComponent();
                        lut.setVectorComponent(selectedComp);
                    }
                }
            }
            this._scalarBarActor.setAxisLabel(colorByArrayName);
            this._scalarBarActor.setVisibility(true);
            this._mapper.set({
                colorByArrayName,
                colorMode,
                interpolateScalarsBeforeMapping,
                scalarMode,
                scalarVisibility
            });
            this.applyPreset({
                colorSchema: this._sharedModel.getControlViewStateByKey('colorSchema')
            });
        };
        this.applyPreset = (options) => {
            if (!options.colorSchema) {
                options.colorSchema = 'erdc_rainbow_bright';
            }
            if (!options.dataRange) {
                options.dataRange = this._dataRange;
            }
            const preset = ColorMaps/* default */.A.getPresetByName(options.colorSchema);
            this._lookupTable.applyColorMap(preset);
            this._lookupTable.setMappingRange(options.dataRange[0], options.dataRange[1]);
            this._lookupTable.updateRange();
            setTimeout(() => this._renderWindow.render(), 250);
        };
        this.createComponentSelector = () => {
            const pointDataArray = this._source.getPointData().getArrays();
            const option = [
                { value: ':', label: 'Solid color' }
            ];
            pointDataArray.forEach((a) => {
                const name = a.getName();
                const numberComp = a.getNumberOfComponents();
                option.push({
                    label: `${name}`,
                    value: `PointData:${name}:-1`
                });
                if (numberComp > 1) {
                    for (let index = 0; index < numberComp; index++) {
                        option.push({
                            label: `${name} - ${index}`,
                            value: `PointData:${name}:${index}`
                        });
                    }
                }
            });
            const cellDataArray = this._source.getCellData().getArrays();
            cellDataArray.forEach((a) => {
                const name = a.getName();
                const numberComp = a.getNumberOfComponents();
                option.push({
                    label: `${name}`,
                    value: `CellData:${name}:-1`
                });
                for (let index = 0; index < numberComp; index++) {
                    option.push({
                        label: `${name} ${index}`,
                        value: `CellData:${name}:${index}`
                    });
                }
            });
            return option;
        };
        this.createPipeline = (polyResult) => {
            this._lookupTable = ColorTransferFunction/* default.newInstance */.Ay.newInstance();
            this._mapper = Mapper/* default.newInstance */.Ay.newInstance({
                interpolateScalarsBeforeMapping: true,
                useLookupTableScalarRange: true,
                scalarVisibility: false
            });
            this._mapper.setLookupTable(this._lookupTable);
            this._actor = Actor/* default.newInstance */.Ay.newInstance();
            this._actor.setMapper(this._mapper);
            this._actor.getProperty().setColor(...OBJECT_COLOR[this.state.theme]);
            this._lookupTable.onModified(() => {
                this._renderWindow.render();
            });
            this._source = polyResult;
            this._warpScalar = WarpScalar/* default.newInstance */.Ay.newInstance({
                scaleFactor: 0,
                useNormal: true
            });
            this._warpScalar.setNormal([0, 0, 1]);
            this._warpScalar.setInputData(this._source);
            const scalars = this._source.getPointData().getScalars();
            this._dataRange = scalars
                ? [scalars.getRange().min, scalars.getRange().max]
                : [0, 1];
            if (!this._sharedModel.getContent('mainViewState')) {
                const colorByOptions = this.createComponentSelector();
                this._sharedModel.setMainViewState({
                    colorByOptions,
                    dataRange: [...this._dataRange]
                });
            }
            const fontColor = this.state.theme === LIGHT_THEME
                ? 'rgba(0, 0, 0, 0.87)'
                : 'rgba(255, 255, 255, 0.87)';
            this._scalarBarActor = ScalarBarActor/* default.newInstance */.Ay.newInstance();
            this._scalarBarActor.setAxisTextStyle({
                fontColor,
                fontFamily: JUPYTER_FONT,
                fontSize: '18px'
            });
            this._scalarBarActor.setTickTextStyle({
                fontColor,
                fontFamily: JUPYTER_FONT,
                fontSize: '12px'
            });
            this._scalarBarActor.setScalarsToColors(this._mapper.getLookupTable());
            this._scalarBarActor.setVisibility(false);
            this._scalarBarActor.setDrawNanAnnotation(false);
            this._mapper.setInputData(this._warpScalar.getOutputData());
            // this._mapper.setInputData(this._source);
            this._renderer.addActor(this._scalarBarActor);
            this._renderer.addActor(this._actor);
            this._renderer.resetCamera();
            const currentState = this._sharedModel.getControlViewState();
            if (Object.keys(currentState).length > 0) {
                this.controlStateChanged(null, currentState);
            }
            else {
                this._renderWindow.render();
            }
        };
        this.rotate = (angle) => {
            const camera = this._renderer.getActiveCamera();
            const focalPoint = camera.getFocalPoint();
            const position = camera.getPosition();
            const viewUp = camera.getViewUp();
            const axis = [
                focalPoint[0] - position[0],
                focalPoint[1] - position[1],
                focalPoint[2] - position[2]
            ];
            MatrixBuilder/* default */.A
                .buildFromDegree()
                .rotate(Number.isNaN(angle) ? 90 : angle, axis)
                .apply(viewUp);
            camera.setViewUp(...viewUp);
            camera.modified();
            // model.orientationWidget.updateMarkerOrientation();
            this._renderWindow.render();
        };
        this.rotateWithAnimation = (direction) => {
            const sign = direction === 'left' ? 1 : -1;
            return () => {
                const interactor = this._renderWindow.getInteractor();
                interactor.requestAnimation(this._renderWindow);
                let count = 0;
                let intervalId = undefined;
                const rotate = () => {
                    if (count < 90) {
                        count += ROTATION_STEP;
                        this.rotate(sign * ROTATION_STEP);
                    }
                    else {
                        clearInterval(intervalId);
                        interactor.cancelAnimation(this._renderWindow);
                        this._syncCamera();
                    }
                };
                intervalId = setInterval(rotate, 8);
            };
        };
        this.updateOrientation = (mode) => {
            if (!this._inAnimation) {
                this._inAnimation = true;
                const { axis, orientation, viewUp } = VIEW_ORIENTATIONS[mode];
                // const axisIndex  = VIEW_ORIENTATIONS[mode].axis
                const animateSteps = 100;
                const interactor = this._renderWindow.getInteractor();
                const camera = this._renderer.getActiveCamera();
                const originalPosition = camera.getPosition();
                const originalViewUp = camera.getViewUp();
                const originalFocalPoint = camera.getFocalPoint();
                const model = { axis, orientation, viewUp: viewUp };
                const position = camera.getFocalPoint();
                position[model.axis] += model.orientation;
                camera.setPosition(...position);
                camera.setViewUp(...model.viewUp);
                this._renderer.resetCamera();
                const destFocalPoint = camera.getFocalPoint();
                const destPosition = camera.getPosition();
                const destViewUp = camera.getViewUp();
                // Reset to original to prevent initial render flash
                camera.setFocalPoint(...originalFocalPoint);
                camera.setPosition(...originalPosition);
                camera.setViewUp(...originalViewUp);
                moveCamera(camera, this._renderer, interactor, destFocalPoint, destPosition, destViewUp, animateSteps).then(() => {
                    this._inAnimation = false;
                    this._syncCamera();
                });
            }
        };
        this.resetCamera = () => {
            this._renderer.resetCamera();
            this._renderer.resetCameraClippingRange();
            setTimeout(this._renderWindow.render, 0);
            this._syncCamera();
        };
        this._inAnimation = false;
        this._mouseDown = false;
        this._syncCamera = debounce(() => {
            const position = this._camera.getPosition();
            const focalPoint = this._camera.getFocalPoint();
            const viewUp = this._camera.getViewUp();
            this._sharedModel.setMainViewState({
                camera: { position, focalPoint, viewUp }
            });
        }, 100);
        const theme = (window.jupyterlabTheme ||
            LIGHT_THEME);
        this.state = {
            id: (0,index_js_.v4)(),
            theme,
            loading: true,
            colorOption: [],
            counter: 0
        };
        this._context = props.context;
        this._sharedModel = props.context.model.sharedModel;
        this.container = consume_shared_module_default_react_18_2_singleton_.createRef();
        this._fileData = {};
    }
    componentDidMount() {
        setTimeout(() => {
            const rootContainer = this.container.current;
            this._fullScreenRenderer = RenderWindowWithControlBar/* default.newInstance */.Ay.newInstance({
                controlSize: 0
            });
            this._fullScreenRenderer.setContainer(rootContainer);
            this._renderer = this._fullScreenRenderer.getRenderer();
            this._renderer.setBackground([0, 0, 0, 0]);
            this._renderWindow = this._fullScreenRenderer.getRenderWindow();
            const axes = AxesActor/* default.newInstance */.Ay.newInstance();
            const orientationWidget = OrientationMarkerWidget/* default.newInstance */.Ay.newInstance({
                actor: axes,
                interactor: this._renderWindow.getInteractor()
            });
            orientationWidget.setEnabled(true);
            orientationWidget.setViewportSize(0.15);
            orientationWidget.setMinPixelSize(100);
            orientationWidget.setMaxPixelSize(300);
            const camera = (this._camera = this._renderer.getActiveCamera());
            const widgetManager = WidgetManager/* default.newInstance */.Ay.newInstance();
            widgetManager.setRenderer(orientationWidget.getRenderer());
            const widget = InteractiveOrientationWidget/* default.newInstance */.Ay.newInstance();
            widget.placeWidget(axes.getBounds());
            widget.setBounds(axes.getBounds());
            widget.setPlaceFactor(1);
            const vw = widgetManager.addWidget(widget);
            vw.onOrientationChange(({ up, direction, action, event }) => {
                const focalPoint = camera.getFocalPoint();
                const position = camera.getPosition();
                const viewUp = camera.getViewUp();
                const distance = Math.sqrt(Core_Math/* distance2BetweenPoints */.fm(position, focalPoint));
                camera.setPosition(focalPoint[0] + direction[0] * distance, focalPoint[1] + direction[1] * distance, focalPoint[2] + direction[2] * distance);
                let axis = [];
                if (direction[0]) {
                    axis = majorAxis(viewUp, 1, 2);
                }
                if (direction[1]) {
                    axis = majorAxis(viewUp, 0, 2);
                }
                if (direction[2]) {
                    axis = majorAxis(viewUp, 0, 1);
                }
                camera.setViewUp(axis[0], axis[1], axis[2]);
                orientationWidget.updateMarkerOrientation();
                widgetManager.enablePicking();
                this._renderWindow.render();
                this._syncCamera();
            });
            this._renderer.resetCamera();
            widgetManager.enablePicking();
            this._renderWindow.render();
            const interactor = this._fullScreenRenderer.getInteractor();
            document
                .querySelector('body')
                .removeEventListener('keypress', interactor.handleKeyPress);
            document
                .querySelector('body')
                .removeEventListener('keydown', interactor.handleKeyDown);
            document
                .querySelector('body')
                .removeEventListener('keyup', interactor.handleKeyUp);
            this._context.ready.then(() => {
                this._model = this._context.model;
                this._kernel = this._model.getKernel();
                this._model.themeChanged.connect((_, arg) => {
                    this.handleThemeChange(arg.newValue);
                });
                this._sharedModel.controlViewStateChanged.connect(this.controlStateChanged);
                this._sharedModel.mainViewStateChanged.connect(this.mainViewStateChanged);
                const fullPath = convertPath(this._context.path);
                const dirPath = fullPath.substring(0, fullPath.lastIndexOf('/') + 1);
                const fileName = fullPath.replace(/^.*(\\|\/|:)/, '');
                const fileContent = this._sharedModel.getContent('content');
                const contentPromises = this.prepareFileContent(dirPath, fileName, fileContent);
                let counter = 0;
                const entries = Object.entries(contentPromises);
                const totalItems = entries.length;
                const firstName = entries[0][0];
                const fileList = Object.keys(contentPromises);
                for (const [path, promise] of entries) {
                    const name = path.split('::')[0];
                    const fileNameOnly = coreutils_6_5_singleton_.PathExt.basename(name);
                    promise.then(vtkParsedContent => {
                        this.stringToPolyData(vtkParsedContent.binary, `${fileNameOnly}.${vtkParsedContent.type}`)
                            .then(polyResult => {
                            counter = Math.round(counter + 100 / totalItems);
                            this._fileData[path] = (0,vtk/* default */.A)(polyResult.polyData);
                            polyResult.webWorker.terminate();
                            if (counter >= 99) {
                                this.createPipeline(this._fileData[firstName]);
                                this.setState(old => ({ ...old, loading: false, counter }));
                                this._sharedModel.setMainViewState({ fileList });
                            }
                            else {
                                this.setState(old => ({ ...old, counter }));
                            }
                        })
                            .catch(e => {
                            throw e;
                        });
                    });
                }
                const renderContainer = this._fullScreenRenderer.getRenderWindowContainer();
                renderContainer.addEventListener('mousedown', event => {
                    this._mouseDown = true;
                });
                renderContainer.addEventListener('mouseup', event => {
                    this._mouseDown = false;
                });
                renderContainer.addEventListener('mousemove', (event) => {
                    if (this._mouseDown) {
                        this._syncCamera();
                    }
                });
                renderContainer.addEventListener('wheel', (event) => {
                    this._syncCamera();
                });
            });
        }, 500);
    }
    prepareFileContent(filePath, fileName, fileContent) {
        const pathList = fileName.split('.');
        const ext = pathList[pathList.length - 1];
        const promises = {};
        if (ext.toLowerCase() === 'pvd') {
            if (filePath.startsWith('RTC:')) {
                filePath = filePath.split(':')[1];
            }
            const xmlStr = b64_to_utf8(fileContent);
            const xmlParser = new DOMParser();
            const doc = xmlParser.parseFromString(xmlStr, 'application/xml');
            const contents = new services_7_5_singleton_.ContentsManager();
            doc.querySelectorAll('DataSet').forEach(item => {
                const timeStep = item.getAttribute('timestep');
                const vtuPath = item.getAttribute('file');
                const content = contents
                    .get(`${filePath}/${vtuPath}`, {
                    format: 'base64',
                    content: true,
                    type: 'file'
                })
                    .then(iModel => ({ type: 'vtu', binary: iModel.content }));
                promises[`${vtuPath}::${filePath}::${timeStep}`] = content;
            });
            return promises;
        }
        else {
            const fileExt = ext.toLowerCase();
            const path = `${filePath}${fileName}`;
            const parser = this.props.parsers.getParser(fileExt);
            if (!parser) {
                throw Error('Parser not found');
            }
            const content = parser.readFile(fileContent, fileExt, path, this._kernel);
            let output;
            if (parser.nativeSupport) {
                output = `${fileName}::${filePath}::0::${fileName}`;
            }
            else {
                output = `${fileName}.vtk::${filePath}::0::${fileName}`;
            }
            return { [output]: content };
        }
        // return { [`${fileName}::${filePath}::0`]: Promise.resolve(fileContent) };
    }
    async stringToPolyData(fileContent, filePath) {
        const str = `data:application/octet-stream;base64,${fileContent}`;
        return fetch(str)
            .then(b => b.arrayBuffer())
            .then(buff => (0,readPolyDataArrayBuffer/* default */.A)(null, buff, filePath, ''))
            .then(polyResult => {
            polyResult.webWorker.terminate();
            return polyResult;
        });
    }
    render() {
        return (consume_shared_module_default_react_18_2_singleton_.createElement("div", { style: {
                width: '100%',
                height: 'calc(100%)'
            } },
            consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: 'jpview-Spinner', style: { display: this.state.loading ? 'flex' : 'none' } },
                consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: 'jpview-SpinnerContent' }),
                consume_shared_module_default_react_18_2_singleton_.createElement("p", { style: {
                        position: 'relative',
                        right: '50%',
                        fontSize: 'var(--jp-ui-font-size2)',
                        color: '#27b9f3'
                    } }, `${this.state.counter}%`)),
            consume_shared_module_default_react_18_2_singleton_.createElement("div", { ref: this.container, style: {
                    width: '100%',
                    height: 'calc(100%)',
                    background: BG_COLOR[this.state.theme] //'radial-gradient(#efeded, #8f9091)'
                } }),
            consume_shared_module_default_react_18_2_singleton_.createElement(CameraToolbar, { rotateHandler: this.rotateWithAnimation, resetCamera: this.resetCamera, updateOrientation: this.updateOrientation })));
    }
}

;// ./lib/mainview/widget.js





class JupyterViewWidget extends docregistry_4_5.DocumentWidget {
    constructor(options) {
        super(options);
        this.onResize = (msg) => {
            window.dispatchEvent(new Event('resize'));
        };
    }
    /**
     * Dispose of the resources held by the widget.
     */
    dispose() {
        this.content.dispose();
        super.dispose();
        setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
    }
}
class JupyterViewPanel extends apputils_4_6_singleton_.ReactWidget {
    /**
     * Construct a `ExamplePanel`.
     *
     * @param context - The documents context.
     */
    constructor(context, parsers) {
        super();
        this.parsers = parsers;
        this.addClass('jp-jupyterview-panel');
        this._context = context;
    }
    /**
     * Dispose of the resources held by the widget.
     */
    dispose() {
        if (this.isDisposed) {
            return;
        }
        signaling_2_0_singleton_.Signal.clearData(this);
        super.dispose();
    }
    render() {
        return consume_shared_module_default_react_18_2_singleton_.createElement(MainView, { context: this._context, parsers: this.parsers });
    }
}

;// ./lib/mainview/factory.js



class JupyterViewWidgetFactory extends docregistry_4_5.ABCWidgetFactory {
    constructor(options, parsers) {
        super(options);
        this.parsers = parsers;
    }
    /**
     * Create a new widget given a context.
     *
     * @param context Contains the information of the file
     * @returns The widget
     */
    createNewWidget(context) {
        return new JupyterViewWidget({
            context,
            content: new JupyterViewPanel(context, this.parsers)
        });
    }
}
/**
 * A Model factory to create new instances of JupyterViewModel.
 */
class JupyterViewModelFactory {
    constructor() {
        this._disposed = false;
    }
    /**
     * The name of the model.
     *
     * @returns The name
     */
    get name() {
        return 'jupyterview-model';
    }
    /**
     * The content type of the file.
     *
     * @returns The content type
     */
    get contentType() {
        return 'file';
    }
    /**
     * The format of the file.
     *
     * @returns the file format
     */
    get fileFormat() {
        return 'base64';
    }
    /**
     * Get whether the model factory has been disposed.
     *
     * @returns disposed status
     */
    get isDisposed() {
        return this._disposed;
    }
    /**
     * Dispose the model factory.
     */
    dispose() {
        this._disposed = true;
    }
    /**
     * Get the preferred language given the path on the file.
     *
     * @param path path of the file represented by this document model
     * @returns The preferred language
     */
    preferredLanguage(path) {
        return '';
    }
    /**
     * Create a new instance of JupyterViewModel.
     */
    createNew(options) {
        const model = new JupyterViewModel(options);
        return model;
    }
}

// EXTERNAL MODULE: ./node_modules/@mui/icons-material/ExpandMore.js
var ExpandMore = __webpack_require__(2048);
// EXTERNAL MODULE: ./node_modules/@mui/material/Accordion/Accordion.js + 20 modules
var Accordion = __webpack_require__(1256);
// EXTERNAL MODULE: ./node_modules/@mui/material/AccordionDetails/AccordionDetails.js + 1 modules
var AccordionDetails = __webpack_require__(1752);
// EXTERNAL MODULE: ./node_modules/@mui/material/AccordionSummary/AccordionSummary.js + 9 modules
var AccordionSummary = __webpack_require__(6340);
;// ./lib/panelview/colorpanel.js




class ColorPanel extends consume_shared_module_default_react_18_2_singleton_.Component {
    constructor(props) {
        super(props);
        this.rangeSettingComponent = () => {
            let dataRangeBlock = consume_shared_module_default_react_18_2_singleton_.createElement("div", null);
            if (this.props.controlViewState.modifiedDataRange) {
                const step = (this.props.controlViewState.modifiedDataRange[1] -
                    this.props.controlViewState.modifiedDataRange[0]) /
                    100;
                dataRangeBlock = (consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: "jpview-input-wrapper" },
                    consume_shared_module_default_react_18_2_singleton_.createElement("div", { style: { width: '40%' } },
                        consume_shared_module_default_react_18_2_singleton_.createElement("label", null, "Min"),
                        consume_shared_module_default_react_18_2_singleton_.createElement("input", { className: "jpview-input", type: "number", value: this.props.controlViewState.modifiedDataRange[0], onChange: e => this.props.onRangeChange('min', e.target.value), step: step })),
                    consume_shared_module_default_react_18_2_singleton_.createElement("div", { style: {
                            width: '15%',
                            display: 'flex',
                            flexDirection: 'column-reverse'
                        } },
                        consume_shared_module_default_react_18_2_singleton_.createElement("button", { className: "jp-Button jpview-toolbar-button", title: "Reset range", onClick: this.props.resetRange }, ui_components_4_5_singleton_.LabIcon.resolveReact({ icon: ui_components_4_5_singleton_.refreshIcon }))),
                    consume_shared_module_default_react_18_2_singleton_.createElement("div", { style: { width: '40%' } },
                        consume_shared_module_default_react_18_2_singleton_.createElement("label", null, "Max"),
                        consume_shared_module_default_react_18_2_singleton_.createElement("input", { className: "jpview-input", type: "number", value: this.props.controlViewState.modifiedDataRange[1], onChange: e => this.props.onRangeChange('max', e.target.value), step: step }))));
            }
            return dataRangeBlock;
        };
        this.state = { clientId: this.props.clientId };
        this._colorMapOptions = ColorMaps/* default */.A.rgbPresetNames.map(option => ({ value: option, label: option }));
    }
    render() {
        var _a;
        const colorSelectorData = (_a = this.props.mainViewState.colorByOptions) !== null && _a !== void 0 ? _a : [
            { value: ':', label: 'Solid color' }
        ];
        return (consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: "jpview-control-panel-component" },
            selectorFactory({
                defaultValue: this.props.controlViewState.selectedColor,
                options: colorSelectorData,
                onChange: this.props.onSelectedColorChange,
                label: 'Color by'
            }),
            selectorFactory({
                defaultValue: this.props.controlViewState.colorSchema,
                options: this._colorMapOptions,
                onChange: this.props.onColorSchemaChange,
                label: 'Color map option'
            }),
            this.rangeSettingComponent()));
    }
}

;// ./lib/panelview/datasetpanel.js


class DatasetPanel extends consume_shared_module_default_react_18_2_singleton_.Component {
    constructor(props) {
        super(props);
        this.switchDataset = (step = 1) => {
            var _a;
            const fileList = (_a = this.props.mainViewState.fileList) !== null && _a !== void 0 ? _a : [];
            const length = fileList.length;
            if (length < 2) {
                return;
            }
            const current = this.props.controlViewState.selectedDataset;
            const idx = fileList.indexOf(current);
            if (idx === -1) {
                return;
            }
            let next = idx + step;
            if (next === length) {
                next = 0;
            }
            else if (next < 0) {
                next = length - 1;
            }
            this.props.onSelectDatasetChange(fileList[next]);
        };
        this.toggleAnimation = () => {
            this.setState(old => {
                const current = old.animating;
                if (!current) {
                    this._interval = setInterval(this.switchDataset, 200);
                }
                else {
                    clearInterval(this._interval);
                }
                return { ...old, animating: !current };
            });
        };
        this.state = {
            clientId: this.props.clientId,
            animating: false,
            selectedDataset: ''
        };
    }
    componentDidUpdate(oldProps, oldState) {
        if (!this.props.clientId && oldState.animating) {
            clearInterval(this._interval);
            this.setState(old => ({
                ...old,
                animating: false
            }));
            return;
        }
        if (!oldState.clientId && this.props.clientId) {
            this.setState(old => ({ ...old, clientId: this.props.clientId }));
        }
        else if (oldState.clientId &&
            this.props.clientId &&
            oldState.clientId !== this.props.clientId) {
            if (this.state.animating) {
                clearInterval(this._interval);
            }
            this.setState(old => ({
                ...old,
                clientId: this.props.clientId,
                animating: false
            }));
        }
    }
    render() {
        var _a, _b;
        const fileList = ((_a = this.props.mainViewState.fileList) !== null && _a !== void 0 ? _a : ['None']).map(item => {
            var _a;
            const labelList = item.split('::');
            return { label: (_a = labelList[3]) !== null && _a !== void 0 ? _a : labelList[0], value: item };
        });
        return (consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: "jpview-control-panel-component" },
            selectorFactory({
                defaultValue: (_b = this.props.controlViewState.selectedDataset) !== null && _b !== void 0 ? _b : fileList[0].value,
                options: fileList,
                onChange: e => this.props.onSelectDatasetChange(e.target.value),
                label: 'Dataset'
            }),
            consume_shared_module_default_react_18_2_singleton_.createElement("div", { style: {
                    margin: '3px 3px 5px',
                    display: 'flex',
                    justifyContent: 'space-between'
                } },
                consume_shared_module_default_react_18_2_singleton_.createElement("button", { style: { width: '25%' }, className: "jpview-button", title: "Previous", onClick: () => this.switchDataset(-1) }, "Previous"),
                consume_shared_module_default_react_18_2_singleton_.createElement("button", { style: { width: '25%' }, className: "jpview-button", title: "Play", onClick: this.toggleAnimation }, this.state.animating ? 'Pause' : 'Play'),
                consume_shared_module_default_react_18_2_singleton_.createElement("button", { style: { width: '25%' }, className: "jpview-button", title: "Next", onClick: () => this.switchDataset(1) }, "Next"))));
    }
}

;// ./lib/panelview/displaypanel.js


const DISPLAY_MODE = [
    { label: 'Surface', value: '1:2:0' },
    { label: 'Surface with Edge', value: '1:2:1' },
    { label: 'Wireframe', value: '1:1:0' },
    { label: 'Points', value: '1:0:0' },
    { label: 'Hidden', value: '0:-1:0' }
];
class DisplayPanel extends consume_shared_module_default_react_18_2_singleton_.Component {
    constructor(props) {
        super(props);
        this.state = { clientId: this.props.clientId };
    }
    render() {
        return (consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: "jpview-control-panel-component" },
            selectorFactory({
                defaultValue: this.props.controlViewState.displayMode,
                options: DISPLAY_MODE,
                onChange: this.props.onDisplayModeChange,
                label: 'Display mode'
            }),
            consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: "jpview-input-wrapper" },
                consume_shared_module_default_react_18_2_singleton_.createElement("div", { style: { width: '100%' } },
                    consume_shared_module_default_react_18_2_singleton_.createElement("label", null,
                        "Opacity: ",
                        this.props.controlViewState.opacity),
                    consume_shared_module_default_react_18_2_singleton_.createElement("input", { className: "jpview-slider", type: "range", name: "opacity", min: 0.01, max: 1, step: 0.01, value: this.props.controlViewState.opacity, onChange: this.props.onOpacityChange })))));
    }
}

;// ./lib/panelview/wrappanel.js


const INPUT_STYLE = {
    width: '100%',
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '5px'
};
class WrapPanel extends consume_shared_module_default_react_18_2_singleton_.Component {
    constructor(props) {
        super(props);
        this.onUserNormalChange = (e) => {
            const checked = e.target.checked;
            this.props.onWarpUseNormalChange(e);
            if (!checked) {
                this.setState(old => ({
                    ...old,
                    normalX: 0,
                    normalY: 0,
                    normalZ: 1
                }));
            }
        };
        this.onNormalChange = (ax, value) => {
            this.setState(old => ({ ...old, [`normal${ax}`]: value }), () => {
                this.props.onWarpNormalAxisChange([
                    this.state.normalX,
                    this.state.normalY,
                    this.state.normalZ
                ]);
            });
        };
        this.state = {
            clientId: this.props.clientId,
            normalX: 0,
            normalY: 0,
            normalZ: 1
        };
    }
    componentDidUpdate(prevProps, prevState) {
        if (this.props !== prevProps) {
            let needUpdate = false;
            const warpNormalAxis = this.props.controlViewState.warpNormalAxis;
            if (warpNormalAxis) {
                needUpdate =
                    warpNormalAxis[0] !== this.state.normalX ||
                        warpNormalAxis[1] !== this.state.normalY ||
                        warpNormalAxis[2] !== this.state.normalZ;
                if (needUpdate) {
                    this.setState(old => ({
                        ...old,
                        normalX: warpNormalAxis[0],
                        normalY: warpNormalAxis[1],
                        normalZ: warpNormalAxis[2]
                    }));
                }
            }
        }
    }
    render() {
        var _a, _b, _c;
        const warpSelectorData = [{ value: ':', label: 'None' }].concat((_b = (_a = this.props.mainViewState.colorByOptions) === null || _a === void 0 ? void 0 : _a.filter(item => {
            return item.value.endsWith('-1');
        })) !== null && _b !== void 0 ? _b : []);
        return (consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: "jpview-control-panel-component" },
            selectorFactory({
                defaultValue: this.props.controlViewState.selectedWarp,
                options: warpSelectorData,
                onChange: this.props.onSelectedWarpChange,
                label: 'Warp by'
            }),
            consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: "jpview-input-wrapper", style: { flexDirection: 'column' } },
                consume_shared_module_default_react_18_2_singleton_.createElement("div", { style: INPUT_STYLE },
                    consume_shared_module_default_react_18_2_singleton_.createElement("label", null, "Scale factor"),
                    consume_shared_module_default_react_18_2_singleton_.createElement("input", { className: "jpview-input", type: "number", style: { width: '25%' }, value: (_c = this.props.controlViewState.warpFactor) !== null && _c !== void 0 ? _c : 0, onChange: this.props.onWarpFactorChange, 
                        // step={step}
                        disabled: !this.props.controlViewState.enableWarp })),
                consume_shared_module_default_react_18_2_singleton_.createElement("div", { style: INPUT_STYLE },
                    consume_shared_module_default_react_18_2_singleton_.createElement("label", null, "Use normal"),
                    consume_shared_module_default_react_18_2_singleton_.createElement("input", { className: "jpview-input", type: "checkbox", style: { width: 'auto' }, disabled: !this.props.controlViewState.enableWarp, checked: !!this.props.controlViewState.warpNormal, onChange: this.onUserNormalChange })),
                consume_shared_module_default_react_18_2_singleton_.createElement("div", { style: INPUT_STYLE }, ['X', 'Y', 'Z'].map(ax => {
                    return (consume_shared_module_default_react_18_2_singleton_.createElement("input", { type: 'number', style: { width: '25%' }, className: "jpview-input", key: ax, placeholder: ax, disabled: !this.props.controlViewState.enableWarp ||
                            !this.props.controlViewState.warpNormal, value: this.state[`normal${ax}`], onChange: e => {
                            this.onNormalChange(ax, parseFloat(e.target.value));
                        } }));
                })))));
    }
}

;// ./lib/panelview/panelview.js










const panelTitleStyle = {
    background: 'var(--jp-layout-color2)',
    color: 'var(--jp-ui-font-color1)'
};
const panelBodyStyle = {
    color: 'var(--jp-ui-font-color1)',
    background: 'var(--jp-layout-color1)',
    padding: '8px'
};
const STOCK_STATE = {
    datasetPanel: true,
    colorPanel: true,
    displayPanel: true,
    filterPanel: true,
    mainViewState: {},
    controlViewState: {
        selectedColor: ':',
        colorSchema: 'erdc_rainbow_bright',
        displayMode: DISPLAY_MODE[0].value,
        opacity: 1
    }
};
class panelview_MainView extends consume_shared_module_default_react_18_2_singleton_.Component {
    constructor(props) {
        super(props);
        this.sharedControlViewModelChanged = (_, changed) => {
            this.setState(old => ({
                ...old,
                controlViewState: { ...old.controlViewState, ...changed }
            }));
        };
        this.sharedMainViewModelChanged = (_, changed) => {
            this.setState(old => {
                const newState = {
                    ...old,
                    mainViewState: { ...old.mainViewState, ...changed }
                };
                if (changed.dataRange) {
                    newState.controlViewState.modifiedDataRange = [...changed.dataRange];
                }
                if (changed.fileList) {
                    newState.controlViewState.selectedDataset = changed.fileList[0];
                }
                return newState;
            });
        };
        this.togglePanel = (panel) => {
            this.setState(old => ({ ...old, [panel]: !old[panel] }));
        };
        this.onSelectedColorChange = (evt) => {
            const selectedColor = evt.target.value;
            this.updateLocalAndSharedState({ selectedColor });
        };
        this.onColorSchemaChange = (evt) => {
            const colorSchema = evt.target.value;
            this.updateLocalAndSharedState({ colorSchema });
        };
        this.onRangeChange = (option, value) => {
            if (!this.state.controlViewState.modifiedDataRange) {
                return;
            }
            const index = { min: 0, max: 1 };
            const modifiedDataRange = [
                ...this.state.controlViewState.modifiedDataRange
            ];
            modifiedDataRange[index[option]] = parseFloat(value);
            this.updateLocalAndSharedState({ modifiedDataRange });
        };
        this.resetRange = () => {
            const selectedColor = this.state.controlViewState.selectedColor;
            if (selectedColor) {
                this.updateLocalAndSharedState({ selectedColor });
            }
        };
        this.onDisplayModeChange = (e) => {
            const displayMode = e.target.value;
            this.updateLocalAndSharedState({ displayMode });
        };
        this.onOpacityChange = (e) => {
            const opacity = parseFloat(e.target.value);
            this.updateLocalAndSharedState({ opacity });
        };
        this.onWarpActivationChange = (enableWarp) => {
            this.updateLocalAndSharedState({ enableWarp });
        };
        this.onWarpFactorChange = (e) => {
            const warpFactor = parseFloat(e.target.value);
            this.updateLocalAndSharedState({ warpFactor });
        };
        this.onSelectedWarpChange = (e) => {
            const selectedWarp = e.target.value;
            const enableWarp = e.target.value !== ':';
            const warpFactor = 0;
            this.updateLocalAndSharedState({ selectedWarp, enableWarp, warpFactor });
        };
        this.onWarpUseNormalChange = (e) => {
            const warpNormal = e.target.checked;
            const payload = { warpNormal };
            if (!warpNormal) {
                payload['warpNormalAxis'] = [0, 0, 1];
            }
            this.updateLocalAndSharedState(payload);
        };
        this.onWarpNormalAxisChange = (warpNormalAxis) => {
            this.updateLocalAndSharedState({ warpNormalAxis });
        };
        this.onSelectDatasetChange = (selectedDataset) => {
            this.updateLocalAndSharedState({ selectedDataset });
        };
        this.updateLocalAndSharedState = (payload) => {
            this.setState(old => ({
                ...old,
                controlViewState: {
                    ...old.controlViewState,
                    ...payload
                }
            }));
            this.updateSharedState(payload);
        };
        this.updateSharedState = debounce((payload) => {
            if (this.props.sharedModel) {
                this.props.sharedModel.setControlViewState(payload);
            }
        }, 100);
        this.state = STOCK_STATE;
        this.onSharedModelPropChange(this.props.sharedModel);
    }
    componentWillUnmount() {
        if (this.props.sharedModel) {
            this.props.sharedModel.mainViewStateChanged.disconnect(this.sharedMainViewModelChanged);
            this.props.sharedModel.controlViewStateChanged.disconnect(this.sharedControlViewModelChanged);
        }
    }
    componentDidUpdate(oldProps, oldState) {
        if (oldProps.sharedModel === this.props.sharedModel) {
            return;
        }
        if (oldProps.sharedModel) {
            oldProps.sharedModel.changed.disconnect(this.sharedMainViewModelChanged);
            oldProps.sharedModel.controlViewStateChanged.disconnect(this.sharedControlViewModelChanged);
        }
        this.onSharedModelPropChange(this.props.sharedModel);
    }
    onSharedModelPropChange(sharedModel) {
        if (sharedModel) {
            sharedModel.mainViewStateChanged.connect(this.sharedMainViewModelChanged);
            sharedModel.controlViewStateChanged.connect(this.sharedControlViewModelChanged);
            this.setState(old => {
                var _a, _b, _c;
                const controlViewState = sharedModel.getControlViewState();
                const mainViewState = sharedModel.getMainViewState();
                controlViewState.selectedColor = (_a = controlViewState.selectedColor) !== null && _a !== void 0 ? _a : ':';
                controlViewState.modifiedDataRange =
                    (_b = controlViewState.modifiedDataRange) !== null && _b !== void 0 ? _b : mainViewState.dataRange;
                controlViewState.displayMode = (_c = controlViewState.displayMode) !== null && _c !== void 0 ? _c : '1:2:0';
                return {
                    ...old,
                    mainViewState,
                    controlViewState
                };
            });
        }
        else {
            this.setState(old => STOCK_STATE);
        }
    }
    render() {
        return (consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: "jpview-control-panel" },
            consume_shared_module_default_react_18_2_singleton_.createElement("div", { className: "lm-Widget p-Widget jpview-control-panel-title" },
                consume_shared_module_default_react_18_2_singleton_.createElement("h2", null, this.props.filePath)),
            consume_shared_module_default_react_18_2_singleton_.createElement(Accordion/* default */.A, { expanded: this.state.datasetPanel, sx: { margin: '0px 0px' } },
                consume_shared_module_default_react_18_2_singleton_.createElement(AccordionSummary/* default */.A, { expandIcon: consume_shared_module_default_react_18_2_singleton_.createElement(ExpandMore/* default */.A, null), "aria-controls": "dataSetPanela-content", id: "displayPanela-header", sx: panelTitleStyle, onClick: () => this.togglePanel('datasetPanel') },
                    consume_shared_module_default_react_18_2_singleton_.createElement("span", null, "Dataset")),
                consume_shared_module_default_react_18_2_singleton_.createElement(AccordionDetails/* default */.A, { sx: panelBodyStyle },
                    consume_shared_module_default_react_18_2_singleton_.createElement(DatasetPanel, { clientId: this.props.filePath, controlViewState: this.state.controlViewState, mainViewState: this.state.mainViewState, onSelectDatasetChange: this.onSelectDatasetChange }))),
            consume_shared_module_default_react_18_2_singleton_.createElement(Accordion/* default */.A, { expanded: this.state.displayPanel },
                consume_shared_module_default_react_18_2_singleton_.createElement(AccordionSummary/* default */.A, { expandIcon: consume_shared_module_default_react_18_2_singleton_.createElement(ExpandMore/* default */.A, null), "aria-controls": "displayPanela-content", id: "displayPanela-header", sx: panelTitleStyle, onClick: () => this.togglePanel('displayPanel') },
                    consume_shared_module_default_react_18_2_singleton_.createElement("span", null, "Display")),
                consume_shared_module_default_react_18_2_singleton_.createElement(AccordionDetails/* default */.A, { sx: panelBodyStyle },
                    consume_shared_module_default_react_18_2_singleton_.createElement(DisplayPanel, { clientId: "", onOpacityChange: this.onOpacityChange, onDisplayModeChange: this.onDisplayModeChange, controlViewState: this.state.controlViewState }))),
            consume_shared_module_default_react_18_2_singleton_.createElement(Accordion/* default */.A, { expanded: this.state.colorPanel },
                consume_shared_module_default_react_18_2_singleton_.createElement(AccordionSummary/* default */.A, { expandIcon: consume_shared_module_default_react_18_2_singleton_.createElement(ExpandMore/* default */.A, null), "aria-controls": "colorPanela-content", id: "colorPanela-header", sx: panelTitleStyle, onClick: () => this.togglePanel('colorPanel') },
                    consume_shared_module_default_react_18_2_singleton_.createElement("span", { className: "lm-Widget" }, "Color")),
                consume_shared_module_default_react_18_2_singleton_.createElement(AccordionDetails/* default */.A, { sx: panelBodyStyle, className: 'lm-Widget' },
                    consume_shared_module_default_react_18_2_singleton_.createElement(ColorPanel, { clientId: "", controlViewState: this.state.controlViewState, mainViewState: this.state.mainViewState, onRangeChange: this.onRangeChange, resetRange: this.resetRange, onColorSchemaChange: this.onColorSchemaChange, onSelectedColorChange: this.onSelectedColorChange }))),
            consume_shared_module_default_react_18_2_singleton_.createElement(Accordion/* default */.A, { expanded: this.state.filterPanel },
                consume_shared_module_default_react_18_2_singleton_.createElement(AccordionSummary/* default */.A, { expandIcon: consume_shared_module_default_react_18_2_singleton_.createElement(ExpandMore/* default */.A, null), "aria-controls": "filterPanela-content", id: "filterPanela-header", sx: panelTitleStyle, onClick: () => this.togglePanel('filterPanel') },
                    consume_shared_module_default_react_18_2_singleton_.createElement("span", null, "Warp by scalar")),
                consume_shared_module_default_react_18_2_singleton_.createElement(AccordionDetails/* default */.A, { sx: panelBodyStyle },
                    consume_shared_module_default_react_18_2_singleton_.createElement(WrapPanel, { clientId: "", controlViewState: this.state.controlViewState, onWarpActivationChange: this.onWarpActivationChange, onWarpFactorChange: this.onWarpFactorChange, mainViewState: this.state.mainViewState, onSelectedWarpChange: this.onSelectedWarpChange, onWarpUseNormalChange: this.onWarpUseNormalChange, onWarpNormalAxisChange: this.onWarpNormalAxisChange })))));
    }
}

;// ./lib/panelview/widget.js



class PanelWidget extends apputils_4_6_singleton_.ReactWidget {
    constructor(tracker) {
        var _a, _b;
        super();
        this._tracker = tracker;
        this._filePath = (_a = tracker.currentWidget) === null || _a === void 0 ? void 0 : _a.context.localPath;
        this._sharedModel = (_b = tracker.currentWidget) === null || _b === void 0 ? void 0 : _b.context.model.sharedModel;
        tracker.currentChanged.connect((_, changed) => {
            if (changed) {
                this._filePath = changed.context.localPath;
                this._sharedModel = changed.context.model.sharedModel;
            }
            else {
                this._filePath = undefined;
                this._sharedModel = undefined;
            }
            this.update();
        });
    }
    get tracker() {
        return this._tracker;
    }
    dispose() {
        super.dispose();
    }
    render() {
        return (consume_shared_module_default_react_18_2_singleton_.createElement(panelview_MainView, { filePath: this._filePath, sharedModel: this._sharedModel }));
    }
}

;// ./lib/reader/manager.js
class ParserManager {
    constructor() {
        this._parser = new Map();
    }
    registerParser(parser) {
        parser.supportedType.forEach(ext => {
            if (!this._parser.has(ext)) {
                this._parser.set(ext, parser);
            }
        });
    }
    get parser() {
        return this._parser;
    }
    supportedFormat() {
        return Array.from(this._parser.keys());
    }
    getParser(ext) {
        return this._parser.get(ext);
    }
}

;// ./lib/reader/meshioParser.js
class MeshIOParser {
    constructor() {
        this.supportedType = [
            'msh',
            'f3grid',
            'mdpa',
            'ply',
            'stl',
            'xdmf',
            'xmf',
            'cgns',
            'h5m',
            'inp',
            'avs',
            'xml',
            'e',
            'exo',
            'ex2',
            'hmf',
            'med',
            'mesh',
            'meshb',
            'bdf',
            'fem',
            'nas',
            'vol',
            'vol.gz',
            'obj',
            'off',
            'post',
            'post.gz',
            'dato',
            'dato.gz',
            'su2',
            'svg',
            'dat',
            'tec',
            'ele',
            'node',
            'ugrid',
            'wkt'
        ];
    }
    readFile(fileContent, fileExtension, fullPath, kernel) {
        if (!this.supportedType.includes(fileExtension)) {
            throw Error('Not supported file');
        }
        if (!kernel) {
            throw Error('Kernel is required for this file');
        }
        if (!fullPath) {
            throw Error('Full path is required for this file');
        }
        const content = kernel.startKernel().then(() => {
            const result = kernel.convertFile(fullPath, fileContent);
            return result;
        });
        return content;
    }
}

;// ./lib/reader/vtkParser.js
class VtkParser {
    constructor() {
        this.supportedType = ['vtu', 'vtk', 'vtp'];
        this.nativeSupport = true;
    }
    readFile(fileContent, fileExtension) {
        if (!this.supportedType.includes(fileExtension)) {
            throw Error('Not supported file');
        }
        return Promise.resolve({ binary: fileContent, type: fileExtension });
    }
}

;// ./lib/token.js

const IJupyterViewDocTracker = new coreutils_2_0_singleton_.Token('jupyterViewDocTracker');

;// ./lib/vtkTracker.js


class VtkTracker extends apputils_4_6_singleton_.WidgetTracker {
    constructor() {
        super(...arguments);
        this._widgetDisposed = new signaling_2_0_singleton_.Signal(this);
    }
    add(widget) {
        widget.disposed.connect(() => {
            this._widgetDisposed.emit(widget);
        });
        return super.add(widget);
    }
    get widgetDisposed() {
        return this._widgetDisposed;
    }
}

;// ./lib/index.js













const FACTORY = 'Jupyterview Factory';
const NAME_SPACE = 'jupyterview';
const activate = (app, restorer, themeManager, shell) => {
    const tracker = new VtkTracker({ namespace: NAME_SPACE });
    JupyterViewModel.kernel = new KernelExecutor({
        manager: app.serviceManager,
        jupyterLite: !!document.getElementById('jupyter-lite-main')
    });
    if (restorer) {
        restorer.restore(tracker, {
            command: 'docmanager:open',
            args: widget => ({ path: widget.context.path, factory: FACTORY }),
            name: widget => widget.context.path
        });
    }
    const parserManager = new ParserManager();
    const vtkParser = new VtkParser();
    parserManager.registerParser(vtkParser);
    const meshioParser = new MeshIOParser();
    parserManager.registerParser(meshioParser);
    const supportedFormat = parserManager.supportedFormat();
    // Creating the widget factory to register it so the document manager knows about
    // our new DocumentWidget
    const widgetFactory = new JupyterViewWidgetFactory({
        name: FACTORY,
        modelName: 'jupyterview-model',
        fileTypes: ['pvd', ...supportedFormat],
        defaultFor: ['pvd', ...supportedFormat]
    }, parserManager);
    // Add the widget to the tracker when it's created
    widgetFactory.widgetCreated.connect((sender, widget) => {
        // Notify the instance tracker if restore data needs to update.
        window.jupyterlabTheme = themeManager.theme;
        widget.context.pathChanged.connect(() => {
            tracker.save(widget);
        });
        themeManager.themeChanged.connect((_, changes) => widget.context.model.themeChanged.emit(changes));
        tracker.add(widget);
    });
    app.docRegistry.addWidgetFactory(widgetFactory);
    // Creating and registering the model factory for our custom DocumentModel
    const modelFactory = new JupyterViewModelFactory();
    app.docRegistry.addModelFactory(modelFactory);
    // const vtkSharedModelFactory: SharedDocumentFactory = () => {
    //   return new JupyterViewDoc();
    // };
    supportedFormat.forEach((fileType) => {
        const FILETYPE = fileType.toUpperCase();
        app.docRegistry.addFileType({
            name: fileType,
            displayName: FILETYPE,
            mimeTypes: ['binary'],
            extensions: [`.${fileType}`, `.${FILETYPE}`],
            fileFormat: 'base64',
            contentType: 'file'
        });
    });
    app.docRegistry.addFileType({
        name: 'pvd',
        displayName: 'PVD',
        mimeTypes: ['text'],
        extensions: ['.pvd', '.PVD'],
        fileFormat: 'text',
        contentType: 'file'
    });
    // drive.sharedModelFactory.registerDocumentFactory(
    //   'pvd',
    //   vtkSharedModelFactory
    // );
    console.log('JupyterLab extension jupyterview is activated!');
    shell.currentChanged.connect((shell, change) => {
        const widget = change.newValue;
        if (widget instanceof JupyterViewWidget) {
            window.dispatchEvent(new Event('resize'));
        }
    });
    return tracker;
};
/**
 * Initialization data for the jupyterview extension.
 */
const lib_plugin = {
    id: 'jupyterview:plugin',
    autoStart: true,
    requires: [application_4_5_singleton_.ILayoutRestorer, apputils_4_6_singleton_.IThemeManager, application_4_5_singleton_.ILabShell],
    provides: IJupyterViewDocTracker,
    activate
};
const controlPanel = {
    id: 'jupyterview:controlpanel',
    autoStart: true,
    requires: [application_4_5_singleton_.ILayoutRestorer, application_4_5_singleton_.ILabShell, IJupyterViewDocTracker],
    activate: (app, restorer, shell, tracker) => {
        const controlPanel = new PanelWidget(tracker);
        controlPanel.id = 'jupyterview::controlPanel';
        controlPanel.title.caption = 'JupyterView Control Panel';
        controlPanel.title.icon = jvcLightIcon;
        if (restorer) {
            restorer.add(controlPanel, NAME_SPACE);
        }
        app.shell.add(controlPanel, 'left');
    }
};
/* harmony default export */ const lib = ([lib_plugin, controlPanel]);


/***/ },

/***/ 4393
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   A: () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(4526);
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__);

let basePath = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__.PageConfig.getOption('baseUrl');
if (!basePath) {
    basePath = '/';
}
const _public_path__ = basePath + 'lab/extensions/jupyterview/static/';
const itkConfig = {
    itkModulesPath: _public_path__ + 'itk'
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (itkConfig);


/***/ }

}]);