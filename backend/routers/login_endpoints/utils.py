import hashlib
import hmac

from backend.routers.login_endpoints.env import *


def verify_auth_data(data_og):
    data = data_og.copy()
    check_hash = data.pop('hash')
    check_list = []
    for k, v in data.items():
        if v is not None:
            check_list.append(f'{k}={v}')

    check_string = '\n'.join(sorted(check_list))
    secret_key = hashlib.sha256(str.encode(BOT_TOKEN)).digest()
    hmac_hash = hmac.new(
        secret_key,
        str.encode(check_string, "utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac_hash == check_hash
