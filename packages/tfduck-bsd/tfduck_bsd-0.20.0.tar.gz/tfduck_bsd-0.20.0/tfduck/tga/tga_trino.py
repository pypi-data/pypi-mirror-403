"""
@des: 这个文件仅仅作为views，接口调用访问，归因内部不用这个文件
@des: 调用方法
if 1:  # spark的python环境指定
    os.environ["PYSPARK_PYTHON"] = (
        "/root/.pyenv/versions/celery4.4_virtualenv/bin/python"
    )
    os.environ["PYSPARK_DRIVER_PYTHON"] = (
        "/root/.pyenv/versions/celery4.4_virtualenv/bin/python"
    )

版本记录:
trino=0.327.0
pyspark=2.4
"""

import requests
import pandas

# import json
import time
import os
from tfduck.common.defines import BMOBJ

# from django.conf import settings
from tfduck.tga.base_tga import BaseTga
from trino.dbapi import connect as trino_connect


class ThinkDataTrinoQuery(BaseTga):
    """
    @des: thinkdata openapi查询基础类----这个只能再thinkdata内网执行
    """

    def __init__(self, trino_conn_info=["host", 0], media_root="/mydata/media"):
        """
        @des:初始化类
        """
        self.trino_conn_info = trino_conn_info
        self.media_root = media_root

    def gen_local_unique_file(self, ext="csv"):
        """
        @des:生成本地文件唯一路径
        """
        # media_root = settings.MEDIA_ROOT
        base_dir = os.path.join(self.media_root, "docs")
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        real_name = "%s%s.%s" % (BMOBJ.get_unique_id2(), BMOBJ.get_unique_id2(), ext)
        file_path = os.path.join(base_dir, real_name)
        return file_path

    def g_to_csv_notmp(
        self, filepath, df, index=True, compression=None, mode="w", header=True
    ):
        """
        @des: pandas生成csv文件---用于追加文件，不能用临时文件
        compression: 压缩格式 ‘gzip’, ‘bz2’, ‘zip’, ‘xz’.
        """
        tmp_filepath = filepath
        if index is None:  # 不保存行索引
            if compression is None:  # 不压缩
                df.to_csv(tmp_filepath, index=None, mode=mode, header=header)
            else:
                df.to_csv(
                    tmp_filepath,
                    index=None,
                    compression=compression,
                    mode=mode,
                    header=header,
                )
        else:
            if compression is None:  # 不压缩
                df.to_csv(tmp_filepath, mode=mode, header=header)
            else:
                df.to_csv(
                    tmp_filepath, compression=compression, mode=mode, header=header
                )
        return True

    def get_app_info(self):
        """
        @des: 获取应用信息
        """
        conn = trino_connect(
            host=self.trino_conn_info[0],
            port=int(self.trino_conn_info[1]),
            user="ta",
            catalog="mysql",
            schema="ta",
        )
        #
        result = []
        sql = """select project_id, project_name,appid, api_secret from ta_project_info where status=1"""
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        result = [
            {
                "project_id": x[0],
                "project_name": x[1],
                "appid": x[2],
                "api_secret": x[3],
            }
            for x in result
        ]
        return result

    def get_table_describe(self, table_name):
        """
        @des: 获取表结构
        """
        conn = trino_connect(
            host=self.trino_conn_info[0],
            port=int(self.trino_conn_info[1]),
            user="ta",
            catalog="hive",
            schema="ta",
        )
        cursor = conn.cursor()
        cursor.execute(f""" DESCRIBE {table_name} """)
        tk_fields = cursor.fetchall()
        return tk_fields

    def get_data_trino(
        self,
        ctx,
        sql,
        block_size=100000,
        fetch_size=10000,
        retry_count=2,
        read_timeout=300,
        upcount=None,
        print_size=100000,
        conn_timeout=30,
        retry_wait=1,
        all_str=False,
        timezone='UTC',
    ):
        '''
        @des:presto直连方式读取-----重试的方式----当get_data_csv接口出问题，则启用这个接口
        tobj = ThinkDataQuery("http://queryhost:port/querySql", "查询token",
                          ["presto直连的host", 直连的port])
        sql = """select * from v_event_7 where "$part_date"='2022-02-24' limit 100 """
        unique_path = tobj.get_data_raw_pyhive({}, sql)
        '''
        # unique_path = "./test.csv"
        unique_path = self.gen_local_unique_file()
        gol_e = None
        for i in range(retry_count):
            try:
                result = self.get_data_trino_i(
                    ctx,
                    unique_path,
                    sql,
                    block_size,
                    fetch_size,
                    read_timeout,
                    upcount,
                    print_size,
                    conn_timeout,
                    all_str,
                    timezone
                )
                return result
            except Exception as e:
                gol_e = e
                BMOBJ.remove_file(unique_path)
                BMOBJ.remove_folder(unique_path)
                # modify by yx 2024-05-08---加强出错重试---
                # if str(e).find("Read timed out") != -1:
                #     BMOBJ.clog(ctx, f'retry {i}')
                #     continue
                # else:
                #     break
                if 1:
                    time.sleep(retry_wait)
                    BMOBJ.clog(ctx, f"retry {i}")
                    continue
        if gol_e is not None:
            raise gol_e

    def get_data_trino_i(
        self,
        ctx,
        unique_path,
        sql,
        block_size=100000,
        fetch_size=10000,
        read_timeout=300,
        upcount=None,
        print_size=100000,
        conn_timeout=30,
        all_str=False,
        timezone='UTC',
    ):
        """
        @des: 内部调用
        """

        #
        BMOBJ.log_error("in query")
        session = requests.session()
        #
        datas = []
        i = 0  # 循环引用计数
        icount = 0  # 数据的数量
        cols = []  # 表头
        try:
            conn = trino_connect(
                host=self.trino_conn_info[0],
                port=int(self.trino_conn_info[1]),
                user="ta",
                catalog="hive",
                schema="ta",
                timezone=timezone, #Asia/Shanghai UTC # 很重要, 这里会影响传过来的时间的内容。如果这里拉取csv， spark读取，指定spark的时区是没有用的, 需要trino这里指定正确。 而且timezone如果不填，默认是执行脚本的本机时区.
                http_session=session,
                # 这里stream为true和false没有关系，fetchmany每次都会通过request_session传nexturl重新get获取数据
                # 参考pyhive/presto.py的_fetch_more，每次fetchmany其实是多次fetchone
                http_scheme="http",
                # --- 修改重点开始 ---
                # 1. SSL 验证直接作为参数传入
                verify=False,
                # 2. 超时设置直接使用 request_timeout 参数
                # requests 库支持传入 tuple (connect_timeout, read_timeout)
                request_timeout=(conn_timeout, read_timeout),
                # 3. stream 参数在 trino 客户端中不需要显式设置
                # trino 客户端默认的 cursor 实现就是分批拉取(paging)的
                # --- 修改重点结束 ---
            )

            cursor = conn.cursor()
            cursor.execute(sql)
            BMOBJ.clog(ctx, "文件大小")
            if 1:
                cols_description = cursor.description
                cols = [item[0] for item in cursor.description]
                # print(cols)
                df = pandas.DataFrame(data=[], columns=cols)  # 保存表头
                if all_str:
                    # 解决科学计数法的问题
                    df = df.astype(str)
                    df = df.astype("string")
                #
                self.g_to_csv_notmp(unique_path, df, index=None)
            # for row in cursor.fetchall():
            rows = []
            # def yx_fetch_many():
            #     for kkk in range(5):  # 最多重试五次
            #         try:
            #             myres = cursor.fetchmany(fetch_size)
            #             return myres
            #         except Exception as e:
            #             if str(e).find("Read timed out")!=-1:
            #                 continue
            #             else:
            #                 raise e

            def yx_fetch_many():
                myres = cursor.fetchmany(fetch_size)
                return myres

            rows = yx_fetch_many()
            while rows:
                for row in rows:
                    if not row:
                        continue
                    datas.append(row)
                    i += 1
                    if len(datas) == block_size:  # 1000000条保存一次
                        df = pandas.DataFrame(data=datas, columns=cols)  # 保存表头
                        if all_str:
                            # 解决科学计数法的问题
                            df = df.astype(str)
                            df = df.astype("string")
                        #
                        self.g_to_csv_notmp(
                            unique_path, df, index=None, mode="a", header=False
                        )  # 追加保存
                        icount += block_size
                        datas = []
                    if i % print_size == 0:
                        BMOBJ.clog(ctx, i)
                rows = yx_fetch_many()
            #
            BMOBJ.clog(ctx, f"total: {i}")
            if len(datas) > 0:  # 保存最后收尾的
                df = pandas.DataFrame(data=datas, columns=cols)  # 保存表头
                self.g_to_csv_notmp(
                    unique_path, df, index=None, mode="a", header=False
                )  # 追加保存
                if all_str:
                    # 解决科学计数法的问题
                    df = df.astype(str)
                    df = df.astype("string")
                #
                icount += len(datas)
                datas = []
        except Exception as e:
            # BMOBJ.log_error("get data error", e)
            BMOBJ.clog(ctx, "get data error:", f"{e}")
            if upcount is not None:
                if i < upcount:  # 看是否达到可以接受的数量，否则重新查询
                    raise e
            else:
                raise e
        finally:
            try:
                conn.close()
            except:
                pass
            try:
                session.close()
            except:
                pass
        return unique_path, cols_description

    def get_spark_schema_from_trino(
        self, cursor_description, force_string_types=False, array_and_row_mode=1
    ):
        """
        @des: 利用 Trino 的元数据生成 Spark Schema
        @param force_string_types: 是否强制所有字段为字符串类型，用于先读取所有数据防止类型转换错误
        """
        from pyspark.sql.types import (
            StringType,
            LongType,
            DoubleType,
            BooleanType,
            StructField,
            StructType,
            TimestampType,
            IntegerType,
            FloatType,
            NullType,
        )
        #
        # 这里和td_producer_playdaddy_tf_2/src/local_hdfs_to_raw.py以及td_producer_playdaddy/td_producer_playdaddy_tf_2/src/k8s/hdfs_to_raw/main.py 一致即可。根据array_and_row_as_string参数,设置是否array和row类型为nullType类型，如果不是nullType。则转为json字符串即可。

        dtypes = []
        for tk_field in cursor_description:
            field_name, field_type = tk_field[:2]
            field_name = str(field_name)

            # 如果force_string_types为True，所有字段都设置为StringType
            if force_string_types:
                spark_field_type = StringType
            else:
                spark_field_type = StringType
                if field_type in ("timestamp", "timestamp(3)"):
                    spark_field_type = TimestampType
                elif field_type == "bigint":
                    spark_field_type = LongType
                elif field_type == "integer":
                    spark_field_type = IntegerType
                elif field_type == "double":
                    spark_field_type = DoubleType
                elif field_type == "float":
                    spark_field_type = FloatType
                elif field_type == "boolean":
                    spark_field_type = BooleanType
                elif field_type == "varchar":
                    spark_field_type = StringType
                # 支持tga的array类型--如果不想要这种类型可以删除掉
                elif field_type.startswith("array"):
                    if array_and_row_mode in (1, 2):
                        spark_field_type = StringType
                    else:
                        spark_field_type = NullType
                elif field_type.startswith("row"):
                    if array_and_row_mode in (1, 2):
                        spark_field_type = StringType
                    else:
                        spark_field_type = NullType

            dtypes.append(StructField(field_name, spark_field_type(), True))
        # print(dtypes)
        schema = StructType(dtypes)
        return schema

    def gen_tga_spark_df(
        self,
        ctx,
        spark_client,
        sql,
        is_cache=True,
        is_direct_connect=False,
        array_and_row_mode=1,
        timezone='UTC',
    ):
        """
        @des: 生成spark dataframe
        @params: spark_client: spark客户端, 可以通过下面get_spark方法创建;
        @注意: 调用这个方法最后一定要
        finally:
            spark_client.catalog.clearCache()  # 清除缓存
            spark_client.stop()
        @注意: is_direct_connect=True, 目前没有实现，先不要这样用。
        @params:
        array_and_row_mode:
            1-----将array和row转为string类型保留json字符串
            2-----将array和row转为string类型但是内容为null
            3-----将array和row转为NullType类型
        @注意: spark_client的时区要和timezone保持一致，否则时间类型会出问题
        """
        try:
            unique_path = ""
            from pyspark import StorageLevel
            from pyspark.sql.functions import col, lit
            from pyspark.sql.types import NullType, StringType

            if not is_direct_connect:  # 下载文件再读取
                unique_path, cols_description = self.get_data_trino(
                    ctx, sql, all_str=True, timezone=timezone
                )
                if cols_description is not None:
                    # 先用字符串读取所有字段，再根据需要转换类型,防止读取失败所有数据都为null的情况
                    # 创建字符串类型的schema用于初始读取
                    string_schema = self.get_spark_schema_from_trino(
                        cols_description, force_string_types=True
                    )

                    # 使用字符串schema读取CSV文件
                    spark_df = (
                        spark_client.read.option("header", "true")
                        .option("quote", '"')
                        .option("escape", '"')
                        .option("nullValue", "None")  # 这个要不要加后面再观察
                        .option("multiLine", "true")
                        .option("timestampFormat", "yyyy-MM-dd HH:mm:ss.SSS")
                        .schema(string_schema)
                        .csv(unique_path)
                    )
                    # 获取正确的类型schema用于后续类型转换
                    correct_schema = self.get_spark_schema_from_trino(
                        cols_description,
                        array_and_row_mode=array_and_row_mode,
                    )

                    if 1:  # 批量转换
                        select_expressions = []
                        for struct_field in correct_schema.fields:
                            col_name = struct_field.name
                            target_type = struct_field.dataType
                            if not isinstance(target_type, NullType):
                                oper = col(col_name).cast(target_type).alias(col_name)
                            else:
                                oper = lit(None).cast(NullType()).alias(col_name)
                            select_expressions.append(oper)
                        spark_df = spark_df.select(*select_expressions)
                    else:  # 逐列进行类型转换
                        for struct_field in correct_schema.fields:
                            col_name = struct_field.name
                            target_type = struct_field.dataType
                            if not isinstance(target_type, NullType):
                                # 对每列尝试转换类型，转换失败的保持字符串类型
                                spark_df = spark_df.withColumn(
                                    col_name, col(col_name).cast(target_type)
                                )
                            else:
                                spark_df = spark_df.withColumn(
                                    col_name, lit(None).cast(NullType())
                                )

                    if array_and_row_mode == 2:
                        # 将 array 和 row 类型的列内容设置为 null
                        for tk_field in cols_description:
                            f_name, f_type = tk_field[:2]
                            if f_type.startswith("array") or f_type.startswith("row"):
                                spark_df = spark_df.withColumn(
                                    f_name, lit(None).cast(StringType())
                                )
                else:
                    spark_df = (
                        spark_client.read.option("header", "true")
                        .option("nullValue", "None")
                        .option("inferSchema", "true")
                        .csv(unique_path)
                    )
            else:  # 直接连接trino读取----目前未实现----
                spark_df = (
                    spark_client.read.format("jdbc")
                    .option("driver", "io.trino.jdbc.TrinoDriver")
                    .option(
                        "url",
                        f"jdbc:trino://{self.trino_conn_info[0]}:{self.trino_conn_info[1]}/hive/ta",
                    )
                    .option("user", "ta")
                    # .option("dbtable", f"""({sql}) as t""")
                    .option("query", sql)
                    .load()
                )
            if is_cache:
                spark_df.persist(StorageLevel.MEMORY_AND_DISK)
            count = spark_df.count()  # 这一句必须执行，否则不会真正的将数据持久化
            BMOBJ.clog(ctx, f"spark read {count} rows")
            return spark_df
        finally:
            BMOBJ.remove_file(unique_path)
            pass

    def get_spark(self, cpus=1, memory="512M", time_zone=None):
        """
        @time_zone: 时区字符串，比如'Asia/Shanghai'
        """
        import uuid
        from pyspark.sql import SparkSession, Row
        from pyspark.sql import functions
        from pyspark import SparkContext, SparkConf
        from pyspark.sql import SparkSession, Row

        # jars_path = (
        #     "/opt/data_warehose/maxcompute_dev/trino-jdbc-435.jar"
        # )
        conf = (
            SparkConf()
            .setAppName(f"td_spark_txtfile_{uuid.uuid4().hex}")
            .setMaster(f"local[{cpus}]")
            .set("spark.debug.maxToStringFields", "400")
            # .set('spark.driver.cores', '2')
            # .set('spark.executor.cores', '2')
            .set("spark.driver.memory", f"{memory}")
            # .set("spark.jars", jars_path)
            # .set('spark.executor.memory', '1G') # 这里千万不要和driver设置一样，否则会出奇怪的问题，比如csv找不到这些
            # .set(
            #     "spark.driver.extraClassPath",
            #     ":".join(sagemaker_pyspark.classpath_jars()),
            # )
            # .set("fs.s3a.access.key", self.get_access_key())
            # .set("fs.s3a.secret.key", self.get_secret_key())
            # .set("com.amazonaws.services.s3a.enableV4", "true")
            # .set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        )
        #
        if time_zone is None:
            spark = SparkSession.builder.config(conf=conf).getOrCreate()
        else:
            spark = (
                SparkSession.builder.config(conf=conf)
                # 这两句有效果
                .config("spark.driver.extraJavaOptions", f"-Duser.timezone={time_zone}")
                # 这两句有效果
                .config(
                    "spark.executor.extraJavaOptions", f"-Duser.timezone={time_zone}"
                )
                .getOrCreate()
            )
        return spark


if __name__ == "__main__":
    oper = ThinkDataTrinoQuery(
        trino_conn_info=["127.0.0.1", 80],
        media_root="/Users/yuanxiao/Downloads/0media",
    )
    if 0:
        app_info = oper.get_app_info()
        print(app_info)
    if 0:
        table_info = oper.get_table_describe("v_user_62")
        print(table_info)
    if 0:
        data_file, cols_description = oper.get_data_trino(
            {},
            """select "#user_id", "#account_id", "#reg_time" from v_user_62 limit 100""",
            block_size=100000,
            fetch_size=10000,
            read_timeout=300,
            all_str=True,
        )
    if 1:  # 可以自己修改文件数据，看看spark读取不同的类型数据是怎么做的
        try:
            sql = """select "#user_id", "#account_id", "#active_time", "#reg_time" from v_user_62 limit 100"""
            # 测试array字段
            # sql = """select "#user_id", g_taskpass_task_info, g_box from v_event_48 where "$part_date"='2026-01-29' and g_taskpass_task_info is not null limit 10"""
            # 测试row字段
            # sql = """select "#user_id", g_taskpass_task_info, g_box from v_event_48 where "$part_date"='2026-01-29' and g_box is not null limit 10"""
            spark_client = oper.get_spark(cpus=2, memory="2G",time_zone='UTC')
            spark_df = oper.gen_tga_spark_df(
                {},
                spark_client,
                sql,
                is_cache=True,
                is_direct_connect=False,
                # array_and_row_mode=1
            )
            # spark show 显示完全
            spark_df.show(10, truncate=False)
            # 转为csv看是否正常--overwrite模式
            spark_df.coalesce(1).write.option("header", "true").option(
                "timestampFormat", "yyyy-MM-dd HH:mm:ss.SSS"
            ).option("quote", '"').option("escape", '"').option(
                "multiLine", "true"
            ).csv(
                "/Users/yuanxiao/Downloads/0media/docs/spark_trino_test_output",
                mode="overwrite",
            )
        finally:
            try:
                spark_client.catalog.clearCache()  # 清除缓存
                spark_client.stop()
            except:
                pass
