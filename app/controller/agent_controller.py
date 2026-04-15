import uuid
import base64
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from app.core.orchestrator import Orchestrator
from app.memory_store.session_store import SessionStore


router = APIRouter(prefix="/api/v1", tags=["report"])
orchestrator = Orchestrator()
session_store = SessionStore()


class TextInput(BaseModel):
    content: str
    session_id: str | None = None


@router.post("/report/parse")
async def parse_report_text(input_data: TextInput):
    """文本报告解读"""
    request_id = str(uuid.uuid4())

    # 加载会话历史
    history = None
    if input_data.session_id:
        session_store.get_or_create_session(input_data.session_id)
        session_store.save_message(input_data.session_id, "user", input_data.content)
        history = session_store.get_messages(input_data.session_id)

    result = orchestrator.process(
        request_id=request_id,
        content=input_data.content,
        input_type="text",
        history=history,
    )

    # 保存 AI 回复到会话
    if input_data.session_id:
        session_store.save_message(input_data.session_id, "assistant", result.get("answer", ""))

    return result


@router.post("/report/upload")
async def upload_report(file: UploadFile = File(...)):
    """文件报告解读（PDF/图片）"""
    request_id = str(uuid.uuid4())
    content = await file.read()
    b64_content = base64.b64encode(content).decode("utf-8")

    input_type = "pdf" if file.filename and file.filename.endswith(".pdf") else "image"
    result = orchestrator.process(
        request_id=request_id,
        content=b64_content,
        input_type=input_type,
    )
    return result
