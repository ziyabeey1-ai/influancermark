import requests

from config import APIFY_TOKEN

APIFY_BASE = "https://api.apify.com/v2"


def _run_actor(actor_id: str, actor_input: dict) -> list[dict]:
    if not APIFY_TOKEN:
        return []
    try:
        run = requests.post(
            f"{APIFY_BASE}/acts/{actor_id}/runs",
            params={"token": APIFY_TOKEN},
            json=actor_input,
            timeout=60,
        )
        run.raise_for_status()
        run_data = run.json().get("data", {})
        dataset_id = run_data.get("defaultDatasetId")
        if not dataset_id:
            return []
        items = requests.get(
            f"{APIFY_BASE}/datasets/{dataset_id}/items",
            params={"token": APIFY_TOKEN, "clean": "true"},
            timeout=60,
        )
        items.raise_for_status()
        return items.json() if isinstance(items.json(), list) else []
    except Exception:
        return []


def _normalize(item: dict) -> dict | None:
    username = item.get("username") or item.get("ownerUsername")
    if not username:
        return None
    return {
        "username": username,
        "full_name": item.get("fullName") or item.get("full_name") or "",
        "bio": item.get("biography") or item.get("bio") or "",
        "followers": item.get("followersCount") or item.get("followers") or 0,
        "following": item.get("followsCount") or item.get("following") or 0,
        "post_count": item.get("postsCount") or item.get("posts") or 0,
        "email": item.get("businessEmail") or item.get("email"),
        "website": item.get("externalUrl") or item.get("website") or "",
        "profile_url": f"https://instagram.com/{username}",
    }


def search_by_hashtag(hashtags: list[str], max_per_tag: int = 20) -> list[dict]:
    profiles = []
    actor_id = "apify/instagram-hashtag-scraper"
    for hashtag in hashtags:
        data = _run_actor(actor_id, {"hashtags": [hashtag], "resultsLimit": max_per_tag})
        for item in data:
            normalized = _normalize(item)
            if normalized:
                profiles.append(normalized)
    return _dedupe_profiles(profiles)


def search_by_keyword(keywords: list[str], max_results: int = 50) -> list[dict]:
    # Basit yaklaşım: keyword'leri hashtag gibi ele al
    tags = [k.replace(" ", "") for k in keywords]
    return search_by_hashtag(tags, max_per_tag=max(1, max_results // max(len(tags), 1)))


def enrich_profiles(profiles: list[dict]) -> list[dict]:
    return profiles


def _dedupe_profiles(profiles: list[dict]) -> list[dict]:
    unique = {}
    for profile in profiles:
        unique[profile["username"].lower()] = profile
    return list(unique.values())
