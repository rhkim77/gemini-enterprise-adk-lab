# Task 1 checkpoint: the three enterprise tables exist in enterprise_finops_gold
# and hold 100 rows in total (32 + 36 + 32).
#
# Row counts are read from the table metadata rather than by running a query:
# get_table returns num_rows directly, which avoids creating a query job in the
# student's project and avoids the streaming-buffer lag that makes a freshly
# loaded table report zero rows for a short window.

DATASET_ID = 'enterprise_finops_gold'.freeze

EXPECTED_ROWS = {
  'cloud_billing_export' => 32,
  'it_security_policy_embeddings' => 36,
  'itsm_realtime_incidents' => 32
}.freeze

def check_bigquery_seed(handles:, maximum_score:, resources:)
  bq = handles['primary_project.BigqueryV2']
  raise 'Invalid handle' if bq.nil?

  project_id = bq.request_options.quota_project || resources['primary_project']['project_id']

  begin
    bq.get_dataset(project_id, DATASET_ID)
  rescue Google::Apis::ClientError
    return {
      score: 0,
      message: "dataset #{DATASET_ID} not found",
      student_message: 'dataset_missing'
    }
  end

  tables = (bq.list_tables(project_id, DATASET_ID)&.tables || []).map do |t|
    t.table_reference.table_id
  end

  missing = EXPECTED_ROWS.keys - tables
  unless missing.empty?
    return {
      score: 0,
      message: "missing tables: #{missing.join(', ')}",
      student_message: 'tables_missing'
    }
  end

  mismatched = []
  EXPECTED_ROWS.each do |table_id, expected|
    actual = bq.get_table(project_id, DATASET_ID, table_id).num_rows.to_i
    mismatched << "#{table_id}=#{actual}(expected #{expected})" if actual != expected
  end

  unless mismatched.empty?
    # Partial credit: the student clearly ran the bootstrap and created the
    # schema, they just did not finish loading the data.
    return {
      score: (maximum_score / 2),
      message: "row count mismatch: #{mismatched.join(', ')}",
      student_message: 'row_count_mismatch'
    }
  end

  { score: maximum_score, message: 'step completed', student_message: 'success' }
end
