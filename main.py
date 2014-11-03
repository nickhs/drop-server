from core import app
from routes import *


if __name__ == '__main__':
    app.run(port=app.config['PORT'])
