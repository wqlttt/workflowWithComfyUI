import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from config import get_comfyui_url

router = APIRouter(prefix="/api/comfyui", tags=["comfyui"])


def _url():
    return get_comfyui_url()


@router.get("/object_info")
async def get_object_info():
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{_url()}/object_info")
    return resp.json()


@router.post("/prompt")
async def queue_prompt(data: dict):
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{_url()}/prompt", json=data)
    result = resp.json()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/history/{prompt_id}")
async def get_history(prompt_id: str):
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{_url()}/history/{prompt_id}")
    return resp.json()


@router.get("/view")
async def view_image(filename: str, subfolder: str = "", type: str = "output"):
    params = {"filename": filename, "subfolder": subfolder, "type": type}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(f"{_url()}/view", params=params)
    return StreamingResponse(resp.aiter_bytes(), media_type=resp.headers.get("content-type", "image/png"))


@router.post("/upload/image")
async def upload_image(image: UploadFile = File(...), overwrite: bool = False):
    files = {"image": (image.filename, await image.read(), image.content_type)}
    data = {"overwrite": str(overwrite).lower()}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{_url()}/upload/image", data=data, files=files)
    return resp.json()


@router.get("/queue")
async def get_queue():
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{_url()}/queue")
    return resp.json()


@router.delete("/queue")
async def clear_queue():
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{_url()}/queue", json={"clear": True})
    return resp.json()
