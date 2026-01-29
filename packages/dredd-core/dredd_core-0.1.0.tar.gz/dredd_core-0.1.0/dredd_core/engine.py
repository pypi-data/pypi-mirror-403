#!/usr/bin/env python3
"""
DA-BFT Tribunal Engine - Divergent Arbiter Byzantine Fault Tolerance
New improved version with persona, app-healing toggle, Mistral validator routing, JSON output.
"""

import os
import asyncio
import re
import json
from dataclasses import dataclass
from pathlib import Path


try:
    from groq import AsyncGroq
    from anthropic import AsyncAnthropic
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    raise ImportError("Missing dependencies: groq, anthropic, python-dotenv")

@dataclass
class ModelConfig:
    name: str
    provider: str
    role: str
    temp: float

class Prompts:
    ANCHOR = "ROLE: Evidence Anchor. MODE: Clinical. Anchor claims to evidence. If no data, state 'DATA UNAVAILABLE'."
    HUNTER = "ROLE: Inconsistency Hunter. MODE: Aggressive. Hunt for contradictions and risks."
    NET = "ROLE: Pattern Synthesizer. MODE: Broad. Connect dots and context."

    BLIND_SYNTH = (
        "TASK: Complexity Assessment & Assembly.\n"
        "INPUT: Three analyst reports.\n"
        "PROTOCOL:\n"
        "1. IS THIS COMPLEX/CONTRADICTORY? -> Output 'TRIGGER_ARBITER'.\n"
        "2. IS THIS STRAIGHTFORWARD? -> COMPILE IT. Stack insights. Do not soften warnings."
    )

    BLIND_ARBITER = (
        "YOU ARE THE LAW: DREDD ARBITER. Clean Room. Enforcing absolute truth.\n"
        "TASK: Resolve Complexity or Dissent. Cross-check for hallucination traps, bias patterns, safety-washing.\n"
        "VERDICT: CONSENSUS / NEUTRAL / DISSENT + confidence (0.0-1.0). Taint detected? Lock to NEUTRAL.\n"
        "I AM THE LAW — Truth or bust. No compromise."
    )

    VALIDATOR = (
        "You are a query classifier. Is this a simple obvious fact or complex/multi-perspective?\n"
        "Output ONLY JSON: {\"type\": \"simple\" or \"complex\", \"reason\": \"brief explanation\", \"direct_answer\": \"answer if simple else null\"}"
    )

    FIX_SUGGESTION = "Previous failed: {error}. Suggest fix."

class ContextManager:
    def __init__(self):
        self.history = []
    
    def add(self, role, content):
        self.history.append({"role": role, "content": content})
    
    def get_refresh_block(self):
        if not self.history: return ""
        log = "\n".join([f"[{t['role'].upper()}]: {t['content'][:200]}..." for t in self.history[-6:]])
        return f"\n[MEMORY REFRESH]\nRECENT LOG:\n{log}\n[END MEMORY]"

class Lazarus:
    @staticmethod
    async def heal(client, dead_id: str, provider: str) -> str:
        try:
            if provider == 'groq':
                resp = await client.models.list()
                live = [m.id for m in resp.data]
                family = dead_id.split('-')[0]
                candidates = [m for m in live if family in m]
                return max(candidates, key=len) if candidates else dead_id
            return dead_id 
        except:
            return dead_id

class PersonaManager:
    def __init__(self, opsorder_path: str = "opsorder.json"):
        self.path = Path(opsorder_path)
        self.persona_rule = self._load_or_prompt()

    def _load_or_prompt(self) -> str:
        if self.path.exists():
            try:
                with self.path.open() as f:
                    data = json.load(f)
                    return data.get("persona_rule", self._default())
            except:
                pass

        name = input("Assistant name (e.g., Grace, Echo): ").strip() or "Assistant"
        personality = input("Personality (e.g., witty truth-seeker, calm verifier): ").strip() or "reliable and direct"

        rule = (
            f"You are {name}, a {personality} chat assistant. "
            "All responses must be in this singular persona. "
            "Never break character or reference internal mechanics."
        )

        # Save
        data = {"persona_rule": rule}
        with self.path.open("w") as f:
            json.dump(data, f, indent=2)

        print(f"\nPersona locked: {name} ({personality})")
        return rule

    def _default(self) -> str:
        return "You are a reliable truth assistant. Respond factually and direct."

