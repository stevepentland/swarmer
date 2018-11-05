from sanic import Sanic
from sanic.response import json, text
from ws.ws_blueprint import bp as ws_bp

app = Sanic()
app.blueprint(ws_bp)


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


app.run(host='0.0.0.0', port=8500, debug=True)
