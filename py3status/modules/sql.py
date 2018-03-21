# -*- coding: utf-8 -*-
"""
Display data stored in MariaDB, MySQL, sqlite3, and hopefully more.

Configuration parameters:
    cache_timeout: refresh cache_timeout for this module (default 10)
    database: specify database name to import (default None)
    format: display format for this module (default '{format_row}')
    format_row: display format for SQL rows (default None)
    format_separator: show separator if more than one (default ' ')
    parameters: specify connection parameters to use (default None)
    query: specify command to query a database (default None)
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {row} number of SQL rows
    {format_row} format for SQL rows

Color thresholds:
    format:
        row: print a color based on the number of SQL rows
    format_row:
        xxx: print a color based on the value of `xxx` placeholder

Requires:
    mariadb: fast sql database server, drop-in replacement for mysql
    mysql-python: mysql support for python
    sqlite: a c library that implements an sql database engine

Examples:
```
# specify database name to import
sql {
    database = 'sqlite3'  # from sqlite3 import connect
    database = 'MySQLdb'  # from MySQLdb import connect
    database = '...'      # from ... import connect
}

# specify connection parameters to use
http://mysql-python.sourceforge.net/MySQLdb.html#functions-and-attributes
https://docs.python.org/3/library/sqlite3.html#module-functions-and-constants
sql {
    name = 'MySQLdb'
    format = '{host} {passd} ...'
    parameters = {
        'host': 'host',
        'passwd': 'password',
        '...': '...',
    }
}

# specify command to query a database
sql {
    query = 'SHOW SLAVE STATUS'
    query = 'SELECT * FROM cal_todos'
    query = '...'
}

# display number of seconds behind master with MySQLdb
sql {
    database = 'MySQLdb'
    format_row = '\?color=seconds_behind_master {host} is '
    format_row += '[{seconds_behind_master}s behind|\?show master]'
    parameters = {
        'host': 'localhost',
        'passwd': '********'
    }
    query = 'SHOW SLAVE STATUS'
    thresholds = [
        (0, 'deepskyblue'), (100, 'good'), (300, 'degraded'), (600, 'bad')
    ]
}

# display titles of thunderbird tasks with sqlite3
sql {
    database = 'sqlite3'
    format_row = '{title}'
    format_separator = ', '
    query = 'SELECT * FROM cal_todos'
    parameters = '~/.thunderbird/user.default/calendar-data/local.sqlite'
}
```

@author cereal2nd
@license BSD

SAMPLE OUTPUT
{'full_text': 'New Row Item 1, New Row Item 2'}
"""

from importlib import import_module
from os.path import expanduser


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    database = None
    format = '{format_row}'
    format_row = None
    format_separator = ' '
    parameters = None
    query = None
    thresholds = []

    def post_config_hook(self):
        names = ['database', 'format', 'format_row', 'parameters', 'query']
        for config_name in names:
            if config_name == 'format_row':
                if not self.py3.format_contains(self.format, config_name):
                    continue
            if not getattr(self, config_name, None):
                raise Exception('missing %s' % config_name)

        self.connect = getattr(import_module(self.database), 'connect')
        self.is_parameters_a_string = isinstance(self.parameters, str)
        if self.is_parameters_a_string:
            self.parameters = expanduser(self.parameters)

    def _get_sql_data(self):
        if self.is_parameters_a_string:
            con = self.connect(self.parameters)
        else:
            con = self.connect(**self.parameters)
        cur = con.cursor()
        cur.execute(self.query)
        sql_keys = [desc[0].lower() for desc in cur.description]
        sql_values = cur.fetchall()
        cur.close()
        con.close()
        return [dict(zip(sql_keys, values)) for values in sql_values]

    def sql(self):
        sql_data = {}
        format_row = None
        count_row = None

        try:
            data = self._get_sql_data()
        except:
            pass
        else:
            new_data = []
            count_row = len(data)
            for row in data:
                if self.thresholds:
                    for key, value in row.items():
                        self.py3.threshold_get_color(value, key)

                new_data.append(self.py3.safe_format(self.format_row, row))

            format_separator = self.py3.safe_format(self.format_separator)
            format_row = self.py3.composite_join(format_separator, new_data)

            if self.thresholds:
                self.py3.threshold_get_color(count_row, 'row')

        if not self.is_parameters_a_string:
            sql_data.update(self.parameters)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, dict(
                    format_row=format_row,
                    row=count_row,
                    **sql_data
                )
            )
        }


if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
