
from tencentcloud.common.profile import http_profile, client_profile
from tencentcloud.common.credential import Credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.dlc.v20210125 import dlc_client, models, errorcodes
from tdlc_connector import constants, exceptions

from qcloud_cos import CosS3Client, CosConfig

import time
import base64
import json
import logging 
import urllib.parse


LOG = logging.getLogger(__name__)


class APIClient:
    
    def __init__(self, region, secret_id, secret_key, token=None, dlc_endpoint=None, cos_endpoint=None):
        LOG.debug(f"初始化 APIClient: region={region}, dlc_endpoint={dlc_endpoint}, cos_endpoint={cos_endpoint}")

        self._region = region
        self._cos_endpoint = cos_endpoint

        credential = Credential(secret_id, secret_key, token)
        profile = client_profile.ClientProfile(httpProfile=http_profile.HttpProfile(endpoint=dlc_endpoint))

        self._DLC_CLIENT = WrappedDlcClient(credential, region, profile)
        self._COS_CLIENT = None

        self._lakefs_url = None
        self._cos_auth = {
            'secretId': secret_id,
            'secretKey': secret_key,
            'token': token,
            'expiredTime': None
        }
        LOG.debug("APIClient 初始化完成")
    
    def enable_lakefs_token(self, url):
        self._lakefs_url = url
        self._cos_auth['expiredTime'] = 0
   
    def get_cos_client(self):

        current = int(time.time())
        expired_time = self._cos_auth['expiredTime']
        ahead = 180

        LOG.debug(f"检查 COS Token 状态: expired_time={expired_time}, current={current}")
        if expired_time is not None and expired_time - ahead < current:
            LOG.info(f"COS Token 即将过期或已过期, 刷新 Token...")
            auth = self.get_lakefs_auth(self._lakefs_url)
            self._cos_auth['secretId'] = auth['secretId']
            self._cos_auth['secretKey'] = auth['secretKey']
            self._cos_auth['token'] = auth['token']
            self._cos_auth['expiredTime'] = auth['expiredTime']
            self._COS_CLIENT = None
            LOG.info(f"COS Token 已刷新, 新过期时间: {auth['expiredTime']}")

        if self._COS_CLIENT is None and self._DLC_CLIENT is not None:
            LOG.debug(f"创建 COS 客户端: region={self._region}, endpoint={self._cos_endpoint}")
            config = CosConfig(Region=self._region,
                               Secret_id=self._cos_auth['secretId'], 
                               Secret_key=self._cos_auth['secretKey'], 
                               Token=self._cos_auth['token'], 
                               Endpoint=self._cos_endpoint)
            self._COS_CLIENT = CosS3Client(config)
            LOG.debug("COS 客户端创建成功")
        return self._COS_CLIENT

    def describe_engine_type(self, name):
        LOG.debug(f"查询引擎类型: engine_name={name}")

        request = models.DescribeDataEnginesRequest()
        filter = models.Filter()
        filter.Name = 'data-engine-name'
        filter.Values = [name, ]
        request.Filters = [filter]

        response = self._DLC_CLIENT.DescribeDataEngines(request)
        LOG.info(f"查询引擎类型响应: RequestId={response.RequestId}, TotalCount={response.TotalCount}")

        if response.TotalCount == 0:
            raise exceptions.ProgrammingError(f"The engine[{name}] is not exists.")
        
        engine = response.DataEngines[0]
        LOG.info(f"Engine: name={name}, EngineExecType={engine.EngineExecType}, EngineGeneration={engine.EngineGeneration}")

        if engine.EngineType == 'presto':
            return constants.EngineType.PRESTO
        
        if engine.EngineType == 'spark':
            if engine.EngineExecType == 'SQL' or (engine.EngineExecType == 'BATCH' and engine.EngineGeneration == "Native"):
                return constants.EngineType.SPARK_SQL
            elif engine.EngineExecType == 'BATCH':
                return constants.EngineType.SPARK_BATCH
        
        LOG.warning(f"无法识别的引擎类型: EngineType={engine.EngineType}, EngineExecType={engine.EngineExecType}")
        return constants.EngineType.UNKNOWN

    def kill_statement(self, statement_id):
        LOG.info(f"发送终止任务请求: task_id={statement_id}")

        request = CancelTasksRequest()
        request._TaskId = [statement_id]
        response = self._DLC_CLIENT.CancelTasks(request)
        LOG.info(f"任务终止请求已发送: task_id={statement_id}, RequestId={response.RequestId}")

    def submit_statement_to_spark_batch(self, engine, driver_size, executor_size, executor_num, executor_max_num, statement, config={}):
        LOG.debug(f"提交 Spark Batch SQL: engine={engine}, driver_size={driver_size}, "
                  f"executor_size={executor_size}, executor_num={executor_num}, executor_max_num={executor_max_num}")

        request = models.CreateSparkSessionBatchSQLRequest()
        request.DataEngineName = engine
        request.DriverSize = driver_size
        request.ExecutorSize = executor_size
        request.ExecutorNumbers = executor_num
        request.ExecutorMaxNumbers = executor_max_num
        request.ExecuteSQL = base64.b64encode(statement.encode('utf8')).decode('utf8')
        request.Arguments = []

        if 'dlc.eni' in config:
            pair = models.KVPair()
            pair.Key = 'dlc.eni'
            pair.Value = config.pop('dlc.eni')
            request.Arguments.append(pair)
        
        if 'dlc.role.arn' in config:
            pair = models.KVPair()
            pair.Key = 'dlc.role.arn'
            pair.Value = config.pop('dlc.role.arn')
            request.Arguments.append(pair)
        
        if config:
            pair = models.KVPair()
            pair.Key = 'dlc.sql.set.config'
            values = []
            for key, value in config.items():
                values.append(f"set {key}={value}")

            pair.Value = base64.b64encode(';'.join(values).encode('utf8')).decode('utf8')
            request.Arguments.append(pair)

        response = self._DLC_CLIENT.CreateSparkSessionBatchSQL(request)
        LOG.info(f"Spark Batch SQL 提交成功: RequestId={response.RequestId}, BatchId={response.BatchId}")
        return response.BatchId

    def get_statements_from_spark_batch(self, batch_id, convert=True):
        LOG.debug(f"查询 Spark Batch 任务状态: batch_id={batch_id}")

        request = models.DescribeSparkSessionBatchSQLRequest()
        request.BatchId = batch_id

        response = self._DLC_CLIENT.DescribeSparkSessionBatchSQL(request)
        LOG.info(f"Spark Batch 任务状态: RequestId={response.RequestId}, batch_id={batch_id}, state={response.State}")

        state = response.State

        if convert:
            state = constants.SparkBatchTaskStatus.toTaskStatus(state)
            LOG.debug(f"Converted state={state}")

        return {
            'state': state,
            'tasks': response.Tasks,
            'message': response.Event
        }

    def get_statement_result_for_spark_batch(self, task_id):
        return self.get_statement_results_for_spark_batch([task_id])[task_id]

    def get_statement_results_for_spark_batch(self, task_ids):

        request = models.DescribeNotebookSessionStatementSqlResultRequest()

        task_set = {}
        for task_id in task_ids:
            request.TaskId = task_id
            response = self._DLC_CLIENT.DescribeNotebookSessionStatementSqlResult(request)
            LOG.info(f"Task {task_id} result: RequestId={response.RequestId}, OutputPath={response.OutputPath}")
            task_set[task_id] = {
                'rowAffectInfo': '',
                'path': response.OutputPath,
            }
        return task_set

    def submit_statement(self, engine, resource_group, engine_type, catalog, statement, database='', config={}):
        LOG.debug(f"提交 SQL 任务: engine={engine}, resource_group={resource_group}, "
                  f"engine_type={engine_type}, catalog={catalog}, database={database}")

        request = models.CreateTaskRequest()
        request.DataEngineName = engine
        request.ResourceGroupName = resource_group
        request.DatasourceConnectionName = catalog
        request.Task = models.Task()
        request.DatabaseName = database

        task = models.SQLTask()
        task.SQL = base64.b64encode(statement.encode('utf8')).decode('utf8')
        task.Config = []

        for k, v in config.items():
            pair = models.KVPair()
            pair.Key = k
            pair.Value = str(v)
            task.Config.append(pair)

        if engine_type == constants.EngineType.SPARK:
            request.Task.SparkSQLTask = task
        else:
            request.Task.SQLTask = task

        response = self._DLC_CLIENT.CreateTask(request)
        LOG.info(f"SQL 任务提交成功: RequestId={response.RequestId}, TaskId={response.TaskId}")

        return response.TaskId

    def get_statements(self, *statement_ids):
        LOG.debug(f"查询任务状态: statement_ids={statement_ids}")
            
        request = models.DescribeTasksRequest()

        f = models.Filter()
        f.Name = "task-id"
        f.Values = statement_ids
        request.Filters = [f]

        response = self._DLC_CLIENT.DescribeTasks(request)
        LOG.info(f"任务状态查询结果: RequestId={response.RequestId}, 返回 {len(response.TaskList)} 条记录")

        task_set = {}

        for task in response.TaskList:
            task_set[task.Id] = {
                "rowAffectInfo": task.RowAffectInfo,
                "message": task.OutputMessage,
                "path": task.OutputPath,
                "state": task.State,
            }
        return task_set
    
    def get_statement(self, statement_id):
        return self.get_statements(statement_id)[statement_id]
        
    def get_statement_results(self, statement_id, next=None):
        LOG.debug(f"获取任务结果: task_id={statement_id}, next_token={next}")

        request = models.DescribeTaskResultRequest()
        request.TaskId = statement_id
        request.NextToken = next

        response = self._DLC_CLIENT.DescribeTaskResult(request)
        LOG.info(f"任务结果: RequestId={response.RequestId}, task_id={statement_id}, state={response.TaskInfo.State}, "
                 f"result_count={len(json.loads(response.TaskInfo.ResultSet)) if response.TaskInfo.ResultSet else 0}")
        columns = []
        for schema in response.TaskInfo.ResultSchema:
            columns.append(to_column(schema))

        return {
            "requestId": response.RequestId,
            "state": response.TaskInfo.State,
            "sqlType": response.TaskInfo.SQLType,
            "message": response.TaskInfo.OutputMessage,
            "rowAffectInfo": response.TaskInfo.RowAffectInfo,
            "path": response.TaskInfo.OutputPath,
            "columns":columns,
            "results": json.loads(response.TaskInfo.ResultSet) if response.TaskInfo.ResultSet else [],
            "next": response.TaskInfo.NextToken
        }

    def get_lakefs_auth(self, url):
        LOG.debug(f"获取 LakeFS 认证: url={url}")
        request = DescribeLakeFsPathRequest()
        request._FsPath = url
        response = self._DLC_CLIENT.DescribeLakeFsPath(request)
        LOG.info(f"LakeFS 认证获取成功: RequestId={response.RequestId}")
        return {
            "requestId": response._RequestId,
            "secretId": urllib.parse.unquote(response._AccessToken._SecretId),
            "secretKey": urllib.parse.unquote(response._AccessToken._SecretKey),
            "token": urllib.parse.unquote(response._AccessToken._Token),
            "expiredTime": response._AccessToken._ExpiredTime,
        }

    def object_exists(self, bucket, key):
        LOG.debug(f"检查 COS 对象是否存在: bucket={bucket}, key={key}")
        return self.get_cos_client().object_exists(bucket, key)

    def get_cos_object_stream(self, bucket, key):
        LOG.debug(f"获取 COS 对象流: bucket={bucket}, key={key}")
        return self.get_cos_client().get_object(Bucket=bucket, Key=key)['Body'].get_raw_stream()

    def get_cos_object_header_bytes(self, bucket, key, size=4):
        """
        获取 COS 对象的头部字节（使用 Range 请求）
        
        Args:
            bucket: 存储桶名称
            key: 对象键
            size: 需要获取的字节数，默认 4 字节
            
        Returns:
            bytes: 文件头部的字节数据
        """
        LOG.debug(f"获取 COS 对象头部字节: bucket={bucket}, key={key}, size={size}")
        response = self.get_cos_client().get_object(
            Bucket=bucket,
            Key=key,
            Range=f'bytes=0-{size - 1}'
        )
        return response['Body'].get_raw_stream().read(size)

    def get_cos_object_stream_to_file(self, bucket, key, name):
        LOG.debug(f"下载 COS 对象到文件: bucket={bucket}, key={key}, file={name}")
        return self.get_cos_client().get_object(Bucket=bucket, Key=key)['Body'].get_stream_to_file(name)

    def iter_cos_objects(self, bucket, prefix):
        LOG.debug(f"遍历 COS 对象: bucket={bucket}, prefix={prefix}")
        marker = ""
        while True:
            response = self.get_cos_client().list_objects(
                Bucket=bucket,
                Prefix=prefix.strip('/') + "/",
                Marker=marker,
            )

            contents = response.get('Contents', [])

            for item in contents:
                key = item['Key'].strip('/')
                size = int(item['Size'])

                if item['Key'] == prefix or key.endswith('_SUCCESS') or size == 0:
                    # 过滤 parent 文件夹
                    # 过滤 _SUCCESS 文件
                    # 过滤 size == 0 对象
                    continue

                yield item

            if response['IsTruncated'] == 'false':
                break 
            marker = response['NextMarker']


