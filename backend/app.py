from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from models import db
from routes import api

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instagram.db"
app.config["JWT_SECRET_KEY"] = "secret123"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
JWTManager(app)

app.register_blueprint(api)

with app.app_context():
    db.create_all()

print("Starting Flask server...")

if __name__ == "__main__":
    app.run(debug=True)
