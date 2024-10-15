#####
#
# dagexec.py: Load and create DAG and tasks
#
# Copyright 2024 Broda Group Software Inc.
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
#
# Created:  2024-07-22 by eric.broda@brodagroupsoftware.com
#####

import logging
import os
import re
import sys
from typing import List, Any, Dict

import yaml
from datetime import datetime, timedelta
from docker.types import Mount

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.providers.docker.operators.docker import DockerOperator

# Add the src directory (which includes 'comon') to the Python path
# sys.path.append('/opt/airflow/src')
# Show the contents of the added path (for debugging)
# directory = '/opt/airflow/src'
# print([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])

logger = logging.getLogger(__name__)


def read_config(file_path: str):
    logger.info(f"Opening configuration file:{file_path}")
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def load_configurations():
    # Path to the configuration directory
    working_dir = "/opt/airflow/working"
        #os.environ.get("WORKING_DIR")
    print(f"\n\nDAVIS_DEBUG: working dir was {working_dir}\n\n")
    config_dir = f'{working_dir}/config'
    logger.info(f"Using main configuration directory:{config_dir}")

    # Path to the DAGs configuration directory
    dags_config_dir = os.path.join(config_dir, 'dags')
    logger.info(f"Using DAGS configuration directory:{dags_config_dir}")

    # Path to the tasks configuration directory
    tasks_config_dir = os.path.join(config_dir, 'tasks')
    logger.info(f"Using tasks configuration directory:{tasks_config_dir}")

    # Get DAGs based on the configuration files
    dag_configurations = {}
    for dag_config_file in os.listdir(dags_config_dir):
        if dag_config_file.endswith('.yaml'):
            logger.info(f"Using DAG configuration file: {dag_config_file}")
            dag_id = os.path.splitext(dag_config_file)[0]

            fqdags_config_dir = os.path.join(dags_config_dir, dag_config_file)
            config = read_config(fqdags_config_dir)
            dag_configurations[dag_id] = config
            logger.info(f"Using dag:{dag_id} with configuration:{config}")

    # Get tasks based on the configuration files
    task_configurations = {}
    for task_config_file in os.listdir(tasks_config_dir):
        if task_config_file.endswith('.yaml'):
            logger.info(f"Using task configuration file:{task_config_file}")
            task_id = os.path.splitext(task_config_file)[0]

            fqtasks_config_dir = os.path.join(tasks_config_dir,
                                              task_config_file)
            config = read_config(fqtasks_config_dir)
            task_configurations[task_id] = config
            logger.info(f"Using task:{task_id} with configuration:{config}")

    return dag_configurations, task_configurations


def create_dag(dag_id, dag_configuration, task_configurations) -> DAG:
    logger.info(
        f"Using dag_configuration:{dag_configuration} task_configurations:{task_configurations}")

    default_args = {
        "owner": "airflow",
        "description": "Use of the DockerOperator",
        "depend_on_past": False,
        "start_date": datetime(2021, 5, 1),
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5)
    }

    additional_dag_arguments = dict()
    if "dag" in dag_configuration:
        additional_dag_arguments = dag_configuration["dag"]

    with DAG(dag_id, default_args=default_args,
             schedule_interval=dag_configuration.get("schedule_interval", None),
             catchup=False, **additional_dag_arguments) as dag:
        tasks = {}
        for task_id, task_config in dag_configuration["tasks"].items():
            logger.info(f"Creating task:{task_id} configuration:{task_config}")
            task_config = task_configurations[task_id]
            tasks[task_id] = create_task(task_id, task_config)

        # Check for the existence of "task-preprocessing" and "task-postprocessing"
        if "task-preprocessing" not in tasks:
            raise ValueError(
                "Mandatory task-preprocessing does not exist in the DAG configuration")
        if "task-postprocessing" not in tasks:
            raise ValueError(
                "Mandatory task-postprocessing does not exist in the DAG configuration")

        # Add start and end tasks
        start_dag = EmptyOperator(task_id="start")
        end_dag = EmptyOperator(task_id="end")

        # Set "start" as the predecessor of "task-preprocessing"
        start_dag >> tasks["task-preprocessing"]

        # Set "end" as the successor of "task-postprocessing"
        tasks["task-postprocessing"] >> end_dag

        # Set up other task dependencies
        for task_id, task_config in dag_configuration["tasks"].items():
            downstream_tasks = task_config.get("downstream", [])
            for downstream_task_id in downstream_tasks:
                if downstream_task_id not in tasks:
                    raise ValueError(
                        f"Task:{task_id} missing downstream task:{downstream_task_id}")
                logger.info(
                    f"Configuring task:{task_id} with downstream task:{downstream_task_id}")
                tasks[task_id] >> tasks[downstream_task_id]

    return dag


