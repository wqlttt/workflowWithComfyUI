import json
import os
import uuid
from fastapi import APIRouter, HTTPException
from config import WORKFLOW_DIR

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.get("")
async def list_workflows():
    """列出所有保存的工作流"""
    workflows = []
    for f in os.listdir(WORKFLOW_DIR):
        if f.endswith(".json"):
            path = os.path.join(WORKFLOW_DIR, f)
            with open(path) as fp:
                wf = json.load(fp)
            workflows.append({"id": wf.get("id", f[:-5]), "name": wf.get("name", f[:-5])})
    return workflows


@router.post("")
async def save_workflow(data: dict):
    """保存工作流"""
    wf_id = data.get("id") or str(uuid.uuid4())[:8]
    wf_name = data.get("name", wf_id)
    data["id"] = wf_id
    path = os.path.join(WORKFLOW_DIR, f"{wf_id}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return {"id": wf_id, "name": wf_name}


@router.get("/{wf_id}")
async def load_workflow(wf_id: str):
    """加载指定工作流"""
    path = os.path.join(WORKFLOW_DIR, f"{wf_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Not found")
    with open(path) as f:
        return json.load(f)


@router.delete("/{wf_id}")
async def delete_workflow(wf_id: str):
    """删除工作流"""
    path = os.path.join(WORKFLOW_DIR, f"{wf_id}.json")
    if os.path.exists(path):
        os.remove(path)
    return {"ok": True}
