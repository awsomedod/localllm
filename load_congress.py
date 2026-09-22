import argparse
import asyncio

from congress_api_house_votes import get_transformed_house_votes_by_congress
from congress_api_members import get_transformed_members_by_congress
from congress_http import new_client, new_semaphore
from db import create_house_votes, create_members, init_db


async def load(congress: int):
    init_db()
    sem = new_semaphore()
    async with new_client() as client:
        members, votes = await asyncio.gather(
            get_transformed_members_by_congress(congress, client, sem),
            get_transformed_house_votes_by_congress(congress, client, sem),
        )
    create_members(members)
    print(f"loaded {len(members)} members for congress {congress}", flush=True)
    create_house_votes(votes)
    print(f"loaded {len(votes)} votes for congress {congress}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("congress", type=int, help="Congress number, e.g. 118")
    args = parser.parse_args()
    asyncio.run(load(args.congress))


if __name__ == "__main__":
    main()
