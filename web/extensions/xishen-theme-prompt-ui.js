import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

app.registerExtension({
    name: "Xishen.ThemePrompt",
    async nodeCreated(node, app) {
        // 1. 确认这是我们的节点
        if (node.comfyClass !== "XishenThemePromptNode") return;

        // 2. 获取 Widget (输入框) 对象
        const mainCategoryWidget = node.widgets.find(w => w.name === "primary_category");
        const subCategoryWidget = node.widgets.find(w => w.name === "secondary_category");

        if (!mainCategoryWidget || !subCategoryWidget) return;

        // 3. 从后端 API 获取 JSON 数据
        let subjectsData = {};
        try {
            // 使用相对路径加载JSON文件
            const scriptUrl = new URL(import.meta.url);
            const scriptPath = scriptUrl.pathname;
            const extensionPath = scriptPath.substring(0, scriptPath.lastIndexOf('/') + 1);
            const jsonUrl = extensionPath + "xishen_theme_prompts.json";
            
            const response = await fetch(jsonUrl);
            subjectsData = await response.json();
        } catch (error) {
            console.error("Xishen Theme Prompt: Failed to fetch xishen_theme_prompts.json", error);
            return; // 失败则退出
        }

        // 4. 定义一个更新子菜单的函数
        const updateSubCategories = (selectedMain) => {
            const subItems = subjectsData[selectedMain] || ["None"];
            
            // 更新子菜单的选项列表
            subCategoryWidget.options.values = subItems;
            
            // 如果当前选中的子项不在新列表里，默认选中第一个
            if (!subItems.includes(subCategoryWidget.value)) {
                subCategoryWidget.value = subItems[0];
            }
        };

        // 5. 初始化主菜单
        // 获取所有主分类 Key
        const mainKeys = Object.keys(subjectsData);
        if (mainKeys.length > 0) {
            mainCategoryWidget.options.values = mainKeys;
            // 如果当前值为空或不在列表里，设为第一个
            if (!mainKeys.includes(mainCategoryWidget.value)) {
                mainCategoryWidget.value = mainKeys[0];
            }
            // 初始化子菜单
            updateSubCategories(mainCategoryWidget.value);
        }

        // 6. 监听主菜单的“回调/变更”事件
        // 保存原始的回调函数（如果有的话）
        const originalCallback = mainCategoryWidget.callback;
        
        mainCategoryWidget.callback = function(value) {
            // 更新子菜单
            updateSubCategories(value);
            
            // 触发重绘（让UI更新显示）
            if (node.graph) {
                node.setDirtyCanvas(true); 
            }
            
            // 如果原本有回调，执行它
            if (originalCallback) {
                return originalCallback.apply(this, arguments);
            }
        };
    }
});