
from flask import Flask, request, jsonify, render_template
import os
from code_agent.code_agent import CodeAgent
import logging
import traceback
from rag.hybrid_vector_graph_rag.ingest_corpus import ingest_corpus

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more verbosity
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
)

app = Flask(__name__, static_folder='static', template_folder='templates')

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

        tools = [
            {
                "tool_name": "numpy",
                "lib_name": ["numpy"]
            },
            {   
                "tool_name": "geopy",
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
            tools=tools,
        )

        final_answer = code_agent.run_agent()
        return jsonify({"assistant": final_answer}), 200
    
    except Exception as e:
        logging.error("Exception occurred in /run-code-agent: %s", str(e))
        logging.error(traceback.format_exc())
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/hybrid-vector-graph-rag-ingest-corpus', methods=['POST'])
def hybrid_vector_graph_rag_ingest_corpus():
    try:
        ingest_corpus()
        return jsonify({"message": "Script executed successfully"}), 200
    except Exception as e:
        logging.error("Exception occurred in /hybrid-vector-graph-rag-ingest-corpus: %s", str(e))
        logging.error(traceback.format_exc())
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=True
    )
