# Swarmer
[![Build Status](https://travis-ci.com/stevepentland/swarmer.svg?branch=master)](https://travis-ci.com/stevepentland/swarmer)


Python application and API to run services from within a docker swarm.

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

To be completed soon...
