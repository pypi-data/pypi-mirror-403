client_id = None
apikey = None
api_url = 'https://api.mangopay.com/v2.01/'
api_sandbox_url = 'https://api.sandbox.mangopay.com/v2.01/'
temp_dir = None
api_version = 2.01
sandbox = True
uk_header_flag = False

package_version = None
try:
    # try importlib.metadata first
    from importlib.metadata import version
    package_version = version('mangopay4-python-sdk')
except Exception:
    # fallback for development/editable installs
    try:
        with open('./setup.py', 'r') as f:
            for line in f:
                if line.startswith('    version'):
                    package_version = line.split('=')[1].replace("'", "").replace(",", "").replace("\n", "").strip()
    except:
        None


from .api import APIRequest  # noqa
from .utils import memoize


def _get_default_handler():
    return APIRequest()

get_default_handler = memoize(_get_default_handler, {}, 0)
