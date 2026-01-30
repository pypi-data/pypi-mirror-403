from tdlc_connector import formats, constants, api, exceptions
import json
import urllib.parse
import re
import os
import csv
import tempfile
import logging


LOG = logging.getLogger(__name__)


class Column:

    def __init__(self, name, type, nullable, is_partition=False, precision=0, scale=0, comment=None) -> None:

        self.name = name
        self.type = type
        self.nullable = nullable
        self.is_partition = is_partition
        self.precision = precision
        self.scale = scale

        self._fn_type = formats.getConvert(self.type)
    
    def to(self, value):
        v = value 
        try:
            if formats.RESULT_TYPE == constants.ResultType.PARQUET:
                return v.as_py()
            v = self._fn_type(value, nullable=self.nullable, precision=self.precision, scale=self.scale)
        except Exception as e:
            LOG.error(f"类型转换失败: column={self.name}, type={self.type}, value={repr(value)[:100]}, error={e}")
        return v
    
REGEXP_ROWS = re.compile(r'\d+(?= rows affected)')


class ResultGenerator:

    def __init__(self, client: api.APIClient, statement_id, result_style, url, *args, **kwargs) -> None:
        LOG.debug(f"初始化 ResultGenerator: task_id={statement_id}, result_style={result_style}, url={url}")

        self._client = client
        self._statement_id = statement_id
        self._result_style = result_style
        self._url = url

        self._columns = []

        self._row_handler = None

        if self._result_style == constants.ResultStyles.DICT:
            self._row_handler = lambda row: {self._columns[i].name:  self._columns[i].to(row[i]) for i in range(0, len(row))}
        else:
            self._row_handler = lambda row: tuple(self._columns[i].to(row[i]) for i in range(0, len(row)))
        
        self._initialize()
        LOG.debug(f"ResultGenerator 初始化完成: 列数={len(self._columns)}")
    
            
    @property
    def description(self):
        return tuple([(column.name, formats.getTypeCode(column.type), None, None, column.precision, column.scale, column.nullable) for column in self._columns])

    def _initialize(self, *args, **kwargs):
        pass

    def _iter_rows(self):
        pass

    @property
    def iterator(self):
        for row in self._iter_rows():
            yield self._row_handler(row)


class LasyRemoteResultGenerator(ResultGenerator):

    def __init__(self, client: api.APIClient, statement_id, result_style, url, *args, **kwargs) -> None:
        LOG.debug(f"初始化 LasyRemoteResultGenerator: task_id={statement_id}")

        self._next_token = None
        self._results = []

        super().__init__(client, statement_id, result_style, url, *args, **kwargs)

    def _initialize(self):
        LOG.debug(f"LasyRemoteResultGenerator._initialize: 获取远程结果")

        response = self._client.get_statement_results(self._statement_id)
        if response['state'] != constants.TaskStatus.SUCCESS:
            raise exceptions.ProgrammingError(f"Remote task state error. RequestId={response['requestId']}")

        for column in response['columns']:
            self._columns.append(Column(**column))

        self._next_token = response['next']
        self._results = response['results']
        LOG.debug(f"LasyRemoteResultGenerator 初始化完成: 首批结果数={len(self._results)}, has_next={self._next_token is not None}")

    def _iter_rows(self):
        LOG.debug(f"LasyRemoteResultGenerator._iter_rows: 开始遍历结果")
        total_rows = 0

        for row in self._results:
            total_rows += 1
            yield row

        next = self._next_token
        page = 1
        while next:
            page += 1
            LOG.debug(f"获取下一页远程结果: page={page}")
            response = self._client.get_statement_results(self._statement_id, next)
            if response['state'] != constants.TaskStatus.SUCCESS:
                raise exceptions.ProgrammingError(f"Remote task state error. RequestId={response['requestId']}")
            LOG.debug(f"获取到 {len(response['results'])} 行数据")
            for row in response['results']:
                total_rows += 1
                yield row
            next = response['next']
        
        LOG.info(f"LasyRemoteResultGenerator 遍历完成: 总页数={page}, 总行数={total_rows}")
    

class RemoteResultGenerator(LasyRemoteResultGenerator):

    def _iter_rows(self):
        LOG.debug(f"RemoteResultGenerator._iter_rows: 预加载所有结果")

        results = []
        
        for row in super()._iter_rows():
            results.append(row)

        LOG.info(f"RemoteResultGenerator 预加载完成: 总行数={len(results)}")
        for row in results:
            yield row


