import physrisk
import osc_physrisk_financial
from importlib import metadata

from airflow.decorators import dag as dagd
from airflow.decorators import task

import pendulum



DAG_ID = "physrisk_versions_dag"
TAGS = ["example", "physrisk"]
SCHEDULE = "0 6 * * 1-5"
START_DATE = pendulum.datetime(2023, 3, 5, 19, 30, tz="Europe/Madrid")
CATCHUP = False


@dagd(
    dag_id=DAG_ID, schedule=SCHEDULE, start_date=START_DATE, catchup=CATCHUP, tags=TAGS
)
def physrisk_versions():

    @task
    def print_physrisk_package_name():
        print(physrisk.__package__)

    @task
    def print_physrisk_financial_version():
        print(f"osc_physrisk_financial installed with version {metadata.version(osc_physrisk_financial.__package__)}")


    print_physrisk_package_name()
    print_physrisk_financial_version()

physrisk_versions()