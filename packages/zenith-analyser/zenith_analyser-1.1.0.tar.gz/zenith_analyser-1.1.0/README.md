# zenith_analyser
# Zenith Analyser

[![PyPI version](https://badge.fury.io/py/zenith-analyser.svg)](https://pypi.org/project/zenith-analyser/)
[![Python Versions](https://img.shields.io/pypi/pyversions/zenith-analyser.svg)](https://pypi.org/project/zenith-analyser/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI Status](https://github.com/frasasu/zenith-analyser/actions/workflows/ci.yml/badge.svg)](https://github.com/frasasu/zenith-analyser/actions)


A powerful Python library for analyzing structured temporal laws with events, chronocoherence, chronodispersal, and hierarchical targets.

## Features

- **Complete Lexer & Parser**: Full Zenith language syntax support
- **Temporal Analysis**: Analyze laws with events, chronocoherence, and chronodispersal
- **Target Hierarchy**: Navigate through nested targets with inheritance
- **Event Simulation**: Simulate event sequences with temporal constraints
- **Time Conversion**: Convert between Zenith point format (Y.M.D.H.M) and minutes
- **AST Manipulation**: Parse, analyze, and unparse Zenith code
- **Validation**: Comprehensive syntax and semantic validation
- **Extensible**: Easy to extend with custom analyzers



# Zenith-Analyser - Complete Documentation

## 📚 Table of Contents
1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [API Documentation](#api-documentation)
4. [CLI Usage](#cli-usage)
5. [Zenith Language Specification](#zenith-language-specification)
6. [Advanced Features](#advanced-features)
7. [Examples](#examples)
8. [Installation](#installation)

---

## Introduction

Zenith-Analyser is a comprehensive time management and temporal analysis library that provides tools for modeling, analyzing, and visualizing temporal structures using the Zenith language. It helps users plan, analyze, and optimize their time allocation across various objectives and activities.

### Key Features
- **Temporal Modeling**: Define laws (temporal sessions) and targets (objectives)
- **Hierarchical Analysis**: Analyze objectives across generations and populations
- **Advanced Metrics**: Calculate complexity, density, rhythm, and entropy metrics
- **Visualization**: Generate comprehensive visualizations of temporal data
- **CLI Interface**: Full command-line interface for analysis workflows

---

## Core Concepts

### 1. Generation & Population

#### Generation
In Zenith, a **generation** refers to the hierarchical level of an objective within a goal system. It expresses the structural depth of an objective, from global intentions to concrete and immediate actions. Each objective belongs to a single generation, allowing precise positioning of its role, degree of specialization, and connection with more general or specific objectives.

#### Population
The **population** represents the set of active and influential objectives at a given moment. Unlike generation, which is a positional concept, population is a contextual concept. It groups objectives from several generations that interact simultaneously and guide decisions, priorities, and time allocation in lived reality.

#### Relationship Between Generation and Population
Generation allows understanding where an objective is located, while population allows understanding with which other objectives it acts. An objective can only belong to one generation, but it always participates in a broader population. In Zenith, this distinction enables coherent temporal analysis by separating the structure of objectives from their actual influence on time dynamics.

### 2. Target (Objective)

#### Definition
A target is a general or specific objective within a time management project framework. It represents a plannable, hierarchical, and analytically exploitable entity.

#### Characteristics
1. **Key**: A unique textual identifier for the target
2. **Dictionary**: List of specific objectives associated with the target
3. **Laws**: Planned sessions for working on target objectives
4. **Sub-targets**: A target can contain other targets for hierarchical structuring

#### Example
```python
target programming:
    key: "programming"
    dictionnary:
        d1[d1]: "Software development expertise."
        d2[d1]: "Android and IOS development expertise."
    law Software:
        start_date:1950-01-22 at 12:00
        period:3.45
        Event:
             A[d1]:"Frontend developpement."
             B[d1]:"Backend developpement."
        GROUP:( A 2.15^0 - B 1.30^0)
    end_law
    target Mobile:
         key:"Android and IOS developpement expertise."
         dictionnary:
             d1[d2]:"Android developpement."
             d2[d2]:"IOS developpement."
        law android:
            start_date:1950-01-24 at 12:00
            period:6.0
            Event:
                 A[d1]:"Frontend developpement."
                 B[d1]:"Backend developpement."
            GROUP:(A 1.0^1.0 - A 2.0^15 - B 1.45^0)
        end_law
        law ios:
            start_date:1950-01-25 at 12:00
            period:5.15
            Event:
                 A[d2]:"Frontend developpement."
                 B[d2]:"Backend developpement."
            GROUP:(A 1.0^15 - A 2.0^15 - B 1.45^0)
        end_law
     end_target
end_target
```

### 3. Law (Temporal Session)

#### Definition
A law is a planned session designed to achieve one or more specific objectives of a target. It allows quantifying and structuring time dedicated to each objective.

#### Characteristics
1. **start_date**: Date and time when the session begins
2. **period**: Total planned duration for the session
3. **Event**: List of actions or learnings, referenced via the target's dictionary
4. **GROUP**: Notation (A subscript^superscript - B subscript^superscript - C subscript^superscript - D subscript^superscript ) where:
   - subscript represents chronocoherence duration (useful and directly contributive time)
   - superscript represents chronodispersal duration (used but not directly contributive time)

#### Example
```python
law a2025_12_25_15_45:
    start_date:2025-12-25 at 15:45
    period:4.45
    Event:
        A: "Learning pandas."
        B:"Sweeping room."
        C:"Preparing of foods."
    GROUP:(A 30^0 - B 1.15^0 - C 45^0 - A 15^0 - B 2.0^0)
end_law
```

### 4. Chronocoherence & Chronodispersal

- **Chronocoherence**: Time that is useful and directly contributive to objectives
- **Chronodispersal**: Time that is used but not directly contributive to objectives

---

## API Documentation

### 1. LawAnalyser

#### Role
Manipulates temporal laws - planning structures that define events, their durations (chronocoherence/chronodispersal), and their relationships (order, simultaneity, exclusive/inclusive choices) in this version we hold one relationship which is order (`-`).

#### Methods

##### `get_law_names()`
**Parameters**: None
**Returns**: `List[str]` - names of all defined laws
**Interpretation**: Provides a list of all available temporal programs. Useful for visualizing planning options before deciding which one to use.

```python
names = analyser.law_analyser.get_law_names()
print(names)
# Returns: ['DailyWork', 'WeeklyPlanning', 'ResearchSessions']
```

##### `get_law(name)`
**Parameters**: `name (str)` - law name
**Returns**: `dict` - complete law structure
**Interpretation**: Allows reading the time exploitation plan in detail before simulation.

```python
law = analyser.law_analyser.get_law("DailyWork")
print(law.keys())
# Keys returned:
# - name: law name
# - date: start date
# - time: start time
# - period: total planned duration
# - dictionnary: internal dictionary of events
# - group: list of events with durations (chronocoherence^chronodispersal)
# - source_node: internal AST representation of the law

# Access events:
for event_name, event_data in law['dictionnary'].items():
    print(event_name, event_data)
```

##### `validate_law(name)`
**Parameters**: `name (str)` - law name
**Returns**: `List[str]` - detected errors (empty if valid)
**Interpretation**: Verifies that the law is temporally coherent.

```python
errors = analyser.law_analyser.validate_law("DailyWork")
if errors:
    print("Errors detected:", errors)
else:
    print("Valid law!")
# Returns: [] or ['Event A overlaps Event B', 'Total period exceeds planned duration']
```

### 2. TargetAnalyser

#### Role
Manages objectives (targets), their hierarchy (generations), and their active context (populations). Allows visualizing how time is invested in different objectives.

#### Methods

##### `get_targets_by_generation(generation)`
**Parameters**: `generation (int)` - hierarchical level of objectives
**Returns**: `List[dict]` - objectives of this generation
**Interpretation**: Isolates objectives at the same level to understand where time is concentrated.

```python
targets_gen1 = analyser.target_analyser.get_targets_by_generation(1)
for t in targets_gen1:
    print(t['name'])
```

##### `extract_laws_for_target(target_name)`
**Parameters**: `target_name (str)` - objective name
**Returns**: `dict` - laws directly and indirectly linked to the objective
**Interpretation**: Shows the temporal field mobilized to achieve an objective.

```python
laws = analyser.target_analyser.extract_laws_for_target("MyTarget")
for law_name, law_data in laws.items():
    print(law_name, law_data['group'])
```

##### `extract_laws_population(population)`
**Parameters**: `population (int)` - cumulative depth of generations
**Returns**: `dict` - set of active laws up to this population
**Interpretation**: Simulates the lived temporal reality where multiple objectives interact.

```python
population_laws = analyser.target_analyser.extract_laws_population(2)
print(list(population_laws.keys()))
```

### 3. ZenithAnalyser

#### Role
Simulates the actual exploitation of time. Combines laws, objectives, and populations to produce concrete readings on temporal coherence, dispersion, and efficiency.

#### Methods

##### `law_description(name, population=0)`
**Parameters**:
- `name (str)` - law name
- `population (int)` - population context

**Returns**: `dict` - complete description of the simulated law

```python
desc = analyser.law_description("DailyWork")
print(desc.keys())
# Main dictionary keys:
# - name, start_date, start_time, start_datetime
# - period, period_minutes, end_datetime
# - sum_duration, coherence, dispersal
# - event_count, unique_event_count
# - simulation, event_metrics
# - dispersion_metrics, mean_coherence, mean_dispersal
# - events

# Mini-simulation:
for event in desc['simulation']:
    print(event['event_name'], event['start'], event['end'], event['duration_minutes'])
```

##### `target_description(target_name)`
**Parameters**: `target_name (str)` - objective name
**Returns**: `dict` - complete temporal synthesis of the objective
**Interpretation**: Shows the time actually invested per objective.

```python
target_desc = analyser.target_description("MyTarget")
print(target_desc['events'])
```

##### `population_description(population=-1)`
**Parameters**: `population (int)` - population to analyze (-1 = maximum)
**Returns**: `dict` - complete population simulation
**Interpretation**: Represents cumulative temporal load.

```python
pop = analyser.population_description(population=2)
print(pop['sum_duration'])
```

##### `analyze_corpus()`
**Parameters**: None
**Returns**: `dict` - global corpus diagnostic
**Interpretation**: Provides a complete time management dashboard.

```python
corpus = analyser.analyze_corpus()
print(corpus['corpus_statistics'])
# Main keys returned:
# - corpus_statistics, ast_summary, laws, targets, validation
```
## ⏱️ Zenith Point System

### Time Conversion Functions

#### `point_to_minutes(point: str) → int`
Converts Zenith point notation to total minutes.

**Format:** `years.months.days.hours.minutes` (dot-separated)
**Multipliers:** 1 minute = 1 min, 1 hour = 60 min, 1 day = 1440 min (24h), 1 month = 43200 min (30d), 1 year = 518400 min (360d)

```python
point_to_minutes("30")      # → 30 minutes
point_to_minutes("1.0")     # → 60 minutes (1 hour)
point_to_minutes("0.1.30")  # → 90 minutes (1h30)
point_to_minutes("30.0.0")  # → 43200 minutes (30 days)
point_to_minutes("-1.30")   # → -90 minutes
```

#### `minutes_to_point(total_minutes: int | float) → str`
Converts total minutes back to Zenith point notation.

```python
minutes_to_point(30)    # → "30"
minutes_to_point(60)    # → "1.0"
minutes_to_point(90)    # → "0.1.30"
minutes_to_point(150)   # → "0.2.30" (2h30)
minutes_to_point(1440)  # → "1.0.0" (1 day)
```

### Quick Reference

| Minutes | Point Format | Meaning |
|---------|--------------|---------|
| 30 | `"30"` | 30 minutes |
| 60 | `"1.0"` | 1 hour |
| 90 | `"0.1.30"` | 1 hour 30 minutes |
| 150 | `"0.2.30"` | 2 hours 30 minutes |
| 1440 | `"1.0.0"` | 1 day |
| 43200 | `"30.0.0"` | 30 days |

### Common Usage

```python
# Calculate total duration
total = point_to_minutes("2.30") + point_to_minutes("1.15")  # 225 minutes
formatted = minutes_to_point(total)  # "0.3.45" (3h45)

# Convert for display
duration = point_to_minutes("1.45")  # 105 minutes
hours = duration // 60               # 1
minutes = duration % 60              # 45
```

## 📁 Zenith Corpora System

### Definition

A **Zenith Corpora** is a structured text file containing temporal data formatted in the Zenith language. These files store time management structures including targets (objectives), laws (temporal sessions), events, and their hierarchical relationships for analysis and planning.

### File Specifications

#### Supported Extensions
Zenith corpus files are identified by three extensions:
- `.zenith` (primary, recommended format)
- `.zth` (short form)
- `.znth` (alternate form)

#### File Format
Corpora files are **plain text** with UTF-8 encoding, containing:
- Target definitions with objectives
- Law definitions with time sessions
- Event specifications
- Chronocoherence/dispersal configurations

#### Example Structure
```python
target Project:
    key: "project_management"
    dictionnary:
        planning: "Project planning phase"

    law WorkSession:
        start_date: 2025-01-15 at 09:00
        period: 2.0
        Event:
            task1[planning]: "Morning review"
        GROUP:(task1 2.0^0)
    end_law
end_target
```

### Loading Corpus Files

#### `load_corpus(path: str) → str`
Loads and validates a Zenith corpora file.

```python
from zenith_analyser.utils import load_corpus

# Load corpus file
code = load_corpus("my_project.zenith")  # or .zth, .znth

# Use with analyser
from zenith_analyser.analysers import ZenithAnalyser
analyser = ZenithAnalyser(code)
```

**Requirements:**
- File must exist at specified path
- Must have valid extension (`.zenith`, `.zth`, or `.znth`)
- Read as UTF-8 encoded text

**Error Cases:**
```python
load_corpus("data.txt")      # ❌ Invalid extension
load_corpus("missing.zth")   # ❌ File not found
load_corpus("project.zenith") # ✅ Valid
```

### Usage Example

```python
# Complete workflow
from zenith_analyser.utils import load_corpus
from zenith_analyser.analysers import ZenithAnalyser
from zenith_analyser.metrics import ZenithMetrics

# 1. Load corpus
zenith_code = load_corpus("weekly_schedule.zenith")

# 2. Create analyser
analyser = ZenithAnalyser(zenith_code)

# 3. Generate metrics
metrics = ZenithMetrics(analyser)
simulations = metrics.population_description(1)["simulation"]
results = metrics.get_comprehensive_metrics(simulations)

print(f"Analysis complete: {results['event_count']} events")
```

### 🛠️ Development Tools

#### Zenith Time - VS Code Extension

To streamline the creation and editing of `.zenith` ,`.zth` et `.znth`files, we've developed a dedicated VS Code extension available on the [Visual Studio Code Marketplace](https://marketplace.visualstudio.com/items?itemName=zenith-dev.zenith-time).

##### ✨ Key Features

**Syntax Highlighting**
- Full language support for Zenith Time syntax
- Color-coded elements: targets, laws, events, dictionaries, dates, and operators
- Clear visual distinction between different language constructs

**Smart Code Snippets**
- `target` - Complete target block structure with dictionary
- `law` - Law block with event and group configurations
- `event` - Quick event declaration
- `dict` - Dictionary definition template
- `mevents` - Multiple events with group configuration

**Enhanced Productivity**
- **Automatic bracket/parenthesis/quotes completion**
- **Code folding** for target and law blocks


##### 🚀 Installation

**Method 1: VS Code Marketplace**
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
3. Search for "Zenith Time"
4. Click Install

**Method 2: Command Line**
```bash
code --install-extension zenith-dev.zenith-time
```

##### 🎯 Usage Examples

The extension automatically activates when you open `.zenith`, `.zth` et  `.znth` files. Try these shortcuts:

1. **Create a target block**: Type `target` and press Tab
2. **Add a law**: Type `law` and press Tab
3. **Quick events**: Type `event` or `mevents`

#### 🛠️ Development Features

- **Language Server Protocol ready** structure
- **Scalable syntax definitions** for future language updates
- **Cross-platform compatibility** (Windows, macOS, Linux)
- **Regular updates** with new features and improvements

##### 📁 File Support
- `.zenith` - Primary Zenith Time files
- `.znth` - Alternative extension
- `.zth` - Short extension format

The Zenith Time extension significantly improves development workflow by providing intelligent code completion, syntax validation, and visual enhancements specifically tailored for the Zenith Time language ecosystem.

#### 🔗 Integration with Zenith Analyser
The extension works seamlessly with `zenith-analyser` projects, ensuring consistent syntax highlighting and code structure validation across your development environment.
---

### CLI Usage

#### Installation
```bash
# Installation via pip
pip install zenith-analyser

# Or from source
git clone  https://github.com/frasasu/zenith-analyser
cd zenith-analyser
pip install -e .
```

#### Available Commands

##### `zenith analyze` - Main Analysis
Analyzes a Zenith corpus and produces a structured report.

Syntaxe :

       zenith analyze <input> [options]

Options :

-	`-o, --output `: Output file (stdout by default)
-	`--format `: output format (json, yaml, text) - default: json
-	`--law `: Analyze a specific law
-	`--target `:Analyze a specific target
-	`--population` : Population level (-1 for maximum)
-	`--pretty` :  Pretty-print for JSON



```bash
# Basic analysis
zenith analyze corpus.zenith --format json --pretty

# Analyze specific law
zenith analyze corpus.zenith --law "TemporalLaw" --format text

# Analyze from stdin
cat corpus.zenith | zenith analyze -
```

##### `zenith validate` - Syntax Validation
Validates Zenith file syntax.

Syntax :

        zenith validate <input> [options]

Options :

-	`--strict `: treat warnings as errors


```bash
# Basic validation
zenith validate corpus.zenith

# Strict validation
zenith validate corpus.zenith --strict
```
#### `zenith unparse `-  Code Reconstruction  

Converts a JSON AST to Zenith code.
Syntax :

        zenith unparse <input> [options]

Options :

-	`-o, --output `:Output file
-	`--format` : Format output code

Examples :
```bash
# Reconstruire depuis un AST
zenith unparse ast.json -o reconstructed.zenith

# Avec formatage
zenith unparse ast.json --format
zenith convert - Conversion de format
```
Converts between different formats.

Syntaxe :

        zenith convert <input> <output> [options]

Options :

-	`--from` : Input format (zenith, json) - default: zenith
-	`--to `:Output format (zenith, json) - default: json

Examples :
```bash
# Zenith vers JSON
zenith convert corpus.zenith corpus.json --from zenith --to json

# JSON vers Zenith
zenith convert ast.json reconstructed.zenith --from json --to zenith
```


##### `zenith metrics` - Advanced Metrics
Calculates advanced temporal metrics.

Syntaxe :

        zenith metrics <input> [options]

Options :

-	`--type` : Type of metrics (all, temporal, complexity, density, rhythm, entropy, patterns) - default: all
-	`-o, --output` : Output file
-	`--format` : Output format (json, yaml, text, csv) - default: json
-	`--law` :Analyze a specific law
-	`--target` : Analyze a specific target
-	`--population` : Population level
-	`--pretty `:Pretty-print for JSON



```bash
# All metrics
zenith metrics corpus.zenith --type all --format json --pretty

# Temporal metrics in CSV
zenith metrics corpus.zenith --type temporal --format csv -o metrics.csv

# Detailed metrics for a law
zenith metrics corpus.zenith --law "MainSequence" --detailed
```

##### `zenith visualize` - Visualization
Creates visualizations of temporal data.

Syntaxe :

       zenith visualize <input> [options]

Options :

-	`--type `: Visualization type (histogram, pie, scatter, timeline, summary, frequency, all) - default: histogram
-	`-o, --output `: Output file
-	`--format `:Image format (png, jpg, svg, pdf) - default: png
-	`--law `:Visualize a specific law
-	`--target` :Visualize a specific target
-	`--population` :Population level
-	`--width `: Image width in pixels - default: 1200
-	`--height `: Image height in pixels - default: 800
-	`--title` : Custom title

```bash
# Duration histogram
zenith visualize corpus.zenith --population 3 --type histogram -o histogram.png

# All visualizations
zenith visualize corpus.zenith --population 3 --type all --output-dir ./visualizations

# Specific timeline
zenith visualize corpus.zenith --law "KeyEvents" --type timeline --title "Chronology"
```
#### `zenith export` - Export complet

Exports data and visualizations to a structured folder.

Syntaxe :

         zenith export <input> [options]

Options :

-	`-o, --output-dir `:Output directory - default: ./zenith_export
-	`--formats` : Formats to export (png, pdf, json, csv) - default: png, json
-	`--law` : Export a specific law
-	`--target` :Export a specific target
-	`--population` : Population level
-	`--resolution` : Image resolution in DPI - default: 300
-	`--zip` : Create a ZIP archive

Exemples :
```bash

# Export complet
zenith export corpus.zenith --formats png json csv

# Export spécifique avec ZIP
zenith export corpus.zenith --target "ProjetPrincipal" --formats pdf json --zip

# Export haute résolution
zenith export corpus.zenith --resolution 600
```

#### `zenith compare` - Comparaison multiple

Compare multiple Zenith analyses.

Syntaxe :

         zenith compare <input1> <input2> ... [options]

Options :

-	`-o, --output` :Output file
-	`--format` : Output format (json, text) - default: text
-	`--labels` :Labels for each input
-	`--population` : population level default -1 for max population.
-	`--visualize` :Generate comparison visualizations

Exemples :
```bash
# Comparaison basique
zenith compare corpus1.zenith corpus2.zenith corpus3.zenith

# Avec labels personnalisés
zenith compare file1.zenith file2.zenith --labels "VersionA" "VersionB"

# Comparaison avec visualisation
zenith compare corpus_1.zenith corpus_2.zenith --visualize --format json
```



##### Complete Analysis Pipeline
```bash
# Step 1: Validation
zenith validate my_corpus.zenith --strict

# Step 2: Analysis
zenith analyze my_corpus.zenith --pretty -o analysis.json

# Step 3: Metrics
zenith metrics my_corpus.zenith --population 1 --type all  -o metrics.json

# Step 4: Visualizations
zenith visualize my_corpus.zenith --population 1  --type all --output-dir ./viz

# Step 5: Complete export
zenith export my_corpus.zenith --formats png pdf json --zip
```

---

## Zenith Language Specification

### 1. General Presentation
Zenith is a specialized language designed to structure and organize temporal textual corpora. It allows modeling temporal laws, events, and their relationships within an organized hierarchy.

### 2. Basic Structure

#### Law Example
```python
law LawName:
    start_date: YYYY-MM-DD at HH:MM
    period: number|dotted_number
    Event:
        event1: "description"
        event2: "description"
    GROUP:(event1 5.0^30 - event2 1.20.15^0)
end_law
```

#### Target Example
```python
target TargetName:
    key: "main_key"
    dictionnary:
        entry1: "description"
        entry2[index]: "description"
    # Nested blocks (laws or targets) but comments aren't allowed!
end_target
```

### 3. Syntax Components

#### Token Types
- **Structural keywords**: `law`, `target`, `end_law`, `end_target`
- **Sections**: `Event`, `GROUP`, `start_date`, `period`, `key`, `dictionnary`
- **Operators**: `:`, `^`, `-`, `(`, `)`, `[`, `]`
- **Data types**: `identifier`, `string`, `date`, `time`, `number`, `dotted_number`

#### AST Structure
```
corpus_textuel
├── law
│   ├── name
│   └── contents
│       ├── start_date (date + time)
│       ├── period
│       ├── events[]
│       └── group[]
└── target
    ├── name
    └── contents
        ├── key
        ├── dictionnary[]
        └── blocks[]
```

### 4. Complete Example
```python
target HistoricalProject:
    key: "industrial_revolution"
    dictionnary:
        innovation: "period of technical innovations"
        social: "major social changes"

    law MainPeriod:
        start_date: 1760-01-01 at 00:00:00
        period: 1.45
        Event:
            steam_engine[innovation]: "invention of the steam engine"
            textile[social]: "textile mechanization"
        GROUP:(steam_engine 30^0 - textile 1.15^0)
    end_law
end_target
```

---

## Advanced Features

### 1. ZenithMetrics
Advanced statistical analysis, pattern detection, and temporal characterization.

#### Key Methods:
- `calculate_temporal_statistics()`: Duration statistics
- `calculate_sequence_complexity()`: Sequence complexity scoring
- `detect_patterns()`: Pattern detection using Suffix Array O(n log n)
- `calculate_temporal_density()`: Event density in time
- `calculate_event_frequency()`: Event frequency counting

#### `calculate_temporal_statistics()`

Calculate temporal statistics of an event sequence.

Paramètres :

-	`simulations (List[Dict])` :List of event simulations

Retour :

```python
{
    "avg_duration": 45.2,
    "median_duration": 42.5,
    "min_duration": 10.0,
    "max_duration": 120.0,
    "duration_std": 25.3,
    "sum_duration": 904.0,
    "avg_dispersion": 15.8,
    "sum_dispersion": 158.0,
    "events_count": 20
}
```
Example :
```python
stats = metrics.calculate_temporal_statistics(simulations)
print(f"Durée moyenne: {stats['avg_duration']:.1f} minutes")
```

##### `calculate_rhythm_metrics()`

Analyze the temporal regularity between events.

Paramètres :

-	`simulations (List[Dict])` : List of event simulations

Retour :

```python
{
    "rhythm_consistency": 0.87,
    "avg_interval": 18.5,
    "interval_std": 5.2,
    "intervals": [15, 20, 16, ...]
}
```
Consistency index:
-	1.0 : Perfectly regular rhythm
-	0.0 : No discernible rhythm

 #### Complexity Analysis - `calculate_sequence_complexity()`

Evaluates the complexity of an event sequence.

Paramètres :

-	`simulations (List[Dict]) `: List of event simulations.

Retour :

```python
{
    "complexity_score": 78.5,
    "unique_events_ratio": 0.65,
    "transition_variety": 0.85,
    "unique_transitions_count": 42
}
```
Score formula :

`complexity_score = (unique_ratio * 0.4 + transition_variety * 0.6) * 100`

#### `calculate_entropy()`

Calculates the information entropy of the sequence.

Paramètres :

-	`simulations (List[Dict])` : List of event simulations.

Retour : float - Entropy in bits 

Exemple :
```python
entropy = metrics.calculate_entropy(simulations)
print(f"Entropie de la séquence: {entropy:.2f} bits")
```
#### Pattern Detection- `detect_patterns() ⚡ (Optimisé)`

Detects recurring patterns in event sequences.

Algorithm: Suffix Array + LCP in O(n log n)

Paramètres :

-	`simulations (List[Dict])` :List of event simulations.
-	`min_pattern_length (int, optionnel)` : Minimum pattern length (default: 2)

Retour :

```python
[
    {
        "pattern": ["eventA", "eventB", "eventC"],
        "occurrences": [(0, 3), (15, 18), (42, 45)],
        "length": 3
    },
]
```
Usage Example :

```python
patterns = metrics.detect_patterns(simulations, min_pattern_length=3)
for pattern in patterns:
    print(f"Motif '{' -> '.join(pattern['pattern'])}' trouvé {len(pattern['occurrences'])} fois")
```
#### Temporal Density - `calculate_temporal_density()`

It calculates the density of events over time.

Paramètres :

-	`simulations (List[Dict]) `: List of Simulations

Retour :
```python
{
    "temporal_density": 0.75,
    "coverage_ratio": 75.0,
    "total_simulation_time": 1200,
    "effective_event_time": 900
}
```
Formule :
`temporal_density = effective_event_time / total_simulation_time`

#### Event Frequencies- `calculate_event_frequency()`

It counts the frequency of each type of event.

Arguments :

-	`simulations (List[Dict]) `: List of Simulations
Retour :
```python
Dict[str, int] - Dictionary {event_name: frequency}
```
Example :
```python
freq = metrics.calculate_event_frequency(simulations)
for event, count in sorted(freq.items(), key=lambda x: x[1], reverse=True):
    print(f"{event}: {count} occurrences")
```


#### Example:
```python
from zenith_analyser.metrics import ZenithMetrics

metrics = ZenithMetrics(code_zenith)
simulations = metrics.law_description("TemporalLaw", population=3)["simulation"]
comprehensive = metrics.get_comprehensive_metrics(simulations)

print(f"Complexity Score: {comprehensive['sequence_complexity']['complexity_score']:.1f}")
print(f"Temporal Density: {comprehensive['temporal_density']['temporal_density']:.2f}")
```

### 2. ZenithVisualizer
Comprehensive visualization of temporal data.

#### Key Methods:
- `plot_duration_histogram()`: Duration distribution
- `plot_event_pie_chart()`: Event proportion
- `plot_sequence_scatter()`: Temporal sequence scatter plot
- `plot_timeline()`: Event timeline
- `create_all_plots()`: Generate all visualizations at once

#### Example:
```python
from zenith_analyser.visuals import ZenithVisualizer

visualizer = ZenithVisualizer(metrics)

# Generate all plots
files = visualizer.create_all_plots(
    simulations,
    metrics_data=metrics_data,
    prefix="analysis_law",
    output_dir="./visualizations"
)
```

---

## Examples

### Example 1: Complete Historical Analysis
```bash
# 1. Complete corpus analysis (JSON format)
zenith analyze data/corpus.zenith --format json --pretty -o outputs/analyse_brute.json

# 2. Analysis in readable text format
zenith analyze data/corpus.zenith --population 1 --format text -o outputs/analyse_lisible.txt

# 3. Analysis in YAML format (if pyyaml is installed)
zenith analyze data/corpus.zenith --population 1 --format yaml -o outputs/analyse.yaml

# 4. Analysis of a specific law
zenith analyze data/corpus.zenith --law "session_matin" --format json -o outputs/loi_session_matin.json

# 5. Analysis of a specific target
zenith analyze data/corpus.zenith --target "projet_web" -o outputs/cible_projet_web.json

# 6. Analysis by population level
zenith analyze data/corpus.zenith --population 2 -o outputs/population_niveau2.json

# 7. Analysis from stdin via pipe
cat data/corpus.zenith | zenith analyze - --format json | ConvertFrom-Json | Select-Object -ExpandProperty corpus_statistics | ConvertTo-Json

# 8. All corpus metrics
zenith metrics data/corpus.zenith --population 2 --type all --format json --pretty -o metrics/toutes_metriques.json

# 9. Temporal metrics in CSV format
zenith metrics data/corpus.zenith --population 2 --type temporal --format csv -o metrics/metriques_temporelles.csv

# 10. Complexity metrics
zenith metrics data/corpus.zenith --population 2 --type complexity --detailed -o metrics/complexite_detaillee.json

# 11. Density metrics
zenith metrics data/corpus.zenith --population 2  --type density --format json -o metrics/densite.json

# 12. Rhythm metrics
zenith metrics data/corpus.zenith --population 2 --type rhythm -o metrics/rythme.json

# 13. Entropy metrics
zenith metrics data/corpus.zenith --population 2  --type entropy --format yaml -o metrics/entropie.yml

# 14. Pattern detection
zenith metrics data/corpus.zenith --population 2  --type patterns --format json --pretty -o metrics/motifs.json

# 15. Metrics for a specific population
zenith metrics data/corpus.zenith  --population 3 --type all -o metrics/population3_metriques.json

# 16. Metrics for a specific law
zenith metrics data/corpus.zenith --law "reunion_equipe" --type all -o metrics/loi_reunion.json

# 17. Duration histogram
zenith visualize data/corpus.zenith --target "developpement" --type histogram --width 1600 --height 900 -o visualizations/histogramme_durees.png --title "Distribution des Durées"

# 18. Event timeline
zenith visualize data/corpus.zenith --type timeline --population 2 -o visualizations/timeline_population2.svg --format svg

# 19. Event pie chart
zenith visualize data/corpus.zenith --type pie --target "zenith" -o visualizations/repartition_sante.pdf --format pdf

# 20. Sequence scatter plot
zenith visualize data/corpus.zenith --type scatter --law "sprint_1"  -o visualizations/scatter_sprint1.jpg

# 21. Metrics summary
zenith visualize data/corpus.zenith --type summary --population 1 -o visualizations/resume_metriques.png

# 22. Event frequency
zenith visualize data/corpus.zenith --type frequency --law "sprint_1" -o visualizations/frequence_evenements.png

# 23. All visualizations at once
zenith visualize data/corpus.zenith --population 1 --type all  --width 1400 --height 800 --title "Analyse Complète du Corpus"

# 24. Complete export (data + visuals)
zenith export data/corpus.zenith --population 1 --output-dir exports/complete --formats png json csv --resolution 300 --zip

# 25. Target-specific export
zenith export data/corpus.zenith --target "developpement" --output-dir exports/developpement --formats pdf json --zip

# 26. Zenith → JSON conversion
zenith convert data/corpus.zenith exports/corpus.json --from zenith --to json

# 27. JSON → Zenith conversion
zenith convert exports/ast.json exports/reconstructed.zenith --from json --to zenith

# 28. Unparse from AST
zenith unparse data/ast_template.json -o exports/code_regenere.zenith --format

# 29. Comparison of two corpora
zenith compare data/corpusv1.zenith data/corpusv2.zenith --labels "Version 1.0" "Version 2.0" --format json -o comparisons/v1_v2.json

# 30. Population comparison
zenith compare data/corpus.zenith data/corpus_optimise.zenith --population 2  --format text --output comparisons/populations_diff.txt

# 31. Automated analysis pipeline
zenith validate data/corpus.zenith --strict 
zenith analyze data/corpus.zenith --population 1 --pretty > analysis/full_analysis.json 
zenith metrics data/corpus.zenith  --population 1 --type all > analysis/metrics.json 
zenith export data/corpus.zenith --population 1 --output-dir analysis/export --zip
```

### Example 2: Python Integration
```python
import subprocess
import json

# Execute zenith from Python
result = subprocess.run(
    ["zenith", "analyze", "corpus.zenith", "--format", "json"],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)

# Process the data
print(f"Total events: {data['corpus_statistics']['total_events']}")
print(f"Total duration: {data['corpus_statistics']['total_duration_minutes']} minutes")
```

### Example 3: Example analysis with metrics
```python
import json
from zenith_analyser.metrics import ZenithMetrics
from zenith_analyser.utils import load_corpus

corpus = load_corpus("Corpus_Zenith.zth")
metrics = ZenithMetrics(corpus)

simulations = metrics.target_description("maitrise_soi")["simulation"]
statistics = metrics.calculate_temporal_statistics(simulations)
print(json.dumps(statistics, indent=4))

# event frequency
frequencies = metrics.calculate_event_frequency(simulations)
print(json.dumps(frequencies, indent=4))

# sequence complexity
sequences = metrics.calculate_sequence_complexity(simulations)
print(json.dumps(sequences, indent=4))

#temporal density

temporal = metrics.calculate_temporal_density(simulations)
print(json.dumps(temporal, indent=4))

# rhythms
rhythms = metrics.calculate_rhythm_metrics(simulations)
print(json.dumps(rhythms, indent=4))

# patterns
patterns = metrics.detect_patterns(simulations)
print(json.dumps(patterns, indent=4))

# entropy
entropy = metrics.calculate_entropy(simulations)
print(json.dumps(entropy, indent=4))

# all metrics for target
metrics_target = metrics.get_metrics_target("maitrise_soi")
print(json.dumps(metrics_target, indent=4))

# all metrics for population
metrics_population = metrics.get_metrics_population(3)
print(json.dumps(metrics_population, indent=4))

#  all metrics for law
metrics_law = metrics.get_metrics_law("a2026_01_04_05_15",5)
print(json.dumps(metrics_law, indent=4))

# get data with pandas
data_target = metrics.get_data_population(3)
print(data_target)
```

### Example 4: Example analysis with visualisations

```python
from zenith_analyser.metrics import ZenithMetrics
from zenith_analyser.visuals import ZenithVisualizer,create_simple_plot
from zenith_analyser.utils import load_corpus

corpus = load_corpus("Corpus_Zenith.zth")
metrics = ZenithMetrics(corpus)
visual = ZenithVisualizer(metrics)

#plot duration histogram
simulations = metrics.target_description("vie_equilibre")["simulation"]
visual.plot_duration_histogram(simulations=simulations,title="Duration histogram") # you can save path

# plot  event_pie chart
visual.plot_event_pie_chart(simulations=simulations, title="Event pie chart.")

# plot sequence sactter
visual.plot_sequence_scatter(simulations=simulations)

# plot timeline
simu = metrics.target_description("developpement")["simulation"]
visual.plot_timeline(simulations=simu)


#plot metrics summary
metrics_ = metrics.get_metrics_target("vie_equilibre")
visual.plot_metrics_summary(metrics_)

#plot event frequency
visual.plot_event_frequency(simulations=simulations)

#create all plots
visual.create_all_plots(simulations=simulations, metrics_data=metrics_)

#comparison
simulations_1 = metrics.target_description("maitrise_soi")['simulation']
simulations_2 = metrics.target_description("developpement")['simulation']

visual.plot_simple_comparison(simulations_list=[simulations_1,simulations_2], labels=["maitrise_soi","developpement"])

#simple plot
data = metrics.get_data_target("vie_equilibre")
create_simple_plot(data=data["coherence"],plot_type="line")
create_simple_plot(data=data["coherence"],plot_type="bar")
create_simple_plot(data=data["coherence"],plot_type="scatter")
```

---

## Installation

### Basic Installation
```bash
pip install zenith-analyser
```

### Development Installation
```bash
git clone https://github.com/frasasu/zenith-analyser.git
cd zenith-analyser
pip install -e ".[dev]"
```

---

## Conclusion

Zenith-Analyser provides a comprehensive framework for temporal management and analysis. By distinguishing between generations (structural hierarchy) and populations (contextual activity), it offers unique insights into time allocation and objective management.

### Key Benefits:
1. **Structural Clarity**: Clear separation between objective hierarchy and active context
2. **Temporal Precision**: Accurate modeling of time allocation with chronocoherence/dispersal
3. **Analytical Depth**: Advanced metrics for complexity, rhythm, and pattern analysis
4. **Visual Insight**: Comprehensive visualization of temporal structures
5. **Workflow Integration**: Full CLI and Python API for seamless integration

### Use Cases:
- **Personal Time Management**: Plan and analyze daily/weekly activities
- **Project Management**: Structure objectives and track temporal investment
- **Research Analysis**: Model historical or sequential processes
- **Process Optimization**: Identify temporal patterns and inefficiencies

For more information, examples, and contributions, visit the [GitHub repository](https://github.com/frasasu/zenith-analyser).