def to_column(schema):
    return {
        "name": schema.Name,
        "type": schema.Type,
        "nullable": schema.Nullable == 'NULLABLE',
        "scale": schema.Scale,
        "precision": schema.Precision,
        "is_partition": schema.IsPartition,
        "comment": schema.Comment,
    }


class DescribeLakeFsPathRequest(models.AbstractModel):

    def __init__(self):
        self._FsPath = None
    
    def _deserialize(self, params):
        self._FsPath = params.get("FsPath")


class DescribeLakeFsPathResponse(models.AbstractModel):

    def __init__(self) -> None:
        self._RequestId = None
        self._AccessToken = None

    @property
    def RequestId(self):
        r"""唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。
        :rtype: str
        """
        return self._RequestId

    def _deserialize(self, params):
        
        if params.get("AccessToken") is not None:
            self._AccessToken =  LakeFileSystemToken()
            self._AccessToken._deserialize(params.get("AccessToken"))
        self._RequestId = params.get("RequestId")


class LakeFileSystemToken(models.AbstractModel):

    def __init__(self) -> None:

        self._SecretId = None
        self._SecretKey = None
        self._Token = None
        self._ExpiredTime = None
        self._IssueTime = None
    
    def _deserialize(self, params):
        self._SecretId = params.get("SecretId")
        self._SecretKey = params.get("SecretKey")
        self._Token = params.get("Token")
        self._ExpiredTime = params.get("ExpiredTime")
        self._IssueTime = params.get("IssueTime")


