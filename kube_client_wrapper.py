from kubernetes import client as kube_client
from kubernetes import config as kube_config
from kubernetes import watch as kube_watch
from util import Utilities
from collections import defaultdict
import logging
from datetime import datetime
import json


class KubeClientApiWrapper(object):
    def __init__(self, api_server='https://localhost', api_user='admin', api_pass='admin', conf_file=None):
        # By default it uses the local .kube/confi info
        kube_config.load_kube_config(config_file=conf_file)
        kube_client.configuration.host = api_server
        kube_client.configuration.username = api_user
        kube_client.configuration.password = api_pass
        self.kube_client_wrapper_client = kube_client.CoreV1Api()
        self.kube_ext_discovery_client = kube_client.ExtensionsV1beta1Api()
        self.resource_details = lambda: defaultdict(self.resource_details)
        self.util = Utilities()
        logging.basicConfig(level=logging.INFO)
        self.m_logger = logging.getLogger(__name__)

    ############## Generic watch operations ###################

    def get_all_resources_details(self, **kwargs):
        '''
        This method will do RESTApi calls to the Kubernetes APIServer and get all deployed resource/s details
        :param kwargs: Dict with APIServer Details
        :return: api_output
        '''
        watch = kwargs['WATCH'] if 'WATCH' in kwargs else False
        pretty_output = kwargs['PRETTY'] if 'PRETTY' in kwargs else False
        kind = kwargs['KIND'].lower() if 'KIND' in kwargs else 'pod'
        if kind == "pod" or kind == "deployment":
            all_resources = self.kube_client_wrapper_client.list_pod_for_all_namespaces(pretty=pretty_output, watch=watch)
        elif kind == "service":
            all_resources = self.kube_client_wrapper_client.list_service_for_all_namespaces(pretty=pretty_output, watch=watch)
        elif kind == "configmap":
            all_resources = self.kube_client_wrapper_client.list_config_map_for_all_namespaces(pretty=pretty_output, watch=watch)
        elif kind == "secret":
            all_resources = self.kube_client_wrapper_client.list_secret_for_all_namespaces(pretty=pretty_output, watch=watch)
        elif kind == "ingress":
            all_resources = self.kube_ext_discovery_client.list_ingress_for_all_namespaces(pretty=pretty_output, watch=watch)
        elif kind == "endpoint":
            all_resources = self.kube_client_wrapper_client.list_endpoints_for_all_namespaces(pretty=pretty_output, watch=watch)
        elif kind == "namespace":
            all_resources = self.kube_client_wrapper_client.list_namespace(pretty=pretty_output, watch=watch)
        elif kind == "node":
            all_resources = self.kube_client_wrapper_client.list_node(pretty=pretty_output, watch=watch)

        return all_resources

    def get_all_resources_details_for_namespace(self, **kwargs):
        '''
        This method will do RESTApi calls to the Kubernetes APIServer and get all deployed resource/s details
        for the given namespace
        :param kwargs: Dict with APIServer Details
        :return: api_output
        '''
        namespace = kwargs['NAMESPACE'] if 'NAMESPACE' in kwargs else 'default'
        watch = kwargs['WATCH'] if 'WATCH' in kwargs else False
        pretty_output = kwargs['PRETTY'] if 'PRETTY' in kwargs else False
        kind = kwargs['KIND'].lower() if 'KIND' in kwargs else 'pod'
        if kind == "pod" or kind == "deployment":
            all_namespaced_resources = self.kube_client_wrapper_client.list_namespaced_pod(namespace=namespace, pretty=pretty_output,
                                                                      watch=watch)
        elif kind == "service":
            all_namespaced_resources = self.kube_client_wrapper_client.list_namespaced_service(namespace=namespace, pretty=pretty_output,
                                                                      watch=watch)
        elif kind == "configmap":
            all_namespaced_resources = self.kube_client_wrapper_client.list_namespaced_config_map(namespace=namespace, pretty=pretty_output,
                                                                      watch=watch)
        elif kind == "secret":
            all_namespaced_resources = self.kube_client_wrapper_client.list_namespaced_secret(namespace=namespace, pretty=pretty_output,
                                                                      watch=watch)
        elif kind == "namespace" or kind == "node":
            # Not supported
            return None

        return all_namespaced_resources

    ############## Generic create operations ###################

    def create_resource(self, **kwargs):
        '''
        This method with create pod using the API
        :param kwargs: YML_LIST: List of YML Files
        :return: True or False
        '''
        create_output_fail = 0
        yml_list = kwargs['YML_LIST'] if 'YML_LIST' in kwargs else None
        namespace = kwargs['NAMESPACE'] if 'NAMESPACE' in kwargs else 'default'
        for yml in yml_list:
            yml_obj = self.util.get_yaml_dict_as_object(yml)
            namespace = yml_obj.metadata.namespace if hasattr(yml_obj.metadata, 'namespace') else yml_obj.metadata.name
            if namespace not in self.get_all_available_namespaces_names():
                create_namespace = self.kube_client_wrapper_client.create_namespace(body='')
            json_body = json.dumps(yml_obj, sort_keys=True, indent=2)
            kind =  yml_obj.kind.lower()
            create_output = ""
            if kind == "pod" or kind == "deployment":
                create_output = self.kube_client_wrapper_client.create_namespaced_pod(namespace, json.loads(json_body))
            elif kind == "secret":
                create_output = self.kube_client_wrapper_client.create_namespaced_service(namespace, json.loads(json_body))
            elif kind == "configmap":
                create_output = self.kube_client_wrapper_client.create_namespaced_config_map(namespace, json.loads(json_body))
            elif kind == "secret":
                create_output = self.kube_client_wrapper_client.create_namespaced_secret(namespace, json.loads(json_body))
            elif kind == "namespace":
                create_output = self.kube_client_wrapper_client.create_namespace(json.loads(json_body))
                
            if create_output:
                self.m_logger.info('Descriptor %s created' % create_output.metadata.name)
            else:
                create_output_fail += 1
                self.m_logger.error('Resource creation failed for the Descriptor : %s' % yml)
        return True if not create_output_fail else False

    ############## Resource specific parsing operations ###################

    def get_all_available_namespaces_names(self, **kwargs):
        '''
        This method gives the list of names of the all available namespaces in the K8s Cluster
        :param kwargs:
        :return: namespace_list
        '''
        namespaces_details = self.get_all_resources_details(KIND="namespace", **kwargs)
        return ['%s' % namespace.metadata.name for namespace in namespaces_details.items]

    def get_details_of_all_nodes(self, **kwargs):
        '''
        This method gets all output/details for all nodes available in the cluster
        :param kwargs: kwargs key/value
        :return: node_dict with all node details
        '''
        node_output = self.get_all_resources_details(KIND="node", **kwargs)

        # Select details and flatten
        node_details_dict = defaultdict(self.resource_details)
        for node in node_output.items:
            node_name = node.metadata.name
            node_details_dict[node_name]['node_name'] = node_name
            node_details_dict[node_name]['cluster_name'] = node.metadata.cluster_name
            node_details_dict[node_name]['namespace'] = node.metadata.namespace
            node_details_dict[node_name]['created_timestamp'] = node.metadata.creation_timestamp
            node_details_dict[node_name]['kubelet_version'] = node.status.node_info.kubelet_version
            node_details_dict[node_name]['os_image'] = node.status.node_info.os_image
            node_details_dict[node_name]['kernel_version'] = node.status.node_info.kernel_version
            node_role = 'Master' if 'node-role.kubernetes.io/master' in node.metadata.labels else 'Minion'
            node_details_dict[node_name]['node_role'] = node_role
            for address in node.status.addresses:
                node_details_dict[node_name][address.type] = address.address
            for condition in node.status.conditions:
                if 'Ready' in condition.type:
                    status = True if 'True' in condition.status else False
                    node_details_dict[node_name]['%s_%s' % (condition.type, 'State')] = status
                    node_details_dict[node_name]['%s_%s' % (condition.type, 'Message')] = condition.message
                    node_details_dict[node_name]['%s_%s' % (condition.type, 'Reason')] = condition.reason
                    node_details_dict[node_name]['%s_%s' % (condition.type,
                                                            'Latest_Heartbeat')] = condition.last_heartbeat_time
                    node_details_dict[node_name]['%s_%s' % (condition.type,
                                                            'Latest_Transition')] = condition.last_transition_time

        return node_details_dict

    def get_details_of_all_pods(self, **kwargs):
        '''
        This method gets all output/details for all pods available in a given NAMESPACE, if NAMESPACE is not
        provided in the kwargs, output/details for all pods in all namespaces is returned as pod_details_dict
        :param kwargs: kwargs key/value eg; POD_NAME, NAMESPACE
        :return: pod_details_dict with all pod details
        '''
        pod_output = self.get_all_resources_details_for_namespace(KIND="pod", **kwargs) if 'NAMESPACE' in kwargs \
                               else self.get_all_resources_details(KIND="pod", **kwargs)

        # Select details and flatten
        pod_details_dict = defaultdict(self.resource_details)
        for pod in pod_output.items:
            pod_status, pod_message, pod_reason = [], [], []
            pod_name = pod.metadata.name
            pod_details_dict[pod_name]['pod_name'] = '%s' % pod_name
            pod_details_dict[pod_name]['namespace'] = '%s' % pod.metadata.namespace
            containers = ['%s' % container.name for container in pod.spec.containers]
            pod_details_dict[pod_name]['containers'] = containers
            pod_details_dict[pod_name]['node_name'] = '%s' % pod.spec.node_name
            pod_details_dict[pod_name]['pod_ip'] = '%s' % pod.status.pod_ip
            pod_details_dict[pod_name]['host_ip'] = '%s' % pod.status.host_ip
            status = '%s' % pod.status.phase
            message = '%s' % pod.status.message
            reason = '%s' % pod.status.reason
            if pod.status.container_statuses:
                for container_id in pod.status.container_statuses:
                    container_state = container_id.state.running
                    container_waiting = container_id.state.waiting
                    if not container_state and 'Running' in status:
                        pod_status.append('%s Not Running' % container_id.name)
                    container_message = container_waiting.message if container_waiting else None
                    pod_message.append(container_message) if container_message else pod_message
                    container_reason = container_waiting.reason if container_waiting else None
                    pod_reason.append(container_reason) if container_reason else pod_reason
            pod_details_dict[pod_name]['status'] = ' & '.join(pod_status) if pod_status else status
            pod_details_dict[pod_name]['status_message'] = ' & '.join(pod_message) if pod_message else message
            pod_details_dict[pod_name]['status_reason'] = ' & '.join(pod_reason) if pod_reason else reason

        return pod_details_dict

    def get_details_of_all_services(self, **kwargs):
        '''
        This method gets all output/details for all services available in a given NAMESPACE, if NAMESPACE is not
        provided in the kwargs, output/details for all services in all namespaces is returned as pod_details_dict
        :param kwargs: kwargs key/value eg; POD_NAME, NAMESPACE
        :return: pod_details_dict with all pod details
        '''
        service_output = self.get_all_resources_details_for_namespace(KIND="service", **kwargs) if 'NAMESPACE' in kwargs \
                               else self.get_all_resources_details(KIND="service", **kwargs)

        # Select details and flatten
        service_details_dict = defaultdict(self.resource_details)
        for service in service_output.items:
            service_name = service.metadata.name
            service_details_dict[service_name]['service_name'] = '%s' % service_name
            service_details_dict[service_name]['namespace'] = '%s' % service.metadata.namespace
            service_details_dict[service_name]['ports'] = []
            for port in service.spec.ports:
                dict_port = { 
                        'name': port.name,
                        'node_port': port.node_port,
                        'port': port.port,
                        'protocol': port.protocol,
                        'target_port': port.target_port }
                service_details_dict[service_name]['ports'].append(dict_port)
            #service_details_dict[service_name]['endpoints'] = service.endpoints
            service_details_dict[service_name]['service_ip'] = '%s' % service.spec.cluster_ip

        return service_details_dict

# TODO Add parser for endpoints and ingresses
# print kube_client_wrapper.get_all_resources_details(KIND="ingress", PRETTY=True)
# print kube_client_wrapper.get_all_resources_details(KIND="endpoint", PRETTY=True)

############## Testing ###################

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

if __name__ == '__main__':
    kube_client_wrapper = KubeClientApiWrapper()

    print "==== NAMESPACES ===="
    namespace_list = kube_client_wrapper.get_all_available_namespaces_names()
    print namespace_list

    print "==== NODES ========="
    node_dict = kube_client_wrapper.get_details_of_all_nodes(PRETTY=True)
    print json.dumps(node_dict, cls=DateTimeEncoder, indent=4)

    print "==== PODS =========="
    pod_dict = kube_client_wrapper.get_details_of_all_pods()
    print json.dumps(pod_dict, indent=4)

    print "==== SERVICES ======"
    service_dict = kube_client_wrapper.get_details_of_all_services()
    print json.dumps(service_dict, cls=DateTimeEncoder, indent=4)

    # pod_create = kube_client_wrapper.create_resource(YML_LIST=['./mysqldb-service.yaml'])
    # print pod_create
