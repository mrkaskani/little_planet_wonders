# Lesson 3: Resolve the Scene Context

**Study time:** 15 minutes  
**Practice time:** 15 minutes

---

## 1. Lesson objective

By the end of this lesson, you will be able to:

- load an episode through the local Python API;
- understand what LPW adds to the compact episode source;
- inspect the same resolved context through MCP;
- diagnose missing character, emotion, intensity, and location IDs.

---

## 2. What resolution means

The episode contains selections such as:

```yaml
- id: riri
  emotion:
    id: happy
    intensity: level_2
    contract: happiness
```

LPW resolves that compact selection into:

```text
episode character state
  + complete characters/riri/character.yaml
  + expression_library.happy
  + acting-style.intensity_scale.level_2
  + acting-style.emotion_contracts.happiness
  + Riri's performance signature
```

The result keeps both the episode-specific choice and the reusable source
authority. This is the context an eventual prompt compiler should consume.

---

## 3. Load the episode directly

From the repository root, run:

```bash
.venv/bin/python - <<'PY'
from lpw.context.loader import get_project_directory, load_episode_context

project = get_project_directory("riri-yoyo")
context = load_episode_context(project, "episode-001")

print("episode:", context["metadata"]["episode_id"])
print("location:", context["metadata"]["location_id"])
print("characters:", context["metadata"]["character_ids"])
print("hash:", context["metadata"]["context_hash"])

for item in context["characters"]:
    emotion = item["resolved_emotion"]
    print(item["id"], emotion["id"], emotion["intensity"])
PY
```

The example should report:

```text
episode: episode-001
location: kindergarten-evening-night
characters: ['riri', 'yoyo']
hash: <16-character context hash>
riri happy level_2
yoyo curious level_2
```

The hash represents the resolved context. Store it with a future prompt or
generation job so you can prove which source state produced that job.

---

## 4. Load the complete project with the episode

Use `load_project_context` when prompt planning needs the wider project layers:

```bash
.venv/bin/python - <<'PY'
from lpw.context.loader import load_project_context

context = load_project_context("riri-yoyo", episode_id="episode-001")

print("episode:", context["metadata"]["episode_id"])
print("characters:", [item["id"] for item in context["characters"]])
print("location:", context["location"]["id"])
print("project hash:", context["metadata"]["context_hash"])
PY
```

When `character_ids` and `location_id` are omitted, the episode supplies their
defaults. You may override them explicitly for controlled inspection, but a
production prompt should not silently contradict the episode.

---

## 5. Inspect the episode through MCP

Start the stdio server through the MCP host configuration:

```bash
lpw
```

Then use either interface offered by the server.

### MCP resource

```text
cinema://projects/riri-yoyo/episodes/episode-001
```

This returns resolved YAML, which is convenient for an MCP client that wants a
readable source document.

### MCP tool

```text
inspect_episode_context(
  project_id="riri-yoyo",
  episode_id="episode-001"
)
```

This returns the resolved object directly, which is convenient for tool-driven
planning. The tool and resource are read-only; neither one creates an image,
changes approval state, or contacts an external service.

---

## 6. Know the resolved shape

The episode resolver returns five top-level sections:

| Key | Contents |
|---|---|
| `episode` | The original episode YAML |
| `characters` | Episode state plus full identity and resolved emotion per character |
| `acting_style` | Shared intensity, emotion, and performance rules |
| `location` | The selected location context, or `null` if none was selected |
| `metadata` | Episode ID, selected IDs, and stable context hash |

For one character, inspect:

```python
riri = context["characters"][0]
riri["episode_state"]
riri["character"]
riri["resolved_emotion"]["expression"]
riri["resolved_emotion"]["intensity_context"]
riri["resolved_emotion"]["contract"]
riri["performance_signature"]
```

An image prompt should use the relevant values from those resolved sections,
not merely the word `happy`.

---

## 7. Diagnose resolution failures

LPW fails early when a selection cannot be trusted:

| Failure | Likely cause | Correction |
|---|---|---|
| Episode does not exist | Wrong path or ID | Make folder, filename, and YAML `id` agree |
| Character does not exist | Unknown character ID | Use an existing character authority |
| Expression is not defined | Emotion absent from `expression_library` | Choose a valid key or review a new reusable expression |
| Intensity is unknown | Level absent from `intensity_scale` | Use a defined acting level |
| Emotion contract is unknown | Contract absent from `emotion_contracts` | Correct the ID or add it through acting-style review |
| Location does not exist | Wrong YAML ID | Read the top-level `id` in the intended location file |
| Duplicate character IDs | Same character listed twice | Keep one episode state per character |

Do not work around these failures by pasting missing details into a prompt. Fix
the authoritative context or select an authority that already exists.

---

## 8. Practice activity

1. Load `episode-001` with `load_episode_context`.
2. Print Riri's resolved eye, mouth, and body cues for `happy`.
3. Print Yoyo's intensity description for `level_2`.
4. Print the location ID and status.
5. Record the context hash.
6. Temporarily test an invalid emotion in an untracked copy, observe the error,
   and discard the copy without modifying canonical context.

---

## 9. Completion checklist

- [ ] The episode loads without changing source files.
- [ ] Each character contains full identity and resolved emotion context.
- [ ] The intended location resolves by exact ID.
- [ ] I understand the difference between episode and project resolution.
- [ ] I can read the episode through its MCP resource.
- [ ] I can call `inspect_episode_context` through MCP.
- [ ] I recorded the context hash for the next production stage.

