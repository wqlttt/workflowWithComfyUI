import json
import os
from fastapi import APIRouter
from config import PROJECT_FILE

router = APIRouter(prefix="/api/project", tags=["project"])


@router.post("/save")
async def save_project(data: dict):
    """保存当前项目快照（工作流 + 输出结果）到文件"""
    data.setdefault("saved_at", __import__("datetime").datetime.now().isoformat())
    try:
        with open(PROJECT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/load")
async def load_project():
    """加载项目快照"""
    if not os.path.exists(PROJECT_FILE):
        return {"nodes": [], "edges": [], "generated_images": []}
    try:
        with open(PROJECT_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"nodes": [], "edges": [], "generated_images": []}
