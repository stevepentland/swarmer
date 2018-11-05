from sanic import Blueprint
from sanic.websocket import WebSocketProtocol

bp = Blueprint('ws_print', url_prefix='ws')


@bp.websocket('/report')
async def report_result(request, ws):
    """ Provides the reporting feed for runners

    :param request: The original HTTP request
    :param ws: The websocket conection
    """
    pass
