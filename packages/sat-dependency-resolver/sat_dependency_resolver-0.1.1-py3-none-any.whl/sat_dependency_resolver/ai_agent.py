try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    Anthropic = None


class ConflictHelper:
    def __init__(self, api_key=None):
        if not HAS_ANTHROPIC:
            self.client = None
            self.enabled = False
            return
            
        if api_key:
            self.client = Anthropic(api_key=api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
    
    def get_recommendation(self, requirements: dict, conflicts: list, available_packages: dict) -> str:
        if not self.enabled:
            return None
            
        if not HAS_ANTHROPIC:
            return "AI recommendations require 'anthropic' package. Install with: pip install sat-dependency-resolver[ai]"
            
        try:
            prompt = self.build_prompt(requirements, conflicts, available_packages)
            
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        
        except Exception as e:
            return f"couldn't get recommendation: {str(e)}"
    
    def build_prompt(self, reqs: dict, conflicts: list, pkgs: dict) -> str:
        prompt = "I'm trying to resolve package dependencies but got conflicts.\n\n"
        
        prompt += "What I want:\n"
        for name, constraint in reqs.items():
            prompt += f"  - {name} {constraint}\n"
        prompt += "\nConflicts:\n"
        for conflict in conflicts:
            prompt += f"  - {conflict}\n"
        
        prompt += "\nAvailable versions:\n"
        for name, versions in pkgs.items():
            vers = [v['version'] for v in versions]
            prompt += f"  - {name}: {', '.join(vers)}\n"
        
        prompt += "\nHow can I fix this? Give me 2-3 concrete suggestions in a brief, actionable format."
        
        return prompt