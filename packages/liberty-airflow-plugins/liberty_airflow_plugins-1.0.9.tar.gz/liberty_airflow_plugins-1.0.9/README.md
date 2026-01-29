# liberty-plugins
Plugins for Liberty Framework

## ✅ Dags

### **Daily DAGs**
- **`airflow-purge-daily-1`**: Purges old Airflow logs and metadata on a daily schedule (`@daily`).
- **`database-backup-daily-1`**: Backs up databases every day at 01:00 AM (`00 1 * * *`).

### **Weekly DAGs**
- **`database-purge-weekly-1`**: Performs database cleanup and purging on a weekly schedule (`@weekly`).

### **Unscheduled DAGs**
- **`airflow-sync-1`**: Synchronizes repositories as needed (manually triggered).


## ✅ Airflow Purge

### **Overview**
This function automates the purge of Airflow dags, jobs and logs.


### **Purge Functions**
- **`dag_runs`**: Deletes old DAG run records from the Airflow database based on the retention period set in the `airflow_retention_days` variable.
- **`task_instances`**: Removes outdated task instance records from the database, ensuring only recent executions are retained.
- **`jobs`**: Cleans up old job entries by deleting records where the job's end date is beyond the retention threshold.
- **`logs_in_db`**: Deletes historical log entries stored in the Airflow database to free up space and improve query performance.
- **`logs_on_disk`**: Scans and removes log files from the Airflow logs directory that exceed the configured retention period, keeping disk usage in check.

### **Configuration**
- The retention period is controlled by the **Airflow Variable**: `airflow_retention_days`.
- If the variable is not set, the default retention period is **30 days**.
- Logs stored in the database and on disk are purged accordingly.

### **Usage**
- These functions should be executed periodically to prevent excessive log and metadata buildup.
- They can be added to an **Airflow DAG** that runs on a **daily schedule (`@daily`)**.

## ✅ Airflow PostgreSQL Backup

### **Overview**
This function automates the backup of PostgreSQL databases using `pg_dump`, managed as an Airflow task.

### **Function**
- **`pg_dump(dag, database_name, conn_id="postgres_conn")`**: Creates a BashOperator task to back up a PostgreSQL database.
  - **`dag`**: The DAG to which this task belongs.
  - **`database_name`**: The name of the database to be backed up.
  - **`conn_id`**: The Airflow connection ID for PostgreSQL (default: `postgres_conn`).
  - **Returns**: A BashOperator task that executes the backup.

### **Configuration**
- The **connection details** are fetched dynamically from Airflow using `get_connection`.
- The **backup location** is inside `$AIRFLOW_HOME/tmp/`.
- **Environment variables** are used to avoid storing credentials in plaintext.

### **Usage**
- This function should be used within an Airflow DAG.
- It ensures database backups are automated and stored securely.
- Can be scheduled to run at desired intervals using DAG scheduling.

## ✅ Database Utils

### **Overview**
This module provides utility functions for retrieving database connection details and column metadata for Oracle and PostgreSQL.

### **Functions**
- **`get_column_lengths(spark, table, schema, conn_source)`**: Retrieves column lengths based on the database type.
- **`get_column_types(data_df, column_lengths, conn_source)`**: Generates a SQL column type definition string for Oracle or PostgreSQL.
- **`get_connection(conn_id, schema=None)`**: Dynamically retrieves database connection details from Airflow based on the connection type.

### **Configuration**
- Supports both Oracle (`oracle.jdbc.driver.OracleDriver`) and PostgreSQL (`org.postgresql.Driver`).
- Uses Airflow's `BaseHook` to dynamically retrieve connection details.
- Calls appropriate helper functions based on the detected database type.

### **Usage**
- Can be integrated into Airflow DAGs for database connection handling.
- Useful for schema extraction, table metadata analysis, and type mapping.
- Ensures compatibility with both Oracle and PostgreSQL environments.

## ✅ Postgres Utils

### **Overview**
This module provides utility functions for working with Apache Spark and PostgreSQL within an Airflow environment.

### **Functions**
- **`create_spark_session()`**: Initializes and returns a Spark session with predefined configurations.
- **`get_all_tables(spark, conn)`**: Retrieves all tables from the database, categorizing them based on foreign key dependencies.
- **`get_foreign_key_dependencies(spark, conn)`**: Fetches foreign key relationships between tables.
- **`topological_sort(dependencies)`**: Performs a topological sort on a given dependency graph.
- **`get_primary_key_for_table(spark, table_name, conn)`**: Retrieves the primary key columns for a specified table.
- **`delete_existing_rows(target_conn, primary_keys, table, rows_to_update)`**: Deletes rows from the target database that need to be updated.
- **`merge_all_tables(conn_source, conn_target, source_schema, target_schema)`**: Manages table synchronization by processing tables without foreign keys first and then handling dependent tables.
- **`merge_single_table(spark, table, source_conn, target_conn)`**: Handles the data merging process for a single table, identifying rows to insert or update in the target database.

### **Configuration**
- Spark session is configured with JDBC drivers for PostgreSQL and Oracle.
- PostgreSQL connections are retrieved dynamically using `get_connection`.
- Foreign key dependencies are processed using topological sorting.

### **Usage**
- Used for efficient data synchronization and migration between databases.
- Can be integrated into Airflow DAGs for automated execution.
- Supports large datasets by leveraging Spark’s distributed processing capabilities.

## ✅ Data Transfer Utils

### **Overview**
This module provides utility functions for reading, processing, and writing data between databases using Apache Spark.

### **Functions**
- **`read_data_from_db(spark, table, source_conn, source_schema)`**: Reads data from a source database using JDBC.
- **`lowercase_columns(df)`**: Converts all column names in a DataFrame to lowercase.
- **`write_data_to_db(spark, data_df, table, source_conn, source_schema, target_conn, target_schema)`**: Writes data to a target database, ensuring proper column types and formatting.
- **`create_spark_session()`**: Initializes a Spark session with necessary configurations.
- **`copy_table(conn_source, conn_target, table_name, source_schema, target_schema)`**: Copies a table from a source schema to a target schema, handling data transformation and loading.

### **Configuration**
- Uses JDBC for database interactions.
- Handles column data type conversion to ensure compatibility.
- Utilizes `get_column_lengths`, `get_column_types`, and `get_connection` for metadata extraction and connection handling.

### **Usage**
- Facilitates ETL operations between databases.
- Ensures clean and structured data processing.
- Can be integrated into Airflow DAGs for automated data migration workflows.


## ✅ Git Backup Utils

### **Overview**
This module provides utility functions for managing backups in Git, including pulling, pushing, and purging old backups.

### **Functions**
- **`pull_repository(local_path, repo_name, conn_id="git_conn")`**: Pulls the latest changes from a Git repository.
- **`push_backup(local_path, repo_name, databases, conn_id="git_conn")`**: Pushes database backups to a Git repository.
- **`purge_old_backups(local_path, repo_name, conn_id="git_conn")`**: Deletes backups older than the configured retention period and commits the changes.

### **Configuration**
- Uses Airflow’s `BaseHook` to retrieve Git connection details dynamically.
- Retrieves the backup retention period from the `backup_retention_days` Airflow variable (default: 30 days).
- Automatically configures Git user details for committing changes.

### **Usage**
- Automates backup management by storing database dumps in Git.
- Ensures that outdated backups are removed efficiently.
- Can be scheduled within an Airflow DAG for periodic execution.

