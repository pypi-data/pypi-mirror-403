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

"""
Simple visualizations for Zenith Metrics.
Uses matplotlib to create basic charts.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Optional
from .metrics import ZenithMetrics


class ZenithVisualizer:
    """
    Simple class for creating visualizations from Zenith metrics.
    """

    def __init__(self, metrics: ZenithMetrics):
        """
        Initialize the visualizer with a metrics object.

        Args:
            metrics: Instance of ZenithMetrics
        """
        self.metrics = metrics

    def plot_duration_histogram(self, simulations: List[Dict[str, Any]],
                                title: str = "Duration Distribution",
                                save_path: Optional[str] = None) -> None:
        """
        Creates a simple histogram of durations.

        Args:
            simulations: List of simulations
            title: Chart title
            save_path: Path to save the image
        """

        durations = [sim["duration_minutes"] for sim in simulations]


        plt.figure(figsize=(10, 6))

        plt.hist(durations, bins=10, edgecolor='black', alpha=0.7, color='skyblue')

        avg_duration = sum(durations) / len(durations)
        plt.axvline(avg_duration, color='red', linestyle='--',
                   label=f'Average: {avg_duration:.1f} min')

        plt.xlabel('Duration (minutes)', fontsize=12)
        plt.ylabel('Number of Events', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_event_pie_chart(self, simulations: List[Dict[str, Any]],
                             title: str = "Event Distribution",
                             save_path: Optional[str] = None) -> None:
        """
        Creates a pie chart of event types.

        Args:
            simulations: List of simulations
            title: Chart title
            save_path: Path to save the image
        """

        events = [sim["event_name"] for sim in simulations]
        unique_events = {}

        for event in events:
            if event in unique_events:
                unique_events[event] += 1
            else:
                unique_events[event] = 1

        labels = list(unique_events.keys())
        sizes = list(unique_events.values())

        plt.figure(figsize=(10, 8))

        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=colors,
                                          autopct='%1.1f%%', startangle=90)

        plt.title(title, fontsize=14, fontweight='bold', pad=20)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_sequence_scatter(self, simulations: List[Dict[str, Any]],
                              title: str = "Event Sequence",
                              save_path: Optional[str] = None) -> None:
        """
        Creates a scatter plot of the sequence.

        Args:
            simulations: List of simulations
            title: Chart title
            save_path: Path to save the image
        """

        sequences = list(range(1, len(simulations) + 1))
        durations = [sim["duration_minutes"] for sim in simulations]
        events = [sim["event_name"] for sim in simulations]

        unique_events = list(set(events))
        color_map = plt.cm.tab10(np.linspace(0, 1, len(unique_events)))
        event_to_color = {event: color_map[i] for i, event in enumerate(unique_events)}
        colors = [event_to_color[event] for event in events]

        plt.figure(figsize=(12, 6))

        scatter = plt.scatter(sequences, durations, c=colors, s=100, alpha=0.7, edgecolor='black')

        plt.plot(sequences, durations, 'gray', alpha=0.3, linestyle='--')

        plt.xlabel('Position in Sequence', fontsize=12)
        plt.ylabel('Duration (minutes)', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)

        legend_elements = [plt.Line2D([0], [0], marker='o', color='w',
                                     markerfacecolor=event_to_color[event],
                                     markersize=10, label=event)
                          for event in unique_events]
        plt.legend(handles=legend_elements, title="Event Types",
                  bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_timeline(self, simulations: List[Dict[str, Any]],
                      title: str = "Event Timeline",
                      save_path: Optional[str] = None) -> None:
        """
        Creates a simple timeline of events.

        Args:
            simulations: List of simulations
            title: Chart title
            save_path: Path to save the image
        """

        plt.figure(figsize=(14, 8))

        for i, sim in enumerate(simulations):
            start_min = sim.get("start_minute", i * 10)
            duration = sim["duration_minutes"]

            plt.barh(i, duration, left=start_min,
                    color=plt.cm.tab20(i % 20), alpha=0.7, edgecolor='black')

            plt.text(start_min + duration/2, i, sim["event_name"],
                    ha='center', va='center', fontweight='bold', color='white')

        plt.xlabel('Time (minutes)', fontsize=12)
        plt.ylabel('Event', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='x')

        plt.yticks(range(len(simulations)),
                  [f"Ev.{i+1}" for i in range(len(simulations))])

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_metrics_summary(self, metrics_data: Dict[str, Any],
                             title: str = "Metrics Summary",
                             save_path: Optional[str] = None) -> None:
        """
        Creates a bar chart of key metrics.

        Args:
            metrics_data: Metrics data
            title: Chart title
            save_path: Path to save the image
        """

        temporal = metrics_data.get("temporal_statistics", {})
        complexity = metrics_data.get("sequence_complexity", {})

        metric_names = [
            'Average Duration',
            'Total Duration',
            'Complexity',
            'Density',
            'Entropy'
        ]

        metric_values = [
            temporal.get("avg_duration", 0),
            temporal.get("sum_duration", 0),
            complexity.get("complexity_score", 0),
            metrics_data.get("temporal_density", {}).get("temporal_density", 0) * 100,
            metrics_data.get("entropy", 0)
        ]

        plt.figure(figsize=(12, 6))

        bars = plt.bar(metric_names, metric_values, color=plt.cm.viridis(np.linspace(0, 1, 5)))

        for bar, value in zip(bars, metric_values):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{value:.2f}', ha='center', va='bottom')

        plt.xlabel('Metrics', fontsize=12)
        plt.ylabel('Value', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_event_frequency(self, simulations: List[Dict[str, Any]],
                             title: str = "Event Frequency",
                             save_path: Optional[str] = None) -> None:
        """
        Creates a bar chart of event frequencies.

        Args:
            simulations: List of simulations
            title: Chart title
            save_path: Path to save the image
        """

        events = [sim["event_name"] for sim in simulations]
        event_counts = {}

        for event in events:
            if event in event_counts:
                event_counts[event] += 1
            else:
                event_counts[event] = 1

        sorted_events = sorted(event_counts.items(), key=lambda x: x[1], reverse=True)
        event_names = [item[0] for item in sorted_events]
        counts = [item[1] for item in sorted_events]

        plt.figure(figsize=(12, 6))

        bars = plt.bar(event_names, counts, color='lightcoral', edgecolor='black')

        for bar, count in zip(bars, counts):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    str(count), ha='center', va='bottom')

        plt.xlabel('Event Type', fontsize=12)
        plt.ylabel('Number of Occurrences', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved: {save_path}")
        else:
            plt.show()

        plt.close()

    def create_all_plots(self, simulations: List[Dict[str, Any]],
                         metrics_data: Optional[Dict[str, Any]] = None,
                         prefix: str = "zenith_plot",
                         output_dir: str = ".") -> List[str]:
        """
        Creates all charts and saves them.

        Args:
            simulations: List of simulations
            metrics_data: Metrics data (optional)
            prefix: Prefix for file names
            output_dir: Output directory

        Returns:
            List of created file paths
        """
        import os

        os.makedirs(output_dir, exist_ok=True)

        saved_files = []

        if metrics_data is None:
            metrics_data = self.metrics.get_comprehensive_metrics(simulations)

        hist_path = os.path.join(output_dir, f"{prefix}_histogram.png")
        self.plot_duration_histogram(simulations, save_path=hist_path)
        saved_files.append(hist_path)

        pie_path = os.path.join(output_dir, f"{prefix}_pie_chart.png")
        self.plot_event_pie_chart(simulations, save_path=pie_path)
        saved_files.append(pie_path)

        scatter_path = os.path.join(output_dir, f"{prefix}_scatter.png")
        self.plot_sequence_scatter(simulations, save_path=scatter_path)
        saved_files.append(scatter_path)

        freq_path = os.path.join(output_dir, f"{prefix}_frequency.png")
        self.plot_event_frequency(simulations, save_path=freq_path)
        saved_files.append(freq_path)

        summary_path = os.path.join(output_dir, f"{prefix}_summary.png")
        self.plot_metrics_summary(metrics_data, save_path=summary_path)
        saved_files.append(summary_path)

        if len(simulations) <= 20:
            timeline_path = os.path.join(output_dir, f"{prefix}_timeline.png")
            self.plot_timeline(simulations, save_path=timeline_path)
            saved_files.append(timeline_path)

        print(f"Created {len(saved_files)} charts in {output_dir}")
        return saved_files

    def plot_simple_comparison(self, simulations_list: List[List[Dict[str, Any]]],
                               labels: List[str],
                               title: str = "Sequence Comparison",
                               save_path: Optional[str] = None) -> None:
        """
        Compares multiple event sequences.

        Args:
            simulations_list: List of simulation lists
            labels: Labels for each sequence
            title: Chart title
            save_path: Path to save the image
        """

        avg_durations = []
        total_events = []

        for simulations in simulations_list:
            avg_duration = sum([sim["duration_minutes"] for sim in simulations]) / len(simulations)
            avg_durations.append(avg_duration)
            total_events.append(len(simulations))

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        bars1 = axes[0].bar(labels, avg_durations, color='skyblue', edgecolor='black')
        axes[0].set_xlabel('Sequences')
        axes[0].set_ylabel('Average Duration (min)')
        axes[0].set_title('Average Duration per Sequence')
        axes[0].grid(True, alpha=0.3)

        for bar, value in zip(bars1, avg_durations):
            axes[0].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.1,
                        f'{value:.1f}', ha='center', va='bottom')

        bars2 = axes[1].bar(labels, total_events, color='lightcoral', edgecolor='black')
        axes[1].set_xlabel('Sequences')
        axes[1].set_ylabel('Number of Events')
        axes[1].set_title('Number of Events per Sequence')
        axes[1].grid(True, alpha=0.3)

        for bar, value in zip(bars2, total_events):
            axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.1,
                        str(value), ha='center', va='bottom')

        fig.suptitle(title, fontsize=16, fontweight='bold', y=1.02)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved: {save_path}")
        else:
            plt.show()

        plt.close()



def create_simple_plot(data: List[float],
                       title: str = "Simple Chart",
                       xlabel: str = "X",
                       ylabel: str = "Y",
                       plot_type: str = "line") -> None:
    """
    Creates a simple chart.

    Args:
        data: List of numerical values
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        plot_type: Chart type ('line', 'bar', 'scatter')
    """
    plt.figure(figsize=(10, 6))

    if plot_type == "line":
        plt.plot(data, marker='o', linestyle='-', linewidth=2, markersize=6)
    elif plot_type == "bar":
        plt.bar(range(len(data)), data, edgecolor='black', alpha=0.7)
    elif plot_type == "scatter":
        plt.scatter(range(len(data)), data, s=50, alpha=0.7)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()