from tdlc_connector import formats, exceptions
import re
import logging
import time


LOG = logging.getLogger(__name__)


REGEXP_INSERT_VALUES = re.compile(
    r"\s*((?:INSERT)\b.+\bVALUES?\s*)"
    + r"(\(\s*(?:%s|%\(.+\)s)\s*(?:,\s*(?:%s|%\(.+\)s)\s*)*\))",
    re.IGNORECASE | re.DOTALL,
)

MAX_STATEMENT_LENGTH = 1024 * 1024 * 2

class Cursor:

    def __init__(self, connection) -> None:

        self.description = None
        self.rowcount = -1
        self.arraysize = 1

        self.connection = connection
        self.iterator = None

        self._executed = False

    
    def __del__(self):

        self.close()

    def close(self):
        pass
    
    def setinputsizes(self, *args):
        """Does nothing, required by DB API."""

    def setoutputsizes(self, *args):
        """Does nothing, required by DB API."""

    def reset(self):

        self.rowcount = -1
        self.arraysize = 1
        self.description = None
        self.iterator = None

        self._executed = False

    def _escape_args(self, args=None):
        if isinstance(args, (tuple, list)):
            return tuple([formats.literal(item) for item in args])
        elif isinstance(args, dict):
            return {k: formats.literal(v) for (k, v) in args.items()}
        return formats.literal(args)

    def execute(self, statement, args=None):
        LOG.debug(f"Cursor.execute 被调用, args={args is not None}")

        if args is not None:
            statement = statement % self._escape_args(args)
            LOG.debug(f"参数已替换到 SQL 语句中")

        try:
            LOG.info(f"开始执行 SQL: {statement[:100]}{'...' if len(statement) > 100 else ''}")
            start_time = time.time()
            self.rowcount, self.description, self.iterator = self.connection.execute_statement(statement)
            elapsed = time.time() - start_time
            LOG.info(f"SQL 执行完成: rowcount={self.rowcount}, 耗时={elapsed:.3f}s")
        except KeyboardInterrupt as e :
            LOG.warning("SQL 执行被用户中断")
            self.connection.kill()
        except exceptions.ProgrammingError:
            raise
        except Exception as e:
            LOG.error(f"SQL 执行失败: {e}")
            raise exceptions.ProgrammingError(e)

        self._executed = True
        return self.rowcount

    def executemany(self, statement, args):
        if not args:
            LOG.debug("executemany 被调用但参数为空")
            return

        LOG.info(f"executemany 被调用, 参数数量: {len(args)}")
        m = REGEXP_INSERT_VALUES.match(statement)
        rows = 0

        if m:
            LOG.debug("[executemany] 使用批量插入模式")
            prefix = m.group(1)
            values = m.group(2).rstrip()
            # TODO 这里 prefix 直接超长会有异常

            query = prefix
            for arg in args:
                v = values % self._escape_args(arg)
                if len(query) + len(v) + 1 > MAX_STATEMENT_LENGTH:
                    rows += self.execute(query.rstrip(','))
                    query = prefix
                query += v + ','
            rows += self.execute(query.rstrip(','))
        else:
            LOG.debug("[executemany] 使用循环执行模式")
            rows += sum(self.execute(statement, arg) for arg in args)
        
        self.rowcount = rows
        LOG.info(f"executemany 完成, 总影响行数: {self.rowcount}")
        return self.rowcount

    def callproc(self, procname, args=()):
        """ optional """
        pass

    def assert_executed(self):
        if not self._executed:
            raise exceptions.ProgrammingError("Please execute SQL first. ")

    def fetchone(self):
        self.assert_executed()

        value = None
        if not self.iterator:
            return value
        
        try:
            value = next(self.iterator)
        except StopIteration:
            pass
        except Exception:
            raise
        return value

    def fetchmany(self, size=None):
        self.assert_executed()

        values = []
        if not self.iterator:
            return tuple(values)

        take = size or self.arraysize or 1

        for value in self.iterator:
            values.append(value)
            take -= 1
            if take <= 0:
                break

        return tuple(values)

    def fetchall(self):
        self.assert_executed()

        values = []
        if not self.iterator:
            return tuple(values)

        for value in self.iterator:
            values.append(value)
        LOG.debug(f"fetchall 返回 {len(values)} 行数据")
        return tuple(values)

    def nextset(self):
        pass
