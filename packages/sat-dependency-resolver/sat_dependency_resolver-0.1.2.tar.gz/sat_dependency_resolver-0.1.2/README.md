<div align="center">

<img src="https://i.ibb.co/BVCc4tG7/image-2.jpg" alt="SAT Dependency Resolver Banner" width="100%" />

<br/>
<br/>

# SAT Dependency Resolver

### Universal dependency resolution using Boolean Satisfiability (SAT) solvers

[![PyPI version](https://badge.fury.io/py/sat-dependency-resolver.svg)](https://pypi.org/project/sat-dependency-resolver/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Live API](https://img.shields.io/badge/API-Live-green.svg)](https://sat-dependency-resolver-ae207ddb503e.herokuapp.com)

[Live Demo](https://sat-dependency-resolver-ae207ddb503e.herokuapp.com) • [Installation](#installation) • [Quick Start](#quick-start) • [API Reference](#api-reference) • [Examples](#examples)

</div>

---

## 🎯 Overview

SAT Dependency Resolver is a **lightweight, mathematically precise tool** that solves any dependency problem using Boolean Satisfiability (SAT) solvers.

**It answers the question:**
> Given these goals/requirements and these available options with their dependencies, is there a valid combination?
> - ✅ **If yes**: Show one (or more valid solutions)
> - ❌ **If no**: Prove it's impossible and explain why (with optional AI help)

### Why SAT?

- **Guaranteed correctness** — Finds a solution if one exists, or proves none does (no heuristics)
- **Universal** — Not limited to software packages. Works for courses, books, hardware, teams, recipes, scheduling, and more
- **Fast & lightweight** — Built on PySAT + Glucose3 solver

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **SAT-based exact solving** | Uses Glucose3 solver for exhaustive, provably correct results |
| **Conflict detection** | Clear, human-readable explanations of incompatibilities |
| **AI recommendations** | Optional Claude AI suggestions for constraint relaxations or fixes |
| **Flexible constraints** | Supports `"any"`, `==`, `>=`, `<=`, `>`, `<`, comma-separated ranges |
| **REST API** | Simple JSON POST endpoint — call from any language/tool |
| **Python library** | Import and use directly in your Python code |
| **Live demo** | Try instantly at [Heroku](https://sat-dependency-resolver-ae207ddb503e.herokuapp.com) |

---

## 📦 Installation

### Option 1: Install from PyPI (Recommended)

```bash
# Basic installation
pip install sat-dependency-resolver

# With API support
pip install sat-dependency-resolver[api]

# With AI recommendations
pip install sat-dependency-resolver[ai]

# With everything
pip install sat-dependency-resolver[api,ai]
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/Apollo87z/sat-dependency-resolver.git
cd sat-dependency-resolver

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

---

## 🚀 Quick Start

### Using as a Python Library

```python
from sat_dependency_resolver import DependencyResolver

# Define your requirements
requirements = {
    "django": ">=4.0"
}

# Define available packages with their dependencies
available_packages = {
    "django": [
        {"version": "4.0", "requires": {"sqlparse": ">=0.3"}},
        {"version": "4.1", "requires": {"sqlparse": ">=0.4"}},
    ],
    "sqlparse": [
        {"version": "0.3", "requires": {}},
        {"version": "0.4", "requires": {}},
    ]
}

# Solve
resolver = DependencyResolver()
result = resolver.solve(requirements, available_packages)

# Check result
if result.is_satisfiable:
    print(f"✅ Solution found: {result.solution}")
    # Output: ✅ Solution found: {'django': '4.1', 'sqlparse': '0.4'}
else:
    print(f"❌ No solution. Conflicts: {result.conflicts}")
```

### Using the REST API

#### Start the API Server (Local)

```bash
# If installed from PyPI
python -m sat_dependency_resolver.api

# Or if cloned from source
python run_api.py
```

API will be available at `http://localhost:8091`

#### Make a Request

```bash
curl -X POST http://localhost:8091/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": {"django": ">=4.0"},
    "available_packages": {
      "django": [
        {"version": "4.0", "requires": {"sqlparse": ">=0.3"}},
        {"version": "4.1", "requires": {"sqlparse": ">=0.4"}}
      ],
      "sqlparse": [
        {"version": "0.3", "requires": {}},
        {"version": "0.4", "requires": {}}
      ]
    }
  }'
```

**Response:**
```json
{
  "satisfiable": true,
  "solution": {
    "django": "4.1",
    "sqlparse": "0.4"
  },
  "conflicts": []
}
```

---

## 📚 Use Cases

### Software Package Management
Resolve version conflicts for Python, npm, Cargo, RubyGems, etc.

```python
requirements = {
    "package-a": "==1.0",
    "package-b": "==2.0"
}
```

### Course Prerequisites
Plan your academic path with prerequisite constraints.

```python
requirements = {
    "machine-learning": ">=1.0"
}
available_packages = {
    "machine-learning": [{
        "version": "1.0",
        "requires": {
            "linear-algebra": ">=1.0",
            "calculus": ">=1.0",
            "python": ">=1.0"
        }
    }],
    # ... other courses
}
```

### Book Series / Reading Order
Find valid reading sequences for book series.

```python
requirements = {
    "lotr-return-of-king": "any"
}
available_packages = {
    "lotr-return-of-king": [{
        "version": "1.0",
        "requires": {
            "lotr-two-towers": ">=1.0"
        }
    }],
    "lotr-two-towers": [{
        "version": "1.0",
        "requires": {
            "lotr-fellowship": ">=1.0"
        }
    }],
    # ... other books
}
```

### Hardware Compatibility
Check if PC parts are compatible.

```python
requirements = {
    "gpu": "rtx-4090",
    "cpu": "i9-13900k"
}
available_packages = {
    "gpu": [{
        "version": "rtx-4090",
        "requires": {
            "psu": ">=850w",
            "pcie": ">=4.0"
        }
    }],
    # ... other components
}
```

---

## 🌐 API Reference

### Base URLs

- **Live (Production)**: `https://sat-dependency-resolver-ae207ddb503e.herokuapp.com`
- **Local Development**: `http://localhost:8091`

### Endpoints

#### `GET /health`
Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "message": "SAT Dependency Resolver API"
}
```

#### `GET /info`
Get API information and version.

**Response:**
```json
{
  "name": "SAT Dependency Resolver",
  "version": "0.1.1",
  "description": "Universal dependency resolver using SAT solvers"
}
```

#### `POST /resolve`
Resolve dependencies and return a solution or conflicts.

**Headers:**
- `Content-Type: application/json` (required)
- `X-API-Key: sk-ant-...` (optional, required only if `use_ai: true`)

**Request Body:**
```json
{
  "requirements": {
    "package-name": "constraint"
  },
  "available_packages": {
    "package-name": [
      {
        "version": "1.0.0",
        "requires": {
          "dependency": "constraint"
        }
      }
    ]
  },
  "use_ai": false
}
```

**Constraint Syntax:**
- `"any"` — No restriction
- `"==1.2.3"` — Exact version
- `">=1.0"` — Greater than or equal
- `"<=2.0"` — Less than or equal
- `">1.5"` — Greater than
- `"<2.0"` — Less than
- `">=1.0,<2.0"` — Range (comma = AND)

**Response (Success):**
```json
{
  "satisfiable": true,
  "solution": {
    "package-name": "1.0.0",
    "dependency": "2.0.0"
  },
  "conflicts": []
}
```

**Response (Conflict):**
```json
{
  "satisfiable": false,
  "solution": null,
  "conflicts": [
    "package-a requires dependency==1.0 but package-b requires dependency==2.0"
  ],
  "recommendation": "Try relaxing constraint on dependency to >=1.0,<3.0"
}
```

---

## 🧪 Examples

### Example 1: Basic Resolution

```python
from sat_dependency_resolver import DependencyResolver

requirements = {"A": ">=2.0"}
available_packages = {
    "A": [
        {"version": "1.0", "requires": {}},
        {"version": "2.0", "requires": {"B": ">=1.0"}},
        {"version": "3.0", "requires": {"B": ">=2.0"}}
    ],
    "B": [
        {"version": "1.0", "requires": {}},
        {"version": "2.0", "requires": {}}
    ]
}

resolver = DependencyResolver()
result = resolver.solve(requirements, available_packages)
print(result.solution)
# Output: {'A': '3.0', 'B': '2.0'}
```

### Example 2: Conflict Detection

```python
requirements = {
    "package-a": "==1.0",
    "package-b": "==1.0"
}
available_packages = {
    "package-a": [
        {"version": "1.0", "requires": {"shared": "==1.0"}}
    ],
    "package-b": [
        {"version": "1.0", "requires": {"shared": "==2.0"}}
    ],
    "shared": [
        {"version": "1.0", "requires": {}},
        {"version": "2.0", "requires": {}}
    ]
}

resolver = DependencyResolver()
result = resolver.solve(requirements, available_packages)
print(f"Satisfiable: {result.is_satisfiable}")
print(f"Conflicts: {result.conflicts}")
# Output: Satisfiable: False
#         Conflicts: ["can't resolve - probably circular deps or version mismatch"]
```

### Example 3: Using AI Recommendations

```python
from sat_dependency_resolver import DependencyResolver

requirements = {"django": ">=5.0"}  # No version 5.0 available
available_packages = {
    "django": [
        {"version": "4.0", "requires": {}},
        {"version": "4.1", "requires": {}}
    ]
}

resolver = DependencyResolver()
result = resolver.solve(
    requirements, 
    available_packages,
    use_ai=True,
    api_key="sk-ant-your-key-here"
)

if not result.is_satisfiable:
    print(f"AI Recommendation: {result.recommendation}")
    # Output: AI suggestions for fixing the constraint
```

### Example 4: REST API with curl

**Successful Resolution:**
```bash
curl -X POST http://localhost:8091/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": {"python": ">=3.8"},
    "available_packages": {
      "python": [
        {"version": "3.8", "requires": {}},
        {"version": "3.9", "requires": {}},
        {"version": "3.10", "requires": {}}
      ]
    }
  }'
```

**With Conflicts:**
```bash
curl -X POST http://localhost:8091/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": {
      "app": "==1.0"
    },
    "available_packages": {
      "app": [
        {"version": "1.0", "requires": {"lib": "==1.0"}},
        {"version": "2.0", "requires": {"lib": "==2.0"}}
      ],
      "lib": [
        {"version": "2.0", "requires": {}}
      ]
    }
  }'
