# WATS Domain Knowledge for AI Agents

This document contains essential domain knowledge for AI agents working with WATS. Understanding these concepts is crucial for correctly interpreting and answering questions about manufacturing test data.

---

## Core Concepts

### Units, Reports, and Runs

| Term | Definition |
|------|------------|
| **Unit** | A single device/product being tested, identified by serial number |
| **Report** | The test result document from a single test execution |
| **Run** | A test execution sequence number (Run 1, Run 2, etc.) |
| **Retest** | Any run after Run 1 |

**Key relationship**: One unit can have multiple reports (one per run).

### Process / Test Operation

A **process** (also called **test_operation**) is a type of test a product goes through:

- ICT (In-Circuit Test)
- FCT (Functional Test)
- EOL (End-of-Line Test)
- FQC (Final Quality Check)
- etc.

**Critical**: A product typically goes through MULTIPLE processes. Each process has its own yield metrics.

### Operation Types (Terminology!)

WATS uses different operation types depending on the workflow:

| Term | Domain | Records | Used For |
|------|--------|---------|----------|
| `test_operation` | Report | UUT / UUTReport | Testing (yields, failures) |
| `repair_operation` | Report | UUR / UURReport | Repair logging (repair actions) |
| `wip_operation` | Production | WIP records | Production tracking only |

**Important**: When users ask about "process" or "operation" for yield analysis, they almost always mean `test_operation`.

Only use `repair_operation` when specifically analyzing repair workflow (not yield).

---

## Process Name Matching

### The Problem

Users often use imprecise process names:
- "PCBA" instead of "PCBA test"
- "board test" instead of "PCBA Test Station"
- "fct" instead of "FCT Functional Test"

### How to Handle

1. **Fuzzy matching**: The agent tool attempts to match user input to actual process names
2. **Common aliases**: Standard manufacturing abbreviations are recognized
3. **Suggestions**: If no match found, suggest closest alternatives
4. **List processes**: Use `perspective="by operation"` to see available processes

### Common Aliases

| User Input | May Match |
|------------|-----------|
| "pcba", "board test" | PCBA test, PCBA Test, Board Test |
| "ict", "in-circuit" | ICT, ICT Test, In-Circuit Test |
| "fct", "functional" | FCT, FCT Test, Functional Test |
| "aoi", "optical" | AOI, AOI Test, Automated Optical Inspection |
| "eol", "end of line" | EOL, EOL Test, End of Line Test |
| "fqc", "final" | FQC, Final Quality Check |

### Best Practice

When in doubt, query available processes first:

```python
# See all processes for a product
yield_tool.analyze(YieldFilter(
    part_number="WIDGET-001",
    perspective="by operation"
))
```

---

## The Mixed Process Problem (Critical!)

### The Scenario

Some customers send **different test types to the same process**:

```
Process "Structural Tests" receives:
  - AOI tests (sw_filename: "aoi.exe")
  - ICT tests (sw_filename: "ict.exe")
```

### Why This Causes Problems

1. Unit's first run (AOI) determines that unit as "tested"
2. Unit's second run (ICT) is seen as a "retest after pass"
3. ICT yields show **0 units** because AOI already "passed" those units!

### Symptoms

| Symptom | Explanation |
|---------|-------------|
| "ICT shows 0 units" | AOI ran first, ICT is treated as retest |
| "FPY doesn't make sense" | Mixed test types corrupt yield calculation |
| "Unit counts mismatch" | Different sw_filename = different "tests" |

### Diagnosis

Look for **different `sw_filename` values** in the same process:

- If multiple sw_filename exist for one process → Mixed process problem
- Each sw_filename represents a different test type

### Agent Response

When user reports 0 units for a process that should have data:

1. **Check for mixed process**: Query reports, look for different sw_filename
2. **Explain the issue**: "This process receives multiple test types (AOI, ICT). The first test type determines units."
3. **Recommend solution**: "Each test type should have its own process for accurate yield tracking."

