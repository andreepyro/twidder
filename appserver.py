from twidder.database_handler import initialize_database
from twidder.server import app

with app.app_context():
    initialize_database()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
