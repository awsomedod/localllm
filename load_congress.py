import argparse

from congress_api_members import get_transformed_members_by_congress
from congress_api_house_votes import get_transformed_house_votes_by_congress
from db import create_members, create_house_votes, init_db

parser = argparse.ArgumentParser()
parser.add_argument("congress", type=int, help="Congress number, e.g. 118")
args = parser.parse_args()

init_db()
members = get_transformed_members_by_congress(args.congress)
votes = get_transformed_house_votes_by_congress(args.congress)
create_members(members)
print(f"loaded {len(members)} members for congress {args.congress}")
create_house_votes(votes)
print(f"loaded {len(votes)} votes for congress {args.congress}")