---

## Adaptive Time Filtering

### The Problem with 30-Day Default

For **high-volume production**, 30 days can be too much:

| Volume | Daily Units | 30 Days | Risk |
|--------|-------------|---------|------|
| Very High | >100,000 | >3 million | API timeout |
| High | 10K-100K | 300K-3M | Slow, memory issues |
| Medium | 1K-10K | 30K-300K | OK |
| Low | <1K | <30K | May need more days |

### Adaptive Time Filter

The tool can **automatically adjust** the date range based on volume:

```python
yield_tool.analyze(YieldFilter(
    part_number="HIGH-VOLUME-PRODUCT",
    adaptive_time=True  # Auto-adjust window
))
```

### How It Works

1. Start with small window (1 day)
2. Evaluate volume
3. Expand if insufficient data
4. Stop when target reached

### When to Use

- ✅ High-volume environments
- ✅ Unknown production volume
- ✅ General queries
- ❌ Specific date range needed

---

## Yield Metrics (Critical Knowledge!)

### The Process Context Rule

**Every yield question must be considered in the context of a specific process.**

❌ **Ambiguous**: "What's the yield for WIDGET-001?"
✅ **Clear**: "What's the FCT yield for WIDGET-001?"
✅ **Clear**: "What's the RTY for WIDGET-001?" (overall across all processes)

### Unit-Based Yield (FPY, SPY, TPY, LPY)

| Metric | Name | Definition |
|--------|------|------------|
| FPY | First Pass Yield | % of units passed on Run 1 |
| SPY | Second Pass Yield | % of units passed by Run 2 |
| TPY | Third Pass Yield | % of units passed by Run 3 |
| LPY | Last Pass Yield | % of units eventually passed |

**Relationship**: FPY ≤ SPY ≤ TPY ≤ LPY

### Report-Based Yield (TRY)

| Metric | Name | Definition |
|--------|------|------------|
| TRY | Test Report Yield | Passed reports ÷ All reports |

**Use TRY for**: Station performance, fixture comparison, operator evaluation, repair line analysis.

### Rolled Throughput Yield (RTY)

**RTY = FPY₁ × FPY₂ × ... × FPYₙ**

RTY represents the probability that a unit passes ALL processes on the first try.

**Example**:
```
ICT FPY = 98%
FCT FPY = 95%
EOL FPY = 99%

RTY = 0.98 × 0.95 × 0.99 = 92.2%
```

**Use RTY for**: Overall product quality assessment, comparing products across entire flow.

### The Unit Inclusion Rule

**A unit is included in yield calculations ONLY if its FIRST RUN matches the filter.**

If included, ALL runs for that unit are counted (even runs outside the filter).

**Implications**:
- Filtering by retest-only stations shows 0 units
- Date filters apply to Run 1, not all runs
- Solution for retest stations: Use TRY instead of FPY

### The Repair Line Problem

Repair/retest stations never see Run 1 (they only handle failed units from main line).

**Result**: Unit-based yield shows 0 units for repair stations.
**Solution**: Use TRY (report-based yield) to evaluate repair station performance.

---

## Yield Over Time (Temporal Analysis)

### Date Range Defaults

WATS always assumes you want the **most recent data**:

- If `date_from` and `date_to` are not specified, WATS defaults to **last 30 days**
- This is the server-side default behavior
- Use `days` parameter for simple "last N days" queries

### Time-Based Perspectives

| Perspective | Date Grouping | Use Case |
|-------------|---------------|----------|
| `trend` | DAY | General yield trend |
| `daily` | DAY | Day-by-day breakdown |
| `weekly` | WEEK | Week-by-week analysis |
| `monthly` | MONTH | Month-by-month trends |

### Yield Trend Metrics

Yield trend describes **change compared to the previous equally-sized period**:

