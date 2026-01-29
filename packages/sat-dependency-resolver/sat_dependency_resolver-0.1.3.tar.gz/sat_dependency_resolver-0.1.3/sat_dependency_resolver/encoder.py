from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class Package:
    name: str
    version: str
    requires: Dict[str, str]
    
    def __repr__(self):
        return f"{self.name}=={self.version}"


class SATEncoder:
    def __init__(self):
        self.next_id = 1
        self.pkg_to_id = {}
        self.id_to_pkg = {}
    
    def encode_dependencies(self, packages: Dict[str, List[Package]]) -> Tuple[List[List[int]], Dict]:
        rules = []
        
        for name, versions in packages.items():
            version_rules = self.one_version_only(name, versions)
            rules.extend(version_rules)
            
        for name, versions in packages.items():
            for ver in versions:
                dep_rules = self.build_dep_rules(ver, packages)
                rules.extend(dep_rules)
        
        return rules, self.pkg_to_id
    
    def one_version_only(self, name: str, versions: List[Package]) -> List[List[int]]:
        rules = []
        need_one = []
        for ver in versions:
            vid = self.get_id(name, ver.version)
            need_one.append(vid)
        rules.append(need_one)
        for i in range(len(versions)):
            for j in range(i + 1, len(versions)):
                id1 = self.get_id(name, versions[i].version)
                id2 = self.get_id(name, versions[j].version)
                rules.append([-id1, -id2])
        
        return rules
    
    def build_dep_rules(self, pkg: Package, all_packages: Dict[str, List[Package]]) -> List[List[int]]:
        rules = []
        pkg_id = self.get_id(pkg.name, pkg.version)
        
        for dep_name, constraint in pkg.requires.items():
            if dep_name not in all_packages:
                continue
            ok_versions = self.matching_versions(all_packages[dep_name], constraint)
            if len(ok_versions) == 0:
                rules.append([])
                continue
            
            rule = [-pkg_id]
            for dv in ok_versions:
                did = self.get_id(dep_name, dv.version)
                rule.append(did)
            rules.append(rule)
        
        return rules
    
    def get_id(self, name: str, ver: str) -> int:
        key = (name, ver)
        if key not in self.pkg_to_id:
            self.pkg_to_id[key] = self.next_id
            self.id_to_pkg[self.next_id] = key
            self.next_id += 1
        return self.pkg_to_id[key]
    
    def matching_versions(self, versions: List[Package], constraint: str) -> List[Package]:
        results = []
        reqs = constraint.split(',')
        
        for ver in versions:
            ok = True
            for req in reqs:
                if not self.version_ok(ver.version, req.strip()):
                    ok = False
                    break
            if ok:
                results.append(ver)
        
        return results
    
    def version_ok(self, ver: str, req: str) -> bool:
        if req.startswith('>='):
            return self.ver_cmp(ver, req[2:].strip()) >= 0
        if req.startswith('<='):
            return self.ver_cmp(ver, req[2:].strip()) <= 0
        if req.startswith('>'):
            return self.ver_cmp(ver, req[1:].strip()) > 0
        if req.startswith('<'):
            return self.ver_cmp(ver, req[1:].strip()) < 0
        if req.startswith('=='):
            return ver == req[2:].strip()
        return ver == req.strip()
    
    def ver_cmp(self, a: str, b: str) -> int:
        def parse(v):
            parts = v.split('.')
            nums = []
            for p in parts:
                try:
                    nums.append(int(p))
                except:
                    nums.append(p)
            return tuple(nums)
        va = parse(a)
        vb = parse(b)
        
        if va < vb:
            return -1
        if va > vb:
            return 1
        return 0
    
    def extract_solution(self, model: List[int]) -> Dict[str, str]:
        answer = {}
        for m in model:
            if m > 0 and m in self.id_to_pkg:
                name, ver = self.id_to_pkg[m]
                answer[name] = ver
        return answer