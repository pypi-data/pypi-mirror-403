# Copyright 2026 François TUMUSAVYEYESU.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import sys
import os
import csv
import io
from typing import Optional, List, Dict, Any
from datetime import datetime

from . import ASTUnparser, Validator, ZenithAnalyser, ZenithMetrics
from . import ZenithVisualizer, __version__, __author__, __license__
from .exceptions import (
    ZenithAnalyserError,
    ZenithError,
    ZenithLexerError,
    ZenithParserError,
)


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    try:
        if args.command == "analyze":
            analyze_command(args)
        elif args.command == "validate":
            validate_command(args)
        elif args.command == "unparse":
            unparse_command(args)
        elif args.command == "convert":
            convert_command(args)
        elif args.command == "version":
            version_command()
        elif args.command == "metrics":
            metrics_command(args)
        elif args.command == "visualize":
            visualize_command(args)
        elif args.command == "export":
            export_command(args)
        elif args.command == "compare":
            compare_command(args)
        else:
            parser.print_help()
            sys.exit(1)

    except ZenithError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Zenith Analyser - Analyze structured temporal laws",
        epilog="See https://github.com/frasasu/zenith-analyser for more.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze Zenith code")
    analyze_parser.add_argument("input", help="Input file or - for stdin")
    analyze_parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    analyze_parser.add_argument(
        "--format",
        choices=["json", "yaml", "text"],
        default="json",
        help="Output format",
    )
    analyze_parser.add_argument("--law", help="Analyze specific law")
    analyze_parser.add_argument("--target", help="Analyze specific target")
    analyze_parser.add_argument(
        "--population", type=int, default=-1,
        help="Population level (-1 for max)"
    )
    analyze_parser.add_argument(
        "--pretty", action="store_true", help="Pretty print JSON output"
    )

    validate_parser = subparsers.add_parser("validate", help="Validate Zenith code")
    validate_parser.add_argument("input", help="Input file or - for stdin")
    validate_parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )

    unparse_parser = subparsers.add_parser("unparse", help="Convert AST to Zenith")
    unparse_parser.add_argument("input", help="Input JSON file")
    unparse_parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    unparse_parser.add_argument(
        "--format", action="store_true", help="Format output code"
    )

    convert_parser = subparsers.add_parser("convert", help="Convert between formats")
    convert_parser.add_argument("input", help="Input file")
    convert_parser.add_argument("output", help="Output file")
    convert_parser.add_argument(
        "--from",
        dest="from_format",
        choices=["zenith", "json"],
        default="zenith",
        help="Input format",
    )
    convert_parser.add_argument(
        "--to", choices=["zenith", "json"], default="json", help="Output format"
    )

    subparsers.add_parser("version", help="Show version information")

    metrics_parser = subparsers.add_parser("metrics", help="Calculate metrics")
    metrics_parser.add_argument("input", help="Input file or - for stdin")
    metrics_parser.add_argument(
        "--type",
        choices=["all", "temporal", "complexity", "density",
                 "rhythm", "entropy", "patterns"],
        default="all",
        help="Type of metrics to calculate"
    )
    metrics_parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    metrics_parser.add_argument(
        "--format",
        choices=["json", "yaml", "text", "csv"],
        default="json",
        help="Output format",
    )
    metrics_parser.add_argument("--law", help="Analyze specific law")
    metrics_parser.add_argument("--target", help="Analyze specific target")
    metrics_parser.add_argument(
        "--population", type=int, default=-1,
        help="Population level (-1 for max)"
    )
    metrics_parser.add_argument(
        "--pretty", action="store_true", help="Pretty print JSON output"
    )
    metrics_parser.add_argument(
        "--detailed", action="store_true", help="Show detailed metrics breakdown"
    )

    visualize_parser = subparsers.add_parser(
        "visualize", help="Create visualizations"
    )
    visualize_parser.add_argument("input", help="Input file or - for stdin")
    visualize_parser.add_argument(
        "--type",
        choices=["histogram", "pie", "scatter", "timeline", 
                 "summary", "frequency", "all"],
        default="histogram",
        help="Type of visualization"
    )
    visualize_parser.add_argument("-o", "--output", help="Output file")
    visualize_parser.add_argument(
        "--format",
        choices=["png", "jpg", "svg", "pdf"],
        default="png",
        help="Output format",
    )
    visualize_parser.add_argument("--law", help="Visualize specific law")
    visualize_parser.add_argument("--target", help="Visualize specific target")
    visualize_parser.add_argument(
        "--population", type=int, default=-1,
        help="Population level (-1 for max)"
    )
    visualize_parser.add_argument(
        "--width", type=int, default=1200, help="Image width in pixels"
    )
    visualize_parser.add_argument(
        "--height", type=int, default=800, help="Image height in pixels"
    )
    visualize_parser.add_argument(
        "--title", help="Custom title for visualization"
    )

    export_parser = subparsers.add_parser(
        "export", help="Export data and visualizations"
    )
    export_parser.add_argument("input", help="Input file or - for stdin")
    export_parser.add_argument(
        "-o", "--output-dir",
        default="./zenith_export",
        help="Output directory (default: ./zenith_export)"
    )
    export_parser.add_argument(
        "--formats",
        nargs="+",
        choices=["png", "pdf", "json", "csv"],
        default=["png", "json"],
        help="Formats to export"
    )
    export_parser.add_argument("--law", help="Export specific law")
    export_parser.add_argument("--target", help="Export specific target")
    export_parser.add_argument(
        "--population", type=int, default=-1,
        help="Population level (-1 for max)"
    )
    export_parser.add_argument(
        "--resolution", type=int, default=300, help="Image resolution in DPI"
    )
    export_parser.add_argument(
        "--zip", action="store_true", help="Create ZIP archive of exported files"
    )

    compare_parser = subparsers.add_parser("compare", help="Compare multiple analyses")
    compare_parser.add_argument(
        "inputs",
        nargs="+",
        help="Input files to compare"
    )
    compare_parser.add_argument(
        "-o", "--output",
        help="Output file (default: stdout)"
    )
    compare_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format",
    )
    compare_parser.add_argument(
        "--labels",
        nargs="+",
        help="Labels for each input (must match number of inputs)"
    )
    compare_parser.add_argument(
        "--population", type=int, default=-1,
        help="Population level (-1 for max)"
    )
    compare_parser.add_argument(
        "--visualize", action="store_true", help="Generate comparison visualizations"
    )

    return parser


