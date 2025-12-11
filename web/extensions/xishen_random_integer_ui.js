// 文件：web/extensions/xishen_random_integer_ui.js
// 目的：在 XishenRandomIntegerNode 上添加一个真实按钮用于触发重置
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "xishen.random_integer_button",
    
    async setup() {
        console.log("Xishen Random Integer Button extension loaded");
    },
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 只处理 XishenRandomIntegerNode 类型的节点
        if (nodeData.name === "XishenRandomIntegerNode") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function() {
                const result = onNodeCreated?.apply(this, arguments);

                try {
                    // 在 UI 上添加按钮（不会作为输入端口）
                    const button = this.addWidget("button", "🔄 重新计数", null, () => {
                        try {
                            // 获取当前应该设置的重置值（1或2）
                            const resetValue = button._nextResetValue;
                            
                            // 查找或创建reset_sequence widget
                            let resetWidget = this.widgets.find(w => w.name === "reset_sequence");
                            if (!resetWidget) {
                                // 创建隐藏的reset_sequence widget
                                resetWidget = this.addWidget("number", "reset_sequence", 0, () => {}, {
                                    min: 0, max: 2, step: 1,
                                    hidden: true // 隐藏widget
                                });
                            }
                            
                            // 设置reset_sequence值
                            resetWidget.value = resetValue;

                            // 触发图重新计算（触发节点执行）
                            if (this.graph && typeof this.graph.setDirtyCanvas === "function") {
                                this.graph.setDirtyCanvas(true, true);
                            }

                            // 切换下一次的重置值（1变2，2变1）
                            button._nextResetValue = resetValue === 1 ? 2 : 1;
                        } catch (err) {
                            console.error("xishen button callback error:", err);
                        }
                    });

                    // 确保按钮不会被序列化到工作流中
                    button.serialize = false;
                    
                    // 为按钮添加状态变量，用于跟踪下一次应该设置的重置值
                    button._nextResetValue = 1; // 初始值设为1
                } catch (error) {
                    // 非致命：不要冒泡错误到全局（避免崩溃其他扩展）
                    console.error("xishen_random_integer_ui onNodeCreated error:", error);
                }

                return result;
            };
        }
    }
});
