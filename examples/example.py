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
