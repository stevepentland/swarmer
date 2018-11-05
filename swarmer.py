from sanic import Sanic
from sanic.response import json, text

app = Sanic()


@app.post('/submit')
async def submit_job(request):
    pass
