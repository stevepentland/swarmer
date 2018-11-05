from sanic import Blueprint

bp = Blueprint('result_blueprint', url_prefix='results')


@bp.post('/report/<identifier:string>')
async def report_result(request, identifier):
    """ Provides the reporting feed for runners

    :param request: The original HTTP request
    :param identifier: The job identifier
    """
    pass
