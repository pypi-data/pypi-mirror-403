import click
import datetime
import json
import time

from hcs_cli.service.hoc import diagnostic
from hcs_cli.service import tsctl


@click.command(name="stats-aggregate-connects")
@click.argument("from_", type=int)
@click.argument("to", type=int)
@click.option("--wait", type=bool, required=False, is_flag=True, default=False)
@click.option("--verbose", type=bool, required=False, is_flag=True, default=False)
def aggregate_connects(from_: int, to: int, wait: bool, verbose: bool):
    """
    Aggregate connect events between FROM_ and TO unix timestamps.
    """
    payload = {"from": from_, "to": to}
    result = diagnostic.aggregateConnects(payload, verbose=verbose)
    click.echo(result)

    if not result:
        return "", 1

    if wait:
        wait_for_task(result)


@click.command(name="stats-aggregate-connects-day-before")
@click.option("--wait", type=bool, required=False, is_flag=True, default=False)
@click.option("--verbose", type=bool, required=False, is_flag=True, default=False)
def aggregate_connects_day_before(wait: bool, verbose: bool):
    dt = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    dt_2_days_ago = dt - datetime.timedelta(days=2)
    dt_1_day_ago = dt - datetime.timedelta(days=1)

    print(f"Aggregating connect events from {dt_2_days_ago} to {dt_1_day_ago}")
    from_ = int(dt_2_days_ago.timestamp())
    to = int(dt_1_day_ago.timestamp())
    payload = {"from": from_, "to": to}
    result = diagnostic.aggregateConnects(payload, verbose=verbose)
    click.echo(result)
    if not result:
        return "", 1
    if wait:
        wait_for_task(result)


def wait_for_task(result: dict):
    print("Waiting for task to complete...")
    totalWaitTime = 0
    while True:
        time.sleep(10)
        taskStatus = tsctl.task.lastlog(result.namespace, result.group, result.taskKey)
        if "state" in taskStatus and taskStatus.state == "Error":
            print(f"Task is in {taskStatus.state} state - {taskStatus.error} ")
            print(json.dumps(taskStatus, indent=2))
            break
        if "state" in taskStatus and taskStatus.state == "Success":
            print("Task completed successfully.")
            print(json.dumps(taskStatus, indent=2))
            break
        if ("state" in taskStatus and taskStatus.state == "") or "state" not in taskStatus:
            print("Task is still in progress...")
            totalWaitTime += 10
            if totalWaitTime >= 600:
                print("Waited for 10 minutes, exiting.")
                break
            continue
        print(json.dumps(taskStatus, indent=2))
        break