```

---

## 🧪 Running Tests

### Basic Test Suite

```bash
# Run quick tests
python tests/test_quick.py
```

### Create Your Own Test

Create `test_custom.py`:

```python
from sat_dependency_resolver import DependencyResolver

def test_my_scenario():
    requirements = {
        "my-package": ">=1.0"
    }
    available_packages = {
        "my-package": [
            {"version": "1.0", "requires": {}}
        ]
    }
    
    resolver = DependencyResolver()
    result = resolver.solve(requirements, available_packages)
    
    assert result.is_satisfiable == True
    assert "my-package" in result.solution
    print("✅ Test passed!")

if __name__ == "__main__":
    test_my_scenario()
```

Run it:
```bash
python test_custom.py
```

---

## 🔧 Development

### Project Structure

```
sat-dependency-resolver/
├── sat_dependency_resolver/
│   ├── __init__.py          # Package exports
│   ├── encoder.py           # SAT encoding logic
│   ├── resolver.py          # Main resolver
│   ├── api.py              # Flask REST API
│   └── ai_agent.py         # AI recommendations (optional)
├── examples/
│   ├── basic_usage.py
│   ├── courses.py
│   └── api_example.sh
├── tests/
│   └── test_quick.py
├── run_api.py              # API entry point
├── requirements.txt
├── setup.py
├── README.md
└── LICENSE
```

### Running Locally

```bash
# Clone and setup
git clone https://github.com/Apollo87z/sat-dependency-resolver.git
cd sat-dependency-resolver
python -m venv venv
source venv/bin/activate
pip install -e ".[api,ai]"

# Run API
python run_api.py

# Run tests
python tests/test_quick.py
```

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙋 Support

- **Issues**: [GitHub Issues](https://github.com/Apollo87z/sat-dependency-resolver/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Apollo87z/sat-dependency-resolver/discussions)
- **Author**: [@Apollo87z](https://github.com/Apollo87z)
- **Email**: shehan87h@gmail.com

---

## 🌟 Acknowledgments

- Built with [PySAT](https://pysathq.github.io/) and Glucose3 solver
- Optional AI powered by [Anthropic Claude](https://www.anthropic.com/)
- Inspired by the need for universal, mathematically sound dependency resolution

---

<div align="center">

**Made by [Shehan Horadagoda](https://github.com/Apollo87z)**

⭐ Star this repo if you find it useful!

</div>