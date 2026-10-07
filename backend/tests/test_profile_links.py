import httpx
import pytest

from app.api.v1.schemas.assessment import AssessmentPreviewRequest
from app.services import profile_links


def test_profile_urls_are_restricted_to_expected_public_profile_paths():
    request = AssessmentPreviewRequest.model_validate({
        "profile": {
            "github_profile_url": "github.com/student-dev/",
            "linkedin_profile_url": "https://www.linkedin.com/in/student-name/",
        },
    })
    assert request.profile.github_profile_url == "https://github.com/student-dev"
    assert request.profile.linkedin_profile_url == "https://linkedin.com/in/student-name"
    with pytest.raises(ValueError):
        AssessmentPreviewRequest.model_validate({"profile": {"github_profile_url": "https://example.com/"}})
    with pytest.raises(ValueError):
        AssessmentPreviewRequest.model_validate({"profile": {"linkedin_profile_url": "https://linkedin.com/company/acme"}})


def test_github_summary_uses_public_repo_languages_and_bounded_recent_push_sample(monkeypatch):
    real_client = httpx.Client
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/users/student-dev":
            return httpx.Response(200, json={"public_repos": 12})
        if request.url.path.endswith("/repos"):
            return httpx.Response(200, json=[{"language": "Python"}, {"language": "TypeScript"}, {"language": "Python"}, {"language": None}])
        return httpx.Response(200, json=[
            {"type": "PushEvent", "payload": {"commits": [{"sha": "a"}, {"sha": "b"}]}},
            {"type": "PushEvent", "payload": {"commits": [{"sha": "b"}, {"sha": "c"}]}},
            {"type": "CreateEvent", "payload": {"commits": [{"sha": "d"}]}},
        ])

    monkeypatch.setattr(profile_links.httpx, "Client", lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))
    summary = profile_links.inspect_profile_links("https://github.com/student-dev", "https://linkedin.com/in/student")
    assert summary["github"]["public_repositories"] == 12
    assert summary["github"]["recent_public_commits"] == 3
    assert summary["github"]["languages"] == [{"name": "Python", "repositories": 2}, {"name": "TypeScript", "repositories": 1}]
    assert summary["linkedin"]["status"] == "provided"
    assert "not scraped" in summary["linkedin"]["note"]


def test_github_failures_remain_non_blocking(monkeypatch):
    real_client = httpx.Client
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    monkeypatch.setattr(profile_links.httpx, "Client", lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))
    result = profile_links.inspect_profile_links("https://github.com/student-dev", None)
    assert result["github"]["status"] == "unavailable"
    assert result["github"]["public_repositories"] is None
    assert result["linkedin"]["status"] == "not_provided"
