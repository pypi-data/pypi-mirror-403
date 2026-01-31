
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
Metrics for Zenith language structures.
Contains LawAnalyser, TargetAnalyser, and ZenithAnalyser classes.
"""

from .analysers import ZenithAnalyser
from typing import Dict, List, Any
from .utils import calculate_duration, parse_datetime
import math
import statistics
from collections import Counter

class ZenithMetrics(ZenithAnalyser):
    """
        Initialize ZenithMetrics with Zenith language code.

        Args:
            code (str): Zenith language code string
    """

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code



    def _build_suffix_array(self, s: List[int]) -> List[int]:
        """
        Build Suffix Array in O(n log n) for sequence IDs.

        Args:
            s (List[int]): List of integer IDs representing events

        Returns:
            List[int]: Suffix array indices
        """
        n = len(s)
        sa = list(range(n))
        rank = s[:]
        k = 1
        while k < n:
            key = lambda i: (rank[i], rank[i + k] if i + k < n else -1)
            sa.sort(key=key)
            new_rank = [0] * n
            for i in range(1, n):
                new_rank[sa[i]] = new_rank[sa[i-1]] + (1 if key(sa[i]) > key(sa[i-1]) else 0)
            rank = new_rank
            if rank[sa[n-1]] == n - 1: break
            k *= 2
        return sa

    def _build_lcp(self, s: List[int], sa: List[int]) -> List[int]:
        """
        Build LCP Array in O(n) using Kasai's algorithm.

        Args:
            s (List[int]): Original sequence of IDs
            sa (List[int]): Suffix array

        Returns:
            List[int]: LCP (Longest Common Prefix) array
        """
        n = len(s)
        rank = [0] * n
        for i, pos in enumerate(sa): rank[pos] = i
        lcp, h = [0] * n, 0
        for i in range(n):
            if rank[i] > 0:
                j = sa[rank[i] - 1]
                while i + h < n and j + h < n and s[i + h] == s[j + h]:
                    h += 1
                lcp[rank[i]] = h
                if h > 0: h -= 1
        return lcp



    def get_data_simulations(self, simulations: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        """
        Extract structured data from simulation results.

        Args:
            simulations (List[Dict[str, Any]]): List of simulation dictionaries

        Returns:
            Dict[str, List[Any]]: Dictionary with keys:
                - "sequence": Event sequence numbers
                - "event": Event names
                - "coherence": Event durations in minutes
                - "dispersion": Waiting times before next events
        """
        datas = {
            "sequence": [],
            "event": [],
            "coherence": [],
            "dispersion": []
        }
        for i in range(len(simulations)):
            datas["sequence"].append(i + 1)
            event_name = simulations[i]["event_name"]
            datas["event"].append(event_name)
            coherence = simulations[i]["duration_minutes"]
            datas["coherence"].append(coherence)

            if i < len(simulations) - 1:
                start = simulations[i]["end"]
                start_date = parse_datetime(start["date"], start["time"])
                end = simulations[i + 1]["start"]
                end_date = parse_datetime(end["date"], end["time"])
                dispersion = calculate_duration(start_date, end_date)
                datas["dispersion"].append(dispersion)
            else:
                datas["dispersion"].append(0)
        return datas

    def calculate_temporal_statistics(self, simulations: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate temporal statistics from simulations.

        Args:
            simulations (List[Dict[str, Any]]): List of simulation dictionaries

        Returns:
            Dict[str, float]: Dictionary containing:
                - "avg_duration": Average event duration
                - "median_duration": Median event duration
                - "min_duration": Minimum event duration
                - "max_duration": Maximum event duration
                - "duration_std": Standard deviation of durations
                - "sum_duration": Total duration of all events
                - "avg_dispersion": Average waiting time between events
                - "sum_dispersion": Total waiting time
                - "events_count": Number of events
        """
        durations = []
        dispersions = []
        for i, sim in enumerate(simulations):
            durations.append(sim["duration_minutes"])
            if i < len(simulations) - 1:
                start = sim["end"]
                start_date = parse_datetime(start["date"], start["time"])
                end = simulations[i + 1]["start"]
                end_date = parse_datetime(end["date"], end["time"])
                dispersions.append(calculate_duration(start_date, end_date))
            else:
                dispersions.append(0)

        return {
            "avg_duration": statistics.mean(durations) if durations else 0,
            "median_duration": statistics.median(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "duration_std": statistics.stdev(durations) if len(durations) > 1 else 0,
            "sum_duration": sum(durations),
            "avg_dispersion": statistics.mean(dispersions) if dispersions else 0,
            "sum_dispersion": sum(dispersions) if dispersions else 0,
            "events_count": len(simulations)
        }

    def calculate_event_frequency(self, simulations: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate frequency of each event type.

        Args:
            simulations (List[Dict[str, Any]]): List of simulation dictionaries

        Returns:
            Dict[str, int]: Dictionary with event names as keys and counts as values
        """
        events = [sim["event_name"] for sim in simulations]
        return dict(Counter(events))

    def calculate_sequence_complexity(self, simulations: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate sequence complexity metrics.

        Args:
            simulations (List[Dict[str, Any]]): List of simulation dictionaries

        Returns:
            Dict[str, float]: Dictionary containing:
                - "complexity_score": Overall complexity score (0-100)
                - "unique_events_ratio": Ratio of unique events
                - "transition_variety": Variety of event transitions
                - "unique_transitions_count": Number of unique transitions
        """
        total_events = len(simulations)
        if total_events < 2:
            return {"complexity_score": 0, "unique_events_ratio": 0, "transition_variety": 0}

        unique_events = len(set(sim["event_name"] for sim in simulations))
        unique_ratio = unique_events / total_events

        transitions = []
        for i in range(len(simulations) - 1):
            transition = f"{simulations[i]['event_name']}->{simulations[i+1]['event_name']}"
            transitions.append(transition)

        unique_transitions = len(set(transitions))
        max_possible_transitions = min(unique_events**2, total_events - 1)
        transition_variety = unique_transitions / max_possible_transitions if max_possible_transitions > 0 else 0
        complexity_score = (unique_ratio * 0.4 + transition_variety * 0.6) * 100

        return {
            "complexity_score": complexity_score,
            "unique_events_ratio": unique_ratio,
            "transition_variety": transition_variety,
            "unique_transitions_count": unique_transitions
        }

    def calculate_temporal_density(self, simulations: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate temporal density and coverage metrics.

        Args:
            simulations (List[Dict[str, Any]]): List of simulation dictionaries

        Returns:
            Dict[str, float]: Dictionary containing:
                - "temporal_density": Ratio of event time to total time
                - "coverage_ratio": Coverage percentage (density * 100)
                - "total_simulation_time": Total time span
                - "effective_event_time": Sum of all event durations
        """
        if not simulations: return {"temporal_density": 0, "coverage_ratio": 0}
        first_start = parse_datetime(simulations[0]["start"]["date"], simulations[0]["start"]["time"])
        last_end = parse_datetime(simulations[-1]["end"]["date"], simulations[-1]["end"]["time"])
        total_time = calculate_duration(first_start, last_end)
        event_time = sum(sim["duration_minutes"] for sim in simulations)
        temporal_density = event_time / total_time if total_time > 0 else 0
        return {
            "temporal_density": temporal_density,
            "coverage_ratio": temporal_density * 100,
            "total_simulation_time": total_time,
            "effective_event_time": event_time
        }

    def calculate_rhythm_metrics(self, simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate rhythm and interval consistency metrics.

        Args:
            simulations (List[Dict[str, Any]]): List of simulation dictionaries

        Returns:
            Dict[str, Any]: Dictionary containing:
                - "rhythm_consistency": Rhythm consistency score (0-1)
                - "avg_interval": Average interval between events
                - "interval_std": Standard deviation of intervals
                - "intervals": List of all interval values
        """
        if len(simulations) < 2: return {"rhythm_consistency": 0, "intervals": []}
        intervals = []
        for i in range(len(simulations) - 1):
            end_current = parse_datetime(simulations[i]["end"]["date"], simulations[i]["end"]["time"])
            start_next = parse_datetime(simulations[i + 1]["start"]["date"], simulations[i + 1]["start"]["time"])
            intervals.append(calculate_duration(end_current, start_next))

        cv = statistics.stdev(intervals) / statistics.mean(intervals) if statistics.mean(intervals) > 0 else 0
        return {
            "rhythm_consistency": 1 / (1 + cv),
            "avg_interval": statistics.mean(intervals) if intervals else 0,
            "interval_std": statistics.stdev(intervals) if len(intervals) > 1 else 0,
            "intervals": intervals
        }



    def detect_patterns(self, simulations: List[Dict[str, Any]], min_pattern_length: int = 2) -> List[Dict[str, Any]]:
        """
        Detect recurrent patterns (maximal repeats) in O(n log n).

        Args:
            simulations (List[Dict[str, Any]]): List of simulation dictionaries
            min_pattern_length (int): Minimum pattern length to detect (default: 2)

        Returns:
            List[Dict[str, Any]]: List of detected patterns, each containing:
                - "pattern": List of event names in the pattern
                - "occurrences": List of (start, end) position tuples
                - "length": Length of the pattern
        """
        if len(simulations) < min_pattern_length * 2:
            return []

        events = [sim["event_name"] for sim in simulations]
        unique_names = sorted(list(set(events)))
        name_to_id = {name: i for i, name in enumerate(unique_names)}
        event_ids = [name_to_id[name] for name in events]

        event_ids_sentinel = event_ids + [-1]

        sa = self._build_suffix_array(event_ids_sentinel)
        lcp = self._build_lcp(event_ids_sentinel, sa)

        results = []
        n_sa = len(sa)
        i = 1

        while i < n_sa:
            if lcp[i] >= min_pattern_length:
                current_lcp = lcp[i]
                start_idx = i - 1
                while i < n_sa and lcp[i] >= current_lcp:
                    i += 1
                end_idx = i - 1

                group_sa = sa[start_idx : end_idx + 1]


                left_chars = set()
                for pos in group_sa:
                    left_chars.add(event_ids_sentinel[pos - 1] if pos > 0 else -2)

                if len(left_chars) > 1:
                    pattern_ids = event_ids[group_sa[0] : group_sa[0] + current_lcp]
                    pattern_names = [unique_names[idx] for idx in pattern_ids]

                    results.append({
                        "pattern": pattern_names,
                        "occurrences": [(p, p + current_lcp) for p in sorted(group_sa)],
                        "length": current_lcp
                    })
            else:
                i += 1
        return results



    def calculate_entropy(self, simulations: List[Dict[str, Any]]) -> float:
        """
        Calculate Shannon entropy of event distribution.

        Args:
            simulations (List[Dict[str, Any]]): List of simulation dictionaries

        Returns:
            float: Entropy value (bits)
        """
        events = [sim["event_name"] for sim in simulations]
        if not events: return 0
        counter = Counter(events)
        total = len(events)
        entropy = 0
        for count in counter.values():
            probability = count / total
            entropy -= probability * (math.log2(probability) if probability > 0 else 0)
        return entropy

    def get_comprehensive_metrics(self, simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get all available metrics in a structured dictionary.

        Args:
            simulations (List[Dict[str, Any]]): List of simulation dictionaries

        Returns:
            Dict[str, Any]: Comprehensive metrics dictionary containing:
                - "temporal_statistics": Temporal statistics
                - "event_frequency": Event frequency counts
                - "sequence_complexity": Sequence complexity metrics
                - "temporal_density": Temporal density metrics
                - "rhythm_metrics": Rhythm and interval metrics
                - "patterns_detected": Detected patterns
                - "entropy": Shannon entropy
        """
        return {
            "temporal_statistics": self.calculate_temporal_statistics(simulations),
            "event_frequency": self.calculate_event_frequency(simulations),
            "sequence_complexity": self.calculate_sequence_complexity(simulations),
            "temporal_density": self.calculate_temporal_density(simulations),
            "rhythm_metrics": self.calculate_rhythm_metrics(simulations),
            "patterns_detected": self.detect_patterns(simulations),
            "entropy": self.calculate_entropy(simulations)
        }

    def get_data_law(self, name: str, population: int = 1) -> Any:
        """
        Get simulation data for a specific law as a pandas DataFrame.

        Args:
            name (str): Name of the law
            population (int): Population identifier (default: 1)

        Returns:
            Any: pandas DataFrame containing simulation data

        Raises:
            ImportError: If pandas is not installed
        """
        simulations = self.law_description(name, population)["simulation"]
        try:
            import pandas as pd
            datas = self.get_data_simulations(simulations)
            return pd.DataFrame(datas)
        except ImportError:
            raise ImportError("Installez pandas : pip install zenith-analyser[science]")

    def get_metrics_law(self, name: str, population: int = 1) -> Dict[str, Any]:
        """
        Get comprehensive metrics for a specific law.

        Args:
            name (str): Name of the law
            population (int): Population identifier (default: 1)

        Returns:
            Dict[str, Any]: Comprehensive metrics dictionary
        """
        simulations = self.law_description(name, population)["simulation"]
        return self.get_comprehensive_metrics(simulations)

    def get_data_target(self, name: str) -> Any:
        """
        Get simulation data for a specific target as a pandas DataFrame.

        Args:
            name (str): Name of the target

        Returns:
            Any: pandas DataFrame containing simulation data

        Raises:
            ImportError: If pandas is not installed
        """
        simulations = self.target_description(name)["simulation"]
        try:
            import pandas as pd
            datas = self.get_data_simulations(simulations)
            return pd.DataFrame(datas)
        except ImportError:
            raise ImportError("Installez pandas : pip install zenith-analyser[science]")

    def get_metrics_target(self, name: str) -> Dict[str, Any]:
        """
        Get comprehensive metrics for a specific target.

        Args:
            name (str): Name of the target

        Returns:
            Dict[str, Any]: Comprehensive metrics dictionary
        """
        simulations = self.target_description(name)["simulation"]
        return self.get_comprehensive_metrics(simulations)

    def get_data_population(self, population: int = 0) -> Any:
        """
        Get simulation data for a specific population as a pandas DataFrame.

        Args:
            population (int): Population identifier (default: 0)

        Returns:
            Any: pandas DataFrame containing simulation data

        Raises:
            ImportError: If pandas is not installed
        """
        simulations = self.population_description(population)["simulation"]
        try:
            import pandas as pd
            datas = self.get_data_simulations(simulations)
            return pd.DataFrame(datas)
        except ImportError:
            raise ImportError("Installez pandas : pip install zenith-analyser[science]")

    def get_metrics_population(self, population: int = 0) -> Dict[str, Any]:
        """
        Get comprehensive metrics for a specific population.

        Args:
            population (int): Population identifier (default: 0)

        Returns:
            Dict[str, Any]: Comprehensive metrics dictionary
        """
        simulations = self.population_description(population)["simulation"]
        return self.get_comprehensive_metrics(simulations)