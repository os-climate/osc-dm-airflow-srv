# osc-dm-airflow-srv

This repository contains the Dags that are available
in Project X's airflow instance.

## Getting started

In order to quickly get started with the osc-dm-airflow-srv repository 
instructions below have been provided to quickly spin up a local docker image
and run dags on it.

### Setting up your environment

In order to run this environment the `HOME_DIR` environment variable must be set
to the parent directory of this repository.

~~~
export HOME_DIR=<prepo parent dir>
~~~

Some other environment variables are used the scripts and images in this
repository. Run the below environment script to set them up.
~~~~
source ./bin/environment.sh
~~~~

### Running a local airflow docker

To start a local docker image, first ensure that the docker daemon
is running, then run the below command:

~~~
./bin/start_airflow.sh
~~~

This will start the airflow server, which can be accessed at `localhost:8080`.
To log in to the server using the following credentials:
(username: admin, password: admin)

### Running example DAG

In order to run the example DAG, first the local airflow docker must be
set up (see "Running a local airflow docker" section).
Once that is done access the airflow at
`localhost:8080` and credentials: (username: admin, password: admin).
Once logged in enable the gen_one_dataset-example DAG. Then click on
the DAG named example_loading_pipeline,
which wil bring you to the screen for this specific
DAG. In the top right there will be a trigger DAG button
(which looks like a blue arrow). Click this button to start the DAG.

This dag will take the example_rawdata/example_dataset.parquet
data and generate the `example_loading_pipeline.duckdb`
and `dataset_metadata.duckdb` files in
the `./working_example/output/` directory.

### Production Example DAG

The previous example DAG is very simple to allow for a quick and easy example.
This next DAG will replicate something closer to a production environment by
using more data.

#### Getting data

Flood data from TuDelft will be used as an example dataset.
Note that this data is 5GB in size, though only a small piece of it is used
in the provided example.

Data can be retrieved from the below link

