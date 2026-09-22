# Backend reading checklist

Read in this order (upstream ingest, then the database, then the API). Check a box when that function makes sense.

## 1. Loader — `load_congress.py`

- [ ] `main`
- [ ] `load`

## 2. Shared HTTP — `congress_http.py`

- [ ] `new_client`
- [ ] `new_semaphore`
- [ ] `_congress_params`
- [ ] `_request`
- [ ] `get_json`
- [ ] `get_text`
- [ ] `Progress.__init__`
- [ ] `Progress.tick`

## 3. Members ingest — `congress_api_members.py`

- [ ] `get_transformed_members_by_congress`
- [ ] `get_members_by_congress`
- [ ] `get_member_detail`
- [ ] `fetch_one` (nested in `get_transformed_members_by_congress`)
- [ ] `transform_member`
- [ ] `term_for_congress`
- [ ] `party_for_congress`
- [ ] `congress_years`

## 4. Votes ingest — `congress_api_house_votes.py`

- [ ] `get_transformed_house_votes_by_congress`
- [ ] `get_house_votes`
- [ ] `get_house_votes_with_details`
- [ ] `fill_vote` (nested in `get_house_votes_with_details`)
- [ ] `get_vote_positions`
- [ ] `legislation_text_for` (nested in `get_house_votes_with_details`)
- [ ] `get_legislation_text`
- [ ] `get_text_versions`
- [ ] `pick_text_version`
- [ ] `get_full_text`

## 5. Database — `db.py`

Models (not functions, but read them with the writes):

- [ ] `Base`
- [ ] `Member`
- [ ] `HouseVote`

Loader writes:

- [ ] `init_db`
- [ ] `create_members`
- [ ] `create_house_votes`

API reads / summary write:

- [ ] `list_members`
- [ ] `get_member`
- [ ] `list_house_votes`
- [ ] `get_house_vote`
- [ ] `named_positions`
- [ ] `set_house_vote_summary`

Unused by the live API (still in the file):

- [ ] `edit_member`
- [ ] `edit_house_vote`
- [ ] `delete_member`
- [ ] `delete_house_vote`

## 6. HTTP API — `api.py`

- [ ] `paginated`
- [ ] `validate_pagination`
- [ ] `list_members`
- [ ] `get_member`
- [ ] `list_house_votes`
- [ ] `get_house_vote`
- [ ] `summarize_house_vote`
- [ ] `events` (nested in `summarize_house_vote`)
- [ ] `_sse`

## 7. Local LLM — `summarize.py`

- [ ] `_client`
- [ ] `_model_id`
- [ ] `count_tokens`
- [ ] `summarize_bill_text_stream`
- [ ] `_split_to_budget`
- [ ] `_stream_prompt`
- [ ] `_iter_completion`
- [ ] `_strip_think`
