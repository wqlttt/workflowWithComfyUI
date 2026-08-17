import json
import os

COMFYUI_DEFAULT_URL = os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:8188")
WORKFLOW_DIR = os.path.join(os.path.dirname(__file__), "workflows")
os.makedirs(WORKFLOW_DIR, exist_ok=True)

# 项目快照文件（保存工作流 + 输出结果）
PROJECT_FILE = os.path.join(os.path.dirname(__file__), "project.json")

# SSH 配置持久化文件
SSH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "ssh_config.json")

# AI 配置持久化文件（API Key 写死在这里，支持多个提供商/中转站）
AI_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "ai_config.json")

DEFAULT_AI_CONFIG = {
    "providers": [
        {
            "name": "DeepSeek官方",
            "base_url": "https://api.deepseek.com",
            "api_key": "",
            "models": ["deepseek-chat", "deepseek-reasoner"],
        }
    ],
    "image": {
        "name": "llmgateway",
        "base_url": "https://www.llmgateway.cn",
        "api_key": "",
        "model": "gemini-3.1-flash-image-preview",
    },
}


def load_ai_config():
    if not os.path.exists(AI_CONFIG_FILE):
        with open(AI_CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_AI_CONFIG, f, indent=2, ensure_ascii=False)
        return {**DEFAULT_AI_CONFIG}
    with open(AI_CONFIG_FILE) as f:
        cfg = json.load(f)
    return {**DEFAULT_AI_CONFIG, **cfg}


def save_ai_config(cfg):
    with open(AI_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def get_comfyui_url():
    """获取当前 ComfyUI 地址，优先使用 SSH 隧道"""
    from ssh_tunnel import tunnel
    if tunnel.is_connected and tunnel.local_port:
        return f"http://127.0.0.1:{tunnel.local_port}"
    return COMFYUI_DEFAULT_URL
