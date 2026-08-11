import os

COMFYUI_DEFAULT_URL = os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:8188")
WORKFLOW_DIR = os.path.join(os.path.dirname(__file__), "workflows")
os.makedirs(WORKFLOW_DIR, exist_ok=True)

# SSH 配置持久化文件
SSH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "ssh_config.json")


def get_comfyui_url():
    """获取当前 ComfyUI 地址，优先使用 SSH 隧道"""
    from ssh_tunnel import tunnel
    if tunnel.is_connected and tunnel.local_port:
        return f"http://127.0.0.1:{tunnel.local_port}"
    return COMFYUI_DEFAULT_URL
