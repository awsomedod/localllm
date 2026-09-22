import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError

from db import (
    create_house_votes as db_create_house_votes,
    create_members as db_create_members,
    delete_house_vote as db_delete_house_vote,
    delete_member as db_delete_member,
    edit_house_vote as db_edit_house_vote,
    edit_member as db_edit_member,
    get_house_vote as db_get_house_vote,
    get_member as db_get_member,
    init_db,
    list_house_votes as db_list_house_votes,
    list_members as db_list_members,
    set_house_vote_summary as db_set_house_vote_summary,
)
from summarize import summarize_bill_text_stream

init_db()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def paginated(items, total, offset, limit):
    return {
        "items": items,
        "pagination": {
            "count": total,
            "limit": limit,
            "offset": offset,
        },
    }


def validate_pagination(offset: int, limit: int):
    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be >= 0")
    if limit < 1 or limit > 250:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 250")


@app.get("/members")
def list_members(congress: int | None = None, offset: int = 0, limit: int = 20):
    validate_pagination(offset, limit)
    items, total = db_list_members(congress=congress, offset=offset, limit=limit)
    return paginated(items, total, offset, limit)


@app.get("/members/{bioguide_id}/{congress}")
def get_member(bioguide_id: str, congress: int):
    row = db_get_member(bioguide_id, congress)
    if row is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return row


# @app.post("/members", status_code=201)
# def create_members(payload):
#     data = payload.model_dump()
#     try:
#         db_create_members([data])
#     except IntegrityError:
#         raise HTTPException(status_code=409, detail="Member already exists")
#     return db_get_member(data["bioguide_id"], data["congress"])


# @app.patch("/members/{bioguide_id}/{congress}")
# def edit_member(bioguide_id: str, congress: int, payload):
#     row = db_edit_member(bioguide_id, congress, payload.model_dump(exclude_unset=True))
#     if row is None:
#         raise HTTPException(status_code=404, detail="Member not found")
#     return row


# @app.delete("/members/{bioguide_id}/{congress}", status_code=204)
# def delete_member(bioguide_id: str, congress: int):
#     if not db_delete_member(bioguide_id, congress):
#         raise HTTPException(status_code=404, detail="Member not found")


@app.get("/house-votes")
def list_house_votes(congress: int | None = None, offset: int = 0, limit: int = 20):
    validate_pagination(offset, limit)
    items, total = db_list_house_votes(congress=congress, offset=offset, limit=limit)
    return paginated(items, total, offset, limit)


@app.get("/house-votes/{identifier}")
def get_house_vote(identifier: int):
    row = db_get_house_vote(identifier)
    if row is None:
        raise HTTPException(status_code=404, detail="House vote not found")
    return row


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/house-votes/{identifier}/summary")
def summarize_house_vote(identifier: int):
    vote = db_get_house_vote(identifier)
    if vote is None:
        raise HTTPException(status_code=404, detail="House vote not found")
    if vote.get("summary"):
        return vote
    bill = vote.get("text")
    full_text = bill.get("full_text") if isinstance(bill, dict) else None
    if not full_text:
        raise HTTPException(status_code=400, detail="Vote has no legislation text to summarize")
    label = " ".join(
        part for part in (vote.get("legislationType"), vote.get("legislationNumber")) if part
    ) or "this measure"

    def events():
        yield _sse({"type": "status", "message": "Starting…"})
        try:
            for event in summarize_bill_text_stream(full_text, label):
                if event.get("type") == "done":
                    db_set_house_vote_summary(identifier, event["summary"])
                yield _sse(event)
        except Exception as exc:
            yield _sse({"type": "error", "detail": f"LLM summarizer failed: {exc}"})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# @app.post("/house-votes", status_code=201)
# def create_house_vote(payload):
#     data = payload.model_dump()
#     try:
#         db_create_house_votes([data])
#     except IntegrityError:
#         raise HTTPException(status_code=409, detail="House vote already exists")
#     return db_get_house_vote(data["identifier"])


# @app.patch("/house-votes/{identifier}")
# def edit_house_vote(identifier: int, payload):
#     row = db_edit_house_vote(identifier, payload.model_dump(exclude_unset=True))
#     if row is None:
#         raise HTTPException(status_code=404, detail="House vote not found")
#     return row


# @app.delete("/house-votes/{identifier}", status_code=204)
# def delete_house_vote(identifier: int):
#     if not db_delete_house_vote(identifier):
#         raise HTTPException(status_code=404, detail="House vote not found")
