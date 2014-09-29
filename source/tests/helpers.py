from source.lib.utils import Config

def create_pusher_config():
    config = Config()
    config.QUEUE_HOST = 'localhost'
    config.QUEUE_PORT = 33013
    config.QUEUE_SPACE = 0
    config.QUEUE_TAKE_TIMEOUT = 0.1
    config.QUEUE_TUBE = 'api.push_notifications'

    config.HTTP_CONNECTION_TIMEOUT = 30
    config.SLEEP = 0.1
    config.SLEEP_ON_FAIL = 10
    config.WORKER_POOL_SIZE = 10
    config.LOGGING = {
        'version': 1
    }
    config.CHECK_URL = ''
    config.HTTP_TIMEOUT = 1

    config.EXIT_CODE = 0
    return config

def create_checker_config():
    config = Config()
    config.INPUT_QUEUE_HOST = 'localhost'
    config.INPUT_QUEUE_PORT = 33013
    config.INPUT_QUEUE_SPACE = 0
    config.INPUT_QUEUE_TUBE = 'url.queue'

    config.OUTPUT_QUEUE_HOST = 'localhost'
    config.OUTPUT_QUEUE_PORT = 33013
    config.OUTPUT_QUEUE_SPACE = 0

    config.OUTPUT_QUEUE_TUBE = 'url_redirect.queue'

    config.WORKER_POOL_SIZE = 10
    config.QUEUE_TAKE_TIMEOUT = 0.1

    config.SLEEP = 10

    config.HTTP_TIMEOUT = 3
    config.MAX_REDIRECTS = 30
    config.RECHECK_DELAY = 300
    config.USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36"

    config.CHECK_URL = "http://t.mail.ru"
    return config