| Analysis Period | Compared To |
|-----------------|-------------|
| Today | Yesterday |
| This week | Last week |
| This month | Last month |

**Use Case**: Detecting improvement or degradation patterns in production quality.

### Safe Period Aggregation (Important!)

**Key Rule**: When fetching yield over periods, the **first-pass-included rule** applies.

This means:
- Units are counted only in their first-run period
- **Periods can be safely summed** without double-counting
- Example: Sum Monday-Friday yields for weekly total

### Date Grouping Options

For advanced use, specify `date_grouping` directly:

| Value | Groups By |
|-------|-----------|
| HOUR | Hour |
| DAY | Day |
| WEEK | Week |
| MONTH | Month |
| QUARTER | Quarter |
| YEAR | Year |

---

## Top Runners

### Definition

**Top runners** = Products with the highest test volume (unit count or report count).

### The Per-Process Rule

**Volume must be considered PER PROCESS.**

A product might be a top runner in FCT but not in EOL:

| Product | FCT Volume | EOL Volume |
|---------|------------|------------|
| WIDGET-A | 10,000 ⭐ | 5,000 |
| WIDGET-B | 8,000 | 12,000 ⭐ |

### Finding Top Runners

```python
# Top runners for FCT process
yield_tool.analyze(YieldFilter(
    test_operation="FCT",
    perspective="by product",
    days=30
))
# Results sorted by unit_count shows top runners
```

---

## Handling Ambiguous Questions

### Question: "What's the yield for WIDGET-001?"

**Best response approach**:

1. **Check if single process**: Query with `part_number="WIDGET-001"` and `perspective="by operation"`
   - If only ONE process: Answer with that process's yield
   - If MULTIPLE processes: Ask user to clarify

2. **Clarify with user**:
   - "WIDGET-001 goes through 3 processes (ICT, FCT, EOL). Which process yield would you like?"
   - "Or would you like the RTY (Rolled Throughput Yield) across all processes?"

3. **Default suggestion**: If user doesn't specify, show yield by operation so they can see all processes.

### Question: "Show me the top runners"

**Best response approach**:

1. Ask for process context: "Top runners for which process? (e.g., FCT, EOL)"
2. Or show overall volume by product across all processes as starting point
3. Then drill down to specific process if needed

---

## Unit Verification Rules

### What They Are

Rules that define which processes must pass for each product before it can ship.

### Example Rule

```
Product: WIDGET-001
Required tests: ICT → FCT → EOL
```

### Common Issue

Many customers don't maintain verification rules, even though the API supports them.

### Agent Opportunity

Analyze yield data to SUGGEST verification rules:

1. Query: `part_number="WIDGET-001", perspective="by operation", days=90`
2. Identify all processes with significant volume
3. Suggest: "Based on test data, WIDGET-001 should require: ICT → FCT → EOL"
4. Offer to create the rule (if agent has edit permissions)

---

## Quick Reference: When to Use Each Metric

| Question Type | Recommended Metric |
|--------------|-------------------|
| Product quality (single process) | FPY, LPY |
| Product quality (overall) | RTY |
| Station performance | TRY |
| Fixture comparison | TRY |
| Operator performance | TRY |
| Repair line efficiency | TRY |
| Trend analysis | FPY or TRY (per context) |
| Top runners | Unit count by product (per process) |

---

## Checklist for Yield Questions

1. ☐ Is the process/test_operation specified?
2. ☐ Is unit-based (FPY) or report-based (TRY) yield appropriate?
3. ☐ Are we dealing with a retest-only station? (Use TRY)
4. ☐ Is volume context needed? (Top runners = high volume)
5. ☐ Should RTY be calculated? (Overall quality across processes)

---

## API Tips

### Discover Processes for a Product

```python
yield_tool.analyze(YieldFilter(
    part_number="WIDGET-001",
    perspective="by operation",
    days=30
))
```

### Find Top Runners for a Process

