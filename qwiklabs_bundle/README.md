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

The CE (Explore / Labs for Sales) content library is
**`github.com/CloudVLab/gcp-ce-content`** — "Special content only on
explore.qwiklabs.com" ([go/la-ld-onboarding][onboard]). Access is granted
through the Sphinx group `qwiklabs_cloudvlabgcp-ce-content_editors`, and the
author needs Explore Creator rights via [go/preregister][prereg].

> [!IMPORTANT]
> A v2 bundle **must be published through Alexandria** or it will not work in
> production ([go/authoring-ql-md][authmd], [go/publishing-qwiklabs][pub]).

```bash
# 1. Make sure the bundle instructions match the authored guides.
./scripts/sync_qwiklabs_bundle.sh --check

# 2. Copy the lab directory into the CE content library repository.
cp -r qwiklabs_bundle/labs/gemini-enterprise-adk-lab \
      <path-to>/gcp-ce-content/labs/

# 3. Publish through Alexandria (see go/publishing-qwiklabs).
```

[onboard]: http://go/la-ld-onboarding
[prereg]: http://go/preregister
[authmd]: http://go/authoring-ql-md
[pub]: http://go/publishing-qwiklabs

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

Activity Tracking graders are Ruby methods that run sandboxed (NsJail, on Cloud
Run) and call Google APIs. They can only observe **cloud-side state**: shelling
out via `curl`, backticks or `system()` is prohibited, and the filesystem is
read-only ([go/activity-tracking-best-practices][atbp]). Nothing in the
student's Cloud Shell or on their laptop is reachable.

That is allowed by policy — the Pre-Launch Checklist asks only that
"each objective is linked to activity tracking (AT) **whenever possible**"
([go/lab-architect-docs/checklists-templates][chk]) — so tasks that leave no
cloud artifact simply are not scored. Mapping that against the five lab tasks:

[atbp]: http://go/activity-tracking-best-practices
[chk]: http://go/lab-architect-docs/checklists-templates

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

### Choosing the service handle names

Activity Tracking service names are **not an enum**. `teacups.proto` declares
`string service_name = 2;`, and the allowlist lives outside google3, in
`ALL_SUPPORTED_SERVICES` in `lib/ice/gcp/gcp_handle.rb` in the
`Qwiklabs/qwiklab-website` repository
([go/qwiklabs-docs/runtime/activity_tracking/procedures/adding_apis][addapis]).

The name is the **Ruby API module name**, i.e. the `<X>` in
`Google::Apis::<X>::...Service` — for example `Google::Apis::FormsV1::FormsService`
is registered as `FormsV1`. Applying that rule to Cloud Run gives `RunV1` /
`RunV2`, since the class is `Google::Apis::RunV1::CloudRunService`. **There is
no `CloudRunV1` module**, so that spelling would silently fail.

> [!WARNING]
> Unverified items — confirm before submitting.
>
> 1. **`primary_project.RunV1` registration.** The *spelling* follows the
>    documented naming rule, but whether Cloud Run is actually present in
>    `ALL_SUPPORTED_SERVICES` could not be confirmed (the repo is private and no
>    internal doc publishes the list). Verify by either: (a) opening the
>    Activity Tracking Editor and searching "Run" in the API/Service dropdown —
>    that dropdown *is* `ALL_SUPPORTED_SERVICES`; (b) running
>    `Google::Apis::RunV2::CloudRunService.instance_methods(false).sort` in the
>    staging lab's "Run One-off Activity Tracking Code" box; or (c) reading
>    `qwiklab-website/public/gcp_method_info.txt`. If it is absent, request the
>    addition per [adding_apis][addapis].
>    Fallbacks if unsupported: grade the deployment through `LoggingV2` audit
>    logs, or through the Artifact Registry image, or have the student write a
>    marker object to GCS and check it with `StorageV1`.
> 2. **Provisioned Throughput.** Gemini Enterprise in a Qwiklabs project needs a
>    PT allocation ([go/qwiklabs-pt][pt]) plus a capacity request
>    ([go/lfs-capacity-request][cap]) and the `gcp_pt` project variant; without
>    it Task 5 fails with `Quota has been exceeded`. This bundle currently uses
>    the default variant.
> 3. **`default_locale: ko`** acceptance on CE Qwiklabs is unconfirmed. The
>    canonical example and the CE authoring workflow both assume
>    `instructions/en.md` as the base.


### Pre-submission smoke test (one command, resolves three unknowns)

The three remaining uncertainties can all be settled in a single run. Launch the
lab on staging and paste this into **"Run One-off Activity Tracking Code"** —
the only debugging channel graders have, since they cannot write to disk or
shell out ([go/activity-tracking-best-practices][atbp]):

```ruby
def check(handles:, maximum_score:, resources:)
  bq  = handles['primary_project.BigqueryV2']
  run = handles['primary_project.RunV1']
  out = []
  out << "resources=#{resources.class}:#{resources.inspect}"
  out << "bq.project=#{bq.project}"
  out << "run=#{run.class}"
  begin
    svc = run.get_namespace_service(
      "namespaces/#{run.project}/services/enterprise-hub-agent", freeze_args: true
    )
    out << "knative_ok=#{svc.status.conditions.map { |c| "#{c.type}=#{c.status}" }.join(',')}"
  rescue StandardError => e
    out << "knative_err=#{e.class}: #{e.message}"
  end
  { score: 0, message: 'probe', student_message: out.join(' | ') }
end
```

Reading the output:

| Observation | Conclusion |
| :--- | :--- |
| The code runs at all | `freeze_args: true` is accepted — no `ArgumentError (unknown keyword)` |
| `run=` prints a class | `RunV1` **is** in `ALL_SUPPORTED_SERVICES` |
| Handle construction fails | `RunV1` is not registered → request it per [adding_apis][addapis], or fall back to `LoggingV2` / `StorageV1` marker |
| `knative_ok=Ready=True` | the Knative surface works on whatever endpoint the handle uses |
| `knative_err=...404` | the global endpoint is in play → the `projects/locations/` fallback in the grader is the path that will run |
| `resources=` contents | confirms whether `resources` carries anything; the grader deliberately does not depend on it |

[addapis]: http://go/qwiklabs-docs/runtime/activity_tracking/procedures/adding_apis
[pt]: http://go/qwiklabs-pt
[cap]: http://go/lfs-capacity-request

[spec]: http://google3/cloud/training/qwiklabs/content_bundle/g3doc/lab-bundle-spec.md
