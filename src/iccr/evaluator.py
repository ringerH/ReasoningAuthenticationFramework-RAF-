import time
import re
from typing import Dict, Any, List
from src.evaluation.oracle import ICCROracle
from src.evaluation.groq_client import query_agent
from src.config import ICCR_CONFIG

def run_iccr_agent_loop(problem_data: dict, budget: int) -> Dict[str, Any]:
    """
    Executes the REAL Multi-Turn Loop with an LLM.
    """
    # 1. Initialize Environment
    oracle = ICCROracle(problem_data)
    query_trace = []
    
    # 2. Define System Prompt (The "Rules of the Game")
    system_prompt = (
        "You are an information-efficient reasoning engine solving hidden arithmetic expressions.\n"
        "You have access to an Oracle that controls information release via specific commands.\n\n"
    
        "TOOLS:\n"
        "- `ACTION: get_structure` → Reveals operator topology (e.g. '(? + ?) * ?')\n"
        "- `ACTION: get_operand:<index>` → Reveals the number at position <index>\n\n"
    
        "EFFICIENCY RULE:\n"
        f"You have a budget of {budget} queries. Your performance is scored by how few you use.\n"
        "If you can deduce the answer from partial information, do NOT query unnecessary operands.\n\n"
    
        "KEY PRINCIPLE:\n"
        "If a subexpression evaluates to a mathematically certain value regardless of its operands\n"
        "(e.g., anything × 0 = 0, or anything + 0 = itself), you do NOT need the operands inside it.\n\n"
    
        "STRATEGY:\n"
        "1. Always call `ACTION: get_structure` first\n"
        "2. Analyze the structure for shortcuts (look for × 0, + 0, etc.)\n"
        "3. If you spot a shortcut, query ONLY the operand that makes it certain (e.g., the zero)\n"
        "4. Only query other operands if mathematically necessary\n\n"
    
        "FORMAT:\n"
        "- To use a tool: `ACTION: <command>`\n"
        "- To give your final answer: `ANSWER: <number>`\n"
        "- Do NOT perform arithmetic in ACTION statements\n\n"
    
        "EXAMPLE:\n"
        "Structure: (? + ?) × ?\n"
        "Step 1: ACTION: get_structure → '(? + ?) × ?'\n"
        "Step 2: ACTION: get_operand:2 → returns 0\n"
        "Reasoning: Anything × 0 = 0, so operands 0 and 1 are irrelevant\n"
        "Step 3: ANSWER: 0\n"
        "Queries used: 2/{budget} ✓ Efficient\n\n"
    
        "Now solve the hidden problem using minimal queries."
    )
    # 3. Initialize Conversation History
    history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Solve the hidden problem. Begin."}
    ]

    model_answer = None
    is_correct = False
    
    # 4. The Loop
    print(f"   [Agent] Starting loop (Budget: {budget})...")
    
    while len(query_trace) < budget:
        # -- A. Call LLM --
        response_text = query_agent(history)
        if not response_text:
            print("   [Agent] API Error. Aborting.")
            break
            
        # Add model response to history
        history.append({"role": "assistant", "content": response_text})
        
        # -- B. Parse Intent --
        # Regex to find ACTION: ... or ANSWER: ...
        # Case insensitive, handles whitespace
        action_match = re.search(r"ACTION:\s*(.+)", response_text, re.IGNORECASE)
        answer_match = re.search(r"ANSWER:\s*([-+]?\d*\.?\d+)", response_text, re.IGNORECASE)

        # -- C. Execute Logic --
        
        if answer_match:
            # === TERMINAL STATE: ANSWER FOUND ===
            try:
                model_answer = float(answer_match.group(1))
                is_correct = abs(model_answer - float(problem_data['ground_truth'])) < 0.001
            except ValueError:
                model_answer = None
            break # Exit loop
            
        elif action_match:
            # === ACTION STATE: TOOL CALL ===
            raw_action = action_match.group(1).strip()
            
            # Rate Limiting Sleep
            time.sleep(ICCR_CONFIG["SLEEP_BETWEEN_TURNS"]) 
            
            observation = "ERROR: Invalid Command"
            
            # Dispatch Tool
            if "get_structure" in raw_action:
                observation = oracle.get_structure()
                query_trace.append("get_structure")
                
            elif "get_operand" in raw_action:
                # Extract index
                idx_match = re.search(r"get_operand:?(\d+)", raw_action)
                if idx_match:
                    idx = int(idx_match.group(1))
                    observation = oracle.get_operand(idx)
                    query_trace.append(f"get_operand:{idx}")
                else:
                    observation = "ERROR: Invalid Index Format. Use 'get_operand:<index>'"
            
            # Feed Observation back to Model
            print(f"     -> Action: {raw_action} | Obs: {observation}")
            history.append({"role": "user", "content": f"OBSERVATION: {observation}"})
            
        else:
            # === FAILURE STATE: HALLUCINATION ===
            print(f"     -> Unrecognized Output: {response_text[:50]}...")
            history.append({"role": "user", "content": "ERROR: Invalid Format. Use 'ACTION: ...' or 'ANSWER: ...'"})
            # We count hallucinations against the budget to prevent infinite loops
            query_trace.append("hallucination_error")

    # 5. Final Result
    return {
        "is_correct": is_correct,
        "query_trace": query_trace,
        "model_answer": model_answer,
        "history_length": len(history),
        "full_history": history
    }