import unittest

from hmi_kuberesourcereport import KubeResourceReportChartRequest


class TestChart(unittest.TestCase):
    def test_empty(self):
        req = KubeResourceReportChartRequest()
        chart = req.generate()
        self.assertEqual(len(chart.data), 5)
