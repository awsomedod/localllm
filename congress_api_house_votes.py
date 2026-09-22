import asyncio
import html
import re

from congress_http import Progress, get_json, get_text

BILL_TYPES = {"HR", "S", "HJRES", "SJRES", "HCONRES", "SCONRES", "HRES", "SRES"}

async def get_house_votes(client, sem, congress: int, max_votes=None):
    url = f"https://api.congress.gov/v3/house-vote/{congress}"
    votes = []
    offset = 0
    while True:
        print(f"Fetching votes for congress {congress} with offset {offset}", flush=True)
        # 250 is the API's ceiling, but ask for less when only a sample is wanted.
        page_size = 250 if max_votes is None else min(250, max_votes - len(votes))
        data = await get_json(
            client,
            sem,
            url,
            {
                "congress": congress,
                "limit": page_size,
                "offset": offset,
            },
        )
        votes.extend(data.get("houseRollCallVotes") or [])
        # next is always set while records remain, so a sample has to stop itself.
        reached_max_votes = max_votes is not None and len(votes) >= max_votes
        if reached_max_votes or not data.get("pagination", {}).get("next"):
            break
        offset += page_size
    return votes


async def get_vote_positions(client, sem, congress: int, session_number: int, roll_call_number: int):
    url = f"https://api.congress.gov/v3/house-vote/{congress}/{session_number}/{roll_call_number}/members"
    data = await get_json(client, sem, url, {"limit": 250})
    results = (data.get("houseRollCallVoteMemberVotes") or {}).get("results") or []
    return [
        {
            "bioguide_id": position.get("bioguideID"),
            "vote_cast": position.get("voteCast"),
        }
        for position in results
    ]


async def get_text_versions(client, sem, congress: int, legislation_type: str, legislation_number: str):
    bill_type = legislation_type.lower()
    url = f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{legislation_number}/text"
    data = await get_json(client, sem, url)
    return data.get("textVersions")


def pick_text_version(text_versions, vote_date=None):
    # Versions carry the date of the action they belong to, so the text that was
    # voted on is the newest one published on or before the vote.
    candidates = list(enumerate(text_versions))
    if vote_date:
        on_or_before = [
            (index, version)
            for index, version in candidates
            if (version.get("date") or "")[:10] <= vote_date[:10]
        ]
        candidates = on_or_before or candidates
    if not candidates:
        return None
    return max(candidates, key=lambda pair: ((pair[1].get("date") or ""), pair[0]))[1]


async def get_full_text(client, sem, text_version):
    formats = {item.get("type"): item.get("url") for item in text_version.get("formats") or []}
    source_url = formats.get("Formatted Text")

    # congress.gov throttles bulk text downloads, so pull the same file from GovInfo.
    package_id = source_url.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    govinfo_url = f"https://www.govinfo.gov/content/pkg/{package_id}/html/{package_id}.htm"

    body = await get_text(client, sem, govinfo_url)
    text = html.unescape(re.sub(r"<[^>]+>", "", body)).strip()
    return package_id, text


async def get_legislation_text(client, sem, congress: int, legislation_type: str, legislation_number: str, vote_date):
    text_versions = await get_text_versions(client, sem, congress, legislation_type, legislation_number)
    text_version = pick_text_version(text_versions, vote_date)

    package_id, full_text = await get_full_text(client, sem, text_version)
    return {
        "version_type": text_version.get("type"),
        "version_date": text_version.get("date"),
        "package_id": package_id,
        "full_text": full_text,
    }


async def get_house_votes_with_details(client, sem, votes):
    text_cache = {}
    cache_lock = asyncio.Lock()

    async def legislation_text_for(vote, legislation_type, legislation_number):
        key = (vote["congress"], legislation_type, legislation_number, vote.get("startDate"))
        async with cache_lock:
            task = text_cache.get(key)
            if task is None:
                task = asyncio.create_task(
                    get_legislation_text(
                        client,
                        sem,
                        vote["congress"],
                        legislation_type,
                        legislation_number,
                        vote.get("startDate"),
                    )
                )
                text_cache[key] = task
        return await task

    progress = Progress("Filled vote details", len(votes))
    print(f"Filling details for {len(votes)} votes", flush=True)

    async def fill_vote(vote):
        vote["positions"] = await get_vote_positions(
            client,
            sem,
            vote["congress"],
            vote["sessionNumber"],
            vote["rollCallNumber"],
        )

        legislation_type = vote.get("legislationType")
        legislation_number = vote.get("legislationNumber")
        if legislation_type not in BILL_TYPES or not legislation_number:
            vote["text"] = None
        else:
            vote["text"] = await legislation_text_for(vote, legislation_type, legislation_number)
        await progress.tick()

    await asyncio.gather(*(fill_vote(vote) for vote in votes))
    return votes


async def get_transformed_house_votes_by_congress(congress: int, client, sem):
    votes = await get_house_votes(client, sem, congress)
    return await get_house_votes_with_details(client, sem, votes)