```python
yield_tool.analyze(YieldFilter(
    test_operation="FCT",
    perspective="by product",
    days=30
))
# Sort results by unit_count descending
```

### Get RTY Components

Query each process individually and multiply FPYs:

```python
# Get all process yields
result = yield_tool.analyze(YieldFilter(
    part_number="WIDGET-001",
    perspective="by operation",
    days=30
))

# RTY = product of all FPY values
rty = 1.0
for process in result.data:
    rty *= (process.first_pass_yield / 100)
rty *= 100  # Convert back to percentage
```

---

## Dimensional Analysis (Failure Mode Detection)

### The Bridge to Root Cause

Between top-level yield analysis and detailed root cause investigation lies **dimensional analysis** - systematically comparing yields across different configurations to detect failure modes.

### What is Dimensional Analysis?

Query yield data with additional dimensions (grouping factors), then compare yields to identify which configurations correlate with low yield.

**Key Insight**: If yield varies significantly across a dimension, that dimension is likely related to the failure mode.

### Available Dimensions

| Dimension | What It Reveals |
|-----------|-----------------|
| `stationName` | Equipment issues (calibration, wear) |
| `operator` | Training/technique differences |
| `fixtureId` | Fixture wear or contamination |
| `batchNumber` | Component lot issues (supplier, incoming) |
| `location` | Environment/line differences |
| `swFilename` | Test program differences |
| `swVersion` | Test version differences |
| `period` | Drift over time |

### Common Failure Mode Patterns

| Pattern | Typical Cause | Investigation |
|---------|---------------|---------------|
| Station-specific | Equipment problem | Calibration, maintenance, environment |
| Batch-specific | Component defect | Incoming inspection, supplier quality |
| Operator-specific | Training gap | Standardize procedures, retrain |
| Fixture-specific | Fixture wear | Maintenance, contact cleaning |
| Time-based trend | Drift | Preventive maintenance, SPC |
| Software-specific | Test change | Version comparison, rollback |

### Analysis Workflow

```
1. DETECT: "FCT yield dropped from 95% to 88%"
   → Use yield_tool with perspective="trend"

2. DIAGNOSE: "What's causing it?"
   → Use dimensional_analysis_tool
   → Compare yield across stations, batches, operators, etc.

3. ISOLATE: "Station-3 has 75% FPY, others have 94%"
   → Found the failure mode!

4. ROOT CAUSE: "Why is Station-3 failing?"
   → Use test_step_analysis to find failing steps
   → Use measurement_tool to check Cpk
```

### Example: Finding a Failure Mode

```python
# Step 1: Notice yield problem
yield_result = yield_tool.analyze(YieldFilter(
    part_number="WIDGET-001",
    test_operation="FCT",
    days=30
))
# Result: FPY=88% (below target of 95%)

# Step 2: Dimensional analysis
failure_modes = dimensional_analysis_tool.analyze(FailureModeFilter(
    part_number="WIDGET-001",
    test_operation="FCT",
    days=30
))
# Result:
#   Station-3: FPY=75% (-13% vs baseline) CRITICAL
#   Batch-042: FPY=82% (-6% vs baseline) HIGH
#   All other dimensions: within normal range

# Step 3: Investigate Station-3 specifically
station_3_steps = test_step_analysis_tool.analyze(
    part_number="WIDGET-001",
    test_operation="FCT",
    station_name="Station-3"
)
# Result: "Voltage Test" step has 25% failure rate
```

### Statistical Significance

Not all yield variations are meaningful. The tool considers:

| Factor | Weight |
|--------|--------|
| **Magnitude** | How much below baseline? |
| **Sample size** | More units = higher confidence |
| **Consistency** | Does it repeat over time? |

**Significance Levels:**
- 🔴 CRITICAL: >10% below baseline, high confidence
- 🟠 HIGH: 5-10% below baseline
- 🟡 MODERATE: 2-5% below baseline
- ⚪ LOW: <2% below baseline

