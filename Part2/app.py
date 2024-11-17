from flask import Flask, jsonify
from constants import positions
from agent import start


app = Flask(__name__)

@app.route('/move', methods=['GET'])
def get_position():
    if positions:
        return jsonify(positions.pop(0))
    else:
        return jsonify({'status': 'error'}), 404

@app.route('/move', methods=['PUT'])
def delete_positions():
    global positions
    positions.clear()

    return jsonify({'status': 'success'})

@app.route('/move', methods=['POST'])
def move_object():
    global positions
    start()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)