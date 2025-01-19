
from flask import Flask, request, jsonify, render_template
import os
from state_machine import run_machine
from session_manager import SessionManager
from interactive_multiagent.planner import AgentPlanner
from code_agent.code_agent import CodeAgent
import logging
import traceback

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more verbosity
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
)

app = Flask(__name__, static_folder='static', template_folder='templates')

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

session_manager = SessionManager(redis_host=REDIS_HOST, redis_port=REDIS_PORT, db=REDIS_DB)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/run-code-agent', methods=['POST'])
def run_code_agent():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is empty"}), 400

        # Extract necessary fields for initializing CodeAgent
        chat_history = data.get('session_chat_history', [])

        import_libraries = [
            {
                "lib_name": ["numpy"]
            },
            {
                "lib_name": ["geopy"],
                "instructions": "A library to get the coordinates of a given location.",
                "code_example": """
                    from geopy.geocoders import Nominatim
                    from geopy.exc import GeocoderTimedOut, GeocoderServiceError

                    def get_coordinates({{user_agent, location}}):
                    
                        user_agent = "my-app/1.0"
                        location = "Rome, Italy"
                    
                        geolocator = Nominatim(user_agent=user_agent)

                        try:
                            # Geocode the location
                            geo_location = geolocator.geocode(location)
                            
                            if geo_location:
                                return (geo_location.latitude, geo_location.longitude)
                            else:
                                print(f"Location '{{location}}' not found.")
                                return None

                        except GeocoderTimedOut:
                            print("Geocoding service timed out.")
                            return None
                        except GeocoderServiceError as e:
                            print(f"Geocoding service error: {{e}}")
                            return None

                """
            }
        ]

        code_agent = CodeAgent(
            chat_history=chat_history,
            import_libraries=import_libraries
        )

        final_answer = code_agent.run_agent()
        return jsonify({"assistant": final_answer}), 200
    
    except Exception as e:
        logging.error("Exception occurred in /run-code-agent: %s", str(e))
        logging.error(traceback.format_exc())
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=True
    )
