# WE-03 Progressive Hybrid Performance Budget Governance (plan C) v1.0

Approved by Martin ("批准", 2026-11-29 02:03, scope confirmed by his answer: budget governance, A2 spec, test ceiling 700 / section 16 revision / device matrix 3x3). Recorded as D-068. Source: ChatGPT G0 request (plan C) and Claude G0 review `specs/T-018A2-g0-review-v1.0.md` A2-C13.

This is a governance decision only. It approves **no numeric budget** and authorizes no implementation. It is independent of the T-018A2 spec (D-069).

## 1. Classes
| Class | Meaning | Who may change it |
|---|---|---|
| HARD_GATE | A failing result blocks a task from acceptance. | Only Martin, with evidence. |
| SOFT_TARGET | Reported with reason and improvement advice when missed; does not block by itself. | Martin confirms the value after device evidence. |
| PENDING_EVIDENCE | No value yet; must be measured (MEASURED_DEVICE) before it can become SOFT_TARGET. | Evidence-driven proposal, Martin approves. |

## 2. Initial classification
| Class | Items |
|---|---|
| HARD_GATE | A2 structural gates (bodies, shapes, scene draw calls, triangles, meshes, materials, textures, dependencies, new `localStorage` keys, per-frame allocation, 250-line ceiling); offline and save compatibility; collision safety and no blank substitution (series N5, D-065); B4 device average FPS >= 0.97 x fpsCap (D-065). |
| SOFT_TARGET | Diagnostic sampling cost; P95 <= 40 ms, P99 <= 66.7 ms, minimum 1 s FPS, share of frames > 100 ms (initial values from the draft section 25, unconfirmed until A2 device evidence); added-triangle P95 budget (PHONE_MED interpolated). |
| PENDING_EVIDENCE | Draw-call budget, resource capacity, streaming CPU, LOD distances, physics-time share, active collision radius, Geometry/Texture residency. |

## 3. Promotion and demotion
- PENDING_EVIDENCE -> SOFT_TARGET -> HARD_GATE only by Martin's explicit approval on MEASURED_DEVICE evidence. No automatic promotion.
- A missed SOFT_TARGET must carry cause and improvement advice; the same target missed in two consecutive subtasks is escalated to Martin.
- Headless numbers (SwiftShader, CPU submission time) are never device FPS or VRAM and never promote a class on their own (N8, A1 findings).
- No class assignment approves a numeric value; values still need Martin's separate confirmation.