### Misc Info as Dimensions

WATS supports custom properties via **misc_info**. Common examples:

| Misc Info | Use Case |
|-----------|----------|
| Component lot | Track specific component batches |
| Firmware version | Software-under-test version |
| Configuration | Product variants |
| Supplier | Supplier traceability |
| Chamber ID | Environmental chamber tracking |

If a failure mode correlates with misc_info values, it often points directly to the root cause (e.g., a specific component lot).

---

## Test Step Analysis (TSA)

### What is TSA?

Test Step Analysis (TSA) provides step-by-step visibility into the test sequence. It shows statistics for each test step, enabling root cause identification and process capability assessment.

### Position in Analysis Workflow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│ Yield       │ --> │ Dimensional  │ --> │ TSA /       │ --> │ Measurement │
│ Analysis    │     │ Analysis     │     │ Step        │     │ Deep Dive   │
│             │     │ (optional)   │     │ Analysis    │     │             │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
     |                    |                    |                    |
"What's failing?"   "Where/when?"      "Which step?"        "Why exactly?"
```

### Key TSA Concepts

#### Single Product/Process Analysis

**TSA is designed for ONE product in ONE process at a time.**

- Different products have different test sequences
- Different processes test different things
- Mixing sequences leads to confusing merged results

#### Data Integrity Check

Before analyzing, TSA checks for potential issues:

| Check | Warning |
|-------|---------|
| Multiple SW versions | Different test programs may have different sequences |
| Multiple revisions | Different product revisions may have different tests |

**Recommendation**: Filter to specific `sw_filename` or `revision` for clean analysis.

#### Sequence Merging Behavior

When data includes multiple test sequences:

1. **Identical step paths** are merged (statistics combined)
2. **Different step paths** are kept separate  
3. **Sample counts may vary** per step (not necessarily a problem)

This allows comparing related tests but can be confusing if unintended.

### TSA Statistics Explained

#### Step Failure Statistics

| Field | Meaning | Priority |
|-------|---------|----------|
| `step_failed_count` | Step reported failure | Medium |
| `step_error_count` | Step had an error | Medium |
| `step_terminated_count` | Test terminated at this step | Medium |
| `step_caused_uut_failed` | **Step CAUSED unit to fail** | 🔴 HIGH |
| `step_caused_uut_error` | Step caused unit error | HIGH |

**Critical distinction**: A step can FAIL (report failure) without being the CAUSE of unit failure. The `step_caused_uut_*` fields identify root cause steps.

#### Process Capability (Cp/Cpk)

For measurements, TSA provides process capability indices:

| Metric | Definition | Interpretation |
|--------|------------|----------------|
| **Cpk** | Process capability index | Actual capability (considers centering) |
| **Cp** | Process capability potential | Potential if perfectly centered |
| **Cp_lower** | Capability vs low limit | Lower spec margin |
| **Cp_upper** | Capability vs high limit | Upper spec margin |

#### Cpk Thresholds

| Cpk Value | Status | Action Required |
|-----------|--------|-----------------|
| ≥ 1.33 | ✅ CAPABLE | Process is good, monitor |
| 1.0-1.33 | ⚠️ MARGINAL | Improvement needed, prioritize |
| 0.67-1.0 | ❌ INCAPABLE | Action required, risk of failures |
| < 0.67 | 🚨 CRITICAL | URGENT - high defect rate expected |

**Industry Standard**: Cpk ≥ 1.33 ensures 3-sigma coverage on both sides.

#### Other Statistics

| Field | Description |
|-------|-------------|
| `avg`, `min`, `max` | Measurement statistics |
| `stdev` | Standard deviation (process variation) |
| `sigma_high_3`, `sigma_low_3` | ±3σ limits for control charts |
| `step_time_avg`, `step_time_min`, `step_time_max` | Timing statistics |

### Analysis Priority

When reviewing TSA results, investigate in this order:

#### 1. 🔴 CRITICAL: Steps Causing Unit Failures

Steps where `step_caused_uut_failed > 0` are root causes:

```python
# These steps CAUSED units to fail - investigate first!
critical_steps = [s for s in steps if s.step_caused_uut_failed > 0]
critical_steps.sort(key=lambda x: x.step_caused_uut_failed, reverse=True)
```

#### 2. ⚠️ Cpk Concerns

Measurements with Cpk below threshold indicate capability issues:

```python
# Measurements with poor capability
cpk_concerns = [s for s in steps if s.cpk and s.cpk < 1.33]
cpk_concerns.sort(key=lambda x: x.cpk)  # Worst first
```

#### 3. High Failure Rate Steps

Steps with high failure rates (may not be root cause):

```python
# High failure rate but check if they cause unit failures
high_fail = [s for s in steps if s.pass_rate < 95 and s.step_count >= 10]
```

### Common TSA Workflows

#### Finding Root Cause of Failures

```python
# Step 1: Get step analysis
result = step_analysis_tool.analyze(StepAnalysisInput(
    part_number="PCBA-001",
    test_operation="FCT",
    days=30
))

