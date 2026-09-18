# Task 4 checkpoint: the enterprise-hub-agent service is deployed to Cloud Run in
# us-central1, reports Ready=True, and carries the environment variable that
# keeps the agent on the real ADK runner.
#
# The env-var check matters because a Cloud Run service missing
# GOOGLE_GENAI_USE_VERTEXAI=TRUE still starts, still answers, and still serves a
# valid Agent Card - it just silently degrades to the deterministic fallback
# router. Scoring "Ready" alone would pass a deployment that does not actually
# run ADK, which is the single most common failure in this lab.

SERVICE_NAME = 'enterprise-hub-agent'.freeze
REGION = 'us-central1'.freeze
REQUIRED_ENV = { 'GOOGLE_GENAI_USE_VERTEXAI' => 'TRUE' }.freeze

def check_cloud_run_service(handles:, maximum_score:, resources:)
  run = handles['primary_project.RunV1']
  raise 'Invalid handle' if run.nil?

  # The GCP handle exposes the student's project directly; `resources` only
  # carries references explicitly declared on the step in qwiklabs.yaml.
  project_id = run.project
  parent = "projects/#{project_id}/locations/#{REGION}"

  # Two call shapes are attempted because the Cloud Run Admin API exposes both a
  # Knative-style namespaces/ surface and an AIP-style projects/locations/ one.
  # The Knative surface is documented as requiring the regional endpoint
  # (https://<region>-run.googleapis.com/); if the handle is built against the
  # global endpoint it can return 404 here, in which case the second call is the
  # one that succeeds.
  #
  # freeze_args: true is the documented convention for Google API calls in
  # graders (go/activity-tracking-best-practices).
  begin
    service = run.get_namespace_service(
      "namespaces/#{project_id}/services/#{SERVICE_NAME}", freeze_args: true
    )
  rescue Google::Apis::ClientError
    begin
      service = run.get_project_location_service(
        "#{parent}/services/#{SERVICE_NAME}", freeze_args: true
      )
    rescue Google::Apis::ClientError
      return {
        score: 0,
        message: "service #{SERVICE_NAME} not found in #{REGION}",
        student_message: 'service_missing'
      }
    end
  end

  ready = (service.status&.conditions || []).any? do |condition|
    condition.type == 'Ready' && condition.status == 'True'
  end

  unless ready
    return {
      score: 0,
      message: "service #{SERVICE_NAME} exists but is not Ready",
      student_message: 'service_not_ready'
    }
  end

  containers = service.spec&.template&.spec&.containers || []
  env_pairs = containers.flat_map { |c| c.env || [] }
                        .each_with_object({}) { |e, acc| acc[e.name] = e.value }

  missing_env = REQUIRED_ENV.reject { |key, value| env_pairs[key] == value }
  unless missing_env.empty?
    # Partial credit: the deployment itself succeeded, so the container build and
    # the Cloud Run configuration are correct; only the agent runtime is degraded.
    return {
      score: (maximum_score / 2),
      message: "deployed but missing env: #{missing_env.keys.join(', ')}",
      student_message: 'env_var_missing'
    }
  end

  { score: maximum_score, message: 'step completed', student_message: 'success' }
end
