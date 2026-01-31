import pytest
import math
from src.zenith_analyser import ZenithMetrics

@pytest.fixture
def metrics_instance(sample_code):
    """Fixture pour initialiser ZenithMetrics avec le code d'exemple."""
    return ZenithMetrics(sample_code)

@pytest.fixture
def mock_simulations():
    """Données de simulation contrôlées pour tester la logique mathématique."""
    return [
        {
            "event_name": "START",
            "duration_minutes": 10.0,
            "start": {"date": "2024-01-01", "time": "10:00"},
            "end": {"date": "2024-01-01", "time": "10:10"}
        },
        {
            "event_name": "PROCESS",
            "duration_minutes": 20.0,
            "start": {"date": "2024-01-01", "time": "10:15"},
            "end": {"date": "2024-01-01", "time": "10:35"}
        },
        {
            "event_name": "START",
            "duration_minutes": 10.0,
            "start": {"date": "2024-01-01", "time": "10:40"},
            "end": {"date": "2024-01-01", "time": "10:50"}
        },
        {
            "event_name": "PROCESS",
            "duration_minutes": 20.0,
            "start": {"date": "2024-01-01", "time": "10:55"},
            "end": {"date": "2024-01-01", "time": "11:15"}
        }
    ]

class TestZenithMetrics:

    def test_calculate_event_frequency(self, metrics_instance, mock_simulations):
        """Vérifie le comptage des événements."""
        freq = metrics_instance.calculate_event_frequency(mock_simulations)
        assert freq["START"] == 2
        assert freq["PROCESS"] == 2
        assert len(freq) == 2

    def test_calculate_temporal_statistics(self, metrics_instance, mock_simulations):
        """Vérifie les stats de durée (moyenne, min, max)."""
        stats = metrics_instance.calculate_temporal_statistics(mock_simulations)
        assert stats["avg_duration"] == 15.0
        assert stats["min_duration"] == 10.0
        assert stats["max_duration"] == 20.0
        assert stats["events_count"] == 4

    def test_calculate_entropy(self, metrics_instance, mock_simulations):
        """Vérifie le calcul de l'entropie (incertitude de la séquence)."""
        entropy = metrics_instance.calculate_entropy(mock_simulations)
        # Avec 2 START et 2 PROCESS, l'entropie est exactement 1.0 bit
        assert math.isclose(entropy, 1.0)

    def test_detect_patterns_optimized(self, metrics_instance):
        """
        Test crucial : vérifie que l'algorithme Suffix Array
        détecte correctement les répétitions maximales.
        """
        # Séquence : A-B-C-A-B-C (Pattern A-B-C répété)
        sims = [
            {"event_name": "A"}, {"event_name": "B"}, {"event_name": "C"},
            {"event_name": "X"}, # Interrupteur
            {"event_name": "A"}, {"event_name": "B"}, {"event_name": "C"}
        ]
        
        patterns = metrics_instance.detect_patterns(sims, min_pattern_length=2)
        
        # On s'attend à trouver ['A', 'B', 'C']
        found_pattern = any(p['pattern'] == ['A', 'B', 'C'] for p in patterns)
        assert found_pattern is True
        
        # Vérifie que les occurrences sont bien capturées
        main_pattern = next(p for p in patterns if p['pattern'] == ['A', 'B', 'C'])
        assert len(main_pattern['occurrences']) == 2

    def test_calculate_sequence_complexity(self, metrics_instance, mock_simulations):
        """Vérifie l'indice de complexité (0-100)."""
        complexity = metrics_instance.calculate_sequence_complexity(mock_simulations)
        assert "complexity_score" in complexity
        assert 0 <= complexity["complexity_score"] <= 100

    def test_calculate_rhythm_metrics(self, metrics_instance, mock_simulations):
        """Vérifie la régularité des intervalles entre événements."""
        rhythm = metrics_instance.calculate_rhythm_metrics(mock_simulations)
        assert "rhythm_consistency" in rhythm
        assert isinstance(rhythm["intervals"], list)

    def test_get_comprehensive_metrics(self, metrics_instance, mock_simulations):
        """Vérifie que le rapport global contient toutes les sections."""
        report = metrics_instance.get_comprehensive_metrics(mock_simulations)
        keys = [
            "temporal_statistics", "event_frequency", "sequence_complexity",
            "temporal_density", "rhythm_metrics", "patterns_detected", "entropy"
        ]
        for key in keys:
            assert key in report