# Step 2: Check critical steps (caused unit failures)
for step in result.critical_steps:
    print(f"{step.step_name}: {step.caused_unit_fail} unit failures")
    
# Step 3: If measurement, check capability
if step.cpk:
    print(f"  Cpk: {step.cpk:.2f} ({step.cpk_status})")
```

#### Process Capability Assessment

```python
# Get overall capability picture
summary = result.overall_summary

print(f"Total measurements: {summary.total_measurements}")
print(f"Average Cpk: {summary.avg_cpk:.2f}")
print(f"  Capable (≥1.33): {summary.capable_count}")
print(f"  Marginal (1.0-1.33): {summary.marginal_count}")
print(f"  Incapable (<1.0): {summary.incapable_count}")
```

#### Investigating Specific Step

After identifying a problem step:

```python
# Deep dive on measurement
measurement_result = measurement_tool.analyze(MeasurementFilter(
    part_number="PCBA-001",
    test_operation="FCT",
    measurement_path="Main/Voltage Test/Output",
    days=30
))
# Get distribution, histogram, outliers...
```

### TSA vs Dimensional Analysis

| TSA | Dimensional Analysis |
|-----|---------------------|
| **WHICH step** is failing | **WHERE/WHEN** failures happen |
| Step-level statistics | Configuration comparisons |
| Process capability | Failure mode detection |
| Single product/process | Yield across dimensions |

**Use Together**: Dimensional analysis finds the failure mode (e.g., "Station-3"), then TSA finds the specific step causing issues on that station.

### Best Practices

1. **Always filter to single product + process** for meaningful results
2. **Check data integrity** - alert on multiple SW versions/revisions
3. **Focus on `step_caused_uut_failed`** - these are the true root causes
4. **Use Cpk thresholds** - prioritize measurements below 1.33
5. **Sequence merging is OK** if understood - different step counts may be expected

---

## Process Capability Analysis (Advanced)

Process Capability Analysis builds on TSA to provide deeper statistical assessment. Use this when TSA identifies measurements with Cpk concerns and you need to understand:

1. **Is the process stable?** (If not, Cpk is meaningless)
2. **How are failures affecting capability?**
3. **Are there hidden modes in the data?**

### Position in Analysis Workflow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Yield       │ --> │ Dimensional  │ --> │ Step        │ --> │ Process      │ --> │ Measurement │
│ Analysis    │     │ Analysis     │     │ Analysis    │     │ Capability   │     │ Deep Dive   │
│             │     │ (optional)   │     │ (TSA)       │     │ Analysis     │     │             │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘     └─────────────┘
     |                    |                    |                    |                    |
"What's failing?"   "Where/when?"      "Which step?"     "Is it stable?"      "Why exactly?"
                                                          "Cpk vs Cpk_wof?"
```

