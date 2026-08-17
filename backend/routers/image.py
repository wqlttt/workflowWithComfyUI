import time
import httpx
from fastapi import APIRouter
from config import load_ai_config, save_ai_config

router = APIRouter(prefix="/api/image", tags=["image"])


@router.post("/generate")
def generate_image(data: dict):
    """调用 llmgateway 中转站生成图片：提交任务 + 轮询获取结果"""
    cfg = load_ai_config()
    img_cfg = cfg.get("image", {})
    api_key = img_cfg.get("api_key", "")
    base_url = (img_cfg.get("base_url") or "https://www.llmgateway.cn").rstrip("/")
    model = data.get("model") or img_cfg.get("model", "gemini-3.1-flash-image-preview")
    prompt = (data.get("prompt") or "").strip()
    size = data.get("size") or "1024x1024"
    n = data.get("n") or 1

    if not api_key:
        return {"ok": False, "error": "未配置 llmgateway API Key，请在工具栏设置"}
    if not prompt:
        return {"ok": False, "error": "请输入提示词"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30) as client:
        # 1. 提交任务
        resp = client.post(
            f"{base_url}/v1/images/tasks",
            json={"model": model, "prompt": prompt, "size": size, "n": n},
            headers=headers,
        )
        if resp.status_code not in (200, 201, 202):
            return {"ok": False, "error": f"提交任务失败 ({resp.status_code}): {resp.text[:200]}"}
        task = resp.json()
        task_id = task.get("id")
        if not task_id:
            return {"ok": False, "error": f"未获取到任务 ID: {resp.text[:200]}"}

        # 2. 轮询任务状态
        for _ in range(60):
            time.sleep(3)
            poll = client.get(f"{base_url}/v1/images/tasks/{task_id}", headers=headers)
            if poll.status_code != 200:
                return {"ok": False, "error": f"查询任务失败 ({poll.status_code}): {poll.text[:200]}"}
            info = poll.json()
            status = info.get("status")

            if status == "completed":
                urls = info.get("result_urls") or []
                if not urls:
                    return {"ok": False, "error": "任务完成但未返回图片 URL"}
                return {"ok": True, "urls": urls}
            elif status == "failed":
                return {"ok": False, "error": f"任务失败: {info.get('error', '')}"}

        return {"ok": False, "error": "生成超时（超过 3 分钟）"}


@router.get("/config")
def get_image_config():
    cfg = load_ai_config()
    img = cfg.get("image", {})
    return {
        "name": img.get("name", "llmgateway"),
        "base_url": img.get("base_url", "https://www.llmgateway.cn"),
        "model": img.get("model", ""),
        "has_key": bool(img.get("api_key")),
    }


@router.post("/config")
def set_image_config(data: dict):
    cfg = load_ai_config()
    img = cfg.setdefault("image", {})
    if data.get("api_key"):
        img["api_key"] = data["api_key"]
    if data.get("model"):
        img["model"] = data["model"]
    if data.get("base_url"):
        img["base_url"] = data["base_url"]
    save_ai_config(cfg)
    return {"ok": True, "has_key": bool(img.get("api_key"))}