- [Pan-European data sets of river flood probability of occurrence under present and future climate_1_all.zip](https://data.4tu.nl/file/df7b63b0-1114-4515-a562-117ca165dc5b/5e6e4334-15b5-4721-a88d-0c8ca34aee17)

Which was retrieved from this [parent site](https://data.4tu.nl/articles/dataset/Pan-European_data_sets_of_river_flood_probability_of_occurrence_under_present_and_future_climate/12708122)

Create the `data/geo_data/flood/europe_flood_data` directory as below:

```bash
mkdir -p ./data/geo_data/flood/europe_flood_data
```

Unzip the `Pan-European data sets of river flood probability
 of occurrence under present and future climate_1_all.zip`
file into the `example_rawdata` directory.
This should result in a directory structure that looks like the below:

```console
example_rawdata
    |-- data.zip
    |-- readme_river_floods_v1.1.pdf
```

Create the `example_rawdata` directory as below

```bash
mkdir -p ./example_rawdata/data
```

Unzip the `data.zip` file into the
`./data/geo_data/flood/europe_flood_data/data`
directory. This should result in a file structure like below:

```console
example_rawdata
    |-- data.zip
    |-- readme_river_floods_v1.1.pdf
    |-- data
        |-- River_discharge_1971_2000_hist.dbf
        |-- River_discharge_1971_2000_hist.prj
        ...
```

#### Running the DAG

In order to run the example DAG, first the local airflow docker must be
set up (see "Running a local airflow docker" section).
Once that is done access the airflow at
`localhost:8080` and credentials: (username: admin, password: admin).
Once logged in enable the gen_one_dataset-example DAG. Then click on
the DAG named gen_one_dataset-example,
which wil bring you to the screen for this specific
DAG. In the top right there will be a trigger DAG button
(which looks like a blue arrow). Click this button to start the DAG.

This dag will take the example_rawdata/example_dataset.parquet
data and generate the `tu_delft_River_flood_depth_1971_2000_hist_0010y.duckdb`
and `dataset_metadata.duckdb` files in
the `./working_example/output/` directory.


## Creating DAGs

DAGS are configured through the use of .yaml files that specify the
operations to be performed as part of the dags. To do this both a 
configuration for the entire DAG is needed, as well as configurations
for the individual tasks to be run. 

### Creating Tasks

To create a new task create a new configuration file in the 
`working/tasks` directory (for custom airflow instance) or
`working_example/tasks` directory (for local example airflow). An example
of one of these task configuration files is shown below:

```yaml
task:

  task_id: tu_delft_River_flood_depth_1971_2000_hist_0010y
  type: docker

  image: brodagroupsoftware/osc-geo-h3loader-cli
  container_name: osc-geo-h3loader-cli-tu_delft_River_flood_depth_1971_2000_hist_0010y
  api_version: auto
  auto_remove: true
  docker_url: tcp://docker-proxy:2375
  network_mode: bridge
  command: "python /app/src/cli/cli_load.py load-pipeline --config_path /opt/airflow/task_files/tu_delft_River_flood_depth_1971_2000_hist_0010y.yml"

  mounts:
    - ${RAW_DATA_DIR}/:/opt/airflow/data
    - ${WORKING_DIR}/output:/opt/airflow/geodatabases
    - ${WORKING_DIR}/task_files:/opt/airflow/task_files
```

All parameters in this file will be under the `task` element,
with many of the specific values being dependent on type of task
being run. The id of the tasks is controlled by its file name.
Generic parameters which should be present for every type
of task are listed below. 

Generic parameters

| Parameter | Type | Description                                                |
|-----------|------|------------------------------------------------------------|
| type      | str  | The type of task beign done. supported types: bash, docker |


#### Bash Task

Bash tasks will execute a shell command on the airflow machine
that runs the task. This can be used to perform setup or cleanup
operations, or to run arbitrary commands that do not have a preset
task type.

Bash Parameters

| Parameter | Type | Description                                         |
|-----------|------|-----------------------------------------------------|
| command   | str  | the command that will be run on the airflow machine |

#### Docker Task

A Docker task will run a specified docker image, instantiating it
and running the selected command.

| Parameter      | Type      | Description                                                                                                                                                                                                                                                                    |
|----------------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| image          | str       | The docker image to run. Should be in format [registry]/user/image-name                                                                                                                                                                                                        |
| container name | str       | The name of the container to run. Must be unique within this docker installation                                                                                                                                                                                               |
| api_version    | str       | The version of the api to use. may also be set to `auto`.                                                                                                                                                                                                                      |
| auto_remove    | bool      | Controls whether docker containers should be cleaned up after use. Recommended to set to true                                                                                                                                                                                  |
| docker_url     | str       | The url at which docker can be reached. May be a proxy server, or the location of the docker.sock file                                                                                                                                                                         |
| network mode   | str       | The type of network docker is to use.                                                                                                                                                                                                                                          |
| command        | str       | The command to run inside the instantiated docker container.                                                                                                                                                                                                                   |
| mounts         | List[str] | A list of mounts that link directories on the underlying machine to the docker image. <br/>Expected to be in format <underlying directory>:<dir in docker container><br/>Any environment variables present in the mounts will be resolved before mounting these directories.   |



### Assembling Tasks into DAGs

To create a new DAG a new configuration file must be created in the 
`working/dags` directory (for custom airflow instance) or
`working_example/dags` directory (for local example airflow). An example of
this configuration file is shown below:

```yaml

dag:
  max_active_runs: 1
  concurrency: 4


tasks:
  task-preprocessing:
    downstream: [delete_metadata_output-example]

  delete_metadata_output-example:
    downstream: [delete_single_dataset_output-example]

  delete_single_dataset_output-example:
    downstream: [tu_delft_River_flood_depth_1971_2000_hist_0010y-example]

  tu_delft_River_flood_depth_1971_2000_hist_0010y-example:
    downstream: [task-postprocessing]

  task-postprocessing:
    downstream: []
```

All parameters in this file will be under either the `dag` entry - which
contains parameters that apply to the entire dag - or under the `tasks` entry,
which defines tasks to be performed during the job.

dag parameters

| Parameter       | Type | Description                                                                                                                                     |
|-----------------|------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| max_active_runs | int  | The number of instances of this DAG that can run simultaneously                                                                                 |
| concurrency     | int  | The number of tasks that can run simultaneously. Only tasks whose parallelization does not violate order of operations will be run in parallel. |

For the tasks entry, all sub-entries will consist first of the id of the
task to be run. This id is defined by the filename of the configuration file
for that task (without file extension). Below are all parameters that fall
below the task id. The task-preprocessing and task-postprocessing tasks
are mandatory for every dag, as start and end points respectively.

task parameters

| Parameter   | Type      | Description                                                                                   |
|-------------|-----------|-----------------------------------------------------------------------------------------------|
| downstream  | List[str] | A comma separated list of all tasks that are to be performed strictly after this task is run. |


## Custom Airflow

In addition to the examle airflow provided, the DAGs can be used with a
custom or pre-existing airflow installation. in order to do this the below
environment variables will need to be set, both on the underlying machine,
as well as passed into the airflow docker as environment variables:

| Environment variable | Description                                                                    |
|----------------------|--------------------------------------------------------------------------------|
| RAW_DATA_DIR         | The directory on the underlying machine where raw data is stored               |
| WORKING_DIR          | The directory on the underlying machine where the working directory is located |
| AIRFLOW_HOME_DIR     | The home directory on the airflow docker. Used when executing bash tasks.      |

Furthermore, the contents of the dags folder should be copied into the
airflow instance you are using, to the directory it reads DAGs from.

[occ-geo-h3loader-cli]: (https://github.com/os-climate/osc-geo-h3loader-cli)