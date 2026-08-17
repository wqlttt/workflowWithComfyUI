import json
import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from config import load_ai_config, save_ai_config

router = APIRouter(prefix="/api/ai", tags=["ai"])

SYSTEM_PROMPT = """你是一个专业的人物角色三视图提示词生成器。根据用户提供的角色描述，生成一个用于 AI 图像生成的完整提示词。

要求：
1. 输出英文提示词（图像生成模型对英文理解更好）
2. 生成 character turnaround sheet（角色三视图）格式，必须包含正面(front view)、侧面(side view)、背面(back view)三个视角
3. 详细描述角色的外观特征：发型、发色、瞳色、服装、配饰、配色、体型、年龄、气质等
4. 加入高质量画质词：masterpiece, best quality, highly detailed 等
5. 只输出提示词本身，不要任何解释、标题或 markdown 格式

输出格式示例：
character turnaround sheet, three views (front view, side view, back view), [角色详细描述], full body, white background, masterpiece, best quality"""


def _find_provider(name):
    cfg = load_ai_config()
    for p in cfg.get("providers", []):
        if p["name"] == name:
            return p
    return None


def _public_providers():
    cfg = load_ai_config()
    return [
        {
            "name": p["name"],
            "base_url": p.get("base_url", ""),
            "models": p.get("models", []),
            "has_key": bool(p.get("api_key")),
        }
        for p in cfg.get("providers", [])
    ]


def _error_stream(msg):
    return StreamingResponse(
        iter([f"data: {json.dumps({'error': msg})}\n\n"]),
        media_type="text/event-stream",
    )


# ── 生成 ──

@router.post("/generate")
async def generate(data: dict):
    provider_name = data.get("provider", "")
    model = data.get("model", "")
    description = data.get("description", "")
    temperature = data.get("temperature", 0.8)

    provider = _find_provider(provider_name)
    if not provider:
        return _error_stream("未找到该提供商")
    api_key = provider.get("api_key", "")
    base_url = provider.get("base_url", "").rstrip("/")
    if not api_key:
        return _error_stream(f"提供商「{provider_name}」未配置 API Key")
    if not model:
        model = (provider.get("models") or [""])[0]
    if not description:
        return _error_stream("请输入角色描述")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": description},
        ],
        "stream": True,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async def event_stream():
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST", f"{base_url}/chat/completions", json=payload, headers=headers
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        err_text = body.decode(errors="replace")
                        yield f"data: {json.dumps({'error': f'返回 {resp.status_code}: {err_text}'})}\n\n"
                        return
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            yield f"{line}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── 提供商管理 ──

@router.get("/providers")
async def list_providers():
    return _public_providers()


@router.post("/providers")
async def add_provider(data: dict):
    cfg = load_ai_config()
    name = (data.get("name") or "").strip()
    if not name:
        return {"ok": False, "error": "名称不能为空"}
    if _find_provider(name):
        return {"ok": False, "error": "名称已存在"}
    cfg.setdefault("providers", []).append({
        "name": name,
        "base_url": (data.get("base_url") or "https://api.deepseek.com").rstrip("/"),
        "api_key": data.get("api_key", ""),
        "models": data.get("models", []),
    })
    save_ai_config(cfg)
    return {"ok": True, "providers": _public_providers()}


@router.put("/providers/{name}")
async def update_provider(name: str, data: dict):
    cfg = load_ai_config()
    for p in cfg.get("providers", []):
        if p["name"] == name:
            if data.get("base_url"):
                p["base_url"] = data["base_url"].rstrip("/")
            if data.get("api_key"):
                p["api_key"] = data["api_key"]
            save_ai_config(cfg)
            return {"ok": True, "providers": _public_providers()}
    return {"ok": False, "error": "未找到该提供商"}


@router.delete("/providers/{name}")
async def delete_provider(name: str):
    cfg = load_ai_config()
    cfg["providers"] = [p for p in cfg.get("providers", []) if p["name"] != name]
    save_ai_config(cfg)
    return {"ok": True, "providers": _public_providers()}


# ── 测试连接 ──

@router.post("/providers/{name}/test")
async def test_provider(name: str):
    provider = _find_provider(name)
    if not provider:
        return {"ok": False, "error": "未找到该提供商"}
    api_key = provider.get("api_key", "")
    base_url = provider.get("base_url", "").rstrip("/")
    if not api_key:
        return {"ok": False, "error": "未配置 API Key"}

    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            # 1. 尝试 /models 列出模型（多数中转站支持）
            resp = await client.get(f"{base_url}/models", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                if models:
                    cfg = load_ai_config()
                    for p in cfg.get("providers", []):
                        if p["name"] == name:
                            p["models"] = models
                    save_ai_config(cfg)
                    return {"ok": True, "message": f"连接成功，发现 {len(models)} 个模型", "models": models}

            # 2. /models 不可用，尝试发一个最小 chat 请求
            test_model = (provider.get("models") or ["gpt-3.5-turbo"])[0]
            chat_resp = await client.post(
                f"{base_url}/chat/completions",
                json={
                    "model": test_model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                },
                headers={**headers, "Content-Type": "application/json"},
            )
            if chat_resp.status_code == 200:
                return {"ok": True, "message": "连接成功（chat 接口可用）", "models": provider.get("models", [])}
            err_text = chat_resp.text[:200]
            return {"ok": False, "error": f"连接失败 HTTP {chat_resp.status_code}: {err_text}"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


# ── 模型管理 ──

@router.post("/providers/{name}/models")
async def add_model(name: str, data: dict):
    cfg = load_ai_config()
    model = (data.get("name") or "").strip()
    for p in cfg.get("providers", []):
        if p["name"] == name:
            if model and model not in p["models"]:
                p["models"].append(model)
                save_ai_config(cfg)
            return {"ok": True, "models": p["models"]}
    return {"ok": False, "error": "未找到该提供商"}


@router.delete("/providers/{name}/models/{model}")
async def delete_model(name: str, model: str):
    cfg = load_ai_config()
    for p in cfg.get("providers", []):
        if p["name"] == name:
            if model in p["models"]:
                p["models"].remove(model)
                save_ai_config(cfg)
            return {"ok": True, "models": p["models"]}
    return {"ok": False, "error": "未找到该提供商"}
