import os
import requests
import json
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

def get_members_by_congress(congress: int):
    url = f"https://api.congress.gov/v3/member/congress/{congress}"
    members = []
    offset = 0
    while True:
        params = {
            "api_key": os.getenv("CONGRESS_API_KEY"),
            "format": "json",
            "currentMember": "false",
            "limit": 250,
            "offset": offset,
        }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        members.extend(data.get("members") or [])
        if not data.get("pagination", {}).get("next"):
            break
        offset += 250
    return members


def get_member_detail(bioguide_id: str):
    url = f"https://api.congress.gov/v3/member/{bioguide_id}"
    params = {
        "api_key": os.getenv("CONGRESS_API_KEY"),
        "format": "json",
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()["member"]

def term_for_congress(member, congress: int):
    terms = member.get("terms") or []
    if isinstance(terms, dict):
        terms = terms.get("item") or []
    for term in terms:
        if term.get("congress") == congress:
            return term
    return {}

def congress_years(congress: int):
    start_year = 1789 + (congress - 1) * 2  # 118 -> 2023
    return start_year, start_year + 1

def party_for_congress(member, congress: int):
    term = term_for_congress(member, congress)
    party_name = term.get("partyName") or term.get("party")
    if party_name:
        return party_name
    start_year, end_year = congress_years(congress)
    for spell in member.get("partyHistory") or []:
        spell_start = spell.get("startYear") or 0
        spell_end = spell.get("endYear") or 9999
        if spell_end == "":
            spell_end = 9999
        if spell_start <= end_year and int(spell_end) >= start_year:
            return spell.get("partyName")
    return None

def transform_member(member, congress: int):
    depiction = member.get("depiction") or {}
    cosponsored_legislation = member.get("cosponsoredLegislation") or {}
    sponsored_legislation = member.get("sponsoredLegislation") or {}
    term = term_for_congress(member, congress)
    party_name = party_for_congress(member, congress)
    return {
        "bioguide_id": member.get("bioguideId"),
        "birthYear": member.get("birthYear"),
        "deathYear": member.get("deathYear"),
        "cosponsoredLegislationCount": cosponsored_legislation.get("count"),
        "sponsoredLegislationCount": sponsored_legislation.get("count"),
        "image_url": depiction.get("imageUrl"),
        "name": member.get("directOrderName"),
        "firstName": member.get("firstName"),
        "lastName": member.get("lastName"),
        "honorificName": member.get("honorificName"),
        "party": party_name,
        **term
    }


def get_transformed_members_by_congress(congress: int):
    members = []
    for member in get_members_by_congress(congress):
        detail = get_member_detail(member["bioguideId"])
        members.append(transform_member(detail, congress))
    return members


transformed_members = get_transformed_members_by_congress(118)
print(len(transformed_members))
print(transformed_members[0].keys())