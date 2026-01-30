
- auto-nudge
- unavailable list?
- a way to disable? hotfix? superapprovers? comment? want to do it on open, probably, not after
- unmatched_status - no scopes (can ensure coverage)
- signatures... FDA
- comments, notifications - or this is maybe just instructions now
- review/status/pending label? approved etc?

how else can you manually assign as scope? label, /comment

## admin

- mandates - CEL `scopes.sox.required > 0`
- rate limit monitoring
- suggested owner add/remove
- post-merge reviews?

---

```toml
[hotfix]
label = "hotfix"

[nudge]
hours = [24]

[[scopes]]
name = "fda"
signatures = "required"
```
