"""Test publishprs functionality."""

import os

from publishprs import Publisher


def test_publish_pr():
    """Test publishing a PR from publishprs to laminhub-public.

    This test uses PR #3820 from the private publishprs repo which contains
    user-attached images that need to be processed and uploaded to LaminDB.
    """
    target_token = os.getenv("GH_LAMINHUB_PUBLIC_SUNNYOSUN")
    publisher = Publisher(
        source_repo="https://github.com/laminlabs/publishprs",
        target_repo="https://github.com/laminlabs/laminhub-public",
        target_token=target_token,
    )
    url = publisher.publish(
        pull_id=4,
        close_pr=True,
    )
    assert url.startswith("https://github.com/laminlabs/laminhub-public/pull/")
    assert url.split("/")[-1].isdigit()  # PR number should be numeric


def test_publisher_initialization():
    """Test Publisher initialization with various inputs."""
    target_token = os.getenv("GH_LAMINHUB_PUBLIC_SUNNYOSUN")

    # Test with full URLs
    publisher = Publisher(
        source_repo="https://github.com/laminlabs/publishprs",
        target_repo="https://github.com/laminlabs/laminhub-public",
        target_token=target_token,
    )

    assert publisher.source_owner == "laminlabs"
    assert publisher.source_repo == "publishprs"
    assert publisher.target_owner == "laminlabs"
    assert publisher.target_repo == "laminhub-public"

    # Test with .git suffix
    publisher2 = Publisher(
        source_repo="https://github.com/laminlabs/publishprs.git",
        target_repo="https://github.com/laminlabs/laminhub-public.git",
        target_token=target_token,
    )

    assert publisher2.source_repo == "publishprs"
    assert publisher2.target_repo == "laminhub-public"
