import unittest
from pathlib import Path

from io_csv import load_projects
from rbf_predictor import rbf_predict
from system_stats import MySystem


class DatasetPipelineTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parents[1] / "dataset" / "完整案例庫_新增BIM標註.xls"
        self.projects = load_projects(path)
        self.system = MySystem()
        self.system.projects = self.projects
        self.system.attach()

    def test_bundled_dataset_has_trainable_projects(self):
        self.assertGreaterEqual(len(self.projects), 3)
        self.assertTrue(all(project.duration_actual > 0 for project in self.projects))
        self.assertTrue(all(project.settlement_raw > 0 for project in self.projects))

    def test_bundled_dataset_supports_prediction(self):
        prediction, matches = rbf_predict(
            self.projects[0],
            self.projects[1:],
            lambda project: project.duration_actual,
        )
        self.assertGreater(prediction, 0)
        self.assertTrue(matches)
        self.assertAlmostEqual(sum(weight for _, weight in matches), 1.0)


if __name__ == "__main__":
    unittest.main()
