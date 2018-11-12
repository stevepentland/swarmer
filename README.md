# Swarmer
[![Build Status](https://travis-ci.com/stevepentland/swarmer.svg?branch=master)](https://travis-ci.com/stevepentland/swarmer)


Python application and API to run services from within a docker swarm

# How it works
The swarmer lives in a service inside a docker swarm. Once exposed, it offers an
API to activate one shot docker service runs. There is a companion container to this
service that is responsible for reporting the results back to this service. Once all
tasks within a job are complete, the complete set of results is returned.

# Dependencies
To run, this image requires a redis service to be available

**More information coming soon**

