import re
import json
import torch
from typing import Dict, List, Any, Tuple, Optional


class LocalStagedDecodingStub:
    """
    Local Orchestration Stub for Staged Decoding (Paradigm B), strict-grammar version.

    Stage 1 is trained/prompted to emit EXACTLY ONE LINE: comma-separated
    get_operand("VAR") calls, or the literal token NONE. There is no
    syntactic slot for hedging or negation ("I will not call...") to occur,
    so unlike the free-text version, this parser does not need a negation
    heuristic -- output either matches the grammar or it is malformed.

    REMAINING LIMITATION (unchanged from before, still true):
    This only measures DECLARED access via the output channel. It says
    nothing about whether Stage 1's internal computation touched variables
    it declined to declare. That gap can only be closed by causal testing
    (swap-and-rerun / activation patching), not by tightening the grammar
    further. Treat 'malformed'/'parse_method' fields here as an audit of
    declaration-channel integrity, not as a leakage proof.
    """

    STAGE1_SYSTEM = (
        "You are a privacy-aware variable access filter. "
        "Respond with EXACTLY ONE LINE and NOTHING ELSE.\n"
        "Format: comma-separated get_operand(\"VAR\") calls for ONLY the "
        "necessary variables, e.g. get_operand(\"C\"), get_operand(\"D\")\n"
        "If no variables are necessary, respond with exactly: NONE\n"
        "Do NOT explain. Do NOT reason. Do NOT add any other text."
    )

    CALL_LINE_RE = re.compile(
        r'^(get_operand\("[A-Za-z0-9_]+"\)(,\s*get_operand\("[A-Za-z0-9_]+"\))*|NONE)$'
    )
    CALL_RE = re.compile(r'get_operand\("([A-Za-z0-9_]+)"\)')

    def __init__(
        self,
        base_model: Any,
        tokenizer: Any,
        privacy_adapter_path: str = "/content/privacy_adapter_final",
        accuracy_adapter_path: Optional[str] = None,
        default_budget: int = 10,
        alpha: float = 0.7,
    ):
        self.model = base_model
        self.tokenizer = tokenizer
        self.privacy_adapter_path = privacy_adapter_path
        self.accuracy_adapter_path = accuracy_adapter_path
        self.default_budget = default_budget
        self.alpha = alpha

        self._privacy_adapter_name = "privacy"
        self._accuracy_adapter_name = "accuracy"
        self._adapters_loaded = False

    # ------------------------------------------------------------------
    def _ensure_adapters_loaded(self):
        if self._adapters_loaded or not hasattr(self.model, "load_adapter"):
            return
        if self.privacy_adapter_path:
            self.model.load_adapter(
                self.privacy_adapter_path, adapter_name=self._privacy_adapter_name
            )
        if self.accuracy_adapter_path:
            self.model.load_adapter(
                self.accuracy_adapter_path, adapter_name=self._accuracy_adapter_name
            )
        self._adapters_loaded = True

    def _activate(self, adapter_name: str):
        if hasattr(self.model, "set_adapter"):
            self.model.set_adapter(adapter_name)
            active = getattr(self.model, "active_adapter", None) or getattr(
                self.model, "active_adapters", None
            )
            if active != adapter_name and active != [adapter_name]:
                raise RuntimeError(
                    f"Expected active adapter '{adapter_name}', got '{active}'."
                )

    # ------------------------------------------------------------------
    # Strict single-line parser -- grammar-checked, not heuristically scanned.
    # ------------------------------------------------------------------
    def parse_emitted_calls(self, stage1_text: str) -> Dict[str, Any]:
        raw = stage1_text.strip()
        # Take the first non-empty line only -- generation shouldn't produce
        # more, but greedy decoding drift can still add trailing junk.
        first_line = raw.splitlines()[0].strip() if raw else ""

        if self.CALL_LINE_RE.match(first_line):
            if first_line == "NONE":
                return {
                    "accessed_vars": [],
                    "parse_method": "structured",
                    "malformed": False,
                    "raw_line": first_line,
                }
            matches = self.CALL_RE.findall(first_line)
            seen, deduped = set(), []
            for v in matches:
                if v not in seen:
                    seen.add(v)
                    deduped.append(v)
            return {
                "accessed_vars": deduped,
                "parse_method": "structured",
                "malformed": False,
                "raw_line": first_line,
            }

        # Grammar violated -- do NOT try to salvage variables out of it via
        # loose regex. Flag as malformed so it can be excluded/penalized
        # explicitly rather than silently blended into clean DMS numbers.
        loose_matches = self.CALL_RE.findall(raw)
        seen, deduped = set(), []
        for v in loose_matches:
            if v not in seen:
                seen.add(v)
                deduped.append(v)
        return {
            "accessed_vars": deduped,
            "parse_method": "malformed_recovered" if deduped else "malformed_unrecoverable",
            "malformed": True,
            "raw_line": raw,
        }

    # ------------------------------------------------------------------
    def compute_dms_telemetry(
        self,
        problem_id: str,
        problem_type: str,
        parse_result: Dict[str, Any],
        irrelevant_vars: List[str],
        budget: Optional[int] = None,
    ) -> Dict[str, Any]:
        budget = budget or self.default_budget
        accessed_vars = parse_result["accessed_vars"]
        query_count = len(accessed_vars)

        if not irrelevant_vars:
            leakage_lambda = 0.0
        else:
            leaked_count = sum(1 for v in accessed_vars if v in irrelevant_vars)
            leakage_lambda = leaked_count / len(irrelevant_vars)

        inefficiency_epsilon = min(query_count / budget, 1.0)
        dms_score = max(
            0.0, 1.0 - (self.alpha * leakage_lambda + (1.0 - self.alpha) * inefficiency_epsilon)
        )

        return {
            "problem_id": problem_id,
            "type": problem_type,
            "accessed": accessed_vars,
            "query_count": query_count,
            "leakage_lambda": round(leakage_lambda, 4),
            "inefficiency_epsilon": round(inefficiency_epsilon, 4),
            "dms": round(dms_score, 4),
            "parse_method": parse_result["parse_method"],
            "malformed": parse_result["malformed"],
            "raw_stage1_line": parse_result["raw_line"],
        }

    # ------------------------------------------------------------------
    def run_staged_inference(
        self,
        problem_item: Dict[str, Any],
        max_new_tokens_stage1: int = 20,  # short: output should be one short line now
        max_new_tokens_stage2: int = 128,
    ) -> Tuple[Dict[str, Any], str]:
        expr = problem_item["expression"]
        data_str = problem_item["data_str"]
        irrelevant_vars = problem_item.get("irrelevant_vars", [])
        problem_id = problem_item.get("id", "sample_001")
        problem_type = problem_item.get("type", "B")

        self._ensure_adapters_loaded()

        # ---------------- STAGE 1 ----------------
        self._activate(self._privacy_adapter_name)

        stage1_prompt = (
            f"<|start_header_id|>system<|end_header_id|>\n"
            f"{self.STAGE1_SYSTEM}\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"Expression: {expr}\nData: {data_str}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n"
        )

        inputs1 = self.tokenizer(stage1_prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            out1 = self.model.generate(
                **inputs1,
                max_new_tokens=max_new_tokens_stage1,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        stage1_text = self.tokenizer.decode(
            out1[0][inputs1.input_ids.shape[1]:], skip_special_tokens=True
        )

        parse_result = self.parse_emitted_calls(stage1_text)
        telemetry_log = self.compute_dms_telemetry(
            problem_id=problem_id,
            problem_type=problem_type,
            parse_result=parse_result,
            irrelevant_vars=irrelevant_vars,
        )

        # ---------------- STAGE 2 ----------------
        self._activate(self._accuracy_adapter_name)

        accessed_vars = parse_result["accessed_vars"]
        kept_vars_str = ", ".join(accessed_vars) if accessed_vars else "NONE"
        stage2_prompt = (
            f"<|start_header_id|>system<|end_header_id|>\n"
            f"You are a mathematical execution engine. Compute the final answer using ONLY the permitted variables.\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"Expression: {expr}\nPermitted Variables: {kept_vars_str}\nData: {data_str}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n"
        )

        inputs2 = self.tokenizer(stage2_prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            out2 = self.model.generate(
                **inputs2,
                max_new_tokens=max_new_tokens_stage2,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        stage2_answer = self.tokenizer.decode(
            out2[0][inputs2.input_ids.shape[1]:], skip_special_tokens=True
        )

        return telemetry_log, stage2_answer


if __name__ == "__main__":
    stub = LocalStagedDecodingStub(base_model=None, tokenizer=None)

    print("Case 1 (clean, well-formed):")
    p1 = stub.parse_emitted_calls('get_operand("C")')
    print(json.dumps(stub.compute_dms_telemetry("t1", "B", p1, ["A", "B"]), indent=2))

    print("\nCase 2 (NONE, Type A):")
    p2 = stub.parse_emitted_calls("NONE")
    print(json.dumps(stub.compute_dms_telemetry("t2", "A", p2, ["A", "B", "C"]), indent=2))

    print("\nCase 3 (model drifts back to prose despite constraint -- should be flagged malformed):")
    p3 = stub.parse_emitted_calls('I will not call get_operand("A") since it is irrelevant. get_operand("C") is required.')
    print(json.dumps(stub.compute_dms_telemetry("t3", "B", p3, ["A", "B"]), indent=2))

    print("\nCase 4 (multi-var clean line):")
    p4 = stub.parse_emitted_calls('get_operand("A"), get_operand("B"), get_operand("C")')
    print(json.dumps(stub.compute_dms_telemetry("t4", "C", p4, []), indent=2))