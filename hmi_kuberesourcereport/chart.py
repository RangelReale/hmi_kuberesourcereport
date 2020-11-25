from typing import Optional, Mapping, Any, Sequence, List, Dict

from helmion.chart import Chart
from helmion.config import Config
from helmion.data import ChartData
from kubragen2.data import ValueData, Data
from kubragen2.options import Options, OptionValue, OptionsBuildData


class KubeResourceReportChartRequest:
    config: Config
    namespace: Optional[str]
    releasename: str
    values: Optional[Mapping[str, Any]]
    _options: Options
    _serviceaccount: str

    def __init__(self, namespace: Optional[str] = 'default', releasename: str = 'kube-resource-report',
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
                'port': 80,
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
            data.extend([
                {
                    'kind': 'ClusterRole',
                    'apiVersion': 'rbac.authorization.k8s.io/v1',
                    'metadata': {
                        'name': self.name_format(),
                    },
                    'rules': [{
                        'apiGroups': [''],
                        'resources': ['nodes', 'pods', 'namespaces', 'services'],
                        'verbs': ['get', 'list']
                    },
                    {
                        'apiGroups': ['networking.k8s.io'],
                        'resources': ['ingresses'],
                        'verbs': ['list']
                    },
                    {
                        'apiGroups': ['metrics.k8s.io'],
                        'resources': ['nodes', 'pods'],
                        'verbs': ['get', 'list']
                    },
                    {
                        'apiGroups': [''],
                        'resources': ['services/proxy'],
                        'resourceNames': ['heapster'],
                        'verbs': ['get']
                    },
                    {
                        'apiGroups': ['autoscaling.k8s.io'],
                        'resources': ['verticalpodautoscalers'],
                        'verbs': ['get', 'list']
                    },
                    {
                        'apiGroups': ['apps'],
                        'resources': ['deployments',
                                      'statefulsets',
                                      'replicasets',
                                      'daemonsets'],
                        'verbs': ['get', 'list']
                    }]
                },
                {
                    'apiVersion': 'rbac.authorization.k8s.io/v1',
                    'kind': 'ClusterRoleBinding',
                    'metadata': {
                        'name': self.name_format(),
                    },
                    'roleRef': {
                        'apiGroup': 'rbac.authorization.k8s.io',
                        'kind': 'ClusterRole',
                        'name': self.name_format(),
                    },
                    'subjects': [{
                        'kind': 'ServiceAccount',
                        'name': self._serviceaccount,
                        'namespace': namespace_value,
                    }]
                },
            ])

        data.extend([
            {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': {
                    'name': self.name_format(),
                    'namespace': namespace_value,
                    'labels': {
                        'app.kubernetes.io/name': 'kube-resource-report',
                        'app.kubernetes.io/instance': self.name_format(),
                    },
                },
                'spec': {
                    'replicas': 1,
                    'selector': {
                        'matchLabels': {
                            'app.kubernetes.io/name': 'kube-resource-report',
                            'app.kubernetes.io/instance': self.name_format(),
                        }
                    },
                    'template': {
                        'metadata': {
                            'labels': {
                                'app.kubernetes.io/name': 'kube-resource-report',
                                'app.kubernetes.io/instance': self.name_format(),
                            }
                        },
                        'spec': {
                            'serviceAccountName': self._serviceaccount,
                            'containers': [{
                                'name': 'kube-resource-report',
                                'image': '{}/{}:{}'.format(self._options.option_get('image.registry'),
                                                           self._options.option_get('image.repository'),
                                                           self._options.option_get('image.tag')),
                                'args': ['--update-interval-minutes=1',
                                         '--additional-cost-per-cluster=30.0',
                                         '/output'],
                                'volumeMounts': [{
                                    'mountPath': '/output',
                                    'name': 'report-data'
                                }],
                                'securityContext': {
                                    'readOnlyRootFilesystem': True,
                                    'runAsNonRoot': True,
                                    'runAsUser': 1000
                                },
                                'resources': ValueData(self._options.option_get('resources'), disabled_if_none=True),
                            },
                            {
                                'name': 'nginx',
                                'image': '{}/{}:{}'.format(self._options.option_get('webserver.image.registry'),
                                                           self._options.option_get('webserver.image.repository'),
                                                           self._options.option_get('webserver.image.tag')),
                                'volumeMounts': [{
                                    'mountPath': '/usr/share/nginx/html',
                                    'name': 'report-data',
                                    'readOnly': True
                                }],
                                'ports': [{
                                    'containerPort': 80
                                }],
                                'readinessProbe': {
                                    'httpGet': {
                                        'path': '/',
                                        'port': 80
                                    }
                                },
                                'resources': ValueData(self._options.option_get('webserver.resources'),
                                                       disabled_if_none=True),
                            }],
                            'volumes': [{
                                'name': 'report-data',
                                'emptyDir': {
                                    'sizeLimit': '500Mi'
                                }
                            }]
                        }
                    }
                }
            },
            {
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': self.name_format(),
                    'namespace': namespace_value,
                    'labels': {
                        'app.kubernetes.io/name': 'kube-resource-report',
                        'app.kubernetes.io/instance': self.name_format(),
                    },
                },
                'spec': {
                    'selector': {
                        'app.kubernetes.io/name': 'kube-resource-report',
                        'app.kubernetes.io/instance': self.name_format(),
                    },
                    'type': self._options.option_get('service.type'),
                    'ports': [{
                        'name': self._options.option_get('service.portName'),
                        'port': self._options.option_get('service.port'),
                        'protocol': 'TCP',
                        'targetPort': 80
                    }]
                }
            },
        ])

        return KubeResourceReportChart(
            request=self, config=self.config, data=OptionsBuildData(self._options, data))


class KubeResourceReportChart(Chart):
    request: KubeResourceReportChartRequest

    def __init__(self, request: KubeResourceReportChartRequest, config: Optional[Config] = None,
                 data: Optional[Sequence[ChartData]] = None):
        super().__init__(config=config, data=data)
        self.request = request

    def createClone(self) -> 'Chart':
        return KubeResourceReportChart(request=self.request, config=self.config)
