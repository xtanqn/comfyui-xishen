# comfyui-xishen / ComfyUI Xishen Nodes

## 简介 / Overview
申明：本插件为方便个人使用的整合节点包，部分节点实现参考开源代码，版权归属原作者，本人不做任何版权申明，所有人可以随意修改使用，且本人不承诺后续更新，如有需求可以ISSUES。
- 插件包提供五个节点：`随机整数-xishen`、`常用分辨率-xishen`、`常用提示词-xishen`、`去空行-xishen`、`智能展示文本-xishen`。
- 复制到 ComfyUI 的 `custom_nodes` 目录并重启后即可使用，搜索 `xishen` 即可找到。
- This plugin provides five nodes: `随机整数-xishen`, `常用分辨率-xishen`, `常用提示词-xishen`, `去空行-xishen`, and `智能展示文本-xishen`.
- Copy into ComfyUI `custom_nodes` and restart; search `xishen` to find them.

## 安装 / Installation
- 将仓库放入 ComfyUI 的 `custom_nodes` 目录，无需额外依赖。
- 重启 ComfyUI 后，搜索 `xishen` 添加节点。
- Clone this repository into ComfyUI `custom_nodes` with no extra deps.
- Restart ComfyUI and search `xishen` to add nodes.

## 节点 / Nodes

### 智能展示文本-xishen / Smart Display Text - xishen
- 类别 Category: `xishen`
- 输入 Inputs: `text`(`STRING`, 强制输入)
- 输出 Outputs: `STRING`
- 用法 Usage: 智能展示多行文本内容，自动处理换行符并过滤空行，提供良好的视觉体验。
- Notes: 支持多行文本显示，固定高度文本框带滚动条，节点窗口自动适应内容大小。

### 编辑提示词-xishen / Edit Prompt - xishen
- 类别 Category: `xishen`
- 输入 Inputs: `text`(`STRING`)
- 输出 Outputs: `STRING`
- 用法 Usage: 接收文本输入，暂停工作流执行，允许用户编辑文本内容，点击"继续执行"按钮后将编辑后的文本作为输出。
- Notes: 支持多行文本编辑，暂停工作流等待用户输入，实时更新节点上的文本内容，提供取消和确认按钮控制工作流状态。

### 随机整数-xishen / Random Integer - xishen
- 类别 Category: `xishen`
- 输入 Inputs: `min_value`, `max_value`, `mode`(`random`/`sequence`), `seed`
- 输出 Outputs: `number_text`(`STRING`), `number_int`(`INT`)
- 用法 Usage: 适用于提示词扰动或循环自增；`number_text` 可接入 `CLIP Text Encode` 文本输入。
- Notes: `random` 使用给定 `seed` 产生稳定随机；`sequence` 在范围内递增并循环。

### 常用分辨率-xishen / Common Resolutions - xishen
- 类别 Category: `xishen`
- 输入 Inputs: `resolution`(预设分辨率列表), `batch_size`
- 输出 Outputs: `Latent`(`LATENT`), `Width`(`INT`), `Height`(`INT`)
- 用法 Usage: 将 `Latent` 连接到 `KSampler` 的 `latent_image`；`Width/Height` 提供给需要分辨率的节点。
- 说明 Notes: 选择的宽高会自动量化为 16 的倍数；潜空间尺寸为 `[batch_size, 4, height//8, width//8]`。

### 常用提示词-xishen / Common Prompts - xishen
- 类别 Category: `xishen`
- 输入 Inputs: `category`(`人物`/`风景`), `prompt_key`(`a`/`b`)
- 输出 Outputs: `number_text`(`STRING`), `number_int`(`INT`)
- 用法 Usage: 根据分类与键返回对应文本（当前示例为 `a`/`b`）；`number_text` 可接入 `CLIP Text Encode`；`number_int` 可用于分支逻辑或索引选择。

### 去空行-xishen / Remove Empty Lines - xishen
- 类别 Category: `xishen`
- 输入 Inputs: `text`(`STRING`, 支持多行)
- 输出 Outputs: `text`(`STRING`)
- 用法 Usage: 去除首尾及中间的所有空白行（仅空白或空格的行），保留非空行原有文本与换行风格；适合在传入文本编码前进行清理。

## 使用 / Usage
- 在搜索框输入 `xishen` 即可找到五个节点。
- 将 `随机整数-xishen` 的 `number_text` 输出接入文本编码或任何字符串输入节点。
- 将 `常用分辨率-xishen` 的 `Latent` 输出接入采样器；`Width/Height` 按需使用。
- 将 `常用提示词-xishen` 的 `number_text` 接入文本编码；`number_int` 用于索引或分支。
- 将 `去空行-xishen` 的 `text` 输出用于清理结果，接入文本编码或其他字符串节点。
- 使用 `智能展示文本-xishen` 节点查看多行文本内容，提供良好的视觉体验。
- Search `xishen` to find five nodes.
- Connect `number_text` from `随机整数-xishen` to text encoders or string inputs.
- Connect `Latent` from `常用分辨率-xishen` to samplers; use `Width/Height` as needed.
- Use `常用提示词-xishen` for category-based prompt outputs; `number_int` for branching.
- Use `去空行-xishen` to strip blank lines while preserving original line endings.
- 参考项目：
  - [comfyui-prompt-control](https://github.com/asagi4/comfyui-prompt-control)
  - [ComfyUI_Comfyroll_CustomNodes](https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes)
## 许可 / License
- 使用仓库内的 `LICENSE` 文件；MIT 许可。
- See repository `LICENSE`; MIT licensed.
