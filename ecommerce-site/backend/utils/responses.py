from flask import jsonify


def success_response(data=None, message='Success', status=200):
    payload = {'status': 'success', 'message': message}
    if data is not None:
        payload['data'] = data
    response = jsonify(payload)
    response.status_code = status
    return response


def error_response(message='Error', status=400):
    payload = {'status': 'error', 'message': message}
    response = jsonify(payload)
    response.status_code = status
    return response


def not_found_response(message='Not found'):
    return error_response(message, 404)


def unauthorized_response(message='Unauthorized'):
    return error_response(message, 401)