def create_task(task_id: str, config: Dict[str, Any]):
    logger.info(f"Creating task task_id:{task_id} config:{config}")

    config = fix_config(config)

    logger.info(f"Config after environment variable substitution: {config}")

    config = config["task"]

    task_type = config.get("type", None)
    if not task_type:
        raise ValueError("Missing task configuration type")

    if task_type == "dummy":
        return EmptyOperator(task_id=task_id)

    elif task_type == "bash":
        logger.info(f"Using bash config:{config}")
        return BashOperator(
            task_id=task_id,
            bash_command=config["command"]
        )

    elif task_type == "docker":
        logger.info(f"Using docker config:{config}")
        docker_operator_params = {
            "task_id": task_id,
            "image": config.get("image", "default_image"),
            "container_name": config.get("container_name", None),
            "api_version": config.get("api_version", None),
            "auto_remove": config.get("auto_remove", "force"),
            "command": config.get("command", None),
            "docker_url": config.get("docker_url", "tcp://docker-proxy:2375"),
            "network_mode": config.get("network_mode", None),
            "environment": config.get("environment", None),
            "docker_conn_id": config.get('docker_conn_id', None)
        }

        mounts_raw = config.get("mounts")
        if mounts_raw:
            mounts = mount_strs_to_objs(mounts_raw)
            docker_operator_params['mounts'] = mounts

        return DockerOperator(**docker_operator_params)

    raise ValueError(f"Unsupported task_id:{task_id} task_type:{task_type}")


def fix_config(conf: Dict[str, Any]) -> Dict[str, Any]:
    out = conf.copy()
    for k, v in conf.items():
        out[k] = handle_substitution(v)
    return out


def handle_substitution(in_obj: Any) -> Any:
    if isinstance(in_obj, str):
        return substitute_env_vars(in_obj)
    elif isinstance(in_obj, List):
        new_list = []
        for item in in_obj:
            new_item = handle_substitution(item)
            new_list.append(new_item)
        return new_list
    elif isinstance(in_obj, Dict):
        new_dict = dict()
        for k, v in in_obj.items():
            new_dict[k] = handle_substitution(v)
        return new_dict
    else:
        return in_obj


def substitute_env_vars(raw: str) -> Any:
    # env vars have required format of only containing alphanumeric and _ chars
    env_var_regex = r"(\${[A-Za-z0-9_]*})"
    matches = re.findall(env_var_regex, raw)

    # list of tuples (replace_str, env var name)
    env_vars = list(map(
        lambda s: (s, s.replace("$", "").replace("{", "").replace("}", "")),
        matches
    ))

    out = raw
    for replace, var_name in env_vars:
        out = out.replace(replace, os.environ[var_name])
    return out


def mount_strs_to_objs(m_strs: List[str]) -> List[Mount]:
    mnts = []
    for m_str in m_strs:
        m_str = fix_windows_path_format(m_str)
        strs = m_str.split(":")
        if len(strs) != 2:
            raise ValueError(
                "Supplied mount string did not match expected format."
                " Mount string is expected to contain 2 directories, seperated"
                " by a ':' character."
                f" mount string was: {m_str}"
            )
        source = strs[0]
        target = strs[1]
        mnts.append(Mount(source=source, target=target, type="bind"))
    return mnts

def fix_windows_path_format(mount_str: str) -> str:
    # when running on git-bash on a Windows machine paths are auto-converted
    # from linux format (/c/) to windows format (C:/). However the mounts need
    # to be in linux format for docker to properly mount them. So this
    # function identifies and corrects the formats to linux convention.
    win_drive_regex = r"^([a-zA-Z]):.*"
    win_matches = re.findall(win_drive_regex, mount_str)
    if len(win_matches) == 1:
        match = win_matches[0]
        return mount_str.replace(f"{match}:", f"/{match}", 1)
    else:
        return mount_str



dag_configurations, task_configurations = load_configurations()
for dag_id, dag_configuration in dag_configurations.items():
    try:
        logger.info(
            f"Creating DAG instance:{dag_id} using configuration:{dag_configuration}")
        dag_instance = create_dag(dag_id, dag_configuration,
                                  task_configurations)
        globals()[dag_id] = dag_instance
    except Exception as e:
        logger.error(f"error loading dag {dag_id}", e)
