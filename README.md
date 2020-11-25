# Helmion Plugin: Kube Resource Report

[![PyPI version](https://img.shields.io/pypi/v/hmi_kuberesourcereport.svg)](https://pypi.python.org/pypi/hmi_kuberesourcereport/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/hmi_kuberesourcereport.svg)](https://pypi.python.org/pypi/hmi_kuberesourcereport/)

hmi_kuberesourcereport is a chart generator for [Helmion](https://github.com/RangelReale/helmion) 
that deploys a [Kube Resource Report](https://codeberg.org/hjacobs/kube-resource-report) service in Kubernetes.

Helmion is a python library to download and customize [Helm](https://helm.sh/) charts, and can
also be used to generate custom charts.

* Website: https://github.com/RangelReale/hmi_kuberesourcereport
* Repository: https://github.com/RangelReale/hmi_kuberesourcereport.git
* Documentation: https://hmi_kuberesourcereport.readthedocs.org/
* PyPI: https://pypi.python.org/pypi/hmi_kuberesourcereport

### Example

```python
from kubragen2.output import OutputProject, OutputFile_ShellScript, OutputFile_Kubernetes, OD_FileTemplate, \
    OutputDriver_Print

from hmi_kuberesourcereport import KubeResourceReportChartRequest

out = OutputProject()

shell_script = OutputFile_ShellScript('create_gke.sh')
out.append(shell_script)

shell_script.append('set -e')

#
# OUTPUTFILE: app-namespace.yaml
#
file = OutputFile_Kubernetes('app-namespace.yaml')

file.append([
    {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': 'app-monitoring',
        },
    }
])

out.append(file)
shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

shell_script.append(f'kubectl config set-context --current --namespace=app-monitoring')

#
# SETUP: kube-resource-report
#
kms_req = KubeResourceReportChartRequest(namespace='app-monitoring', values={
    'resources': {
        'requests': {
            'cpu': '5m',
            'memory': '50Mi'
        },
        'limits': {
            'cpu': '10m',
            'memory': '100Mi'
        },
    },
})
kms_chart = kms_req.generate()

#
# OUTPUTFILE: kuberesourcereport.yaml
#
file = OutputFile_Kubernetes('kuberesourcereport.yaml')
out.append(file)

file.append(kms_chart.data)

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# Write files
#
out.output(OutputDriver_Print())
# out.output(OutputDriver_Directory('/tmp/build-gke'))
```

Output:

```text
****** BEGIN FILE: 001-app-namespace.yaml ********
apiVersion: v1
kind: Namespace
metadata:
  name: app-monitoring

****** END FILE: 001-app-namespace.yaml ********
****** BEGIN FILE: 002-kuberesourcereport.yaml ********
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kuberesourcereport
  namespace: app-monitoring
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: kuberesourcereport
rules:
- apiGroups:
  - ''
  resources:
  - nodes
  - pods
  - namespaces
  - services
<...more...>

****** END FILE: 002-kuberesourcereport.yaml ********
****** BEGIN FILE: create_gke.sh ********
#!/bin/bash

set -e
kubectl apply -f 001-app-namespace.yaml
kubectl config set-context --current --namespace=app-monitoring
kubectl apply -f 002-kuberesourcereport.yaml

****** END FILE: create_gke.sh ********
```

## Author

Rangel Reale (rangelreale@gmail.com)
