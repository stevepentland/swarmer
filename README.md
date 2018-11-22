# Swarmer
[![Build Status](https://travis-ci.com/stevepentland/swarmer.svg?branch=master)](https://travis-ci.com/stevepentland/swarmer)

Python application and API to run services from within a docker swarm.

# *NOTE*
There have been some significant changes between versions 0.2.6 and version 0.3.0 that
change the way swarmer is installed and works to provide authentication to private
docker registries. This documentation will be updated soon to reflect that.

# How it works
The swarmer lives in a service inside a docker swarm. Once exposed, it offers an
API to activate one shot docker service runs. There is a companion application to this
service that is responsible for reporting the results back to this service. Once all
tasks within a job are complete, the complete set of results is posted back to a specified
callback URL.

## Clients

While any client that is compatible of running your subject code from within another container
based on the values passed will work, there is a default client you can view. This list
will be updated when more default clients become available:

- [swarmer-client-js](https://github.com/stevepentland/swarmer-client-js)

# Dependencies
To run, this image requires a redis service to be available, and to receive results, you'll
need a callback url accepting POST data (application/json) that is accessible from the your swarm
location.

# Getting started

You can take the compose example in this repository and run it as it is in your docker swarm
via `docker stack deploy -c docker-compose.yml`, changing any of the values that you see fit.

Once started, there will be a service exposed at the address of your swarm that you can 
post jobs to. 

## The initial request

When you want to submit a new job, you send a request to the `/submit` endpoint, with a 
content type of `application/json` and a body with the following:

```json
{
  "image_name": "some-image:latest",
  "callback_url": "your postback url"
}
```

You will receive a response with an identifier, this is a unique job id you can use to submit
tasks to your job. 

## Adding tasks

Once your job has been created, you can submit a list of tasks to it. This is done via the
`/submit/<identifier>/tasks` POST endpoint, where `identifier` is the id value you were
given when the job was created. The body of this request should look like the following:

```
{
  "tasks": [
    {
      "task_name": "<Name>",
      "task_args": ["arg-one", "arg-two", ...]
    },
    ...
  ]
}
```
Once the tasks have been submitted, they will begin running immediately.

## Checking the status of a job

If you have a running job that you would like to check on, you can send
a GET request to the `/status/<identifier>` resource, where `identifier`
is the id value of your job.

# Getting your results

Once all the tasks for your job are complete, the URL you specified
in the `callback_url` field will receive a POST request with the 
collected results. The general format is:

```json
{
  "__image": "your image",
  "__callback_url": "your url",
  "tasks": [
    {
      "name": "task name",
      "status": 0,
      "args": ["your", "args"],
      "result": {
        "stdout": "the output written to stdout",
        "stderr": "the output written to stderr"
      }
    },
    ...
  ]
}
```

For each task, the `status` field represents the exit
status of the task process, while the `result` object
contains the output that your task wrote to the two 
output streams.