import logging

from twidder.database_handler import initialize_database
from twidder.server import app

logger = logging.getLogger("Twidder")
app.logger.handlers.extend(logger.handlers)
app.logger.setLevel(logging.DEBUG)

with app.app_context():
    initialize_database()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
