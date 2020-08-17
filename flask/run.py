from app import app
import os

# Run flask with: python -m flask run --host=0.0.0.0 --port=5001

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=app.config["DEBUG"])
    

    