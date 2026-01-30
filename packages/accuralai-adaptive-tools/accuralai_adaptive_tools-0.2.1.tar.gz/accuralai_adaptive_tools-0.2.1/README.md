# accuralai-adaptive-tools

**Self-improving tool ecosystem for AccuralAI**

## Overview

This package implements the V3 unified adaptive tools architecture that combines:

- **V1 (Exploration)**: Pattern-based tool generation from telemetry analysis
- **V2 (Exploitation)**: Learning-based workflow optimization with PlanLang DSL
- **V3 (Coordination)**: Unified system that compounds gains through cross-system effects

## Features

### V1: Tool Generation
- ✅ Telemetry collection and pattern detection
- ✅ LLM-powered code synthesis
- ✅ Sandboxed evaluation with safety validation
- ✅ Human-in-the-loop approval workflows
- ✅ A/B testing for auto-promotion

### V2: Workflow Optimization
- ✅ PlanLang DSL for declarative tool composition
- ✅ Multi-objective Bayesian optimization
- ✅ Strategy support (caching, retries, parallel execution)
- ✅ Git-versioned recipe memory
- ✅ Statistical A/B testing

### V3: Unified Coordination
- ✅ Shared telemetry routing to V1 and V2
- ✅ Unified registry for tools and plans
- ✅ Cross-system synchronization
- ✅ Compound gains tracking
- ✅ Seamless CLI experience

## Installation

```bash
# From repository root
pip install -e packages/accuralai-adaptive-tools

# With dev dependencies
pip install -e packages/accuralai-adaptive-tools[dev]
```

## Quick Start

See `/plan/QUICKSTART-ADAPTIVE-TOOLS.md` for detailed setup instructions.

### Basic Configuration

Create `~/.accuralai/config.toml`:

```toml
[adaptive_tools]
enabled = true
mode = "v3"  # "v1", "v2", or "v3"

[adaptive_tools.v1.synthesis]
backend_id = "google"
model = "gemini-2.5-flash-lite"
temperature = 0.2

[adaptive_tools.v2.optimizer]
algorithm = "bayesian"
max_trials = 50
```

### Usage Examples

```bash
# Start AccuralAI CLI
accuralai

# Generate new tool from pattern (V1)
>>> /tool propose "merge CSV files"

# Optimize existing workflow (V2)
>>> /plan optimize analyze_logs

# View unified status (V3)
>>> /adaptive status

# Evolve tools and plans together
>>> /tool evolve
```

## Architecture

### Package Structure

```
accuralai_adaptive_tools/
├── contracts/          # Data models and protocols
│   ├── models.py      # Pydantic models
│   └── protocols.py   # Protocol definitions
├── telemetry/         # Shared telemetry system
│   ├── collector.py   # Main collector
│   ├── router.py      # Route to V1/V2
│   └── storage.py     # SQLite persistence
├── registry/          # Unified registry
│   └── unified.py     # Tools + Plans
├── v1/                # Pattern-based generation
│   ├── telemetry/    # Pattern detection
│   ├── synthesis/    # Code generation
│   ├── sandbox/      # Safe execution
│   └── approval/     # Workflows
├── v2/                # Learning-based optimization
│   ├── planlang/     # DSL parser/validator
│   ├── execution/    # Plan executor
│   ├── optimization/ # Bayesian optimizer
│   └── memory/       # Recipe store
├── coordinator/       # V3 coordination
│   └── v3.py         # Main coordinator
└── cli/              # CLI integration
    └── commands.py   # All commands
```

### Data Flow

```
User Action
    ↓
Telemetry Event
    ↓
Router (decides V1 vs V2)
    ↓
┌───────────────┴───────────────┐
↓                               ↓
V1 System                    V2 System
(Pattern → Tool)             (Metrics → Plan)
↓                               ↓
└──────→ Unified Registry ←─────┘
         ↓
    Better Performance
         ↓
    (Loop continues)
```

## Commands

### V1 Commands (Tool Generation)

```bash
/tool evolve              # Analyze patterns and propose improvements
/tool propose <desc>      # Create tool from description
/tool review <id>         # Review specific proposal
/tool approve <id>        # Approve proposal
/tool reject <id>         # Reject proposal
/tool metrics <name>      # View tool performance
/tool versions <name>     # View tool history
/tool rollback <name> <v> # Rollback to version
```

