import { app } from "../../scripts/app.js"

app.registerExtension({
  name: "xishen_common_resolution_filter",
  setup() {
    // 使用setup钩子确保扩展在正确时机加载
    console.log("Xishen Resolution Filter extension loaded");
  },
  
  async nodeCreated(node) {
    if (node.comfyClass !== "XishenCommonResolutionNode") return;
    
    console.log("Setting up filter for resolution node");
    
    // 等待更长时间确保节点完全初始化
    setTimeout(() => {
      const ratioWidget = node.widgets.find(w => w.name === "aspect_ratio");
      const resWidget = node.widgets.find(w => w.name === "resolution");
      
      if (!ratioWidget || !resWidget || !resWidget.options?.values) {
        console.error("Failed to find required widgets");
        return;
      }
      
      // 保存所有原始选项
      const allOptions = [...resWidget.options.values];
      console.log("All options:", allOptions.length);
      
      // 创建一个更可靠的过滤函数
      const filterByRatio = (ratio) => {
        // 构造精确的匹配模式
        const pattern = new RegExp(`\\(\\s*${ratio}\\s*\\)`);
        return allOptions.filter(opt => {
          const text = typeof opt === "string" ? opt : opt.label;
          return pattern.test(text);
        });
      };
      
      // 替换下拉框的渲染函数
      const originalCallback = ratioWidget.callback;
      ratioWidget.callback = function(value) {
        // 调用原始回调
        if (originalCallback) {
          originalCallback.call(this, value);
        }
        
        // 执行过滤
        const filtered = filterByRatio(value);
        console.log(`Filtered for ${value}: ${filtered.length} options`);
        
        // 更新resWidget的选项
        resWidget.options.values = filtered;
        
        // 确保有选中值
        if (filtered.length > 0) {
          // 如果当前值不在过滤列表中，选择第一个
          const currentValue = resWidget.value;
          const exists = filtered.some(opt => 
            (typeof opt === "string" && opt === currentValue) || 
            (opt.label && opt.label === currentValue)
          );
          
          if (!exists) {
            resWidget.value = typeof filtered[0] === "string" ? filtered[0] : filtered[0].label;
          }
        }
        
        // 强制刷新整个节点的UI
        if (resWidget.onChange) {
          resWidget.onChange(resWidget.value);
        }
        
        // 重新渲染画布
        if (node.graph) {
          node.graph.setDirtyCanvas(true, true);
        }
        
        // 直接更新DOM（如果可用）
        if (resWidget.widgetEl) {
          const select = resWidget.widgetEl.querySelector('select');
          if (select) {
            const currentVal = resWidget.value;
            select.innerHTML = '';
            
            filtered.forEach(opt => {
              const option = document.createElement('option');
              const label = typeof opt === "string" ? opt : opt.label;
              option.value = label;
              option.textContent = label;
              select.appendChild(option);
            });
            
            select.value = currentVal;
          }
        }
      };
      
      // 初始应用过滤
      ratioWidget.callback(ratioWidget.value);
      
    }, 500); // 增加等待时间确保节点完全初始化
  }
});

