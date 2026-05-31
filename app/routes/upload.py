from fastapi import APIRouter, File, UploadFile
from app.graph.document_graph import ingest_documents
from app.services.file_reader import extract_text_from_file

router = APIRouter()

@router.post("/upload-docs")
async def upload_docs(
    resume: UploadFile = File(...),
    jd: UploadFile = File(...)
):
    resume_text = await extract_text_from_file(resume)
    jd_text = await extract_text_from_file(jd)
    state = await ingest_documents(resume_text, jd_text)

    return {
        "message": "Documents uploaded & parsed successfully.",
        "session_id": state["session_id"],
        "resume_preview": resume_text[:500],
        "jd_preview": jd_text[:500]
    }
