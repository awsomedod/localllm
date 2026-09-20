from fastapi import FastAPI, HTTPException
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
)

init_db()
app = FastAPI()


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


@app.post("/members", status_code=201)
def create_members(payload):
    data = payload.model_dump()
    try:
        db_create_members([data])
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Member already exists")
    return db_get_member(data["bioguide_id"], data["congress"])


@app.patch("/members/{bioguide_id}/{congress}")
def edit_member(bioguide_id: str, congress: int, payload):
    row = db_edit_member(bioguide_id, congress, payload.model_dump(exclude_unset=True))
    if row is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return row


@app.delete("/members/{bioguide_id}/{congress}", status_code=204)
def delete_member(bioguide_id: str, congress: int):
    if not db_delete_member(bioguide_id, congress):
        raise HTTPException(status_code=404, detail="Member not found")


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


@app.post("/house-votes", status_code=201)
def create_house_vote(payload):
    data = payload.model_dump()
    try:
        db_create_house_votes([data])
    except IntegrityError:
        raise HTTPException(status_code=409, detail="House vote already exists")
    return db_get_house_vote(data["identifier"])


@app.patch("/house-votes/{identifier}")
def edit_house_vote(identifier: int, payload):
    row = db_edit_house_vote(identifier, payload.model_dump(exclude_unset=True))
    if row is None:
        raise HTTPException(status_code=404, detail="House vote not found")
    return row


@app.delete("/house-votes/{identifier}", status_code=204)
def delete_house_vote(identifier: int):
    if not db_delete_house_vote(identifier):
        raise HTTPException(status_code=404, detail="House vote not found")
