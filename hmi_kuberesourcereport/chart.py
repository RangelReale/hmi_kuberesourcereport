from typing import Optional, Mapping, Any, Sequence, List, Dict

from helmion.chart import Chart
from helmion.config import Config
from helmion.data import ChartData
from kubragen2.data import ValueData, Data
from kubragen2.options import Options, OptionValue, OptionsBuildData


class KubeResourceReportBuilderChartRequest:
    config: Config
    namespace: Optional[str]
    releasename: str
    values: Optional[Mapping[str, Any]]
    _options: Options
    _serviceaccount: str

    def __init__(self, namespace: Optional[str] = 'default', releasename: str = 'kuberesourcereport',
                 values: Optional[Mapping[str, Any]] = None, config: Optional[Config] = None):
        self.namespace = namespace
        self.releasename = releasename
        self.values = values
        self.config = config if config is not None else Config()
        self._options = Options({
            'base': {
                'namespace': namespace,
                'releasename': releasename,
            },
        }, self.allowedValues(), self.values)
        self._serviceaccount = self._options.option_get_opt('serviceAccount.name', self.name_format())

    def options(self) -> Options:
        return self._options

    def allowedValues(self) -> Mapping[str, Any]:
        return {
            'image': {
                'registry': 'docker.io',
                'repository': 'hjacobs/kube-resource-report',
                'tag': '20.10.0',
            },
            'serviceAccount': {
                'create': True,
                'name': '',
            },
            'rbac': {
                'create': True,
            },
            'service': {
                'type': 'ClusterIP',
                'port': '80',
                'portName': 'http',
            },
            'resources': None,
            'webserver': {
                'image': {
                    'registry': 'docker.io',
                    'repository': 'nginx',
                    'tag': '1.19.4-alpine',
                },
                'resources': None,
            },
        }

    def name_format(self, suffix: str = ''):
        ret = self.releasename
        if suffix != '':
            ret = '{}-{}'.format(ret, suffix)
        return ret

    def generate(self) -> Chart:
        namespace_value = ValueData(self.namespace, enabled=self.namespace is not None)

        data: List[ChartData] = []

        if self._options.option_get('serviceAccount.create'):
            data.append({
                'apiVersion': 'v1',
                'kind': 'ServiceAccount',
                'metadata': {
                    'name': self._serviceaccount,
                    'namespace': namespace_value,
                }
            })

        if self._options.option_get('rbac.create'):


        return KubeResourceReportBuilderChart(request=self, config=self.config,
                                     data=OptionsBuildData(self._options, data))


class KubeResourceReportBuilderChart(Chart):
    request: KubeResourceReportBuilderChartRequest

    def __init__(self, request: KubeResourceReportBuilderChartRequest, config: Optional[Config] = None,
                 data: Optional[Sequence[ChartData]] = None):
        super().__init__(config=config, data=data)
        self.request = request

    def createClone(self) -> 'Chart':
        return KubeResourceReportBuilderChart(request=self.request, config=self.config)
