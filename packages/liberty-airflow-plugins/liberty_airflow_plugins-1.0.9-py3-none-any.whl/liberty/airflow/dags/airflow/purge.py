#
# Copyright (c) 2024 NOMANA-IT and/or its affiliates.
# All rights reserved. Use is subject to license terms.
#
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.models import Variable

def purge_airflow_dag(dag_id, schedule, default_args):
    """
    Creates a DAG to purge old DAG runs, task instances, jobs, and logs.
    
    :param dag_id: ID of the DAG
    :param schedule: Schedule interval of the DAG
    :param default_args: Default arguments for the DAG
    :return: DAG object
    """
    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        description='Purge old DAG runs, task instances, jobs, and logs',
        schedule=schedule,
        tags=['airflow'],
        catchup=False,
    )

    airflow_retention_days = int(Variable.get("airflow_retention_days", default_var=30))

    purge_airflow = BashOperator(
        task_id="purge_airflow",
        bash_command=f"bash -e /opt/purge_airflow.sh --days {airflow_retention_days}",
        dag=dag
    )

    purge_airflow
    
    return dag