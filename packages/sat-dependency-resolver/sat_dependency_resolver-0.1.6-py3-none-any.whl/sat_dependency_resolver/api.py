from flask import Flask, request, jsonify
from .resolver import DependencyResolver

app = Flask(__name__)
resolver = DependencyResolver()


@app.route('/', methods=['GET'])
def home():
    """Root endpoint with API information"""
    return jsonify({
        'name': 'SAT Dependency Resolver API',
        'version': '0.1.2',
        'description': 'Universal dependency resolver using Boolean Satisfiability (SAT) solvers',
        'author': 'Shehan Horadagoda',
        'endpoints': {
            'GET /': 'API information (this page)',
            'GET /info': 'Detailed API information',
            'POST /resolve': 'Resolve dependencies'
        },
        'documentation': 'https://github.com/Apollo87z/sat-dependency-resolver',
        'live_demo': 'https://sat-dependency-resolver-ae207ddb503e.herokuapp.com'
    })
    
@app.route('/info', methods=['GET'])
def info():
    """Detailed API information and usage guide"""
    return jsonify({
        'name': 'SAT Dependency Resolver',
        'version': '0.1.2',
        'description': 'Universal dependency resolver using Boolean Satisfiability (SAT) solvers',
        'author': 'Shehan Horadagoda',
        'email': 'shehan87h@gmail.com',
        'repository': 'https://github.com/Apollo87z/sat-dependency-resolver',
        'pypi': 'https://pypi.org/project/sat-dependency-resolver/',
        'endpoints': {
            '/': {
                'method': 'GET',
                'description': 'API information'
            },
            '/health': {
                'method': 'GET',
                'description': 'Health check'
            },
            '/info': {
                'method': 'GET',
                'description': 'Detailed API information (this page)'
            },
            '/resolve': {
                'method': 'POST',
                'description': 'Resolve dependencies',
                'content_type': 'application/json',
                'headers': {
                    'Content-Type': 'application/json (required)',
                    'X-API-Key': 'Anthropic API key (optional, required if use_ai=true)'
                },
                'request_body': {
                    'requirements': {
                        'type': 'object',
                        'description': 'Package requirements with version constraints',
                        'example': {
                            'django': '>=4.0',
                            'flask': '==2.0'
                        }
                    },
                    'available_packages': {
                        'type': 'object',
                        'description': 'Available packages with versions and dependencies',
                        'example': {
                            'django': [
                                {
                                    'version': '4.0',
                                    'requires': {
                                        'sqlparse': '>=0.3'
                                    }
                                }
                            ]
                        }
                    },
                    'use_ai': {
                        'type': 'boolean',
                        'description': 'Enable AI-powered conflict recommendations',
                        'default': False,
                        'optional': True
                    }
                },
                'response': {
                    'satisfiable': {
                        'type': 'boolean',
                        'description': 'Whether a solution was found'
                    },
                    'solution': {
                        'type': 'object or null',
                        'description': 'Selected package versions (null if unsatisfiable)'
                    },
                    'conflicts': {
                        'type': 'array',
                        'description': 'List of conflict descriptions'
                    },
                    'recommendation': {
                        'type': 'string',
                        'description': 'AI suggestion (only if use_ai=true and unsatisfiable)',
                        'optional': True
                    }
                }
            }
        },
        'constraint_syntax': {
            'any': 'No restriction, accepts any version',
            '==X.Y.Z': 'Exact version match',
            '>=X.Y': 'Greater than or equal',
            '<=X.Y': 'Less than or equal',
            '>X.Y': 'Greater than',
            '<X.Y': 'Less than',
            '>=X,<Y': 'Range (comma = AND)'
        },
        'examples': {
            'basic_resolution': {
                'request': {
                    'requirements': {
                        'python': '>=3.8'
                    },
                    'available_packages': {
                        'python': [
                            {'version': '3.8', 'requires': {}},
                            {'version': '3.9', 'requires': {}},
                            {'version': '3.10', 'requires': {}}
                        ]
                    }
                },
                'response': {
                    'satisfiable': True,
                    'solution': {'python': '3.10'},
                    'conflicts': []
                }
            },
            'with_dependencies': {
                'request': {
                    'requirements': {
                        'django': '>=4.0'
                    },
                    'available_packages': {
                        'django': [
                            {'version': '4.0', 'requires': {'sqlparse': '>=0.3'}},
                            {'version': '4.1', 'requires': {'sqlparse': '>=0.4'}}
                        ],
                        'sqlparse': [
                            {'version': '0.3', 'requires': {}},
                            {'version': '0.4', 'requires': {}}
                        ]
                    }
                },
                'response': {
                    'satisfiable': True,
                    'solution': {'django': '4.1', 'sqlparse': '0.4'},
                    'conflicts': []
                }
            },
            'conflict_detection': {
                'request': {
                    'requirements': {
                        'package-a': '==1.0'
                    },
                    'available_packages': {
                        'package-a': [
                            {'version': '1.0', 'requires': {'lib': '==1.0'}}
                        ],
                        'lib': [
                            {'version': '2.0', 'requires': {}}
                        ]
                    }
                },
                'response': {
                    'satisfiable': False,
                    'solution': None,
                    'conflicts': ["can't resolve - probably circular deps or version mismatch"]
                }
            }
        },
        'use_cases': [
            'Software package management (Python, npm, Cargo, etc.)',
            'Course prerequisite planning',
            'Book series reading order',
            'Hardware compatibility checking',
            'Team skill requirement matching',
            'Any system with logical dependencies'
        ],
        'features': [
            'SAT-based exact solving (guaranteed correctness)',
            'Conflict detection with explanations',
            'Optional AI recommendations via Claude',
            'Flexible version constraints',
            'Language-agnostic REST API',
            'Open source (MIT License)'
        ]
    })

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