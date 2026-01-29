# Analytics Domain

The Analytics domain provides data analysis and visualization capabilities for test results. It includes yield calculations, measurement aggregation, Cpk analysis, and production flow visualization (Unit Flow). Use this domain to understand manufacturing performance, identify trends, and optimize processes.

## Table of Contents

- [Quick Start](#quick-start)
- [Type-Safe Enums](#type-safe-enums)
- [Core Concepts](#core-concepts)
- [Yield Analysis](#yield-analysis)
- [Measurement Aggregation](#measurement-aggregation)
- [Unit Flow Analysis](#unit-flow-analysis-internal)
- [Advanced Usage](#advanced-usage)
- [API Reference](#api-reference)

---

## Quick Start

### Synchronous Usage

```python
from pywats import pyWATS, WATSFilter, StatusFilter, MeasurementPath
from datetime import datetime, timedelta

# Initialize
api = pyWATS(
    base_url="https://your-wats-server.com",
    token="your-api-token"
)

# Get yield for last 7 days (using type-safe enum)
filter_obj = WATSFilter(
    part_number="WIDGET-001",
    status=StatusFilter.ALL,  # Type-safe enum
    days=7
)

yield_result = api.analytics.get_yield(filter_obj)
print(f"Yield: {yield_result.yield_pct:.1f}%")
print(f"Passed: {yield_result.passed}")
print(f"Failed: {yield_result.failed}")
print(f"Total: {yield_result.total}")

# Get measurements for a step (using friendly path format)
path = MeasurementPath("Numeric Limit Tests/3.3V Rail")
measurements = api.analytics.get_aggregated_measurements(
    filter_obj,
    measurement_paths=path
)

for meas in measurements:
    print(f"{meas.step_name}:")
    print(f"  Avg: {meas.avg:.3f}")
    print(f"  Cpk: {meas.cpk:.2f}")
```

### Asynchronous Usage

For concurrent requests and better performance:

```python
import asyncio
from pywats import AsyncWATS, WATSFilter, StatusFilter

async def analyze_yield():
    async with AsyncWATS(
        base_url="https://your-wats-server.com",
        token="your-api-token"
    ) as api:
        filter_obj = WATSFilter(part_number="WIDGET-001", days=7)
        
        # Concurrent queries - much faster!
        yield_result, measurements = await asyncio.gather(
            api.analytics.get_yield(filter_obj),
            api.analytics.get_aggregated_measurements(filter_obj)
        )
        
        print(f"Yield: {yield_result.yield_pct:.1f}%")

asyncio.run(analyze_yield())
```

---

## Type-Safe Enums

The Analytics domain provides type-safe enums for building queries with IDE autocomplete and compile-time validation.

### Query Enums

```python
from pywats import StatusFilter, RunFilter, StepType, CompOperator

# Status filter - filter by test result status
StatusFilter.PASSED      # "P" - Passed tests only
StatusFilter.FAILED      # "F" - Failed tests only
StatusFilter.ERROR       # "E" - Error/terminated tests
StatusFilter.TERMINATED  # "T" - Terminated tests
StatusFilter.ALL         # "*" - All statuses

# Run filter - filter by test run sequence
RunFilter.FIRST           # 1 - First run only
RunFilter.LAST            # -1 - Last run only
RunFilter.ALL             # 0 - All runs
RunFilter.ALL_EXCEPT_FIRST # 2 - All except first run

# Step types returned in analytics results
StepType.NUMERIC_LIMIT    # Numeric measurement with limits
StepType.STRING_VALUE     # String comparison
StepType.PASS_FAIL        # Binary pass/fail
StepType.SEQUENCECALL     # Sequence call step

# Comparison operators in step results
CompOperator.GELE   # Greater/Equal and Less/Equal (within range)
CompOperator.GT     # Greater than
CompOperator.LT     # Less than
CompOperator.EQ     # Equal
CompOperator.NE     # Not equal
CompOperator.LOG    # Logged value (no comparison)
```

### Dimension and KPI Enums

```python
from pywats import Dimension, KPI, RepairDimension, RepairKPI

# Grouping dimensions for dynamic queries
Dimension.PART_NUMBER     # Group by part number
Dimension.STATION_NAME    # Group by test station
Dimension.PERIOD          # Group by time period
Dimension.PROCESS_CODE    # Group by process code
Dimension.REVISION        # Group by product revision
Dimension.OPERATOR        # Group by operator
Dimension.FIXTURE_ID      # Group by fixture
# ... and 15+ more dimensions

# KPIs for yield/performance queries
KPI.UNIT_COUNT     # Number of units tested
KPI.FPY            # First Pass Yield
KPI.RTY            # Rolled Throughput Yield
KPI.PPM_FPY        # Parts per million (FPY based)
KPI.AVG_TEST_TIME  # Average test time
KPI.RETEST_COUNT   # Number of retests
# ... and 15+ more KPIs

# Repair-specific dimensions and KPIs
RepairDimension.REPAIR_CODE       # Repair code
RepairDimension.COMPONENT_REF     # Component reference
RepairKPI.REPAIR_COUNT            # Number of repairs
RepairKPI.REPAIR_REPORT_COUNT     # Repair reports
```

### DimensionBuilder - Fluent API

Build dimension queries with type safety and IDE autocomplete:

```python
from pywats import DimensionBuilder, Dimension, KPI, WATSFilter

# Build custom dimension query
dims = DimensionBuilder()\
    .add(KPI.UNIT_COUNT, desc=True)\
    .add(KPI.FPY)\
    .add(Dimension.PART_NUMBER)\
    .add(Dimension.PERIOD)\
    .build()
# Result: "unitCount desc;fpy;partNumber;period"

# Use with WATSFilter
filter_obj = WATSFilter(
    part_number="WIDGET-001",
    dimensions=dims,
    period_count=30
)

# Use presets for common patterns
dims = DimensionBuilder.yield_by_product().build()
dims = DimensionBuilder.yield_by_station().build()
dims = DimensionBuilder.repair_analysis().build()
dims = DimensionBuilder.oee_analysis().build()
```

### Path Utilities

Work with measurement paths using a user-friendly format:

```python
from pywats import MeasurementPath, StepPath

# Create paths with forward slashes (user-friendly format)
path = MeasurementPath("Functional Test/Power Supply/3.3V Rail")
print(path.display)     # Functional Test/Power Supply/3.3V Rail
print(path.api_format)  # Functional Test¶Power Supply¶3.3V Rail (internal)
print(path.parts)       # ['Functional Test', 'Power Supply', '3.3V Rail']

# Build paths with concatenation
parent = StepPath("Functional Test")
full_path = parent / "Power Supply" / "3.3V Rail"
print(full_path.display)  # Functional Test/Power Supply/3.3V Rail

# Use from_parts for programmatic construction
path = MeasurementPath.from_parts(["Main", "SubTest", "Measurement"])

# Paths work directly in API calls
measurements = api.analytics.get_aggregated_measurements(
    filter_obj,
    measurement_paths=path  # Automatic conversion to API format
)

# Access display format from results
for meas in measurements:
    print(f"Path: {meas.step_path_display}")  # Friendly format
```

---

## Core Concepts

### Yield
**Yield** is the percentage of units that passed testing:
- `yield_pct`: Percentage (0-100)
- `passed`: Number of passed units
- `failed`: Number of failed units
- `total`: Total units tested

### Measurements
**Aggregated measurements** provide statistical analysis of numeric test steps:
- `avg`: Average value
- `min`, `max`: Minimum and maximum
- `std_dev`: Standard deviation
- `cpk`: Process capability index
- `count`: Number of measurements

### Unit Flow
**Unit Flow** visualizes how units move through production:
- **Nodes**: Operations/processes (e.g., "ICT", "FCT", "Assembly")
- **Links**: Transitions between operations
- **Units**: Individual units tracked through the flow

---

## Yield Analysis

### Get Overall Yield

```python
from pywats import WATSFilter, StatusFilter

# Yield for last 30 days
filter_obj = WATSFilter(
    part_number="WIDGET-001",
    status=StatusFilter.ALL,  # Include all statuses
    days=30
)

yield_result = api.analytics.get_yield(filter_obj)

print(f"=== YIELD ANALYSIS ===")
print(f"Yield: {yield_result.yield_pct:.2f}%")
print(f"Passed: {yield_result.passed}")
print(f"Failed: {yield_result.failed}")
print(f"Total: {yield_result.total}")
```

### Yield by Date Range

```python
from datetime import datetime, timedelta

# Last quarter
end_date = datetime.now()
start_date = end_date - timedelta(days=90)

filter_obj = WATSFilter(
    part_number="WIDGET-001",
    start_date_time=start_date,
    end_date_time=end_date
)

yield_result = api.analytics.get_yield(filter_obj)
print(f"Q1 Yield: {yield_result.yield_pct:.1f}%")
```

### Yield by Station

```python
# Compare yield across stations
stations = ["ICT-01", "ICT-02", "ICT-03"]

print("=== YIELD BY STATION ===")
for station in stations:
    filter_obj = WATSFilter(
        part_number="WIDGET-001",
        station=station,
        days=7
    )
    
    yield_result = api.analytics.get_yield(filter_obj)
    print(f"{station}: {yield_result.yield_pct:.1f}% ({yield_result.total} units)")
```

### Yield Trend Over Time

```python
from datetime import datetime, timedelta

def get_daily_yield(part_number, days=30):
    """Get yield for each of the last N days"""
    
    trends = []
    end_date = datetime.now()
    
    for i in range(days):
        day_end = end_date - timedelta(days=i)
        day_start = day_end - timedelta(days=1)
        
        filter_obj = WATSFilter(
            part_number=part_number,
            start_date_time=day_start,
            end_date_time=day_end
        )
        
        yield_result = api.analytics.get_yield(filter_obj)
        
        trends.append({
            'date': day_start.date(),
            'yield': yield_result.yield_pct,
            'total': yield_result.total
        })
    
    return trends

# Use it
trends = get_daily_yield("WIDGET-001", days=14)

print("=== 14-DAY YIELD TREND ===")
for trend in reversed(trends):
    yield_bar = "█" * int(trend['yield'] / 5)  # Visual bar
    print(f"{trend['date']}: {trend['yield']:.1f}% {yield_bar} ({trend['total']} units)")
```

---

## Measurement Aggregation

### Get Measurement Statistics

```python
from pywats import WATSFilter, MeasurementPath

# Get measurements for a specific test step
filter_obj = WATSFilter(
    part_number="WIDGET-001",
    days=7
)

# Use user-friendly path format (slashes)
path = MeasurementPath("Power Supply Tests/3.3V Rail")
measurements = api.analytics.get_aggregated_measurements(
    filter_obj,
    measurement_paths=path
)

if measurements:
    meas = measurements[0]
    print(f"Step: {meas.step_name}")
    print(f"Count: {meas.count}")
    print(f"Average: {meas.avg:.3f}")
    print(f"Min: {meas.min:.3f}")
    print(f"Max: {meas.max:.3f}")
    print(f"Std Dev: {meas.std_dev:.3f}")
    print(f"Cpk: {meas.cpk:.2f}")
```

### Multiple Measurements

```python
from pywats import MeasurementPath

# Get multiple measurements at once using path objects
step_paths = [
    MeasurementPath("Power Supply Tests/3.3V Rail"),
    MeasurementPath("Power Supply Tests/5V Rail"),
    MeasurementPath("Power Supply Tests/12V Rail")
]

measurements = api.analytics.get_aggregated_measurements(
    filter_obj,
    measurement_paths=step_paths
)

print("=== POWER RAIL MEASUREMENTS ===")
for meas in measurements:
    print(f"\n{meas.step_name}:")
    print(f"  Path: {meas.step_path_display}")  # User-friendly format
    print(f"  Avg: {meas.avg:.3f} (σ={meas.std_dev:.3f})")
    print(f"  Range: {meas.min:.3f} to {meas.max:.3f}")
    print(f"  Cpk: {meas.cpk:.2f}")
```

### Cpk Analysis

```python
from pywats import MeasurementPath

def analyze_process_capability(part_number, step_path, days=30):
    """Analyze process capability (Cpk) for a measurement"""
    
    filter_obj = WATSFilter(
        part_number=part_number,
        days=days
    )
    
    # Accept string or MeasurementPath
    path = MeasurementPath(step_path) if isinstance(step_path, str) else step_path
    
    measurements = api.analytics.get_aggregated_measurements(
        filter_obj,
        measurement_paths=path
    )
    
    if not measurements:
        print("No measurements found")
        return
    
    meas = measurements[0]
    
    print(f"\n=== PROCESS CAPABILITY: {meas.step_name} ===")
    print(f"Cpk: {meas.cpk:.2f}")
    
    if meas.cpk >= 1.33:
        print("✓ Process is capable (Cpk ≥ 1.33)")
    elif meas.cpk >= 1.0:
        print("⚠ Process is marginally capable (1.0 ≤ Cpk < 1.33)")
    else:
        print("✗ Process is not capable (Cpk < 1.0)")
    
    print(f"\nStatistics:")
    print(f"  Mean: {meas.avg:.3f}")
    print(f"  Std Dev: {meas.std_dev:.3f}")
    print(f"  Range: {meas.min:.3f} to {meas.max:.3f}")
    print(f"  Samples: {meas.count}")

# Use it with user-friendly path
analyze_process_capability("WIDGET-001", "Power Supply/3.3V Rail", days=90)
```

---

## Unit Flow Analysis (Internal)

⚠️ **INTERNAL API - Subject to change**

Unit Flow visualizes production flow and identifies bottlenecks.

### Basic Unit Flow Query

```python
from pywats.domains.analytics import UnitFlowFilter
from datetime import datetime, timedelta

# Create filter
flow_filter = UnitFlowFilter(
    part_number="WIDGET-001",
    date_from=datetime.now() - timedelta(days=7),
    date_to=datetime.now()
)

# Get flow data
flow = api.analytics.get_unit_flow(flow_filter)

print(f"=== UNIT FLOW ===")
print(f"Nodes: {len(flow.nodes)}")
print(f"Links: {len(flow.links)}")
print(f"Units: {len(flow.units)}")

# Show nodes (operations)
print("\nOperations:")
for node in flow.nodes:
    print(f"  {node.name}: {node.unit_count} units")

# Show transitions
print("\nTransitions:")
for link in flow.links:
    print(f"  {link.source_name} → {link.target_name}: {link.unit_count} units")
```

### Identify Bottlenecks

```python
# Get bottlenecks (nodes with high unit count)
flow_filter = UnitFlowFilter(
    part_number="WIDGET-001",
    days=7
)

bottlenecks = api.analytics.get_bottlenecks(flow_filter)

print("=== BOTTLENECKS ===")
for bottleneck in bottlenecks:
    print(f"{bottleneck.operation_name}:")
    print(f"  Units waiting: {bottleneck.unit_count}")
    print(f"  Avg time: {bottleneck.avg_time_hours:.1f} hours")
```

### Trace Serial Numbers Through Flow

```python
# Trace specific units
flow_filter = UnitFlowFilter(
    part_number="WIDGET-001",
    serial_numbers=["W12345", "W12346", "W12347"],
    days=30
)

trace_result = api.analytics.trace_serial_numbers(flow_filter)

for unit in trace_result.units:
    print(f"\n{unit.serial_number}:")
    print(f"  Status: {unit.status}")
    print(f"  Path: {' → '.join(unit.node_path)}")
    print(f"  Total time: {unit.total_time_hours:.1f} hours")
```

---

## Advanced Usage

### Yield Dashboard

```python
from pywats import WATSFilter

def yield_dashboard(part_numbers, days=7):
    """Generate yield dashboard for multiple products"""
    
    print("=" * 70)
    print(f"YIELD DASHBOARD ({days} days)")
    print("=" * 70)
    
    results = []
    
    for pn in part_numbers:
        filter_obj = WATSFilter(part_number=pn, days=days)
        yield_result = api.analytics.get_yield(filter_obj)
        
        results.append({
            'part': pn,
            'yield': yield_result.yield_pct,
            'passed': yield_result.passed,
            'failed': yield_result.failed,
            'total': yield_result.total
        })
    
    # Sort by yield (ascending)
    results.sort(key=lambda x: x['yield'])
    
    print(f"\n{'Part Number':<20} {'Yield':>8} {'Passed':>8} {'Failed':>8} {'Total':>8}")
    print("-" * 70)
    
    for r in results:
        status = "✓" if r['yield'] >= 95 else "⚠" if r['yield'] >= 85 else "✗"
        print(f"{r['part']:<20} {r['yield']:>7.1f}% {r['passed']:>8} {r['failed']:>8} {r['total']:>8} {status}")
    
    # Summary
    avg_yield = sum(r['yield'] for r in results) / len(results)
    total_units = sum(r['total'] for r in results)
    
    print("-" * 70)
    print(f"{'AVERAGE':<20} {avg_yield:>7.1f}% {'':>8} {'':>8} {total_units:>8}")
    print("=" * 70)

# Use it
products = ["WIDGET-001", "WIDGET-002", "WIDGET-003", "GADGET-001"]
yield_dashboard(products, days=30)
```

### Measurement Report

```python
from pywats import WATSFilter, MeasurementPath

def measurement_report(part_number, step_paths, days=7):
    """Generate measurement report for multiple steps"""
    
    filter_obj = WATSFilter(part_number=part_number, days=days)
    
    # Convert string paths to MeasurementPath objects
    paths = [MeasurementPath(p) if isinstance(p, str) else p for p in step_paths]
    
    measurements = api.analytics.get_aggregated_measurements(
        filter_obj,
        measurement_paths=paths
    )
    
    print(f"\n=== MEASUREMENT REPORT: {part_number} ({days} days) ===\n")
    print(f"{'Step':<40} {'Avg':>10} {'Std Dev':>10} {'Cpk':>8} {'Count':>8}")
    print("-" * 80)
    
    for meas in measurements:
        cpk_status = "✓" if meas.cpk >= 1.33 else "⚠" if meas.cpk >= 1.0 else "✗"
        print(f"{meas.step_name:<40} {meas.avg:>10.3f} {meas.std_dev:>10.3f} {meas.cpk:>7.2f} {meas.count:>8} {cpk_status}")
    
    print("=" * 80)

# Use it with user-friendly paths
steps = [
    "Power Supply Tests/3.3V Rail",
    "Power Supply Tests/5V Rail",
    "Power Supply Tests/12V Rail",
    "Temperature Tests/Idle Temp",
    "Temperature Tests/Load Temp"
]

measurement_report("WIDGET-001", steps, days=30)
```

---

## API Reference

### AnalyticsService Methods

All methods are accessed via `api.analytics`. Methods marked with ⚠️ use internal WATS endpoints that may change without notice.

#### Yield Operations
- `get_yield(filter)` → `YieldResult` - Calculate yield statistics

#### Measurement Operations
- `get_aggregated_measurements(filter, measurement_paths)` → `List[AggregatedMeasurement]` - Get measurement statistics

#### Unit Flow Operations (⚠️ Internal API)
- `get_unit_flow(filter)` → `UnitFlowResult` - Get complete flow data
- `get_flow_nodes()` → `List[UnitFlowNode]` - Get flow nodes
- `get_flow_links()` → `List[UnitFlowLink]` - Get flow links
- `get_flow_units()` → `List[UnitFlowUnit]` - Get flow units
- `get_bottlenecks(filter, min_yield_threshold)` → `List[UnitFlowNode]` - Identify bottlenecks
- `trace_serial_numbers(serial_numbers, filter)` → `UnitFlowResult` - Trace specific units

#### Step/Measurement Filter Operations (⚠️ Internal API)
- `get_measurement_list(filter_data, step_filters, sequence_filters)` → `List[MeasurementListItem]` - Measurement values with XML filters
- `get_measurement_list_by_product(product_group_id, level_id, days, step_filters, sequence_filters)` → `List[MeasurementListItem]` - Simple query
- `get_step_status_list(filter_data, step_filters, sequence_filters)` → `List[StepStatusItem]` - Step statuses with XML filters
- `get_step_status_list_by_product(product_group_id, level_id, days, step_filters, sequence_filters)` → `List[StepStatusItem]` - Simple query
- `get_top_failed_advanced(filter_data, top_count)` → `List[TopFailedStep]` - Top failed steps with advanced filters
- `get_top_failed_by_product(part_number, process_code, product_group_id, level_id, days, count)` → `List[TopFailedStep]` - Simple query

### Enums

#### Query Enums (from `pywats`)

| Enum | Values | Description |
|------|--------|-------------|
| `StatusFilter` | `PASSED`, `FAILED`, `ERROR`, `TERMINATED`, `ALL` | Filter by test status |
| `RunFilter` | `FIRST`, `LAST`, `ALL`, `ALL_EXCEPT_FIRST` | Filter by run sequence |
| `StepType` | `NUMERIC_LIMIT`, `STRING_VALUE`, `PASS_FAIL`, `SEQUENCECALL`, etc. | Step type classification |
| `CompOperator` | `GELE`, `GT`, `LT`, `EQ`, `NE`, `LOG`, etc. | Comparison operators |
| `SortDirection` | `ASC`, `DESC` | Sort direction for dimension queries |

#### Dimension/KPI Enums (from `pywats` or `pywats.domains.analytics`)

| Enum | Count | Description |
|------|-------|-------------|
| `Dimension` | 23+ | Grouping dimensions (PART_NUMBER, STATION_NAME, PERIOD, etc.) |
| `RepairDimension` | 15 | Repair-specific dimensions |
| `KPI` | 21+ | Key Performance Indicators (FPY, RTY, PPM_FPY, etc.) |
| `RepairKPI` | 2 | Repair KPIs |

#### DimensionBuilder Class Methods

| Method | Description |
|--------|-------------|
| `add(dimension, direction=None, asc=False, desc=False)` | Add dimension with optional sort |
| `add_all(*dimensions)` | Add multiple dimensions |
| `build()` | Build semicolon-separated string |
| `clear()` | Clear all dimensions |
| `yield_by_product()` | Preset for product yield analysis |
| `yield_by_station()` | Preset for station yield analysis |
| `repair_analysis()` | Preset for repair statistics |
| `oee_analysis()` | Preset for OEE metrics |

### Path Utilities (from `pywats`)

| Class | Description |
|-------|-------------|
| `StepPath` | Step path with `/` ↔ `¶` conversion |
| `MeasurementPath` | Measurement path with `/` ↔ `¶` conversion |

**Properties**: `.display` (user-friendly), `.api_format` (internal), `.parts` (list)

**Methods**: `from_parts(parts)`, concatenation with `/` operator

### Models

#### YieldResult
- `yield_pct`: float (percentage)
- `passed`: int
- `failed`: int
- `total`: int

#### AggregatedMeasurement
- `step_name`: str
- `step_path`: str (API format with `¶`)
- `step_path_display`: str (user-friendly with `/`)
- `count`: int
- `avg`: float
- `min`, `max`: float
- `std_dev`: float
- `cpk`: float (process capability index)

#### TopFailedStep
- `step_name`, `step_path`: str
- `step_path_display`: str (user-friendly)
- `step_type`: `Union[StepType, str]`
- `fail_count`, `total_count`: int
- `step_filter`, `sequence_filter`: str (XML for drill-down)

#### StepAnalysisRow
- `step_name`, `step_path`: str
- `step_path_display`: str (user-friendly)
- `step_type`: `Union[StepType, str]`
- `comp_operator`: `Union[CompOperator, str]`
- Statistical fields: `avg`, `std_dev`, `cpk`, etc.

#### UnitFlowFilter
- `part_number`: str
- `date_from`, `date_to`: datetime
- `days`: int (shortcut for last N days)
- `serial_numbers`: List[str] (optional filter)

#### StepStatusItem (⚠️ Internal API)
- `step_name`, `step_path`, `step_type`: str - Step identification
- `pass_count`, `fail_count`, `total_count`: int - Status counts
- `status`: str - Current status
- `serial_number`, `report_id`: str - Associated unit info

#### MeasurementListItem (⚠️ Internal API)
- `serial_number`, `part_number`, `revision`: str - Unit identification
- `step_name`, `step_path`: str - Step identification
- `value`: float - Measured value
- `limit_low`, `limit_high`: float - Limits
- `status`: str - Pass/Fail status
- `unit`: str - Unit of measurement

---

## Best Practices

1. **Use type-safe enums** - Leverage `StatusFilter`, `RunFilter`, `Dimension`, `KPI` for IDE autocomplete
2. **Use path utilities** - `MeasurementPath("Main/SubTest/Meas")` handles format conversion automatically
3. **Use DimensionBuilder presets** - Start with `DimensionBuilder.yield_by_product()` and customize
4. **Start with simple queries** - Use default parameters, add filters as needed
5. **Monitor Cpk trends** - Cpk < 1.0 indicates process capability issues
6. **Investigate anomalies** - Low Cpk or sudden yield drops
7. **Use Unit Flow for bottlenecks** - Visualize production flow

---

## See Also

- [Report Domain](REPORT.md) - Test reports and measurements
- [Production Domain](PRODUCTION.md) - Unit lifecycle and status
- [Process Domain](PROCESS.md) - Operation type definitions
