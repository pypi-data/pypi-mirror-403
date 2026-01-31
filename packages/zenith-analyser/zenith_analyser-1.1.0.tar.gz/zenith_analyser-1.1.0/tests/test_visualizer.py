import pytest
import os
import matplotlib
# Utilisation du backend 'Agg' pour éviter l'ouverture de fenêtres GUI pendant les tests
matplotlib.use('Agg')

from src.zenith_analyser import ZenithVisualizer
from src.zenith_analyser import ZenithMetrics

@pytest.fixture
def viz_setup(sample_code):
    """Initialise les métriques et le visualiseur."""
    metrics = ZenithMetrics(sample_code)
    return ZenithVisualizer(metrics)

@pytest.fixture
def test_sims():
    """Données de simulation pour les tests visuels."""
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

class TestZenithVisualizer:

    def test_plot_duration_histogram(self, viz_setup, test_sims, tmp_path):
        """Vérifie la création de l'histogramme."""
        path = tmp_path / "hist.png"
        viz_setup.plot_duration_histogram(test_sims, save_path=str(path))
        assert path.exists()
        assert path.stat().st_size > 0

    def test_plot_event_pie_chart(self, viz_setup, test_sims, tmp_path):
        """Vérifie la création du diagramme circulaire."""
        path = tmp_path / "pie.png"
        viz_setup.plot_event_pie_chart(test_sims, save_path=str(path))
        assert path.exists()

    def test_plot_sequence_scatter(self, viz_setup, test_sims, tmp_path):
        """Vérifie la création du scatter plot de séquence."""
        path = tmp_path / "scatter.png"
        viz_setup.plot_sequence_scatter(test_sims, save_path=str(path))
        assert path.exists()

    def test_plot_timeline(self, viz_setup, test_sims, tmp_path):
        """Vérifie la création de la timeline."""
        path = tmp_path / "timeline.png"
        viz_setup.plot_timeline(test_sims, save_path=str(path))
        assert path.exists()

    def test_plot_metrics_summary(self, viz_setup, tmp_path):
        """Vérifie le résumé global des métriques."""
        mock_metrics_data = {
            "temporal_statistics": {"avg_duration": 15.5, "sum_duration": 120},
            "sequence_complexity": {"complexity_score": 75.0},
            "temporal_density": {"temporal_density": 0.8},
            "entropy": 1.2
        }
        path = tmp_path / "summary.png"
        viz_setup.plot_metrics_summary(mock_metrics_data, save_path=str(path))
        assert path.exists()

    def test_create_all_plots(self, viz_setup, test_sims, tmp_path):
        """Vérifie que la fonction groupée génère bien tous les fichiers attendus."""
        output_dir = tmp_path / "plots"
        # On passe un dictionnaire de métriques vide ou partiel pour tester la logique
        files = viz_setup.create_all_plots(test_sims, output_dir=str(output_dir), prefix="test")
        
        # Vérifie que les fichiers physiques existent dans le dossier
        for f in files:
            assert os.path.exists(f)
        
        # On s'attend à au moins 5 fichiers (hist, pie, scatter, freq, summary, timeline)
        assert len(files) >= 5

    def test_plot_simple_comparison(self, viz_setup, test_sims, tmp_path):
        """Vérifie la comparaison entre deux séquences."""
        sims_list = [test_sims, test_sims] # On compare la séquence avec elle-même
        labels = ["Batch A", "Batch B"]
        path = tmp_path / "comparison.png"
        viz_setup.plot_simple_comparison(sims_list, labels, save_path=str(path))
        assert path.exists()