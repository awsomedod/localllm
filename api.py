from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import IntegrityError

from db import create_row, delete_row, edit_row, get_row, list_rows, sync_schema
from db_models import HouseVote, Member

sync_schema()
app = FastAPI()


def to_dict(row):
    return {column.key: getattr(row, column.key) for column in sa_inspect(row).mapper.column_attrs}


class MemberIn(BaseModel):
    bioguide_id: str
    congress: int
    birthYear: str | None = None
    deathYear: str | None = None
    cosponsoredLegislationCount: int | None = None
    sponsoredLegislationCount: int | None = None
    image_url: str | None = None
    name: str | None = None
    firstName: str | None = None
    lastName: str | None = None
    honorificName: str | None = None
    party: str | None = None
    chamber: str | None = None
    district: int | None = None
    endYear: int | None = None
    memberType: str | None = None
    startYear: int | None = None
    stateCode: str | None = None
    stateName: str | None = None


class MemberPatch(BaseModel):
    birthYear: str | None = None
    deathYear: str | None = None
    cosponsoredLegislationCount: int | None = None
    sponsoredLegislationCount: int | None = None
    image_url: str | None = None
    name: str | None = None
    firstName: str | None = None
    lastName: str | None = None
    honorificName: str | None = None
    party: str | None = None
    chamber: str | None = None
    district: int | None = None
    endYear: int | None = None
    memberType: str | None = None
    startYear: int | None = None
    stateCode: str | None = None
    stateName: str | None = None


class HouseVoteIn(BaseModel):
    identifier: int
    congress: int
    rollCallNumber: int
    sessionNumber: int
    legislationNumber: str | None = None
    legislationType: str | None = None
    legislationUrl: str | None = None
    result: str | None = None
    sourceDataURL: str | None = None
    startDate: str | None = None
    updateDate: str | None = None
    url: str | None = None
    voteType: str | None = None
    positions: list | None = None
    text: dict | None = None


class HouseVotePatch(BaseModel):
    congress: int | None = None
    rollCallNumber: int | None = None
    sessionNumber: int | None = None
    legislationNumber: str | None = None
    legislationType: str | None = None
    legislationUrl: str | None = None
    result: str | None = None
    sourceDataURL: str | None = None
    startDate: str | None = None
    updateDate: str | None = None
    url: str | None = None
    voteType: str | None = None
    positions: list | None = None
    text: dict | None = None


@app.get("/members")
def list_members(congress: int | None = None):
    return [to_dict(row) for row in list_rows(Member, congress=congress)]


@app.get("/members/{bioguide_id}/{congress}")
def get_member(bioguide_id: str, congress: int):
    row = get_row(Member, (bioguide_id, congress))
    if row is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return to_dict(row)


@app.post("/members", status_code=201)
def create_member(payload: MemberIn):
    try:
        return to_dict(create_row(Member, **payload.model_dump()))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Member already exists")


@app.patch("/members/{bioguide_id}/{congress}")
def edit_member(bioguide_id: str, congress: int, payload: MemberPatch):
    try:
        return to_dict(edit_row(Member, (bioguide_id, congress), **payload.model_dump(exclude_unset=True)))
    except KeyError:
        raise HTTPException(status_code=404, detail="Member not found")


@app.delete("/members/{bioguide_id}/{congress}", status_code=204)
def delete_member(bioguide_id: str, congress: int):
    try:
        delete_row(Member, (bioguide_id, congress))
    except KeyError:
        raise HTTPException(status_code=404, detail="Member not found")


@app.get("/house-votes")
def list_house_votes(congress: int | None = None):
    return [to_dict(row) for row in list_rows(HouseVote, congress=congress)]


@app.get("/house-votes/{identifier}")
def get_house_vote(identifier: int):
    row = get_row(HouseVote, identifier)
    if row is None:
        raise HTTPException(status_code=404, detail="House vote not found")
    return to_dict(row)


@app.post("/house-votes", status_code=201)
def create_house_vote(payload: HouseVoteIn):
    try:
        return to_dict(create_row(HouseVote, **payload.model_dump()))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="House vote already exists")


@app.patch("/house-votes/{identifier}")
def edit_house_vote(identifier: int, payload: HouseVotePatch):
    try:
        return to_dict(edit_row(HouseVote, identifier, **payload.model_dump(exclude_unset=True)))
    except KeyError:
        raise HTTPException(status_code=404, detail="House vote not found")


@app.delete("/house-votes/{identifier}", status_code=204)
def delete_house_vote(identifier: int):
    try:
        delete_row(HouseVote, identifier)
    except KeyError:
        raise HTTPException(status_code=404, detail="House vote not found")