def analyze_command(args: argparse.Namespace) -> None:
    code = read_input(args.input)

    try:
        analyser = ZenithAnalyser(code)

        if args.law:
            result = analyser.law_description(args.law, args.population)
        elif args.target:
            result = analyser.target_description(args.target)
        elif args.population != -1:
            result = analyser.population_description(args.population)
        else:
            result = analyser.analyze_corpus()

        output = format_output(result, args.format, args.pretty)
        write_output(output, args.output)

    except (ZenithLexerError, ZenithParserError, ZenithAnalyserError) as e:
        print(f"Analysis error: {e}", file=sys.stderr)
        sys.exit(1)


def validate_command(args: argparse.Namespace) -> None:
    code = read_input(args.input)

    validator = Validator()
    errors = validator.validate_code(code)

    if errors:
        print(f"Validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)

        if args.strict:
            sys.exit(1)
    else:
        print("✓ Validation passed", file=sys.stderr)

    warnings = validator.warnings
    if warnings:
        print(f"Found {len(warnings)} warning(s):", file=sys.stderr)
        for warning in warnings:
            print(f"  ⚠ {warning}", file=sys.stderr)


def unparse_command(args: argparse.Namespace) -> None:
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            ast = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Failed to read AST: {e}", file=sys.stderr)
        sys.exit(1)

    unparser = ASTUnparser(ast)
    code = unparser.unparse()

    if args.format:
        code = unparser.format_code(code)

    write_output(code, args.output)


def convert_command(args: argparse.Namespace) -> None:
    if args.from_format == "zenith" and args.to == "json":
        code = read_input(args.input)
        analyser = ZenithAnalyser(code)
        result = analyser.analyze_corpus()

        try:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"✓ Converted to {args.output}", file=sys.stderr)
        except IOError as e:
            print(f"Failed to write output: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.from_format == "json" and args.to == "zenith":
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                ast = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Failed to read JSON: {e}", file=sys.stderr)
            sys.exit(1)

        unparser = ASTUnparser(ast)
        code = unparser.unparse()

        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"✓ Converted to {args.output}", file=sys.stderr)
        except IOError as e:
            print(f"Failed to write output: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(
            f"Conversion from {args.from_format} to {args.to} not supported",
            file=sys.stderr,
        )
        sys.exit(1)


def version_command() -> None:
    print(f"Zenith Analyser v{__version__}")
    print(f"Author: {__author__}")
    print(f"License: {__license__}")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")


