# publishprs: Publish private pull requests in a public repo

Install:

```shell
pip install publishprs
```

Connect to the LaminDB instance to be used for assets management:

```shell
lamin connect account/instance
```

Export API tokens for GitHub's API:

```shell
export GITHUB_SOURCE_TOKEN=...  # token with access to source repo, to process assets, needs to be a classic token
export GITHUB_TARGET_TOKEN=...  # token with access to target repo, to assign original user identity, should be fine-grained and issued by the original user account
```

Publish a PR:

```python
from publishprs import Publisher
publisher = Publisher(
    source_repo="https://github.com/laminlabs/laminhub",
    target_repo="https://github.com/laminlabs/laminhub-public",
)
url = publisher.publish(pull_id=3820)
print(f"Published to: {url}")
```
