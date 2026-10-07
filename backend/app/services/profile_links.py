"""Fetch bounded public GitHub evidence and label LinkedIn URL presence."""

from urllib.parse import urlsplit

import httpx

from app.core.config import settings

ACTIVITY_WINDOW_DAYS = 90


def inspect_profile_links(github_url: str | None, linkedin_url: str | None) -> dict:
    github = _github_summary(github_url) if github_url else {
        "status": "not_provided",
        "profile_url": None,
        "public_repositories": None,
        "recent_public_commits": None,
        "activity_window_days": ACTIVITY_WINDOW_DAYS,
        "languages": [],
        "note": "No GitHub profile was supplied.",
    }
    linkedin = {
        "status": "provided" if linkedin_url else "not_provided",
        "profile_url": linkedin_url,
        "note": "Profile URL detected; LinkedIn activity and profile contents are not scraped or verified.",
    } if linkedin_url else {
        "status": "not_provided",
        "profile_url": None,
        "note": "No LinkedIn profile URL was supplied. LinkedIn activity is not scraped.",
    }
    return {"github": github, "linkedin": linkedin}


def _github_summary(profile_url: str) -> dict:
    username = urlsplit(profile_url).path.strip("/")
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    base = {
        "status": "unavailable",
        "profile_url": profile_url,
        "public_repositories": None,
        "recent_public_commits": None,
        "activity_window_days": ACTIVITY_WINDOW_DAYS,
        "languages": [],
        "note": "GitHub public data could not be retrieved; no score is inferred.",
    }
    try:
        with httpx.Client(timeout=httpx.Timeout(2.5), headers=headers) as client:
            user_response = client.get(f"https://api.github.com/users/{username}")
            if user_response.status_code == 404:
                return {**base, "status": "not_found", "note": "That GitHub profile was not found or has no public profile."}
            user_response.raise_for_status()
            user = user_response.json()
            repositories_response = client.get(f"https://api.github.com/users/{username}/repos", params={"type": "owner", "sort": "updated", "per_page": 100})
            repositories_response.raise_for_status()
            repositories = repositories_response.json()
            events_response = client.get(f"https://api.github.com/users/{username}/events/public", params={"per_page": 100})
            events_response.raise_for_status()
            events = events_response.json()
        language_counts: dict[str, int] = {}
        for repo in repositories:
            language = repo.get("language")
            if language:
                language_counts[language] = language_counts.get(language, 0) + 1
        commit_shas = {
            commit.get("sha")
            for event in events
            if event.get("type") == "PushEvent"
            for commit in event.get("payload", {}).get("commits", [])
            if commit.get("sha")
        }
        ranked_languages = sorted(language_counts.items(), key=lambda item: (-item[1], item[0].casefold()))[:5]
        return {
            **base,
            "status": "available",
            "public_repositories": user.get("public_repos", len(repositories)),
            "recent_public_commits": len(commit_shas),
            "languages": [{"name": language, "repositories": count} for language, count in ranked_languages],
            "note": "Repository count comes from the public profile. Languages summarize the primary-language labels of up to 100 most recently updated public repositories you own. Commit count covers distinct commits visible in a sample of up to 100 public push events (events are limited to 90 days); it is not a total contribution count, and private activity is excluded.",
        }
    except (httpx.HTTPError, ValueError, TypeError):
        return base
