# comfyui-xishen
随机生成一个整数，输出到文本。 
比如在使用ollama插件时由于提示词不变，首次执行有结果后第二次重新执行会直接跳过ollama。
此小插件每次执行自动更新提示词，就是为了解决ollama无法多次循环出提示词的痛点。 
A custom node for ComfyUI that generates random numbers as text output.

## Features

- Generate random numbers within a specified range (min/max)
- Output as text string compatible with CLIP Text Encode
- Force resample on each execution

## Installation
放在custom_nodes目录下无需安装依赖，重启生效
搜索xishen 新建节点使用
1. Clone this repository into your ComfyUI's `custom_nodes` directory.
2. Restart ComfyUI.

## Usage

- Find the node in `utils` category.
- Connect the output to CLIP Text Encode text input.