def metrics_command(args: argparse.Namespace) -> None:
    code = read_input(args.input)

    try:
        analyser = ZenithAnalyser(code)
        metrics_calculator = ZenithMetrics(code)

        if args.law:
            data = analyser.law_description(args.law, args.population)
            simulations = data["simulation"]
            source_name = f"Law: {args.law}"
        elif args.target:
            data = analyser.target_description(args.target)
            simulations = data["simulation"]
            source_name = f"Target: {args.target}"
        elif args.population != -1:
            data = analyser.population_description(args.population)
            simulations = data["simulation"]
            source_name = f"Population: {args.population}"
        else:
            corpus = analyser.analyze_corpus()
            simulations = []
            for law in corpus.get("laws", []):
                if "simulation" in law:
                    simulations.extend(law["simulation"])
            source_name = "Full Corpus"

        if not simulations:
            print("No simulations found to analyze", file=sys.stderr)
            sys.exit(1)

        if args.type == "all":
            result = metrics_calculator.get_comprehensive_metrics(simulations)
        elif args.type == "temporal":
            result = metrics_calculator.calculate_temporal_statistics(simulations)
        elif args.type == "complexity":
            result = metrics_calculator.calculate_sequence_complexity(simulations)
        elif args.type == "density":
            result = metrics_calculator.calculate_temporal_density(simulations)
        elif args.type == "rhythm":
            result = metrics_calculator.calculate_rhythm_metrics(simulations)
        elif args.type == "entropy":
            result = metrics_calculator.calculate_entropy(simulations)
        elif args.type == "patterns":
            result = metrics_calculator.detect_patterns(simulations)

        if isinstance(result, dict):
            result["_metadata"] = {
                "source": source_name,
                "event_count": len(simulations),
                "calculation_date": datetime.now().isoformat(),
                "metrics_type": args.type
            }

        if args.format == "csv":
            output = format_metrics_csv(result, args.detailed)
        else:
            output = format_output(result, args.format, args.pretty)

        write_output(output, args.output)

        print(f"✓ Calculated {args.type} metrics for {source_name}", file=sys.stderr)
        print(f"  Events analyzed: {len(simulations)}", file=sys.stderr)

    except Exception as e:
        print(f"Metrics calculation error: {e}", file=sys.stderr)
        sys.exit(1)


def visualize_command(args: argparse.Namespace) -> None:
    code = read_input(args.input)

    try:
        analyser = ZenithAnalyser(code)
        metrics = ZenithMetrics(code)
        visualizer = ZenithVisualizer(metrics)

        if args.law:
            data = analyser.law_description(args.law, args.population)
            simulations = data["simulation"]
            default_title = f"Visualization - Law: {args.law}"
        elif args.target:
            data = analyser.target_description(args.target)
            simulations = data["simulation"]
            default_title = f"Visualization - Target: {args.target}"
        elif args.population != -1:
            data = analyser.population_description(args.population)
            simulations = data["simulation"]
            default_title = f"Visualization - Population: {args.population}"
        else:
            corpus = analyser.analyze_corpus()
            simulations = []
            for law in corpus.get("laws", []):
                if "simulation" in law:
                    simulations.extend(law["simulation"])
            default_title = "Visualization - Full Corpus"

        if not simulations:
            print("No simulations found to visualize", file=sys.stderr)
            sys.exit(1)

        title = args.title or default_title

        # Create output path
        if args.output:
            output_path = args.output
            if not output_path.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.pdf')):
                output_path = f"{output_path}.{args.format}"
        else:
            output_path = None

        # Create the visualization based on type
        if args.type == "histogram" or args.type == "all":
            visualizer.plot_duration_histogram(
                simulations,
                title=f"{title} - Duration Histogram",
                save_path=output_path if args.type == "histogram" else None
            )

        if args.type == "pie" or args.type == "all":
            visualizer.plot_event_pie_chart(
                simulations,
                title=f"{title} - Event Distribution",
                save_path=output_path if args.type == "pie" else None
            )

        if args.type == "scatter" or args.type == "all":
            visualizer.plot_sequence_scatter(
                simulations,
                title=f"{title} - Event Sequence",
                save_path=output_path if args.type == "scatter" else None
            )

        if args.type == "timeline" or args.type == "all":
            visualizer.plot_timeline(
                simulations,
                title=f"{title} - Timeline",
                save_path=output_path if args.type == "timeline" else None
            )

        if args.type == "summary" or args.type == "all":
            metrics_data = metrics.get_comprehensive_metrics(simulations)
            visualizer.plot_metrics_summary(
                metrics_data,
                title=f"{title} - Metrics Summary",
                save_path=output_path if args.type == "summary" else None
            )

        if args.type == "frequency" or args.type == "all":
            visualizer.plot_event_frequency(
                simulations,
                title=f"{title} - Event Frequency",
                save_path=output_path if args.type == "frequency" else None
            )

        # If specific type was requested and output path was given
        if args.type != "all" and output_path:
            print(f"✓ Visualization saved to {output_path}", file=sys.stderr)
        elif args.type == "all":
            print(f"✓ Created all visualizations", file=sys.stderr)
        else:
            print("✓ Visualizations displayed", file=sys.stderr)

    except Exception as e:
        print(f"Visualization error: {e}", file=sys.stderr)
        sys.exit(1)