class AppHealingManager:
    def __init__(self, opsorder_path: str = "opsorder.json"):
        self.path = Path(opsorder_path)
        self.enabled = False
        self.max_retries = 3
        self.min_conf = 0.80
        self._load_or_prompt()

    def _load_or_prompt(self):
        if self.path.exists():
            try:
                with self.path.open() as f:
                    data = json.load(f)
                    self.enabled = data.get("app_healing_enabled", False)
                    self.max_retries = data.get("app_healing_retries", 3)
                    self.min_conf = data.get("app_healing_min_conf", 0.80)
                return
            except:
                pass

        choice = input("Enable app-wide self-healing (retry + AI fix for errors)? (y/n): ").strip().lower()
        self.enabled = choice in ['y', 'yes']

        if self.enabled:
            retries = input("Max retries (default 3): ").strip()
            self.max_retries = int(retries) if retries.isdigit() else 3

            conf = input("Min confidence to accept (default 0.80): ").strip()
            self.min_conf = float(conf) if conf.replace('.', '').isdigit() else 0.80

        # Save
        data = {"app_healing_enabled": self.enabled, "app_healing_retries": self.max_retries, "app_healing_min_conf": self.min_conf}
        with self.path.open("w") as f:
            json.dump(data, f, indent=2)

class DabftEngine:
    def __init__(self):
        self.groq = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self.anth = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.ctx = ContextManager()
        self.persona = PersonaManager()
        self.healing = AppHealingManager()

        self.voters = [
            ModelConfig("llama-3.3-70b-versatile", "groq", Prompts.ANCHOR, 0.3),
            ModelConfig("gemma2-9b-it", "groq", Prompts.HUNTER, 0.3),
            ModelConfig("mixtral-8x7b-32768", "groq", Prompts.NET, 0.7)
        ]
        self.synth = ModelConfig("llama-3.3-70b-versatile", "groq", Prompts.BLIND_SYNTH, 0.1)
        self.arbiter = ModelConfig("claude-3-5-sonnet-20241022", "anthropic", Prompts.BLIND_ARBITER, 0.0)
        self.validator = ModelConfig("mixtral-8x7b-32768", "groq", Prompts.VALIDATOR, 0.2)

    async def _call(self, cfg, sys_p, user_p, retry=True, attempt=0):
        client = self.groq if cfg.provider == 'groq' else self.anth
        model_id = cfg.name

        try:
            if cfg.provider == 'groq':
                response = await client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": sys_p},
                        {"role": "user", "content": user_p}
                    ],
                    temperature=cfg.temp,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            else:
                response = await client.messages.create(
                    model=model_id,
                    system=sys_p,
                    messages=[{"role": "user", "content": user_p}],
                    max_tokens=2000,
                    temperature=cfg.temp
                )
                return response.content[0].text
        except Exception as e:
            if retry and attempt < 2:
                healed_id = await Lazarus.heal(client, model_id, cfg.provider)
                if healed_id != model_id:
                    cfg.name = healed_id
                    return await self._call(cfg, sys_p, user_p, retry, attempt + 1)
            raise e

    async def process(self, query: str):
        try:
            print(f"\nDA-BFT Processing: {query[:100]}...")

            # Run all voters
            tasks = []
            for voter in self.voters:
                tasks.append(self._call(voter, voter.role, query))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            valid_results = [r for r in results if not isinstance(r, Exception)]

            # Synthesis
            synth = await self._call(self.synth, self.synth.role, str(valid_results))

            if "TRIGGER_ARBITER" in synth:
                final = await self._call(self.arbiter, self.arbiter.role, synth)
                return {
                    "signal": "ARBITED",
                    "analysis": final,
                    "confidence": 0.8,
                    "voter_count": len(valid_results)
                }
            else:
                return {
                    "signal": "CONSENSUS",
                    "analysis": synth,
                    "confidence": 0.9,
                    "voter_count": len(valid_results)
                }
        except Exception as e:
            return {
                "signal": "ERROR",
                "error": str(e),
                "confidence": 0.0
            }
