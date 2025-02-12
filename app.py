from flask import Flask
from routes import bp as routes_bp
import logging

app = Flask(__name__)
app.register_blueprint(routes_bp)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', port=5000)
