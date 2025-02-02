
from flask import Flask, request, jsonify, render_template
import os
import logging
import traceback
from surf_ai.engine import SurfAiEngine 

logging.basicConfig( 
    level=logging.DEBUG,  # Change to DEBUG for more verbosity
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
)

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

    
@app.route('/surf-ai', methods=['POST'])   
def surf_ai():
    try:
        data = request.get_json() 
        chat_history = data.get('session_chat_history', [])
        prompt = chat_history[-1]['content']
        surf_ai_engine = SurfAiEngine() 
        result = surf_ai_engine.go_surf(prompt)
        return jsonify({"assistant": result}), 200
    except Exception as e:
        logging.error("Exception occurred in /surf-ai: %s", str(e))
        logging.error(traceback.format_exc())
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=True
    )
