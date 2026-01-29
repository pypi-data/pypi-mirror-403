
import datetime
import json
from google.cloud import bigquery
from ipulse_shared_data_eng_ftredge.cloud_level_one.cloud_gcp_bigquery import read_query_bigquery_table_extended

class BigQueryChangelogManager:
    def __init__(self, project_id):
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id

    def append_changelog(self, table_id, where_clause, description, user_id, timestamp=None, changelog_field_name="changelog_registry"):
        """
        Appends a new entry to the changelog field (JSON string map) in a BigQuery table.
        
        Args:
            table_id (str): Full table ID (project.dataset.table).
            where_clause (str): SQL WHERE clause to filter rows to update.
            description (str): Description of the change.
            user_id (str): ID of the user making the change.
            timestamp (datetime.datetime, optional): Timestamp of the change. Defaults to now.
            changelog_field_name (str, optional): Name of the changelog field. Defaults to "changelog_registry".
        """
        
        if timestamp is None:
            timestamp = datetime.datetime.now(datetime.timezone.utc)
            
        # Format key: YYYYMMDDHHMM
        key = timestamp.strftime("%Y%m%d%H%M")
        
        # Format timestamp string: YYYY-MM-DD HH:MM:SS UTC
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Construct the new entry object
        new_entry = {
            "description": description,
            "timestamp_utc": timestamp_str,
            "user_id": user_id
        }
        
        # Serialize new entry to JSON string for the SQL query
        new_entry_json = json.dumps(new_entry)
        
        # Construct the UPDATE query
        # Logic:
        # 1. Parse existing string to JSON. If NULL, treat as empty object {}.
        # 2. Use JSON_SET to add the new key.
        # 3. Convert back to JSON string.
        
        query = f"""
            UPDATE `{table_id}`
            SET {changelog_field_name} = TO_JSON_STRING(
                JSON_SET(
                    COALESCE(PARSE_JSON({changelog_field_name}), JSON '{{}}'),
                    '$.{key}',
                    JSON '{new_entry_json}'
                )
            )
            WHERE {where_clause}
        """
        
        print(f"Executing changelog update on {table_id}...")
        
        # Use read_query_bigquery_table_extended for execution
        # Note: UPDATE queries return an empty iterator but perform the action
        result = read_query_bigquery_table_extended(
            project_id=self.project_id,
            query=query,
            bigquery_client=self.client,
            print_out=True,
            raise_e=False
        )
        
        if result.is_success:
            # For DML statements, we can't easily get affected rows from this wrapper 
            # without modifying it to return job stats, but we know it succeeded.
            print(f"Changelog update executed successfully.")
        else:
            print(f"Changelog update failed: {result.issues_str}")
