import asyncio
import json
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from routers import comfyui, workflow
from config import get_comfyui_url, SSH_CONFIG_FILE
from ssh_tunnel import tunnel

app = FastAPI(title="ComfyUI Workflow Wrapper")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(comfyui.router)
app.include_router(workflow.router)


@app.get("/api/health")
async def health():
    url = get_comfyui_url()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{url}/system_stats")
        return {
            "status": "ok",
            "comfyui": resp.json(),
            "comfyui_url": url,
            "tunnel_active": tunnel.is_connected,
        }
    except Exception:
        return {
            "status": "ok",
            "comfyui": "unreachable",
            "comfyui_url": url,
            "tunnel_active": tunnel.is_connected,
        }


# ── SSH Tunnel 管理 ──

@app.post("/api/tunnel/connect")
async def tunnel_connect(data: dict):
    """建立 SSH 隧道"""
    try:
        local_port = tunnel.connect(
            host=data["host"],
            port=data.get("port", 22),
            username=data["username"],
            password=data.get("password"),
            key_file=data.get("key_file"),
            remote_port=data.get("remote_port", 8188),
            local_port=data.get("local_port", 8189),
        )
        # 保存配置
        cfg = {k: v for k, v in data.items() if k != "password"}
        with open(SSH_CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)

        return {"ok": True, "local_port": local_port, "comfyui_url": get_comfyui_url()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/tunnel/disconnect")
async def tunnel_disconnect():
    tunnel.disconnect()
    return {"ok": True}


@app.get("/api/tunnel/status")
async def tunnel_status():
    return {
        "connected": tunnel.is_connected,
        "local_port": tunnel.local_port,
        "comfyui_url": get_comfyui_url(),
    }


# ── 服务器 GPU 状态 ──

@app.get("/api/server/gpu")
async def gpu_status():
    if not tunnel.is_connected:
        return {"ok": False, "error": "SSH 隧道未连接"}

    result = tunnel.get_gpu_status()
    return result


@app.get("/api/server/exec")
async def exec_command(cmd: str):
    """执行远程命令（限制白名单）"""
    ALLOWED = ["nvidia-smi", "df -h", "free -h", "ls"]
    if not any(cmd.startswith(a) for a in ALLOWED):
        return {"ok": False, "error": "不允许的命令"}
    if not tunnel.is_connected:
        return {"ok": False, "error": "SSH 隧道未连接"}
    return tunnel.exec_command(cmd)


# ── WebSocket ──

@app.websocket("/ws/progress/{prompt_id}")
async def ws_progress(websocket: WebSocket, prompt_id: str):
    await websocket.accept()
    url = get_comfyui_url()
    try:
        while True:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{url}/history/{prompt_id}")
                data = resp.json()
                if prompt_id in data:
                    await websocket.send_json({"status": "completed", "data": data[prompt_id]})
                    break
                else:
                    q_resp = await client.get(f"{url}/queue")
                    queue = q_resp.json()
                    running = queue.get("queue_running", [])
                    pending = queue.get("queue_pending", [])
                    position = None
                    for i, item in enumerate(running):
                        if item[1] == prompt_id:
                            position = i
                            break
                    for i, item in enumerate(pending):
                        if item[1] == prompt_id:
                            position = len(running) + i
                            break
                    await websocket.send_json({
                        "status": "progress",
                        "queue_position": position,
                        "queue_running": len(running),
                        "queue_pending": len(pending),
                    })
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