### V2 Commands (Plan Optimization)

```bash
/plan generate <task>     # Generate plan from description
/plan run <name>          # Execute saved plan
/plan optimize <name>     # Optimize hyperparameters
/plan compare <p1> <p2>   # Statistical A/B test
```

### V3 Commands (Unified)

```bash
/adaptive status          # View V1+V2+V3 status
```

## Configuration Reference

```toml
[adaptive_tools]
enabled = true
mode = "v3"  # "v1", "v2", or "v3"

[adaptive_tools.v3]
auto_coordinate = true
compound_tracking = true
v1_sequence_threshold = 10
v1_failure_threshold = 0.2
v2_latency_threshold_ms = 500
v2_cost_threshold_cents = 10

[adaptive_tools.v1]
auto_propose = false
approval_mode = "manual"

[adaptive_tools.v1.synthesis]
backend_id = "google"
model = "gemini-2.5-flash-lite"
temperature = 0.2

[adaptive_tools.v1.sandbox]
executor = "subprocess"
timeout_s = 10
max_memory_mb = 256

[adaptive_tools.v2]
max_optimization_trials = 50
ab_test_sample_size = 100
significance_level = 0.05

[adaptive_tools.v2.optimizer]
algorithm = "bayesian"
acquisition_function = "ei"

[adaptive_tools.telemetry]
storage_path = "~/.accuralai/adaptive-tools/telemetry.db"
retention_days = 30
batch_size = 100
```

## Development

### Running Tests

```bash
# All tests
pytest packages/accuralai-adaptive-tools/tests -v

# Specific subsystem
pytest packages/accuralai-adaptive-tools/tests/v1 -v
pytest packages/accuralai-adaptive-tools/tests/v2 -v
pytest packages/accuralai-adaptive-tools/tests/coordinator -v
```

### Linting

```bash
ruff check packages/accuralai-adaptive-tools/
ruff format packages/accuralai-adaptive-tools/
```

### Running Benchmarks

#### Adaptive Tools vs Baseline Benchmark

Compare AccuralAI performance with and without adaptive tools using the Google Gemini backend:

```bash
# Set your Google API key
export GOOGLE_GENAI_API_KEY=your_key_here

# Run all scenarios
python packages/accuralai-adaptive-tools/tests/benchmarks/run_adaptive_benchmark.py

# Run specific scenario
python packages/accuralai-adaptive-tools/tests/benchmarks/run_adaptive_benchmark.py "Multi-Step Data Processing"

# Or via pytest
pytest packages/accuralai-adaptive-tools/tests/benchmarks/test_adaptive_vs_baseline_benchmark.py -v -s
```

**What it tests:**
- **Multi-Step Data Processing**: Processes data across multiple LLM calls
- **Code Generation Workflow**: Generates and refines code iteratively
- **Research and Analysis**: Research synthesis workflow
- **Repeated Pattern Detection**: Tests adaptive tool generation from patterns

**Metrics compared:**
- Latency (response time)
- Cost (API usage costs)
- Token efficiency
- Response quality
- Cache hit rates
- Tools generated and optimizations applied

**Expected results:**
- Adaptive tools should show improvements in repeated scenarios through:
  - Pattern detection and tool generation (V1)
  - Workflow optimization (V2)
  - Caching and optimization strategies
- First-time scenarios may show neutral performance (adaptive tools overhead)
- Repeated scenarios should show 10-30% improvements in latency and cost

#### System Benchmark Suite

Run the comprehensive system benchmark:

```bash
python packages/accuralai-adaptive-tools/tests/benchmarks/test_adaptive_system_benchmark.py
```

This tests all subsystems (V1, V2, V3) and provides scores across 7 categories.

## Documentation

- **Specification**: See `/plan/accuralai-adaptive-tools-v3-spec.md`
- **Quick Start**: See `/plan/QUICKSTART-ADAPTIVE-TOOLS.md`
- **Comparison**: See `/plan/adaptive-tools-comparison.md`
- **Integration**: See `/plan/accuralai-adaptive-tools-integration.md`

## Contributing

Contributions welcome! Please see the main AccuralAI repository for guidelines.

## License

MIT License - see repository root for details.

---

**Questions?** See `/plan/` directory for detailed specifications or open an issue.
