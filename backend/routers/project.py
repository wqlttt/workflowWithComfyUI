import json
import os
import uuid
from datetime import datetime
from fastapi import APIRouter
from config import PROJECTS_DIR

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _project_path(pid):
    return os.path.join(PROJECTS_DIR, f"{pid}.json")


@router.get("")
async def list_projects():
    projects = []
    for f in os.listdir(PROJECTS_DIR):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(PROJECTS_DIR, f), encoding="utf-8") as fp:
                p = json.load(fp)
            projects.append({
                "id": p.get("id", f[:-5]),
                "name": p.get("name", "未命名"),
                "updated_at": p.get("updated_at", ""),
                "node_count": len(p.get("nodes", [])),
                "image_count": len(p.get("generated_images", [])),
            })
        except Exception:
            continue
    projects.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return projects


@router.post("")
async def create_project(data: dict):
    pid = data.get("id") or uuid.uuid4().hex[:12]
    name = (data.get("name") or "未命名项目").strip()
    now = datetime.now().isoformat()
    project = {
        "id": pid,
        "name": name,
        "nodes": data.get("nodes", []),
        "edges": data.get("edges", []),
        "generated_images": data.get("generated_images", []),
        "created_at": now,
        "updated_at": now,
    }
    with open(_project_path(pid), "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)
    return project


@router.get("/{pid}")
async def get_project(pid: str):
    path = _project_path(pid)
    if not os.path.exists(path):
        return {"id": pid, "name": "", "nodes": [], "edges": [], "generated_images": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@router.put("/{pid}")
async def update_project(pid: str, data: dict):
    path = _project_path(pid)
    project = {"id": pid, "name": "", "nodes": [], "edges": [], "generated_images": []}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            project = json.load(f)
    if data.get("name") is not None:
        project["name"] = data["name"]
    if data.get("nodes") is not None:
        project["nodes"] = data["nodes"]
    if data.get("edges") is not None:
        project["edges"] = data["edges"]
    if data.get("generated_images") is not None:
        project["generated_images"] = data["generated_images"]
    project["updated_at"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)
    return {"ok": True}


@router.delete("/{pid}")
async def delete_project(pid: str):
    path = _project_path(pid)
    if os.path.exists(path):
        os.remove(path)
    return {"ok": True}
