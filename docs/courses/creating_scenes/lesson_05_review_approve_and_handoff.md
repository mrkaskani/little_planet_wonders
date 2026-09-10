# Lesson 5: Review, Approve, and Hand Off the Scene

**Study time:** 10 minutes  
**Practice time:** 10 minutes

---

## 1. Lesson objective

By the end of this lesson, you will be able to:

- validate the scene from story, visual, audio, and technical perspectives;
- distinguish a valid file from an approved creative result;
- prepare a reproducible handoff for image or video generation;
- identify the next implementation work without bypassing human approval.

---

## 2. Review in layers

Reviewing everything as “does it look good?” hides the cause of failures. Use
five separate gates.

### Gate 1: YAML and identity

- The file parses.
- Folder, episode ID, and project ID agree.
- Character IDs are unique and resolvable.
- Expressions, intensity levels, and contracts exist.
- The intended location ID resolves.

### Gate 2: story and performance

- The scene has one clear purpose.
- Beginning and ending states are understandable.
- Every character has an intention and readable emotion.
- The emotional intensity matches the small story beat.
- Behavior is safe and age-appropriate.

### Gate 3: conversation and audio

- Dialogue is exact and approved.
- Speaker order is unambiguous.
- The listener has a closed-mouth or closed-beak performance state.
- Music has no competing vocal and ducks below speech.
- Ambience is continuous and below dialogue.
- Every Foley or sound effect is motivated and correctly scaled.

### Gate 4: frame and motion readiness

- The approved character count is exact.
- Character scale, ground contact, gaze, and identity are correct.
- Location geometry, lighting, and time of day match the selected authority.
- The frame supports one next action.
- The camera has one controlled behavior.
- The image contains no board layout, label, watermark, or duplicate subject.

### Gate 5: provenance and authorization

- The context hash is attached to the job.
- Every reference path and asset hash can be audited.
- Provider and generation settings are recorded.
- Candidates are immutable attempts, not overwritten files.
- Human reviewer, decision, notes, and time are recorded.
- Production remains blocked until all required approvals pass.

---

## 3. Run the local preflight

First verify the episode can resolve:

```bash
.venv/bin/python - <<'PY'
from lpw.context.loader import load_project_context

context = load_project_context("riri-yoyo", episode_id="episode-001")
episode = context["episode"]["episode"]

assert episode["id"] == "episode-001"
assert context["location"]["id"] == "kindergarten-evening-night"
assert [character["id"] for character in context["characters"]] == ["riri", "yoyo"]
assert episode["approval_boundary"]["production_authorized"] is False

print("preflight passed")
print("context hash:", context["metadata"]["context_hash"])
PY
```

Then run the focused regression tests for the local episode and MCP path:

```bash
.venv/bin/pytest -q \
  tests/test_context_loader.py \
  tests/test_mcp_server.py
```

Passing tests proves that the loader and MCP contracts work. It does not approve
the story, prompt, reference frame, audio, or final video.

---

## 4. Prepare the handoff manifest

A future generation job should preserve at least:

```yaml
generation_handoff:
  project_id: riri-yoyo
  episode_id: episode-001
  scene_id: moonlit-garden-greeting
  context_hash: <resolved-context-hash>
  prompt_package_version: 1
  source_references:
    - id: riri-neutral-full-body-v001
      sha256: <asset-hash>
    - id: yoyo-neutral-full-body-v001
      sha256: <asset-hash>
    - id: kindergarten-evening-night-primary-master-v001
      sha256: <asset-hash>
  requested_output:
    id: episode-001-moonlit-garden-greeting-s2v-start-frame-v001
    type: clean-single-frame-character-location-composite
  provider:
    name: <configured-provider>
    model: <configured-model>
    request_id: null
  approval:
    technical_passed: false
    identity_passed: false
    location_passed: false
    performance_passed: false
    safety_passed: false
    approved_by: null
    production_authorized: false
```

Store this as runtime evidence, not authoritative episode context. Fill response
and review fields after the corresponding event; do not predict them.

---

## 5. Approval decisions

Use explicit outcomes:

- **Reject:** identity, geometry, safety, or core composition is wrong.
- **Revise prompt:** the source context is correct but direction is ambiguous.
- **Revise source context:** the desired state is absent or contradictory in the
  authorities.
- **Approve start frame:** the clean frame is ready for exactly the planned next
  action.
- **Authorize production:** a responsible human allows the next external or
  costly stage.

Never “fix” an identity or location failure only in downstream prompt text. If
the source authority is wrong, correct and review the source, resolve it again,
and record a new context hash.

---

## 6. What to implement next

After this local context course, the next bounded engineering stage is a manual
image-reference intake and video pipeline with:

1. a prompt-package compiler;
2. reference asset resolution and status checks;
3. a manual image handoff manifest with provenance;
4. immutable candidate storage and hashes;
5. a human reference-frame review record;
6. an S2V handoff that accepts only approved clean composites;
7. Qwen VL frame-range analysis against the same resolved context;
8. bounded Wan 2.2 repair jobs for failed intervals;
9. continuity validation before a repaired interval can replace an edit event.

Keep S2V provider execution disabled by default until tests cover invalid or
missing references, provider failures, retries, partial responses, unsafe
output, provenance, and approval enforcement.

---

## 7. Final course exercise

Take one original scene from idea to local handoff:

1. inventory the existing authorities;
2. write an episode and scene selection;
3. resolve the episode locally;
4. inspect the resolved MCP resource;
5. build a prompt package with the context hash;
6. define the clean S2V start frame;
7. review story, identity, location, performance, audio, safety, and provenance;
8. leave production unauthorized until a human approves the required artifacts.
9. after rendering, complete the Qwen VL and Wan repair loop in Lesson 6.

---

## 8. Final checklist

- [ ] I can find and select existing project authorities.
- [ ] I can write a complete episode scene in YAML.
- [ ] I can resolve character emotions and location through Python and MCP.
- [ ] I can compile relevant context into a focused prompt package.
- [ ] I know why boards and collages are not final S2V frames.
- [ ] I protect exact dialogue and listener behavior.
- [ ] I record hashes, references, provider settings, and decisions.
- [ ] I distinguish parsing, generation, review, approval, and authorization.
- [ ] I know that the image API adapter is planned but not yet implemented.
- [ ] I know that Qwen VL detects and describes failures while Wan 2.2 creates
      replacement footage.
- [ ] I know that a repaired interval must pass continuity review again.