def parse_url(url):

    parser = urllib.parse.urlparse(url)

    scheme = parser.scheme
    netloc = parser.netloc
    path = parser.path
    LOG.debug(f"Parsed: scheme={scheme}, netloc={netloc}, path={path}")

    bucket = netloc
    if scheme == constants.FileSystem.LAKEFS:
        _, bucket = netloc.split('@')

    return scheme, bucket, path.lstrip('/')


# Parquet 文件魔数标识
PARQUET_MAGIC = b'PAR1'


def detect_file_type(file_path):
    """
    检测文件实际类型（通过文件头魔数）

    Args:
        file_path: 文件路径

    Returns:
        constants.ResultType.PARQUET 或 constants.ResultType.CSV
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header == PARQUET_MAGIC:
                LOG.debug(f"检测到 Parquet 文件: {file_path}")
                return constants.ResultType.PARQUET
    except Exception as e:
        LOG.warning(f"检测文件类型失败: {file_path}, error={e}")

    LOG.debug(f"默认使用 CSV 格式: {file_path}")
    return constants.ResultType.CSV


def detect_file_type_from_bytes(header_bytes):
    """
    通过文件头字节检测文件类型

    Args:
        header_bytes: 文件头部的字节数据（至少 4 字节）

    Returns:
        constants.ResultType.PARQUET 或 constants.ResultType.CSV
    """
    if header_bytes and len(header_bytes) >= 4 and header_bytes[:4] == PARQUET_MAGIC:
        LOG.debug("检测到 Parquet 文件（通过字节头）")
        return constants.ResultType.PARQUET
    LOG.debug("默认使用 CSV 格式（通过字节头）")
    return constants.ResultType.CSV


def get_file_iter_handler(file_path):
    """
    根据文件类型获取对应的迭代处理器

    Args:
        file_path: 文件路径

    Returns:
        对应文件类型的迭代器函数
    """
    file_type = detect_file_type(file_path)
    if file_type == constants.ResultType.PARQUET:
        return iter_file_parquet
    return iter_file_csv


def iter_file_csv(name):

    f = open(name, encoding="utf8")
    reader = csv.reader((line.replace('\0', '') for line in f), escapechar=formats.RESULT_ESCAPE_CHAR, delimiter=formats.RESULT_DELIMITER, quotechar=formats.RESULT_QUOTE_CHAR)
    next(reader) # skip header

    for line in reader:
        yield line

    f.close()


def iter_file_parquet(name, batch_size=1000):
    """
    Args:
        name: Parquet 文件路径
        batch_size: 每批读取的行数，默认 1000 行

    Yields:
        tuple: 每行数据的元组
    """
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(name)
    try:
        # 使用 iter_batches 流式读取，每次只加载 batch_size 行到内存
        for batch in pf.iter_batches(batch_size=batch_size):
            batch_dict = batch.to_pydict()
            column_names = batch.schema.names
            # 获取当前批次的行数
            num_rows = batch.num_rows
            # 按行迭代
            for i in range(num_rows):
                yield tuple(batch_dict[col][i] for col in column_names)
    finally:
        pf.close()


class LasyCOSResultGenerator(ResultGenerator):

    def __init__(self, client: api.APIClient, statement_id, result_style, path, *args, **kwargs) -> None:
        LOG.debug(f"初始化 LasyCOSResultGenerator: task_id={statement_id}, path={path}")

        self._scheme = None
        self._bucket = None
        self._key = None

        super().__init__(client, statement_id, result_style, path, *args, **kwargs)

    def _initialize(self, *args, **kwargs):
        LOG.debug(f"LasyCOSResultGenerator._initialize: 解析 COS URL")

        self._scheme, self._bucket, self._key = parse_url(self._url)
        LOG.debug(f"COS 路径解析结果: scheme={self._scheme}, bucket={self._bucket}, key={self._key}")

        if self._scheme == constants.FileSystem.LAKEFS:
            LOG.debug("启用 LakeFS Token 认证")
            self._client.enable_lakefs_token(self._url)
        
        key = os.path.join(self._key, constants.CosKey.RESULT_META)

        if self._client.object_exists(self._bucket, key):
            LOG.debug(f"读取结果元数据: key={key}")
            stream = self._client.get_cos_object_stream(self._bucket, key)
            meta = json.load(stream)
            for column in meta['columns']:
                self._columns.append(Column(**column))
            LOG.debug(f"元数据解析完成: 列数={len(self._columns)}")

    def _iter_rows(self):
        LOG.debug(f"LasyCOSResultGenerator._iter_rows: 开始从 COS 遍历结果")

        prefix = os.path.join(self._key, constants.CosKey.RESULT_DATA)
        file_count = 0
        for item in self._client.iter_cos_objects(self._bucket, prefix):
            file_count += 1
            name = tempfile.mktemp(prefix=f"RESULT-{self._statement_id}")
            LOG.debug(f"下载结果文件 [{file_count}]: key={item['Key']}, size={item['Size']}, temp_file={name}")
            self._client.get_cos_object_stream_to_file(self._bucket, item['Key'], name)

            # 根据实际文件类型动态选择处理器
            iter_file_handler = get_file_iter_handler(name)
            try:
                for line in iter_file_handler(name):
                    yield line
            finally:
                os.remove(name)
                LOG.debug(f"临时文件已删除: {name}")


class COSResultGenerator(LasyCOSResultGenerator):

    def _iter_rows(self):
        LOG.debug(f"COSResultGenerator._iter_rows: 预下载所有结果文件")

        files = []
        prefix = os.path.join(self._key, constants.CosKey.RESULT_DATA)
        for item in self._client.iter_cos_objects(self._bucket, prefix):

            name = tempfile.mktemp(prefix=f"RESULT-{self._statement_id}")
            LOG.debug(f"下载结果文件: key={item['Key']}, size={item['Size']}, temp_file={name}")
            self._client.get_cos_object_stream_to_file(self._bucket, item['Key'], name)
            files.append(name)

        LOG.info(f"COSResultGenerator 预下载完成: 文件数={len(files)}")
        for file in files:
            # 根据实际文件类型动态选择处理器
            iter_file_handler = get_file_iter_handler(file)
            try:
                for line in iter_file_handler(file):
                    yield line
            finally:
                os.remove(file)
                LOG.debug(f"临时文件已删除: {file}")


def iter_streaming_lines(stream):

    while True:
        line = stream.readline()
        if not line:
            break

        yield line.decode('utf8')


class StreamingCOSResultGenerator(LasyCOSResultGenerator):

    def _iter_rows(self):
        LOG.debug(f"StreamingCOSResultGenerator._iter_rows: 流式读取 COS 结果")
        prefix = os.path.join(self._key, constants.CosKey.RESULT_DATA)
        file_count = 0
        total_rows = 0
        for item in self._client.iter_cos_objects(self._bucket, prefix):
            file_count += 1
            LOG.debug(f"流式读取文件 [{file_count}]: key={item['Key']}, size={item['Size']}")
            
            # 仅下载文件头部 4 字节检测文件类型（使用 Range 请求，避免下载整个文件）
            header_bytes = self._client.get_cos_object_header_bytes(self._bucket, item['Key'], size=4)
            file_type = detect_file_type_from_bytes(header_bytes)
            
            if file_type == constants.ResultType.PARQUET:
                # Parquet 文件无法流式解析，流式模式下不支持
                raise NotImplementedError(
                    f"流式读取模式(STREAM)不支持 Parquet 格式文件"
                )
            else:
                # CSV 文件：直接使用流式读取
                LOG.debug(f"CSV 文件使用流式读取: {item['Key']}")
                stream = self._client.get_cos_object_stream(self._bucket, item['Key'])
                stream.readline()  # skip header
                for line in csv.reader(iter_streaming_lines(stream), escapechar=formats.RESULT_ESCAPE_CHAR, delimiter=formats.RESULT_DELIMITER, quotechar=formats.RESULT_QUOTE_CHAR):
                    total_rows += 1
                    yield line
        LOG.info(f"StreamingCOSResultGenerator 流式读取完成: 文件数={file_count}, 总行数={total_rows}")


'''
ResultGenerator
RemoteResultGenerator
LasyRemoteResultGenerator

COSResultGenerator
LasyCOSResultGenerator
StreamingCOSResultGenerator      

'''

RESULT_GENERATORS = {
    'REMOTE_' + constants.Mode.ALL: RemoteResultGenerator,
    'REMOTE_' + constants.Mode.LASY: LasyRemoteResultGenerator,
    'REMOTE_' + constants.Mode.STREAM: LasyRemoteResultGenerator,

    'COS_' + constants.Mode.ALL: COSResultGenerator,
    'COS_' + constants.Mode.LASY: LasyCOSResultGenerator,
    'COS_' + constants.Mode.STREAM: StreamingCOSResultGenerator,
}