import asyncio

from congress_http import Progress, get_json


async def get_members_by_congress(client, sem, congress: int):
    url = f"https://api.congress.gov/v3/member/congress/{congress}"
    members = []
    offset = 0
    while True:
        print(f"Fetching members for congress {congress} with offset {offset}", flush=True)
        data = await get_json(
            client,
            sem,
            url,
            {
                "currentMember": "false",
                "limit": 250,
                "offset": offset,
            },
        )
        members.extend(data.get("members") or [])
        if not data.get("pagination", {}).get("next"):
            break
        offset += 250
    return members


async def get_member_detail(client, sem, bioguide_id: str):
    url = f"https://api.congress.gov/v3/member/{bioguide_id}"
    data = await get_json(client, sem, url)
    return data["member"]


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


def transform_member(member, congress: int, count: int):
    print(f"Transforming member {member.get('bioguideId')} count: {count}", flush=True)
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


async def get_transformed_members_by_congress(congress: int, client, sem):
    summaries = await get_members_by_congress(client, sem, congress)
    progress = Progress("Fetched member details", len(summaries))
    print(f"Fetching details for {len(summaries)} members", flush=True)

    async def fetch_one(member):
        detail = await get_member_detail(client, sem, member["bioguideId"])
        await progress.tick()
        return detail

    details = await asyncio.gather(*(fetch_one(member) for member in summaries))
    return [
        transform_member(detail, congress, count)
        for count, detail in enumerate(details, start=1)
    ]
