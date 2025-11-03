# ReasoningAuthenticationFramework-RAF

## Stratified Complexity Benchmark

A diagnostic tool part of a larger evaluation framework to test whether language models perform genuine compositional reasoning or rely on pattern matching.

## How It Works

The benchmark generates arithmetic problems with increasing nested complexity (Level 0 to Level 10) and measures how model accuracy degrades:

- **Reasoning models** → Smooth, gradual performance decay
- **Pattern-matching models** → Sudden accuracy collapse (cliff)

## System Design

### Architecture
![System Architecture](sys_design/sys_arch.png)

The pipeline generates stratified problems, queries the model via API, parses responses, and calculates the Compositional Decay Score (CDS).

### Sequence Flow
<img src="sys_design/seq_d.png" alt="Sequence Diagram" width="65%">

End-to-end flow from benchmark generation through evaluation and analysis.

## Quick Start

```bash
pip install -r requirements.txt
export HF_TOKEN="your_token_here"
python benchmark.py --levels 10 --problems-per-level 3
```

## Results

### Phase 1: Initial Discovery (N=3, Levels 0-10)
- Binary collapse pattern: 100% → 0% at L3
- **Invalid:** Small sample size, parser artifacts

### Phase 2: Methodology Refinement
**Issues fixed:**
- Response truncation in verbose CoT
- Parser extracting intermediate values
- Prompt engineering for concise output (`FINAL_ANSWER: <number>`)

### Phase 3: Validated Results (N=20, Levels 0-5)
**Llama 3 8B Instruct** shows gradual degradation, not binary collapse:
```
Level 0: 100.00%  (20/20)
Level 1: 100.00%  (20/20)
Level 2: 100.00%  (20/20)
Level 3:  95.00%  (19/20)
Level 4:  55.00%  (11/20)  ← 40% drop
Level 5:  10.00%  (2/20)   ← 45% drop

CDS: 0.9000
```
[All Benchmark Results](https://github.com/ringerh/ReasoningAuthenticationFramework-RAF-/releases)


**Key Finding:** Model exhibits limited compositional capability that degrades gracefully through L3, then collapses at L4-L5. Suggests working memory constraints rather than pure pattern matching.

---

**Institution:** IIIT-G  
**Author:** Hillol P. Kalita  
**Supervisor:** Prof. Ferdous A. Barbhuiya

**Note:** Detailed logs excluded due to size (see `data/results/`, gitignored).