class CancelTasksRequest(models.AbstractModel):

    def __init__(self):
        self._TaskId = None
    
    def _deserialize(self, params):
        self._TaskId = params.get("TaskId")


class CancelTasksResponse(models.AbstractModel):

    def __init__(self) -> None:
        self._RequestId = None

    @property
    def RequestId(self):
        r"""唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。
        :rtype: str
        """
        return self._RequestId

    def _deserialize(self, params):
        self._RequestId = params.get("RequestId")


class WrappedDlcClient(dlc_client.DlcClient):

    RETRY_TIMES = 3

    def __init__(self, credential, region, profile=None):
        super().__init__(credential, region, profile)

    def DescribeLakeFsPath(self, request):
        try:
            params = request._serialize()
            headers = request.headers
            body = self.call("DescribeLakeFsPath", params, headers=headers)
            response = json.loads(body)
            if "Error" not in response["Response"]:
                model = DescribeLakeFsPathResponse()
                model._deserialize(response["Response"])
                return model
            else:
                code = response["Response"]["Error"]["Code"]
                message = response["Response"]["Error"]["Message"]
                reqid = response["Response"]["RequestId"]
                raise TencentCloudSDKException(code, message, reqid)
        except Exception as e:
            if isinstance(e, TencentCloudSDKException):
                raise
            else:
                raise TencentCloudSDKException(e.message, e.message)

    def CancelTasks(self, request):
        try:
            params = request._serialize()
            headers = request.headers
            body = self.call("CancelTasks", params, headers=headers)
            response = json.loads(body)
            if "Error" not in response["Response"]:
                model = CancelTasksResponse()
                model._deserialize(response["Response"])
                return model
            else:
                code = response["Response"]["Error"]["Code"]
                message = response["Response"]["Error"]["Message"]
                reqid = response["Response"]["RequestId"]
                raise TencentCloudSDKException(code, message, reqid)
        except Exception as e:
            if isinstance(e, TencentCloudSDKException):
                raise
            else:
                raise TencentCloudSDKException(e.message, e.message)

    def call(self, action, params, options=None, headers=None):
        LOG.debug(f"调用 DLC API: action={action}")
        retry = 0
        start_time = time.time()

        err = None

        while retry < self.RETRY_TIMES:
            retry += 1
            try:
                if retry > 1:
                    LOG.warning(f"DLC API 重试: action={action}, 第 {retry}/{self.RETRY_TIMES} 次")
                
                body = super().call(action, params, options, headers)
                
                # hack error message
                r = json.loads(body)
                request_id = r['Response'].get('RequestId', 'unknown')
                
                if 'Error' in r['Response']:
                    error_code = r['Response']['Error'].get('Code', 'unknown')
                    LOG.warning(f"DLC API 返回错误: action={action}, RequestId={request_id}, ErrorCode={error_code}")
                    
                    if 'Detail' in r['Response']['Error']:
                        try:
                            o = json.loads(r['Response']['Error']['Detail'])
                            r['Response']['Error']['Message'] = o['errMsg']
                            return json.dumps(r)
                        except Exception as e:
                            LOG.warning(e)
                            r['Response']['Error']['Message'] = r['Response']['Error']['Detail']
                else:
                    elapsed = time.time() - start_time
                    LOG.debug(f"DLC API 调用成功: action={action}, RequestId={request_id}, 耗时={elapsed:.3f}s")
                    
                return body
            # except TencentCloudSDKException as e:
            #     LOG.error(e)
            #     err = e
            #     if e.code in [errorcodes.RESOURCENOTFOUND_DATAENGINENOTFOUND, ]:
            #         retry = self.RETRY_TIMES
            except Exception as e:
                LOG.error(f"DLC API 调用异常: action={action}, 第 {retry}/{self.RETRY_TIMES} 次, error={e}")
                err = e

        if err is not None:
            LOG.error(f"DLC API 调用最终失败: action={action}, 已重试 {self.RETRY_TIMES} 次")
            raise err

        return body