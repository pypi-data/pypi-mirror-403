"""
auhtor: yuanxiao
datetime: 20210423
python3.8
pyspark 提交阿里云ask集群管理器
pip install kubernetes==12.0.1 oss2==2.19.1

如果报错【CA_KEY_TOO_SMALL】则执行(因为k8s的老的秘钥创建是1024位的):
参考: https://www.cnblogs.com/dingnosakura/p/17815410.html
"""

if 1:
    try:
        # 解决 【CA_KEY_TOO_SMALL】的报错，利用猴子补丁[monkey Patching ] ，适用于urllib3==2.x版本
        import urllib3
        from urllib3.util.ssl_ import create_urllib3_context

        # 创建自定义 SSL 上下文（复用 urllib3 默认配置基础上修改）
        ctx = create_urllib3_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=0")  # 例如降低安全级别
        ctx.load_default_certs()  # 确保加载系统证书

        # 保存原始 PoolManager 初始化方法（便于回滚）
        _original_poolmanager_init = urllib3.PoolManager.__init__

        def _patched_poolmanager_init(self, *args, **kwargs):
            # 仅在未显式传递 ssl_context 时注入自定义上下文
            if "ssl_context" not in kwargs:
                kwargs["ssl_context"] = ctx
            _original_poolmanager_init(self, *args, **kwargs)

        # 应用补丁（确保只执行一次）
        if urllib3.PoolManager.__init__ != _patched_poolmanager_init:
            urllib3.PoolManager.__init__ = _patched_poolmanager_init
    except Exception as _:
        pass

import json

# from tfduck.common.defines import BMOBJ, Et
# from tfduck.oss.oss import AliyunOss
from kubernetes import client, config, utils
import uuid
import arrow
import os
import base64
import subprocess
from io import BytesIO, StringIO
import yaml


