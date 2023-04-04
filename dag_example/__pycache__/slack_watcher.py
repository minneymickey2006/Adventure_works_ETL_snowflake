import pendulum
from airflow import DAG
from airflow.decorators import task
from airflow.exceptions import AirflowException
from airflow.operators.bash import BashOperator
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
from airflow.utils.trigger_rule import TriggerRule


@task(trigger_rule=TriggerRule.ALL_DONE)
def watcher():
    raise AirflowException("Failing task because one or more upstream tasks failed.")


with DAG(
        dag_id="slack_watcher",
        schedule_interval=None,
        start_date=pendulum.yesterday(tz="UTC"),
        catchup=False,
) as dag:
    etl_start = SlackWebhookOperator(
        task_id="etl_start",
        http_conn_id="slack_dec",
        message="ETL started",
        channel="#content"
    )

    etl_fail_watcher = SlackWebhookOperator(
        task_id="etl_fail",
        http_conn_id="slack_dec",
        message="ETL failed caught by watcher",
        channel="#content",
        trigger_rule=TriggerRule.ONE_FAILED
    )

    failing_task = BashOperator(task_id="failing", bash_command="exit 1", retries=0)
    passing_task = BashOperator(task_id="passing", bash_command="echo passing_task")

    teardown_task = BashOperator(
        task_id="teardown",
        bash_command="echo teardown",
        trigger_rule=TriggerRule.ALL_DONE,
    )

    etl_start >> failing_task >> passing_task >> teardown_task

    task_list = dag.tasks
    task_list.remove(etl_fail_watcher)
    task_list >> etl_fail_watcher >> watcher()
