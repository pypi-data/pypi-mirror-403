"""
auhtor: yuanxiao
datetime: 20210423
python3.8
ask serverless的提交任务
pip install kubernetes==12.0.1
"""

import json
# from tfduck.common.defines import BMOBJ, Et

# from tfduck.oss.oss import AliyunOss
import arrow
import time
import os
import base64
import subprocess
import uuid

# if 1:
#     from k8s_manage import K8sManage
#     from k8s_upload_oss import AliyunOss


# class YxBMOBJ(object):
#     def clog(self, ctx, *args):
#         print(*args)
#         pass

#     def get_file_path(self, path):
#         """
#         @des: 文件的真实路径
#         """
#         # self.dj44_base_dir = "/Users/yuanxiao/workspace/djcelery44/djcelery44"
#         # return os.path.join(self.dj44_base_dir, os.path.join("dags/sptasks/p_code", path))
#         return os.path.abspath(path)


# BMOBJ = YxBMOBJ()

if 1:
    from tfduck.serverless_k8s.k8s_manage import K8sManage
    from tfduck.common.defines import BMOBJ, Et
    from tfduck.oss.oss import AliyunOss


class Et(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg


class ServerlessTaskManage(object):
    """ """

    def __init__(
        self,
        ctx,
        code_path,
        max_run_time=7200,
        # 参考main的调用
        task_config={
            # pod的名称前缀-必填
            "task_name": "yxtestpodtask",
            # cpu的使用量-必填
            "cpu": "500m",
            # 内存的使用量-必填
            "memory": "500Mi",
            # 镜像地址-必填
            "image_url": "registry-intl.cn-beijing.aliyuncs.com/talefun/python311:base",
            # serverless集群挂载的oss的pvc的名称,必须在【duck-task】命名空间的pvc-必填
            "pvc_name": "tfduck-k8s-pvc",
            # pypi的源，如果为空字符串，则使用官方源
            "pypi_mirror": "https://pypi.tuna.tsinghua.edu.cn/simple",
            # 执行python脚本参数---最好是base64编码的json字符串
            "params": "xxx",
        },
        #
        is_debug=False,
        project_name="playdayy-bj",
        pull_pod_success_log=True,
        pull_pod_fail_log=True,
        is_async=False,
        project_configs={},
    ):
        """
        ######################################特别注意############################################
        code_path: 代码路径
        project_configs: 所有项目配置
        project_name: 项目名称，在project_configs里面找到对应的key
        params: 用法
        param_b64_content = base64.b64encode(json.dumps(self.task_params).encode(
            'utf8')).decode()  # 将参数编辑为base64，防止出现特殊字符分割参数
        # 解码
        # ds = json.loads(base64.b64decode(param_b64_content).decode('utf8'))
        ######################################
        """
        """
        校验
        """
        task_sub_name = task_config.get("task_name", "default")
        if task_sub_name is None:
            raise Et(2, "task name must not be none")
        task_sub_name = task_sub_name.strip()
        if task_sub_name == "":
            raise Et(2, "task name must not be '' ")
        if task_sub_name.find("-") != -1:
            raise Et(2, "task name not clude - char")
        """
        工程配置
        """
        self.project_name = project_name  # 切换本地调试集群
        self.project_configs = project_configs
        self.project_conf = self.project_configs[self.project_name]
        """
        全局初始化
        """
        self.ctx = ctx
        self.is_debug = is_debug  # 如果为true，就在mac本地调试
        self.max_run_time = max_run_time  # pod task最大运行时间
        self.code_path = code_path
        self.pull_pod_success_log = pull_pod_success_log
        self.pull_pod_fail_log = pull_pod_fail_log
        self.task_config = task_config
        self.pod_name = f"{task_sub_name}-{self.max_run_time}-{uuid.uuid4().hex[:8]}"
        self.oss_root_name = "oss_data"
        self.is_async = is_async
        """
        系统oss的配置
        """
        self.oss_config = self.project_conf["oss_pv"]
        """
        生成k8s客户端
        """
        self.name_space = "duck-task"
        self.k8s_client = K8sManage(
            ctx,
            k8s_conn_json=self.project_conf["k8s_serverless_conn"],
            namespace=self.name_space,
        )

    def upload_code(self):
        """
        上传执行代码到oss
        """
        now = arrow.utcnow()
        now_str = now.format("YYYY-MM-DD")
        oss_config = self.oss_config
        ctx = self.ctx
        uoss = AliyunOss(
            oss_config["bucket"],
            oss_config["access_key"],
            oss_config["secret_key"],
            oss_config["endpoint_public"],
        )
        oss_file_path = f"code/{now_str}/{uuid.uuid4().hex}/"  # 注意必须斜杠结尾
        if self.code_path:
            local_file_path = BMOBJ.get_file_path(self.code_path)
            if not local_file_path.startswith("/"):
                local_file_path = f"/{local_file_path}"
            uoss.upload_oss(
                ctx,
                local_file_path,
                oss_file_path,
                False,
                False,
                isrm=True,
                isdel=False,
            )  # 递归查找, 不删除本地文件
        else:
            raise Et("code_path不能为空")
        # uoss.download_oss(ctx, local_file_path+"xx", oss_file_path, isrm=True, isdel=False)  # 测试下载
        self.real_code_path = os.path.join(f"/{self.oss_root_name}", oss_file_path)

    def clean_code(self):
        """
        清理代码
        """
        ctx = self.ctx
        oss_config = self.oss_config
        uoss = AliyunOss(
            oss_config["bucket"],
            oss_config["access_key"],
            oss_config["secret_key"],
            oss_config["endpoint_public"],
        )
        # self.real_code_path 不要self.oss_root_name部分即可
        oss_code_path = self.real_code_path.replace(f"/{self.oss_root_name}/", "")
        BMOBJ.clog(ctx, "clean code path:", oss_code_path)
        uoss.delete_prefix_oss(ctx, oss_code_path, isrm=True)

    def get_submit_task_cmd(self):
        """
        构建
        """
        pypi_mirror = self.task_config.get("pypi_mirror", "")
        pypi_mirror_host = (
            pypi_mirror.split("://")[1].split("/")[0] if pypi_mirror else ""
        )
        pypi_i = (
            f"-i {pypi_mirror} --trusted-host {pypi_mirror_host}" if pypi_mirror else ""
        )
        """
        json命令，参考该目录的k8s_manage.py的如何根据yaml解析json的方式
        参考yaml_to_json.py
        """
        cmd_json = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": self.pod_name, "namespace": self.name_space},
            "spec": {
                "containers": [
                    {
                        "name": "python311-container",
                        "image": self.task_config["image_url"],
                        "command": ["/bin/bash", "-c"],
                        "args": [
                            f"""cd {self.real_code_path} && \
                                python3 --version && \
                                    pip install -U pip {pypi_i} && \
                                    pip install arrow {pypi_i} && \
                                    pip install -r requirements.txt {pypi_i} && \
                                    python main.py --params {self.task_config["params"]}
                            """
                        ],
                        "resources": {
                            "requests": {
                                "memory": self.task_config["memory"],
                                "cpu": self.task_config["cpu"],
                            },
                            "limits": {
                                "memory": self.task_config["memory"],
                                "cpu": self.task_config["cpu"],
                            },
                        },
                        "volumeMounts": [
                            {
                                "name": "tfduck-k8s-pv",
                                "mountPath": f"/{self.oss_root_name}",
                            }
                        ],
                    }
                ],
                "volumes": [
                    {
                        "name": "tfduck-k8s-pv",
                        "persistentVolumeClaim": {
                            "claimName": self.task_config["pvc_name"]
                        },
                    }
                ],
                "restartPolicy": "Never",
            },
        }
        return cmd_json

    def submit_task(self):
        """
        提交任务
        """
        result = True
        ctx = self.ctx
        """
        执行任务
        """
        submit_json = self.get_submit_task_cmd()
        try:
            self.k8s_client.create_by_json(submit_json)
        except Exception as e:
            raise e
        """
        判断任务是否完成---不从日志里面去判断，这样会拉回来很多日志
        """
        pod_obj = self.k8s_client.get_pod_info(self.pod_name)
        if self.is_async:
            BMOBJ.clog(ctx, pod_obj.status.phase)
            if pod_obj.status.phase in ["Pending", "Running"]:
                BMOBJ.clog(ctx, "task success runing")
            else:
                BMOBJ.clog(ctx, "task fail")
                result = False
        else:
            start = time.time()
            #
            wait_time = 0
            # 第一阶段判断--进入Running状态--
            pd_1 = 0
            pd_1_status = ["Running", "Succeeded", "Failed"]
            max_pd_1 = 30  # 最大等待次数
            while pod_obj.status.phase not in pd_1_status and pd_1 < max_pd_1:
                time.sleep(10)
                try:
                    pod_obj = self.k8s_client.get_pod_info(self.pod_name)
                except Exception as _:
                    pass
                pd_1 += 1
            if pod_obj.status.phase not in pd_1_status:
                BMOBJ.clog(
                    ctx,
                    f"task fail in {time.time() - start} seconds state: {pod_obj.status.phase}",
                )
                result = False
                return result
            # 第二阶段判断--进入Succeeded或者Failed状态--
            while (
                pod_obj.status.phase not in ["Succeeded", "Failed"]
                or wait_time > self.max_run_time
            ):
                time.sleep(10)
                try:
                    pod_obj = self.k8s_client.get_pod_info(self.pod_name)
                except Exception as _:
                    pass
                wait_time = time.time() - start
            #
            BMOBJ.clog(ctx, f"pod status: {pod_obj.status.phase}")
            #
            if pod_obj.status.phase == "Succeeded":
                BMOBJ.clog(ctx, "task success complated")
                if self.pull_pod_success_log:
                    success_log = self.k8s_client.get_pod_log(self.pod_name, 500)
                    BMOBJ.clog(ctx, "pod task success log ----------:", success_log)
            else:
                BMOBJ.clog(ctx, "task fail-------------------error log:")
                if self.pull_pod_fail_log:
                    error_log = self.k8s_client.get_pod_log(self.pod_name, 1000)
                    BMOBJ.clog(ctx, "pod task fail log ----------:", error_log)
                result = False
        return result

    def sync(self):
        """
        all in one
        """
        try:
            self.upload_code()
            result = self.submit_task()
        finally:
            if not self.is_async:
                # 清理代码
                try:
                    self.clean_code()
                except Exception as _:
                    pass
                # 清理pod(我觉得正式环境不需要在这里清理，定时调度清理即可)
                if self.is_debug:
                    try:
                        self.k8s_client.delete_pod(self.pod_name)
                    except Exception as _:
                        pass
        return result