class K8sManage(object):
    """ """

    def __init__(
        self, ctx, k8s_conn_yaml=None, k8s_conn_json=None, namespace="default"
    ):
        """
        @des: 初始化
        k8s_conn_yaml ---- k8s的配置文件，从阿里云下载的，保存为yaml文件
        k8s_conn_json ---- 从k8s的配置yaml文件解析成的json对象,解析方法: (list(yaml.safe_load_all(open(self.k8s_conn_config, "r")))[0])
        """
        """
        全局初始化
        """
        self.ctx = ctx
        self.k8s_conn_config = k8s_conn_yaml
        self.k8s_conn_json = k8s_conn_json
        self.namespace = namespace
        """
        生成k8s客户端
        """
        self.k8s_client = self.get_k8s_client(mode="v1")
        self.k8s_api_client = self.get_k8s_client(mode="api")
        #
        # print(self.k8s_client, self.k8s_api_client)

    def get_k8s_client(self, mode="v1"):
        """
        @des: 获取k8s操作客户端
        例子  https://github.com/kubernetes-client/python/tree/master/examples
        api文档 https://github.com/kubernetes-client/python/blob/master/kubernetes/README.md
        """
        # if 1:
        #     # 从yaml生成json文件进行登录，方便后面程序配置
        #     with open(self.k8s_conn_config, "r") as f:
        #         config_jsons = yaml.safe_load_all(f)
        #         config_json = list(config_jsons)[0]
        #         print(111, config_json)
        #         config.load_kube_config_from_dict(config_json)
        # else:
        #     config.load_kube_config(self.k8s_conn_config)
        if self.k8s_conn_config:
            config.load_kube_config(self.k8s_conn_config)
        elif self.k8s_conn_json:
            # 这样获取
            # with open(self.k8s_conn_config, "r") as f:
            #     config_jsons = yaml.safe_load_all(f)
            #     k8s_conn_json = list(config_jsons)[0]
            config.load_kube_config_from_dict(self.k8s_conn_json)
        if mode == "v1":
            c = client.CoreV1Api()
        elif mode == "api":
            c = client.ApiClient()
        return c
        # print("Listing pods with their IPs:")
        # ret = v1.list_pod_for_all_namespaces(watch=False)
        # for i in ret.items:
        #     print("%s\t%s\t%s" %
        #           (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

    def get_all_pods(self):
        """
        @des: 获取所有的k8s的pod, 默认命名空间的
        """
        # print("Listing pods with their IPs:")
        ret = self.k8s_client.list_pod_for_all_namespaces(watch=False)
        pod_infos = []
        for i in ret.items:
            if i.metadata.namespace == self.namespace:
                pod_infos.append(
                    {
                        "name": i.metadata.name,
                        "status": i.status.phase,
                        "create_time": i.metadata.creation_timestamp,
                    }
                )
        return pod_infos

    def get_pod_info(self, pod_name):
        """
        @des: 获取pod的基础信息，状态等信息
        """
        # resp = self.k8s_client.read_namespaced_pod_status(
        #     name="tfspark-test-7200-driver-1e5ab8f2a41d11eb93c3acde48001122", namespace='default')
        # resp = self.k8s_client.read_namespaced_pod(
        #     name="tfspark-test-7200-driver-1e5ab8f2a41d11eb93c3acde48001122", namespace='default')
        pod_obj = self.k8s_client.read_namespaced_pod(
            name=pod_name, namespace=self.namespace
        )
        # print(resp)
        # print(resp.metadata.name, resp.status.phase)
        # return resp.status.phase # Pending,Succeeded, Running, Failed
        return pod_obj

    def get_pod_log(self, pod_name, lines_count=1000):
        """
        @des: 获取pod的日志--测试成功
        """
        # print(help(self.k8s_client.read_namespaced_pod_log))
        # log_content = self.k8s_client.read_namespaced_pod_log(
        #     'tfspark-test-7200-driver-c697aadea41d11eb9d2bacde48001122', 'default', pretty=True, tail_lines=1)  # container='spark-kubernetes-driver'
        log_content = self.k8s_client.read_namespaced_pod_log(
            pod_name, self.namespace, pretty=True, tail_lines=lines_count
        )  # tail_lines 表示从结尾开始获取日志的行数
        # print(log_content)
        return log_content

    # def patch_pod_info(self, pod_name):
    #     """
    #     @des: 修改pod的信息，包括状态
    #     """
    #     pod_obj = self.get_pod_info(pod_name)
    #     pod_obj.status.phase = ""
    #     # print(help(self.k8s_client.patch_namespaced_pod))
    #     self.k8s_client.patch_namespaced_pod(pod_name, 'default', pod_obj)
    def create_by_yaml(self, yaml_file):
        """ """
        result = utils.create_from_yaml(
            k8s_client=self.k8s_api_client,
            yaml_file=yaml_file,
            namespace=self.namespace,
        )
        # print(result)
        # print("count: ", len(result))

    def create_by_yaml_str(self, yaml_str):
        """
        @des: 通过yaml字符串创建pod
        """
        with StringIO(yaml_str) as f:
            yml_document_all = yaml.safe_load_all(f)
            failures = []
            k8s_objects = []
            for yml_document in yml_document_all:
                # print(111, json.dumps(yml_document)) ---- 后面也可以编写json创建
                try:
                    created = utils.create_from_dict(
                        k8s_client=self.k8s_api_client,
                        data=yml_document,
                        namespace=self.namespace,
                    )
                    k8s_objects.append(created)
                except utils.FailToCreateError as failure:
                    failures.extend(failure.api_exceptions)
            if failures:
                raise utils.FailToCreateError(failures)
        # print(k8s_objects)
        # print("count: ", len(k8s_objects))
        return k8s_objects

    def create_by_json(self, json_obj):
        """
        @des: 通过json对象创建pod
        """
        failures = []
        try:
            created = utils.create_from_dict(
                k8s_client=self.k8s_api_client,
                data=json_obj,
                namespace=self.namespace,
            )
        except utils.FailToCreateError as failure:
            failures.extend(failure.api_exceptions)
        if failures:
            raise utils.FailToCreateError(failures)
        return created

    def delete_pod(self, pod_name):
        """
        @des: 删除pod
        delete是删除---
        delete_namespaced_pod
        """
        # print(help(self.k8s_client.delete_namespaced_pod))
        # pod_obj = self.get_pod_info(pod_name)
        # print(pod_obj.metadata.name, pod_obj.metadata.creation_timestamp, pod_obj.status.phase)
        # pod_create = pod_obj.metadata.creation_timestamp
        # status = pod_obj.status.phase
        r = self.k8s_client.delete_namespaced_pod(pod_name, self.namespace)
        return r