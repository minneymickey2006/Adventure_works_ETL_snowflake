import pendulum
from airflow import DAG
from airflow.decorators import task
from airflow.exceptions import AirflowException
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule


@task(trigger_rule=TriggerRule.ONE_FAILED, retries=0)
def watcher():
    raise AirflowException("Failing task because one or more upstream tasks failed.")


with DAG(
        dag_id="watcher_pattern_ins",
        schedule_interval=None,
        start_date=pendulum.yesterday(tz="UTC"),
        catchup=False,
) as dag:
    failing_task = BashOperator(task_id="failing", bash_command="exit 1", retries=0)
    passing_task = BashOperator(task_id="passing", bash_command="echo passing_task")

    teardown_task = BashOperator(
        task_id="teardown",
        bash_command="echo teardown",
        trigger_rule=TriggerRule.ALL_DONE,
    )

    failing_task >> passing_task >> teardown_task

    dag.tasks >> watcher()
