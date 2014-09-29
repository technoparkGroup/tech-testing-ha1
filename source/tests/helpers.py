from source.lib.utils import Config

def create_config():
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