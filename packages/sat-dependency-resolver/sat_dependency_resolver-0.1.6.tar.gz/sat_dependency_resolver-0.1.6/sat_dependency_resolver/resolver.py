from typing import Dict, List, Optional
from dataclasses import dataclass
from pysat.solvers import Glucose3

from .encoder import SATEncoder, Package
from .ai_agent import ConflictHelper


@dataclass
class ResolutionResult:
    is_satisfiable: bool
    solution: Optional[Dict[str, str]]
    conflicts: List[str]
    recommendation: Optional[str] = None

class DependencyResolver:
    def __init__(self):
        self.encoder = SATEncoder()
    
    def solve(self, requirements: Dict[str, str], available_packages: Dict[str, List[Dict]], use_ai: bool = False, api_key: str = None) -> ResolutionResult:
        packages = self.parse_packages(available_packages)
        rules, id_map = self.encoder.encode_dependencies(packages)
        user_rules = self.add_user_requirements(requirements, packages)
        rules.extend(user_rules)
        
        for rule in rules:
            if not rule:
                return ResolutionResult(
                    is_satisfiable=False,
                    solution=None,
                    conflicts=["no solution exists"],
                    recommendation=None
                )
        solver = Glucose3()
        try:
            for rule in rules:
                solver.add_clause(rule)
            works = solver.solve()
            
            if works:
                result = solver.get_model()
                answer = self.encoder.extract_solution(result)
                return ResolutionResult(
                    is_satisfiable=True,
                    solution=answer,
                    conflicts=[],
                    recommendation=None
                )
            else:
                problems = self.find_problems(requirements, packages, id_map)
                rec = None
                if use_ai:
                    ai_helper = ConflictHelper(api_key=api_key)
                    if ai_helper.enabled:
                        rec = ai_helper.get_recommendation(requirements, problems, available_packages)
                return ResolutionResult(
                    is_satisfiable=False,
                    solution=None,
                    conflicts=problems,
                    recommendation=rec
                )
        except Exception as e:
            return ResolutionResult(
                is_satisfiable=False,
                solution=None,
                conflicts=[f"error: {str(e)}"],
                recommendation=None
            )
        finally:
            solver.delete()
    
    def parse_packages(self, data: Dict[str, List[Dict]]) -> Dict[str, List[Package]]:
        packages = {}
        for name, vers in data.items():
            packages[name] = []
            for v in vers:
                pkg = Package(
                    name=name,
                    version=v['version'],
                    requires=v.get('requires', {})
                )
                packages[name].append(pkg)
        return packages
    
    def add_user_requirements(self, reqs: Dict[str, str], packages: Dict[str, List[Package]]) -> List[List[int]]:
        rules = []
        for name, req in reqs.items():
            if name not in packages:
                rules.append([])
                continue
            ok_versions = self.encoder.matching_versions(packages[name], req)
            if len(ok_versions) == 0:
                rules.append([])
                continue
            rule = []
            for ver in ok_versions:
                vid = self.encoder.get_id(name, ver.version)
                rule.append(vid)
            rules.append(rule)
        return rules
    
    def find_problems(self, reqs: Dict[str, str], packages: Dict[str, List[Package]], id_map: Dict) -> List[str]:
        problems = []
        for name in reqs:
            if name not in packages:
                problems.append(f"package '{name}' not found")
        
        for name, req in reqs.items():
            if name not in packages:
                continue
            ok_versions = self.encoder.matching_versions(packages[name], req)
            
            if len(ok_versions) == 0:
                have = [p.version for p in packages[name]]
                problems.append(
                    f"'{name}' needs '{req}' but only have: {', '.join(have)}"
                )
        
        dep_problems = self.check_dep_conflicts(packages)
        problems.extend(dep_problems)
        
        if len(problems) == 0:
            problems.append("can't resolve - probably circular deps or version mismatch")
        return problems
    
    def check_dep_conflicts(self, packages: Dict[str, List[Package]]) -> List[str]:
        problems = []
        dep_needs = {}
        
        for name, versions in packages.items():
            for ver in versions:
                for dep, need in ver.requires.items():
                    if dep not in dep_needs:
                        dep_needs[dep] = []
                    dep_needs[dep].append((f"{name}=={ver.version}", need))
        
        for dep, needs in dep_needs.items():
            if len(needs) < 2:
                continue
            has_upper = False
            has_lower = False
            for _, need in needs:
                if '<' in need:
                    has_upper = True
                if '>' in need:
                    has_lower = True
            
            if has_upper and has_lower:
                msg = f"conflicting needs for '{dep}':\n"
                count = 0
                for src, need in needs:
                    if count >= 3:
                        break
                    msg += f"  {src} needs {dep}{need}\n"
                    count += 1
                problems.append(msg.strip())
        
        return problems