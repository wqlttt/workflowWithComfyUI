# WorkflowWithComfyUI

可视化工作流编辑器，封装 ComfyUI API，通过 SSH 隧道连接云端 GPU 服务器执行 AI 图像/视频生成。

## 架构

```
前端 (Vue 3)
  │
  ├─ 输入节点 ──PARAMS──> ComfyUI节点 ──RESULT──> 输出节点
  │                        │
  │                    上传工作流 JSON
  │                    (含 {{占位符}})
  │
  ▼
FastAPI 后端
  │
  ├─ SSH 隧道 (paramiko) ──> 端口转发
  ├─ ComfyUI API 代理 (prompt / history / view / upload)
  └─ WebSocket 实时进度推送
  │
  ▼
AutoDL GPU 服务器 : ComfyUI
```

## 功能

- **3 节点画布** — 输入、ComfyUI、输出，拖拽连线即可编排工作流
- **SSH 隧道** — 填写 AutoDL 账号密码，自动建立端口转发，无需手动暴露端口
- **GPU 监控** — 连接后右上角实时显示 GPU 利用率、显存、温度、功耗
- **工作流模板** — 上传 ComfyUI 工作流 JSON，用 `{{参数名}}` 占位符标记动态字段
- **占位符注入** — 执行时自动将输入节点参数（prompt、seed、width 等）注入工作流模板
- **实时进度** — WebSocket 推送队列位置和执行状态
- **图片预览** — 生成结果直接显示在右下角
- **保存/加载** — 工作流持久化，可随时加载复用

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Conda (推荐)

### 后端

```bash
# 激活环境（已有 fastapi / httpx / paramiko）
conda activate usually

# 安装缺失依赖
pip install aiofiles python-multipart paramiko

cd backend
uvicorn main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173

## 使用指南

### 1. 连接服务器

点击工具栏 **SSH** 按钮，填写 AutoDL 服务器信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| 主机地址 | AutoDL 实例地址 | `region-1.autodl.com` |
| 端口 | SSH 端口 | `22` |
| 用户名 | 通常为 root | `root` |
| 密码 | AutoDL 登录密码 | - |
| ComfyUI 端口 | 服务端口 | `8188` |
| 本地转发端口 | 本地监听端口 | `8189` |

连接成功按钮变绿 **SSH ✓**，右上角出现 GPU 状态面板。

### 2. 编排工作流

从左侧面板拖拽三个节点到画布，依次连线：

```
[输入] ──PARAMS──> [ComfyUI] ──RESULT──> [输出]
```

### 3. 配置节点

**输入节点** — 选择生成类型（文生图/文生视频/图生图），填写提示词、种子、尺寸。

**ComfyUI 节点** — 上传工作流 JSON 配置文件。文件中的动态参数使用 `{{参数名}}` 占位：

```json
{
  "6": {
    "inputs": {
      "text": "{{prompt}}",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "3": {
    "inputs": {
      "seed": {{seed}},
      "steps": 20,
      "width": {{width}},
      "height": {{height}}
    },
    "class_type": "KSampler"
  }
}
```

支持的全部占位符：`{{prompt}}` / `{{negative_prompt}}` / `{{seed}}` / `{{width}}` / `{{height}}` / `{{batch_size}}`

### 4. 执行

点击 **执行** 按钮，查看输出结果。

## 项目结构

```
├── backend/
│   ├── main.py              # FastAPI 入口 + WebSocket + Tunnel API
│   ├── config.py            # 动态 URL 配置
│   ├── ssh_tunnel.py        # SSH 隧道（连接 + nvidia-smi）
│   ├── routers/
│   │   ├── comfyui.py       # ComfyUI API 代理
│   │   └── workflow.py      # 工作流 CRUD
│   └── requirements.txt
│
└── frontend/src/
    ├── App.vue               # 三栏布局
    ├── api/index.js          # 后端 API 封装
    ├── utils/nodeDefinitions.js  # 节点定义 + 占位符注入
    ├── stores/workflow.js    # Pinia 状态
    └── components/
        ├── Canvas.vue        # 画布 (vue-flow)
        ├── NodePanel.vue     # 可拖拽节点列表
        ├── PropertyPanel.vue # 属性编辑面板
        ├── Toolbar.vue       # 工具栏 + SSH + GPU
        └── nodes/
            └── BaseNode.vue  # 节点渲染组件
```

## API 端点

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/tunnel/connect` | POST | 建立 SSH 隧道 |
| `/api/tunnel/disconnect` | POST | 断开隧道 |
| `/api/tunnel/status` | GET | 隧道状态 |
| `/api/server/gpu` | GET | GPU 状态 |
| `/api/comfyui/prompt` | POST | 提交工作流 |
| `/api/comfyui/history/{id}` | GET | 执行历史 |
| `/api/comfyui/view` | GET | 获取图片 |
| `/api/comfyui/upload/image` | POST | 上传图片 |
| `/api/workflows` | GET/POST | 工作流列表/保存 |
| `/api/workflows/{id}` | GET/DELETE | 工作流加载/删除 |
| `/ws/progress/{prompt_id}` | WS | 执行进度 |

## License

MIT
