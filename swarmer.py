from sanic import Sanic
from sanic.response import json, text
from results.result_bp import bp as res_bp

app = Sanic()
app.blueprint(res_bp)


@app.post('/submit')
async def submit_job(request):
    """ Submit a run job

    :param request: The incoming HTTP request
    """
    pass


@app.get('/status/<identifier:string>')
async def get_job_status(request, identifier):
    """ Retrieve the status of a job

    :param request: The incoming HTTP request
    :param identifier: The job identifier
    """
    pass
