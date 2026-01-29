from flask import Flask, request, jsonify
from .resolver import DependencyResolver

app = Flask(__name__)
resolver = DependencyResolver()

@app.route('/resolve', methods=['POST'])
def resolve():
    try:
        if not request.is_json:
            return jsonify({'error': 'content-type must be application/json'}), 400
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'invalid json in body'}), 400
        reqs = data.get('requirements', {})
        pkgs = data.get('available_packages', {})
        use_ai = data.get('use_ai', False)
        api_key = request.headers.get('X-API-Key')
        if not reqs:
            return jsonify({'error': 'missing requirements'}), 400
        if not pkgs:
            return jsonify({'error': 'missing available_packages'}), 400
        if use_ai and not api_key:
            return jsonify({'error': 'use_ai is true but X-API-Key header is missing'}), 400
        result = resolver.solve(reqs, pkgs, use_ai=use_ai, api_key=api_key)
        response = {
            'satisfiable': result.is_satisfiable,
            'solution': result.solution,
            'conflicts': result.conflicts
        }
        if result.recommendation:
            response['recommendation'] = result.recommendation
        return jsonify(response)
    
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

def start(host='0.0.0.0', port=8091, debug=False):
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    print("starting server on :8091")
    start(debug=True)