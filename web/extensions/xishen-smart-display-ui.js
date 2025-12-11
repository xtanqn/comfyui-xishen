import { app } from '../../scripts/app.js';
import { ComfyWidgets } from '../../scripts/widgets.js';

// Displays input text on a node
// TODO: This should need to be so complicated. Refactor at some point.

app.registerExtension({
    name: "xishen.SmartDisplay",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "XishenSmartDisplayNode") {
            function populate(text) {
                if (this.widgets) {
                    // On older frontend versions there is a hidden converted-widget
                    const isConvertedWidget = +!!this.inputs?.[0].widget;
                    for (let i = isConvertedWidget; i < this.widgets.length; i++) {
                        this.widgets[i].onRemove?.();
                    }
                    this.widgets.length = isConvertedWidget;
                }

                const v = [...text];
                if (!v[0]) {
                    v.shift();
                }
                
                // 创建新的文本框
                for (let list of v) {
                    // Force list to be an array, not sure why sometimes it is/isn't
                    if (!(list instanceof Array)) list = [list];
                    for (const l of list) {
                        const w = ComfyWidgets["STRING"](this, "text_" + this.widgets?.length ?? 0, ["STRING", { multiline: true }], app).widget;
                        w.inputEl.readOnly = true;
                        w.inputEl.style.opacity = 0.6;
                        w.inputEl.style.resize = "none"; // 禁用手动调整大小
                        w.inputEl.style.padding = "8px";
                        w.inputEl.style.marginBottom = "8px";
                        w.inputEl.style.boxSizing = "border-box";
                        w.inputEl.style.lineHeight = "1.8"; // 增大行高，提升可读性
                        w.inputEl.style.fontSize = "9px";
                        w.inputEl.style.height = "80px"; // 设置单个文本框的固定高度
                        w.inputEl.style.overflowY = "auto"; // 内容过多时显示垂直滚动条
                        w.inputEl.style.overflowX = "hidden"; // 隐藏水平滚动条
                        
                        // 设置文本内容
                        w.value = l;
                    }
                }

                // 重置节点大小，确保它能正确调整
                this.size[1] = 0;
                
                // 计算所有文本框的总高度（每个固定80px + 8px间距）
                const isConvertedWidget = +!!this.inputs?.[0].widget;
                const textboxCount = this.widgets.length - isConvertedWidget;
                const totalTextboxesHeight = textboxCount * (80 + 8); // 80px高度 + 8px marginBottom
                
                // 等待DOM更新后重新计算大小
                requestAnimationFrame(() => {
                    // 重新计算节点大小
                    const newSize = this.computeSize();
                    if (newSize[0] < this.size[0]) {
                        newSize[0] = this.size[0];
                    }
                    
                    // 确保节点高度至少能容纳所有文本框
                    const headerHeight = 50; // 节点标题栏高度（包含内边距）
                    const requiredHeight = headerHeight + totalTextboxesHeight;
                    
                    if (newSize[1] < requiredHeight) {
                        newSize[1] = requiredHeight;
                    }
                    
                    this.size = newSize;
                    this.onResize?.(newSize);
                    app.graph.setDirtyCanvas(true, false);
                });
            }

            // When the node is executed we will be sent the input text, display this in the widget
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);
                populate.call(this, message.text);
            };

            const VALUES = Symbol();
            const configure = nodeType.prototype.configure;
            nodeType.prototype.configure = function () {
                // Store unmodified widget values as they get removed on configure by new frontend
                this[VALUES] = arguments[0]?.widgets_values;
                return configure?.apply(this, arguments);
            };

            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function () {
                onConfigure?.apply(this, arguments);
                const widgets_values = this[VALUES];
                if (widgets_values?.length) {
                    // In newer frontend there seems to be a delay in creating the initial widget
                    requestAnimationFrame(() => {
                        populate.call(this, widgets_values.slice(+(widgets_values.length > 1 && this.inputs?.[0].widget)));
                    });
                }
            };
        }
    },
});