def export_command(args: argparse.Namespace) -> None:
    code = read_input(args.input)

    try:
        analyser = ZenithAnalyser(code)
        metrics = ZenithMetrics(code)
        visualizer = ZenithVisualizer(metrics)

        if args.law:
            data = analyser.law_description(args.law, args.population)
            simulations = data["simulation"]
            export_prefix = f"law_{args.law}"
        elif args.target:
            data = analyser.target_description(args.target)
            simulations = data["simulation"]
            export_prefix = f"target_{args.target}"
        elif args.population != -1:
            data = analyser.population_description(args.population)
            simulations = data["simulation"]
            export_prefix = f"population_{args.population}"
        else:
            corpus = analyser.analyze_corpus()
            simulations = []
            for law in corpus.get("laws", []):
                if "simulation" in law:
                    simulations.extend(law["simulation"])
            export_prefix = "corpus"

        if not simulations:
            print("No simulations found to export", file=sys.stderr)
            sys.exit(1)

        os.makedirs(args.output_dir, exist_ok=True)

        print(f"Exporting to: {args.output_dir}", file=sys.stderr)

        exported_files = []

        # Export metrics as JSON
        if "json" in args.formats:
            metrics_data = metrics.get_comprehensive_metrics(simulations)
            json_path = os.path.join(args.output_dir, f"{export_prefix}_metrics.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2)
            exported_files.append(json_path)
            print(f"  ✓ Metrics exported to {json_path}", file=sys.stderr)

        # Export metrics as CSV
        if "csv" in args.formats:
            metrics_data = metrics.get_comprehensive_metrics(simulations)
            csv_path = os.path.join(args.output_dir, f"{export_prefix}_metrics.csv")
            csv_content = format_metrics_csv(metrics_data, detailed=True)
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_content)
            exported_files.append(csv_path)
            print(f"  ✓ Metrics exported to {csv_path}", file=sys.stderr)

        # Export visualizations
        if any(fmt in args.formats for fmt in ["png", "pdf", "svg"]):
            # Create all plots
            saved_files = visualizer.create_all_plots(
                simulations,
                metrics_data=metrics.get_comprehensive_metrics(simulations) if "json" not in args.formats else None,
                prefix=export_prefix,
                output_dir=args.output_dir
            )
            exported_files.extend(saved_files)

        # Create ZIP archive if requested
        if args.zip and exported_files:
            import zipfile
            zip_path = os.path.join(args.output_dir, f"{export_prefix}_export.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in exported_files:
                    zipf.write(file, os.path.relpath(file, args.output_dir))
            print(f"✓ ZIP archive created: {zip_path}", file=sys.stderr)

        print(f"✓ Export completed", file=sys.stderr)
        print(f"  Files exported: {len(exported_files)}", file=sys.stderr)

    except Exception as e:
        print(f"Export error: {e}", file=sys.stderr)
        sys.exit(1)


def compare_command(args: argparse.Namespace) -> None:
    if args.labels and len(args.labels) != len(args.inputs):
        print("Number of labels must match number of inputs", file=sys.stderr)
        sys.exit(1)

    try:
        comparisons = []
        labels = args.labels or [f"Input_{i+1}" for i in range(len(args.inputs))]

        for i, input_file in enumerate(args.inputs):
            code = read_input(input_file)
            analyser = ZenithAnalyser(code)
            metrics = ZenithMetrics(code)

            simulations = []
            if args.population != -1:
               data = analyser.population_description(args.population)
               simulations = data["simulation"]
            else:
                data = analyser.population_description(args.population)
                simulations = data["simulation"]


            metrics_data = metrics.get_comprehensive_metrics(simulations)

            comparisons.append({
                "label": labels[i],
                "file": input_file,
                "event_count": len(simulations),
                "metrics": metrics_data
            })

        if args.format == "json":
            output = json.dumps({"comparisons": comparisons}, indent=2)
        else:
            output = generate_comparison_text(comparisons,args.population)

        write_output(output, args.output)

        if args.visualize:
            generate_comparison_visualizations(comparisons, args.population)

        print(f"✓ Compared {len(comparisons)} inputs", file=sys.stderr)

    except Exception as e:
        print(f"Comparison error: {e}", file=sys.stderr)
        sys.exit(1)


def read_input(input_spec: str) -> str:
    if input_spec == "-":
        return sys.stdin.read()
    else:
        try:
            with open(input_spec, "r", encoding="utf-8") as f:
                return f.read()
        except IOError as e:
            print(f"Failed to read input: {e}", file=sys.stderr)
            sys.exit(1)


def write_output(output: str, output_spec: Optional[str]) -> None:
    if output_spec:
        try:
            with open(output_spec, "w", encoding="utf-8") as f:
                f.write(output)
        except IOError as e:
            print(f"Failed to write output: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        sys.stdout.write(output)


def format_output(result: Any, format_type: str, pretty: bool) -> str:
    if format_type == "json":
        indent = 2 if pretty else None
        return json.dumps(result, indent=indent, default=str)
    elif format_type == "yaml":
        try:
            import yaml
            return yaml.dump(result, default_flow_style=False)
        except ImportError:
            print(
                "YAML format requires PyYAML. Install with: pip install pyyaml",
                file=sys.stderr,
            )
            sys.exit(1)
    elif format_type == "csv":
        return format_metrics_csv(result, detailed=False)
    else:
        return format_text_output(result)


def format_text_output(result: Any) -> str:
    lines = []
    if not isinstance(result, dict):
        lines.append("Metric type:Entropie")
        lines.append(f"Metric value:{result}")
        return "\n".join(lines)

    if "name" in result:
        lines.append(f"Name: {result['name']}")
        lines.append(
            f"Start: {result.get('start_datetime', {}).get('date', 'N/A')} "
            f"at {result.get('start_datetime', {}).get('time', 'N/A')}"
        )
        lines.append(f"Duration: {result.get('sum_duration', 0)} minutes")
        lines.append(f"Events: {result.get('event_count', 0)}")
        lines.append("")

        if "simulation" in result:
            lines.append("Event Simulation:")
            for event in result["simulation"]:
                lines.append(
                    f"  {event.get('event_name', 'N/A')}: "
                    f"{event.get('start', {}).get('date', 'N/A')} at "
                    f"{event.get('start', {}).get('time', 'N/A')} - "
                    f"{event.get('end', {}).get('date', 'N/A')} at "
                    f"{event.get('end', {}).get('time', 'N/A')} "
                    f"({event.get('duration_minutes', 0)} min)"
                )

    elif "corpus_statistics" in result:
        stats = result["corpus_statistics"]
        lines.append("Corpus Statistics:")
        lines.append(f"  Total Laws: {stats.get('total_laws', 0)}")
        lines.append(f"  Total Targets: {stats.get('total_targets', 0)}")
        lines.append(f"  Total Events: {stats.get('total_events', 0)}")
        lines.append(
            f"  Total Duration: {stats.get('sum_duration', 0)} minutes"
        )

    return "\n".join(lines)


def format_metrics_csv(metrics: Any, detailed: bool = False) -> str:
    output = io.StringIO()
    writer = csv.writer(output)

    if not isinstance(metrics, dict):
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Entropy", metrics])
        return output.getvalue()

    if detailed:
        writer.writerow(["Metric Category", "Metric Name", "Value", "Unit"])

        if "temporal_statistics" in metrics:
            temp = metrics["temporal_statistics"]
            writer.writerow(["Temporal", "Average Duration",
                           temp.get("avg_duration", 0), "minutes"])
            writer.writerow(["Temporal", "Max Duration",
                           temp.get("max_duration", 0), "minutes"])
            writer.writerow(["Temporal", "Total Duration",
                           temp.get("sum_duration", 0), "minutes"])
            writer.writerow(["Temporal", "Average Interval",
                           temp.get("avg_dispersion", 0), "minutes"])

        if "sequence_complexity" in metrics:
            comp = metrics["sequence_complexity"]
            writer.writerow(["Complexity", "Complexity Score",
                           comp.get("complexity_score", 0), "0-100"])
            writer.writerow(["Complexity", "Unique Events Ratio",
                           comp.get("unique_events_ratio", 0), "ratio"])

        if "temporal_density" in metrics:
            dens = metrics["temporal_density"]
            writer.writerow(["Density", "Temporal Density",
                           dens.get("temporal_density", 0), "ratio"])
            writer.writerow(["Density", "Coverage Ratio",
                           dens.get("coverage_ratio", 0), "percentage"])

        if "entropy" in metrics:
            writer.writerow(["Entropy", "Sequence Entropy",
                           metrics["entropy"], "bits"])

        if "patterns_detected" in metrics:
            patterns = metrics["patterns_detected"]
            writer.writerow(["Patterns", "Patterns Detected",
                           len(patterns), "count"])
    else:
        writer.writerow(["Metric", "Value"])

        if "temporal_statistics" in metrics:
            temp = metrics["temporal_statistics"]
            writer.writerow(["Average Duration (min)",
                           temp.get("avg_duration", 0)])
            writer.writerow(["Total Duration (min)",
                           temp.get("sum_duration", 0)])
            writer.writerow(["Event Count", temp.get("events_count", 0)])

        if "sequence_complexity" in metrics:
            comp = metrics["sequence_complexity"]
            writer.writerow(["Complexity Score",
                           comp.get("complexity_score", 0)])



    return output.getvalue()


def generate_comparison_text(comparisons: List[Dict],compare_population:Any) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("ZENITH COMPARISON REPORT")
    lines.append("=" * 80)
    lines.append(f"Comparison key:{compare_population}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Comparisons: {len(comparisons)}")
    lines.append("")

    header = ["Metric"] + [comp["label"] for comp in comparisons]
    lines.append(" | ".join(header))
    lines.append("-" * (sum(len(h) for h in header) + 3 * len(header)))

    metrics_to_compare = [
        ("Events", lambda c: c.get("event_count", 0)),
        ("Avg Dur (min)", lambda c: c["metrics"].get("temporal_statistics", {})
         .get("avg_duration", 0) if "temporal_statistics" in c["metrics"] else 0),
        ("Complexity", lambda c: c["metrics"].get("sequence_complexity", {})
         .get("complexity_score", 0) if "sequence_complexity" in c["metrics"] else 0),
        ("Density", lambda c: c["metrics"].get("temporal_density", {})
         .get("temporal_density", 0) if "temporal_density" in c["metrics"] else 0),
        ("Entropy", lambda c: c["metrics"].get("entropy", 0))
    ]

    for metric_name, extractor in metrics_to_compare:
        row = [metric_name]
        for comp in comparisons:
            value = extractor(comp)
            if isinstance(value, float):
                row.append(f"{value:.2f}")
            else:
                row.append(str(value))
        lines.append(" | ".join(row))

    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)


def generate_comparison_visualizations(comparisons: List[Dict],
                                       compare_population: Any) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        labels = [comp["label"] for comp in comparisons]

        metrics_data = {
            "Event Count": [comp.get("event_count", 0) for comp in comparisons],
            "Avg Duration": [comp["metrics"].get("temporal_statistics", {})
                           .get("avg_duration", 0)
                           if "temporal_statistics" in comp["metrics"] else 0
                           for comp in comparisons],
            "Complexity Score": [comp["metrics"].get("sequence_complexity", {})
                               .get("complexity_score", 0)
                               if "sequence_complexity" in comp["metrics"] else 0
                               for comp in comparisons]
        }

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        x = np.arange(len(labels))
        width = 0.6

        colors = ['#2E86AB', '#A23B72', '#F18F01']

        for idx, (metric_name, values) in enumerate(metrics_data.items()):
            ax = axes[idx]
            bars = ax.bar(x, values, width,
                         color=colors[idx % len(colors)], alpha=0.7)
            ax.set_xlabel('Inputs')
            ax.set_ylabel(metric_name)
            ax.set_title(metric_name)
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45)

            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{height:.1f}', ha='center', va='bottom', fontsize=9)

        plt.suptitle(f'Zenith Comparison - {compare_population}',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"zenith_comparison_{compare_population}_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Comparison visualization saved: {filename}", file=sys.stderr)

    except ImportError:
        print("Comparison visualizations require matplotlib", file=sys.stderr)


if __name__ == "__main__":
    main()