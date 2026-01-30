This is a very practical pivot. Building a **"Cost-Aware Analysis Cockpit"** into the frontend first is much smarter than jumping straight to an automated agent loop. It gives you control and lets you "feel" the token dynamics before you automate them.

Here is the architectural blueprint for integrating this **On-Demand, Cost-Controlled Analysis** into `zdeps2`.

### 1. The Core Concept: The "Variable Resolution" Snapshot

We stop treating code context as binary (all or nothing). Instead, we treat it like streaming video resolution (360p vs 4K). You need a backend calculator that trades off **Context Width** (how many files) vs. **Analysis Depth** (how much detail per file) to fit a **Budget**.

### 2. The New Backend Module: `zdeps2/core/estimator.py`

You need a new module dedicated to "Pre-flight Checks." It doesn't call the AI; it just does the math.

**Key Responsibilities:**

1. **Input Calculation:** Reuses `snapshot.py` to get the exact token count of the raw code context.
2. **Output Estimation:** Uses heuristics to guess how much the AI will write based on your selected "Tier."
3. **Cost Projection:** Multiplies by the user's specific API pricing (e.g., Claude 3.5 Sonnet prices vs GPT-4o).

#### The Analysis Tiers (The "Resolution" Settings)

We can define three distinct levels of output fidelity:

* **Tier 1: The Index Card (Low Cost)**
* *Prompt Instruction:* "One sentence summary per file. List main classes only."
* *Output Estimate:* ~40 tokens per file.


* **Tier 2: The Wiki Page (Medium Cost)**
* *Prompt Instruction:* "One paragraph summary. Bullet points for key functions. List external dependencies."
* *Output Estimate:* ~200 tokens per file.


* **Tier 3: The Code Walkthrough (High Cost)**
* *Prompt Instruction:* "Detailed logic flow. Explain 'why' for key decisions. specific Q&A."
* *Output Estimate:* ~800+ tokens per file.



### 3. The Implementation Strategy

Here is how we modify your existing structure:

#### A. The New API Routes (`zdeps2/api/routes.py`)

We add two endpoints. One is "safe" (calculator), one is "active" (spender).

```python
# In zdeps2/api/routes.py

@api.route("/api/analyze/estimate", methods=["POST"])
def estimate_analysis_cost():
    data = request.json
    # 1. Get the raw code context using existing snapshot logic
    snapshot = generate_snapshot(data["path"], options=..., project_root=...)
    
    # 2. Get Input Tokens
    input_tokens = snapshot["metrics"]["token_estimate"]
    
    # 3. Calculate Estimated Output Tokens based on Tier
    tier = data.get("tier", "tier1") # tier1, tier2, tier3
    file_count = snapshot["metrics"]["total_files"]
    
    output_estimates = {
        "tier1": 40 * file_count,  # ~30 words per file
        "tier2": 200 * file_count, # ~150 words per file
        "tier3": 800 * file_count  # ~600 words per file
    }
    
    estimated_output = output_estimates.get(tier, 0)
    
    # 4. Calculate Financial Cost (User provides pricing in UI, passes it here, or we store defaults)
    price_input_per_m = data.get("price_input", 3.00) # e.g. $3.00
    price_output_per_m = data.get("price_output", 15.00) # e.g. $15.00
    
    cost = (input_tokens / 1_000_000 * price_input_per_m) + \
           (estimated_output / 1_000_000 * price_output_per_m)
           
    return jsonify({
        "files": file_count,
        "input_tokens": input_tokens,
        "estimated_output_tokens": estimated_output,
        "estimated_cost_usd": round(cost, 4),
        "tier": tier
    })

```

#### B. The Frontend UI (The "Cockpit")

Instead of a simple "Analyze" button, you build a **Analysis Configuration Modal**.

**UI Elements:**

1. **The "Spider Bar" (Scope Slider):**
* *Left:* "Focused" (Target file only).
* *Middle:* "Local" (Target + Immediate Parents/Children).
* *Right:* "Broad" (Full Dependency Chain).
* *Effect:* This dynamically updates `SnapshotOptions` (changing `child_depth`, `parent_depth`) and re-triggers the estimate endpoint.


2. **The "Resolution" Toggles (Output Detail):**
* `[Brief (Tier 1)]` `[Standard (Tier 2)]` `[Deep (Tier 3)]`
* *Effect:* Changes the `estimated_output_tokens` multiplier.


3. **The Budget Display:**
* A live counter: **$0.042 estimated**.
* Color-coded: Green (<$0.10), Yellow (<$0.50), Red (>$1.00).


4. **The API Key & Model Config:**
* Dropdown: "Claude 3.5 Sonnet", "GPT-4o", "DeepSeek-V3".
* Input: "Max Budget" (e.g., Stop generation if it hits $0.50).



### 4. How the "Dynamic Spider Bar" works

You mentioned: *"We can dynamically change the amount of information... based on the context."*

This is the "Smart Mode." The user sets a **Target Price** (e.g., "I want to spend max $0.05"). The backend then solves for the variables:

1. **Code:** `target_price = $0.05`
2. **Backend Logic:**
* *Try Full Scope + Tier 3?* -> Cost: $0.40. (Too high).
* *Try Full Scope + Tier 1?* -> Cost: $0.12. (Still too high).
* *Try Local Scope (Depth 1) + Tier 2?* -> Cost: $0.048. (**Match!**)


3. **Result:** The UI auto-selects the "Local Scope" and "Standard Detail" settings to fit your budget.

### Next Step

This manual "Analysis Cockpit" is the perfect stepping stone. It builds the **Semantic Layer** (the summaries) one entry point at a time, which you can save to a local JSON file (`.zdeps_cache/semantic_cache.json`).

Do you want to start by implementing the **Backend Estimation Route** (Python) or the **Frontend Modal Logic** (HTML/JS) for this calculator?