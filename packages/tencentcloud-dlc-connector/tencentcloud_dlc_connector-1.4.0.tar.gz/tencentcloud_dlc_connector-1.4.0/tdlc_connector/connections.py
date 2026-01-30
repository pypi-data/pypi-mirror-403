
from tdlc_connector import api, results, constants, cursors, exceptions, formats

import time
import re
import logging

LOG = logging.getLogger(__name__)

REGEXP_ROWS = re.compile(r'\d+(?= rows affected)')


class DlcConnection:

    def __init__(self,
            *,
            region=None,
            secret_id=None,
            secret_key=None,
            token=None,
            endpoint=None,
            catalog=constants.Catalog.DATALAKECATALOG,
            engine="public-engine",
            resource_group = None,
            engine_type=constants.EngineType.AUTO,
            result_style=constants.ResultStyles.LIST,
            download=False,
            mode=constants.Mode.ALL,
            polling_interval=0.5,
            database='',
            config={},
            driver_size=constants.PodSize.SMALL,
            executor_size=constants.PodSize.SMALL,
            executor_num=1,
            executor_max_num=1,
            callback=None,
            callback_events=None,
            ) -> None:

        LOG.debug(f"初始化 DlcConnection: region={region}, engine={engine}, catalog={catalog}, "
                  f"engine_type={engine_type}, result_style={result_style}, download={download}, mode={mode}")

        self._p = {}

        if not region:
            raise exceptions.ProgrammingError("region is required.")

        if not secret_id:
            raise exceptions.ProgrammingError("secret-id is required.")

        if not secret_key:
            raise exceptions.ProgrammingError("secret-key is required.")

        if not engine:
            raise exceptions.ProgrammingError("engine is required.")

        if engine_type not in constants.EngineType.ENUM_VALUES():
            raise exceptions.ProgrammingError(f"Argument engine_type='{engine_type}' is not valid.")

        if result_style not in constants.ResultStyles.ENUM_VALUES():
            raise exceptions.ProgrammingError(f"Argument result_type='{result_style}' is not valid.")

        if driver_size not in constants.PodSize.ENUM_VALUES():
            raise exceptions.ProgrammingError(f"Argument driver_size='{driver_size}' is not valid.")

        if executor_size not in constants.PodSize.ENUM_VALUES():
            raise exceptions.ProgrammingError(f"Argument executor_size='{executor_size}' is not valid.")

        mode = mode.lower()
        if mode not in constants.Mode.ENUM_VALUES():
            raise exceptions.ProgrammingError(f"Argument mode='{mode}' is not valid.")

        if not download and mode == constants.Mode.STREAM:
            LOG.warning("'stream' mode is only supported when download=True, using 'lasy' mode instead.")
            mode = constants.Mode.LASY

        self._engine = engine
        self._resource_group = resource_group
        self._catalog = catalog
        self._loop_interval = polling_interval
        self._result_style = result_style
        self._download = download
        self._mode = mode
        self._config = config
        self._database = database
        self._driver_size = driver_size
        self._executor_size = executor_size
        self._executor_num = executor_num
        self._executor_max_num = executor_max_num

        self._callback = callback
        if callback is None:
            self._callback = lambda statement_id, state: None

        if callback_events is None:
            self._callback_events = []
        elif callback_events in constants.CallbackEvent.ENUM_VALUES():
            self._callback_events = []
            self._callback_events.append(callback_events)
        elif isinstance(callback_events, list or tuple):
            self._callback_events = callback_events
        else:
            self._callback_events = []
            LOG.warning("callback events are invalid and will be ignored.")

        if constants.CallbackEvent.ON_CHANGE in self._callback_events:
            self._callback_events = [constants.CallbackEvent.ON_INIT,
                                     constants.CallbackEvent.ON_RUNNING,
                                     constants.CallbackEvent.ON_SUCCESS,
                                     constants.CallbackEvent.ON_ERROR,
                                     constants.CallbackEvent.ON_KILL,
                                     constants.CallbackEvent.ON_CHANGE]


        self._client = api.APIClient(region, secret_id, secret_key, token, endpoint)
        LOG.debug(f"API 客户端初始化完成")

        if engine_type == constants.EngineType.AUTO:
            LOG.debug(f"自动检测引擎类型: engine={self._engine}")
            engine_type = self._client.describe_engine_type(self._engine)
            LOG.info(f"引擎类型检测结果: engine={self._engine}, type={engine_type}")

        if engine_type == constants.EngineType.UNKNOWN:
            raise exceptions.ProgrammingError('The engine type is unknown, please SET the engine type or change a engine.')

        self._engine_type = engine_type

        # SPARK-BATCH 集群
        if self._engine_type == constants.EngineType.SPARK_BATCH:

            self._loop_interval = 5

            if self._download == False:
                LOG.warning('The engine is only support download = True.')
                self._download = True


        # 添加配置

        if not self._config:
            self._config = {}

        if formats.FORMAT_STRING_NULL is not None:
            self._config.setdefault('livy.sql.result.format.option.nullValue', formats.FORMAT_STRING_NULL)

        if formats.RESULT_TYPE == constants.ResultType.PARQUET:
            self._config.setdefault('livy.sql.result.format', formats.RESULT_TYPE)

        if self._download == True and formats.FORMAT_STRING_NULL == '\0':
            raise exceptions.ProgrammingError("FORMAT_STRING_NULL='\\0' is not compartible for download mode.")
        LOG.info(f"Connection initialized: engine={self._engine}, engine_type={self._engine_type}, download={self._download}, mode={self._mode}, catalog={self._catalog}")

    def open(self):
        pass

    def close(self):
        pass

    def connect(self):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass

    def cursor(self):
        return cursors.Cursor(self)


    def kill(self):
        try:
            if self._p:
                state = self._p['state']
                statement_id = self._p['statement_id']
                LOG.info(f"尝试终止任务: task_id={statement_id}, state={state}")

                if state in [constants.TaskStatus.INIT, constants.TaskStatus.RUNNING]:
                    i = input(f"The task[{statement_id}] is running, press 'Y' to kill.")
                    if i.upper() == 'Y':
                        LOG.warning(f"用户确认终止任务: task_id={statement_id}")
                        self._client.kill_statement(statement_id)
        except KeyboardInterrupt as e:
            LOG.warning("用户取消终止操作")
            exit(0)
        except Exception as e:
            LOG.error(f"终止任务失败: {e}")
            raise e



    def execute_statement_using_spark_batch(self, statement):
        LOG.info(f"使用 Spark Batch 执行 SQL: engine={self._engine}")

        batch_id = self._client.submit_statement_to_spark_batch(
            self._engine,
            self._driver_size,
            self._executor_size,
            self._executor_num,
            self._executor_max_num,
            statement,
            self._config
        )
        LOG.info(f"Spark Batch 任务已提交: batch_id={batch_id}")

        extra = {}
        state = constants.TaskStatus.INIT
        yield state, batch_id, extra

        while True:
            response = self._client.get_statements_from_spark_batch(batch_id)
            extra['message'] = response['message']
            if response['state'] == constants.TaskStatus.SUCCESS:
                LOG.info(f"Spark Batch 任务执行成功: batch_id={batch_id}")
                extra = self._client.get_statement_result_for_spark_batch(response['tasks'][0].TaskId)
            yield response['state'], batch_id, extra


    def execute_statement_using_spark_or_presto_sql(self, statement):
        LOG.info(f"使用 {self._engine_type} 执行 SQL: engine={self._engine}, catalog={self._catalog}")

        statement_id = self._client.submit_statement(self._engine, self._resource_group, self._engine_type, self._catalog, statement, self._database, self._config)
        LOG.info(f"SQL 任务已提交: task_id={statement_id}")
        state = constants.TaskStatus.INIT
        yield state, statement_id, {}

        while True:
            response = self._client.get_statement(statement_id)
            yield response['state'], statement_id, response


    def execute_statement(self, statement):
        func = None
        if self._engine_type in [constants.EngineType.SPARK_SQL,constants.EngineType.PRESTO]:
            func = self.execute_statement_using_spark_or_presto_sql
        else:
            func = self.execute_statement_using_spark_batch
        iter = func(statement)

        _state = None
        path = None
        message = ''

        while True:
            state, statement_id, extra = next(iter)

            self._p = {
                'state': state,
                'statement_id': statement_id
            }

            if state != _state:
                _state = state
                if state in self._callback_events:
                    self._callback(statement_id, state)

            if state == constants.TaskStatus.KILL:
                LOG.warning(f"任务被终止: task_id={statement_id}")
                raise exceptions.OperationalError(f"The task[{statement_id}] is killed.")

            if state == constants.TaskStatus.ERROR:
                LOG.error(f"任务执行失败: task_id={statement_id}, message={extra['message']}")
                raise exceptions.ProgrammingError(extra["message"])

            if state == constants.TaskStatus.SUCCESS:
                path = extra['path']
                message = extra['rowAffectInfo']
                LOG.info(f"SQL 执行成功: task_id={statement_id}, path={path}")
                break

            time.sleep(self._loop_interval)


        prefix = 'REMOTE_'
        if self._download:
            prefix = 'COS_'

        name = prefix + self._mode
        LOG.debug(f"使用结果生成器: {name}")

        g = results.RESULT_GENERATORS[name](self._client, statement_id, self._result_style, path)

        r = REGEXP_ROWS.findall(message)
        total = 0
        if r:
            total = int(r[0])

        return total, g.description, g.iterator