import os
import hmac
import hashlib


GITHUB_SECRET = os.environ.get('GITHUB_SECRET', '')


def update_release_notes(request):
    if request.method != 'POST':
        print(f'Method not allowed: {request.method}')
        return '', 302

    try:
        signature = request.headers['X-Hub-Signature']
    except KeyError:
        print('Missing X-Hub-Signature header')
        return '', 302

    digest_maker = hmac.new(
        bytes(GITHUB_SECRET, 'utf-8'),
        request.get_data(),
        hashlib.sha1
    )
    if signature.split('=')[1] != digest_maker.hexdigest():
        print(f'Invalid signature: {signature}')
        return '', 302

    print('success!')
    return '', 200
