"""Project context and AI prompt management."""

import json
import yaml
import pathlib
from typing import Dict, Any


class PromptBuilder:
    """Strategy for building model-specific prompts."""

    def build(self, task: str, ctx: str, proj: str) -> str:
        raise NotImplementedError


class DeepSeekBuilder(PromptBuilder):
    def build(self, task: str, ctx: str, proj: str) -> str:
        return f"You are a Python expert analyzing {proj}\n\nCTX:\n{ctx}\n\nTASK:\n{task}\n\nFocus on efficiency."


class GPTBuilder(PromptBuilder):
    def build(self, task: str, ctx: str, proj: str) -> str:
        return f"Act as Senior Dev for {proj}\n\nContext:\n{ctx}\n\nTask:\n{task}\n\nBe concise."


class ClaudeBuilder(PromptBuilder):
    def build(self, task: str, ctx: str, proj: str) -> str:
        return f"System: Expert Architect for {proj}\n\nContext:\n{ctx}\n\nTask:\n{task}\n\nDetailed analysis."


class AIContextManager:
    """Manages project context and optimizes prompts."""

    def __init__(self, project_path: str):
        self.project_path = pathlib.Path(project_path)
        self.contexts = self._load_all()

    def _load_all(self) -> Dict[str, Any]:
        res = {}
        for f in ["project_context.json", "AI_CONTEXT.md", ".ai-context.yaml"]:
            p = self.project_path / f
            if p.exists():
                res[f] = self._load_f(p)
        return res

    def _load_f(self, p: pathlib.Path) -> Any:
        try:
            if p.suffix == ".json":
                return json.loads(p.read_text(encoding="utf-8"))
            if p.suffix in (".yaml", ".yml"):
                return yaml.safe_load(p.read_text(encoding="utf-8"))
            return p.read_text(encoding="utf-8")
        except Exception:
            return ""

    def create_optimized_prompt(
        self, task: str, model: str = "gpt", max_tokens: int = 4000
    ) -> str:
        builders = {
            "deepseek": DeepSeekBuilder(),
            "gpt": GPTBuilder(),
            "claude": ClaudeBuilder(),
        }
        builder = next(
            (b for k, b in builders.items() if k in model.lower()), GPTBuilder()
        )

        ctx_str = self._extract_ctx(task)
        return builder.build(task, ctx_str[: max_tokens * 2], self.project_path.name)

    def _extract_ctx(self, task: str) -> str:
        kws = [w.lower() for w in task.split() if len(w) > 3]
        found = []
        for name, content in self.contexts.items():
            s = (
                json.dumps(content)
                if isinstance(content, (dict, list))
                else str(content)
            )
            if any(k in s.lower() for k in kws):
                found.append(f"=== {name} ===\n{s[:1000]}")
        return "\n\n".join(found) if found else "No relevant context."

    def update_context(self, info: Dict[str, Any]):
        p = self.project_path / ".ai-context-updates.yaml"
        cur = {}
        if p.exists():
            try:
                cur = yaml.safe_load(p.read_text()) or {}
            except Exception:
                pass

        for k, v in info.items():
            if k in cur and isinstance(cur[k], dict) and isinstance(v, dict):
                cur[k].update(v)
            elif k in cur and isinstance(cur[k], list) and isinstance(v, list):
                cur[k].extend(v)
            else:
                cur[k] = v

        with open(p, "w", encoding="utf-8") as f:
            yaml.dump(cur, f)
