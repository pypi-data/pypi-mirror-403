from os import getenv
from pathlib import Path

from ytdlp_simple.bins import get_writable_bin_dir
from ytdlp_simple.config import logger
from ytdlp_simple.paths import get_out_dir
from ytdlp_simple.utils import get_cookie_arg

def get_env_bool(var_raw_value: str | None = None) -> bool:
    true_values = ('true', '1', 'yes', 'on', 'y', 'enabled')
    false_values = ('false', '0', 'no', 'off', 'n', 'disabled', '')

    if not var_raw_value:
        return False

    value = var_raw_value.lower().strip()

    if value in true_values:
        return True
    elif value in false_values:
        return False
    logger.warning(f'boolean type variable is set incorrectly in the environment, '
                   f'one of the following is expected: {true_values + false_values}')
    return False


HIDE_HOME = get_env_bool(getenv('HIDE_HOME'))
WEB_UI = get_env_bool(getenv('WEB_UI'))

DOWNLOADS_DIR = get_out_dir(getenv('DOWNLOADS_DIR'))
PORT = int(getenv('PORT', 7860))

_internal_url = f'http://127.0.0.1:{PORT}'

COOKIES_FOLDER = getenv('COOKIES_FOLDER')
if COOKIES_FOLDER is not None:
    COOKIES_FOLDER = Path(COOKIES_FOLDER).resolve()
    if not get_cookie_arg(COOKIES_FOLDER):
        try:
            COOKIES_FOLDER.mkdir(parents=True, exist_ok=True)
        except:
            logger.error(f'cookies folder "{str(COOKIES_FOLDER)}" doesnt exist and unable to create it!')
else:
    COOKIES_FOLDER = get_writable_bin_dir() / 'cookies'
    if not COOKIES_FOLDER.exists():
        COOKIES_FOLDER.mkdir(parents=True, exist_ok=True)
        logger.warning(f'cookies folder "{str(COOKIES_FOLDER)}" created, upload cookies here: {_internal_url}/cookies-ui')
logger.info(f'main UI here: {_internal_url}/ui')
logger.info(f'manage cookies here: {_internal_url}/cookies-ui')


FILE_RETENTION_H = int(getenv('FILE_RETENTION_H', 0)) if getenv('FILE_RETENTION_H') else 0
if FILE_RETENTION_H <= 0:
    logger.warning('\nFile retention period must be greater than 0 (hours)\n'
                   'otherwise, downloaded files will never be deleted and the disk may overflow!\n'
                   'If you run this API locally, this is fine, otherwise set the environment variable "FILE_RETENTION_H" to the correct value')

API_TOKEN = getenv('API_TOKEN', '').strip()

STATIC_DIR = Path(__file__).parent / 'static'


