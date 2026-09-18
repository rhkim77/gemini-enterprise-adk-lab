# CE Qwiklabs Content Bundle

This directory holds the **CE Qwiklabs content bundle** for the lab. It is
deliberately separate from the rest of this repository, because the two serve
different roles in the Qwiklabs publishing model.

## Why the bundle is not at the repository root

| | Asset repository (this repo) | Content library repository |
| :--- | :--- | :--- |
| Contents | Agent source, tool gateways, scripts, lab docs | `qwiklabs.yaml`, instructions, graders |
| Consumed by | The **student**, via `git clone` inside the lab | **GitWhisperer**, at publish time |
| Must be public | Yes — a private repo breaks the ephemeral lab VM | No |

GitWhisperer derives a lab's `content_id` from *the library repository name plus
the lab directory name*, and it expects the layout
`<library-repo>/labs/<lab-slug>/qwiklabs.yaml`
([lab-bundle-spec.md, "GitWhisperer Integration"][spec]).

Putting `qwiklabs.yaml` at the root of this repo would therefore ask
GitWhisperer to treat the entire ADK codebase as a lab bundle, and this repo
already has a top-level `labs/` directory of authored markdown, which collides
head-on with GitWhisperer's convention that `labs/` is the *entity-type*
directory. Keeping the bundle here, in the same shape the library expects, lets
it be copied across verbatim.

## Publishing

```bash
# 1. Make sure the bundle instructions match the authored guides.
./scripts/sync_qwiklabs_bundle.sh --check

# 2. Copy the lab directory into the CE content library repository.
cp -r qwiklabs_bundle/labs/gemini-enterprise-adk-lab \
      <content-library-repo>/labs/
```

## Layout

```
labs/gemini-enterprise-adk-lab/
├── QL_OWNER                      # staging-deployment owner
├── qwiklabs.yaml                 # v2 bundle, default_locale: ko
├── qwiklabs.en.yaml              # English overlay (locale-specific fields only)
├── instructions/
│   ├── ko.md                     # generated from labs/QWIKLABS_LAB_GUIDE.md
│   └── en.md                     # generated from labs/QWIKLABS_LAB_GUIDE_EN.md
└── assessments/
    ├── check_bigquery_seed.rb
    └── check_cloud_run_service.rb
```

`instructions/*.md` are **generated**. Edit the guides under `labs/` and re-run
`./scripts/sync_qwiklabs_bundle.sh`.

## Why only two checkpoints are scored

Activity Tracking graders are Ruby methods that call Google APIs; they can only
observe **cloud-side state**. Mapping that against the five lab tasks:

| Task | Leaves a cloud artifact? | Scored |
| :--- | :--- | :--- |
| 1. Bootstrap + seed BigQuery | Yes — dataset, 3 tables, 100 rows | ✅ 50 pts |
| 2. Read and understand the tool gateways | No — reading source code | ❌ |
| 3. Run the Dual-Contract runtime locally | No — a local `uvicorn` process | ❌ |
| 4. Deploy to Cloud Run | Yes — a Cloud Run service | ✅ 50 pts |
| 5. Register in Gemini Enterprise | Console-side; Discovery Engine `authorizations` is ALPHA-restricted | ❌ |

Scoring a task the grader cannot actually observe would mean either awarding
points unconditionally or failing students for reasons outside their control.
Tasks 2, 3 and 5 are instead taught and **self-verified** in the instructions:

* Task 3 → `scripts/validate_agent.py` (10 checks)
* Task 5 → `scripts/verify_lab04_completion.py` (4 checks)

Both print an explicit PASS/FAIL summary, so the student still gets a hard
signal — it simply is not worth Qwiklabs points.

> [!IMPORTANT]
> Two items remain unverified and must be confirmed before submission:
> 1. `primary_project.RunV1` — the exact Cloud Run service handle name is
>    inferred from the `Google::Apis::RunV1` naming convention, not confirmed
>    against a published list of allowed services.
> 2. Whether `gcp_pt` (Provisioned Throughput) is required. Gemini Enterprise in
>    a Qwiklabs project needs a PT allocation (`go/qwiklabs-pt`) plus a capacity
>    request (`go/lfs-capacity-request`); without it Task 5 fails with
>    `Quota has been exceeded`. The current `gcp_project` resource uses the
>    default variant.

[spec]: http://google3/cloud/training/qwiklabs/content_bundle/g3doc/lab-bundle-spec.md