### Dual Cpk Analysis (Critical!)

WATS provides TWO Cpk datasets for each measurement:

| Dataset | Name | Description |
|---------|------|-------------|
| **Cpk** | All Data | Includes ALL measurements including failures |
| **Cpk_wof** | Without Failures | Excludes failed measurements - shows "good" data |

#### Why Two Datasets?

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Cpk (All Data)         │ Shows ACTUAL process performance                │
│ Cpk_wof (Without Fail) │ Shows POTENTIAL if failures addressed           │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Interpreting the Difference

| Scenario | Interpretation | Action |
|----------|---------------|--------|
| Cpk ≈ Cpk_wof | Process is stable, failures not distorting capability | Focus on reducing variation |
| Cpk << Cpk_wof | Failures significantly impact capability | **Address failure root cause FIRST** |
| Cpk >> Cpk_wof | Unusual - failures catching bad units correctly | Verify limits are correct |

**Example**:
- Cpk = 0.9, Cpk_wof = 1.5
- Ratio = 1.67 (significant!)
- **Conclusion**: Failures are severely impacting capability. Fix the failure mode first, and capability should improve to ~1.5.

#### Other Capability Metrics (_wof variants)

All these statistics have "without failure" variants:

| Metric | With Failures | Without Failures |
|--------|---------------|------------------|
| Cpk | `cpk` | `cpk_wof` |
| Cp | `cp` | `cp_wof` |
| Average | `avg` | `avg_wof` |
| Std Dev | `stdev` | `stdev_wof` |
| Min/Max | `min`, `max` | `min_wof`, `max_wof` |
| σ Limits | `sigma_high_3`, `sigma_low_3` | `sigma_high_3_wof`, `sigma_low_3_wof` |

### Stability Assessment (MUST CHECK FIRST!)

**Before trusting ANY Cpk number, verify process stability.**

An unstable process makes Cpk meaningless - the number will change over time.

#### What Makes a Process Stable?

A stable process has:
- ✅ Consistent mean (no drift)
- ✅ Consistent variation (σ stays constant)
- ✅ No unusual patterns (trends, cycles, shifts)
- ✅ Random variation only (normal distribution)

#### Stability Red Flags

| Issue | Description | Detection |
|-------|-------------|-----------|
| **Trend** | Mean drifting up or down over time | Compare early vs late data |
| **Shift** | Sudden mean change | Large mean difference between periods |
| **Outliers** | Data points beyond 3σ | Values outside control limits |
| **High Variance** | 6σ spread > spec range | Process spread exceeds tolerance |
| **Bimodal** | Two populations mixed | σ_wof much smaller than σ |

#### Stability Decision Flow

```
                    ┌─────────────────┐
                    │ Check Stability │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
         ┌────▼────┐                  ┌─────▼─────┐
         │ STABLE  │                  │ UNSTABLE  │
         └────┬────┘                  └─────┬─────┘
              │                             │
              │                             │
    ┌─────────▼─────────┐        ┌──────────▼──────────┐
    │ Cpk is meaningful │        │ FIX STABILITY FIRST │
    │ Focus on          │        │ Cpk is unreliable   │
    │ improvement       │        │ Find special causes │
    └───────────────────┘        └─────────────────────┘
```

### Hidden Mode Detection

Beyond basic capability, look for these hidden issues:

#### 1. Centering Issues (Cp >> Cpk)

If Cp is much higher than Cpk, the process could be capable but is off-center:

```
┌─────────────────────────────────────────────┐
│ Example:                                    │
│   Cp = 1.8 (good potential)                 │
│   Cpk = 0.9 (poor actual)                   │
│   Ratio = 2.0                               │
│                                             │
│ → Process is off-center from spec midpoint  │
│ → Centering adjustment could double Cpk!    │
└─────────────────────────────────────────────┘
```

#### 2. Approaching Specification Limits

Check sigma margin to specification limits:

| Sigma Margin | Risk Level | Action |
|--------------|------------|--------|
| > 3σ | Low | Process is well-centered |
| 2-3σ | Medium | Monitor closely |
| < 2σ | High | Failures likely, adjust process |

#### 3. Bimodal Distribution

Signs of two populations mixed:
- σ_wof is much smaller than σ
- Mean_wof differs significantly from Mean
- Distribution may have two peaks

**Root Cause**: Often a machine, operator, or component lot causing different behavior.

#### 4. High Variance Relative to Specification

Check if process spread fits within specification:

```
Process Spread = 6σ
Spec Range = Upper Limit - Lower Limit

If 6σ > Spec Range → Process inherently incapable
```

### Improvement Priority Matrix

Use this to prioritize improvement efforts:

| Priority | Criteria | Action |
|----------|----------|--------|
| 🔴 **CRITICAL** | Cpk < 0.67 OR Process unstable | Immediate action |
| 🟠 **HIGH** | Cpk < 1.0 OR Approaching limits | Address soon |
| 🟡 **MEDIUM** | 1.0 ≤ Cpk < 1.33 OR Centering issue | Plan improvement |
| 🟢 **LOW** | Cpk ≥ 1.33 AND Stable | Monitor only |

### Dimensional Considerations

**Important**: For dimensional analysis within process capability:

- TSA returns aggregate statistics across ALL data
- To analyze by dimension (station, operator, SW version), you must:
  1. Filter the data to the specific dimension value
  2. Re-run the analysis
  3. Compare results across dimensions

**Example workflow**:
```python
# Compare capability across stations
for station in ["Station-1", "Station-2", "Station-3"]:
    result = capability_tool.analyze(ProcessCapabilityInput(
        part_number="PCBA-001",
        test_operation="FCT",
        station_name=station  # Filter to specific station
    ))
    print(f"{station}: Cpk={result.avg_cpk_all:.2f}, "
          f"Stable={result.stable_count}/{result.measurements_analyzed}")
```

### Process Capability vs TSA

| Feature | TSA | Process Capability |
|---------|-----|-------------------|
| Scope | All steps overview | Detailed per measurement |
| Cpk Analysis | Basic (single value) | Dual (with/without failures) |
| Stability | Not checked | Full stability assessment |
| Hidden Modes | Not detected | Detects trends, outliers, etc. |
| When to Use | First pass analysis | Deep dive on concerns |

### Best Practices

1. **Check stability BEFORE trusting Cpk** - unstable processes have meaningless Cpk
2. **Compare Cpk vs Cpk_wof** - significant difference means address failures first
3. **Look for centering issues** - Cp >> Cpk means easy improvement available
4. **Check sigma margins** - less than 2σ to limits is high risk
5. **For dimensions, make separate calls** - aggregate data hides variation
6. **Prioritize by improvement priority** - critical first, then high, etc.

---

## Summary

The most important things to remember:

1. **Yield is per process** - Always clarify which test operation
2. **RTY for overall quality** - Multiply FPYs across all processes
3. **TRY for equipment/operator** - Especially for retest stations
4. **Top runners are per process** - Volume varies by test operation
5. **Unit Inclusion Rule** - First run determines inclusion
6. **Dimensional analysis for failure modes** - Compare yields across configurations
7. **TSA for root cause** - Find which STEP is causing failures
8. **Process Capability for deep dive** - Stability, dual Cpk, hidden modes
9. **Cpk vs Cpk_wof** - Compare to understand failure impact
10. **Check stability first** - Unstable process makes Cpk meaningless
11. **Cpk ≥ 1.33 is capable** - <1.0 needs action, <0.67 is critical
12. **step_caused_uut_failed is key** - Identifies true root cause steps
13. **Follow the workflow** - Yield → Dimensions → Steps → Capability → Measurements
