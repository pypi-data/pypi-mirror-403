#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

import pandas
import json

import collections

from pathlib import Path

from abc import ABCMeta, abstractmethod

from typing import Optional, Any


class Representable(metaclass=ABCMeta):
    """Objects with a nice representation on console

    Representable is an abstract class that grant to its heirs a structured
    representation on console. Such representation can be seen

    The representation is composed by two parts: a
    header and a body.

    TODO: finish it here

    Examples
    --------

    .. code-block:: python
        :linenos:
        :name: representable-code-subclassing
        :caption: Subclassing Representable


        from jangada.atomic import Representable

        class CustomRepresentable(Representable):

            def _get_header(self):
                return "REPR EXAMPLE"

            def _get_body(self):

                c1 = "Some Content"
                c2 = "Some More Content"
                c3 = "Last Content"

                body = "{c1}\\n{{fence}}\\n{c2}\\n{{fence}}\\n{c3}".format(c1=c1, c2=c2, c3=c3)

                return body, length



    |
    """

    # ========== ========== ========== ========== ========== ========== class attributes
    _available_colors = {
        'blue': '\033[94m{}\033[0m',
        'cyan': '\033[96m{}\033[0m',
        'darkcyan': '\033[36m{}\033[0m',
        'green': '\033[92m{}\033[0m',
        'purple': '\033[95m{}\033[0m',
        'red': '\033[91m{}\033[0m',
        'yellow': '\033[93m{}\033[0m'
    }
    """available colors"""

    # ========== ========== ========== ========== ========== ========== special methods
    def __str__(self):

        # ---------- ---------- ---------- ---------- ---------- ---------- header
        raw_header = self._get_header()

        # calculates header length
        length = len(raw_header)

        header = raw_header

        # formats header color
        if self.__get_option('header_color'):
            header = self.__get_color_formatted_text(header, self.__get_option('header_color'))

        # formats header weight
        if self.__get_option('header_bold'):
            header = self.__get_bold_formatted_text(header)

        # ---------- ---------- ---------- ---------- ---------- ---------- body
        body = self._get_body()

        # copies body
        contents = body

        # unformats contents
        for index in [0, 1, 36, 91, 92, 93, 94, 95, 96]:
            contents = contents.replace('\033[{}m'.format(index), '')

        # gets max length
        length = max(length, *[len(line) for line in contents.split('\n') if '{{fence}}' not in line])

        # ---------- ---------- ---------- ---------- ---------- ---------- create wall and fence
        wall = self.__wall(length)
        fence = self.__fence(length)

        # ---------- ---------- ---------- ---------- ---------- ---------- align header
        if Representable.__get_option('header_alignment') == 'centre':
            header = "{{:^{}s}}".format(length + len(header) - len(raw_header)).format(header)

        elif Representable.__get_option('header_alignment') == 'right':
            header = "{{:>{}s}}".format(length + len(header) - len(raw_header)).format(header)

        # ---------- ---------- ---------- ---------- ---------- ----------
        return """{{wall}}
{{header}}
{{fence}}
{body}
{{wall}}
""".format(body=body).format(header=header, wall=wall, fence=fence)

    def __repr__(self):
        return str(self)

    # ========== ========== ========== ========== ========== ========== private methods
    @staticmethod
    def __get_option(option_tag: str) -> str | bool:
        """TODO"""
        settings_file_path = Path(__file__).parent / "settings.json"

        with settings_file_path.open() as file:
            return json.load(file)[option_tag]

    @staticmethod
    def __get_color_formatted_text(text: str, color: str) -> str:
        """TODO"""
        return Representable._available_colors[color].format(text)

    @staticmethod
    def __get_bold_formatted_text(text: str) -> str:
        """TODO"""
        return '\033[1m{}\033[0m'.format(text)

    @staticmethod
    def __wall(length: int) -> str:
        """TODO"""
        ret = length * Representable.__get_option('wall_char')

        if Representable.__get_option('wall_color'):
            ret = Representable.__get_color_formatted_text(ret, Representable.__get_option('wall_color'))

        if Representable.__get_option('wall_bold'):
            ret = Representable.__get_bold_formatted_text(ret)

        return ret

    @staticmethod
    def __fence(length: int) -> str:
        """TODO"""
        ret = length * Representable.__get_option('fence_char')

        if Representable.__get_option('fence_color'):
            ret = Representable.__get_color_formatted_text(ret, Representable.__get_option('fence_color'))

        if Representable.__get_option('fence_bold'):
            ret = Representable.__get_bold_formatted_text(ret)

        return ret

    # ========== ========== ========== ========== ========== ========== protected methods
    @staticmethod
    def _format_as_property(text: str) -> str:
        """Formats text as property"""
        if Representable.__get_option('properties_color'):
            text = Representable.__get_color_formatted_text(text, Representable.__get_option('properties_color'))

        if Representable.__get_option('properties_bold'):
            text = Representable.__get_bold_formatted_text(text)

        return text

    @staticmethod
    def _create_formatted_frame(data: dict | pandas.DataFrame,
                                columns: Optional[list[str]] = None,
                                sort_values_by: Optional[str | list[str]] = None,
                                alignment: Optional[dict[str, dict]] = None,
                                index: bool = True,
                                index_offset: int = 1,
                                max_colwidth: int = 50,
                                max_rows: int = 30) -> str:
        """Creates a :py:class:`string <str>` representation of a table

        Parameters
        ----------
        data : :py:class:`dict` | :py:class:`pandas.DataFrame`
            Data to be represented as table. It is internally passed
            to the :py:class:`DataFrame <pandas.DataFrame>` initialiser.

        columns : :py:class:`list` of :py:class:`str` | :py:obj:`None`
            List of column names in the desired order. It is internally passed
            to the :py:class:`DataFrame <pandas.DataFrame>` initialiser.

        sort_values_by : :py:class:`str` | :py:class:`list` of :py:class:`str` | :py:obj:`None`
            Column or columns to sort the data by. It is internally passed to
            the method :py:obj:`sort_values <pandas.DataFrame.sort_values>`.

        alignment : :py:class:`dict` | :py:obj:`None`, optional
            Dictionary describing the desired alignment of the columns

            .. code-block:: python

                alignment = {
                    'col1': {'header': 'left', 'values': 'left'},
                    'col2': {'header': 'centre', 'values': 'centre'},
                    'col3': {'header': 'centre', 'values': 'right'},
                    'col4': {'header': 'right', 'values': 'right'},
                }

        index : :py:class:`bool`
            Controls if the table indices should figure in the output. It is
            internally passed to the method
            :py:obj:`to_string <pandas.DataFrame.to_string>`.

        index_offset : :py:class:`int`
            Index of the first row. Usually 0 or 1.

        max_colwidth : :py:class:`int`
            Controls the maximum width of the columns. It is internally passed
            to the method :py:obj:`to_string <pandas.DataFrame.to_string>`

        max_rows : :py:class:`int`
            Controls the maximum number of showing rows. It is internally passed
            to the method :py:obj:`to_string <pandas.DataFrame.to_string>`.

        Returns
        -------
        out : :py:class:`str`
            The formatted frame.

        """
        if columns is None:
            frame = pandas.DataFrame(data)

        else:
            frame = pandas.DataFrame(data, columns=columns)

        frame = frame.astype(str)  # TODO: Is this line really necessary?

        if sort_values_by:
            frame.sort_values(sort_values_by, inplace=True)


        if isinstance(frame.index.dtype, pandas.Int64Dtype):
            frame.reset_index(inplace=True, drop=True)
            frame.index += index_offset

        # ---------- ---------- ---------- ---------- ---------- ----------

        def left_justified(column):
            def __justify(value):
                return "{{:<{}s}}".format(frame[column].str.len().max()).format(value)

            return __justify

        def centre_justified(column):
            def __justify(value):
                return "{{:^{}s}}".format(frame[column].str.len().max()).format(value)

            return __justify

        def right_justified(column):
            def __justify(value):
                return "  {{:>{}s}}".format(frame[column].str.len().max()).format(value)

            return __justify

        # ---------- ---------- ---------- ---------- ---------- ----------

        header = []

        formatters = {}

        if not alignment:
            alignment = {}

        for col in frame.columns:

            column_alignment = alignment.pop(col, None)

            if column_alignment:

                # ---------- ---------- ---------- ---------- ---------- ---------- header alignment
                header_alignment = column_alignment.pop('header', '').lower()

                if header_alignment in ['left', 'l']:
                    header.append('{{:<{}s}}'.format(frame[col].str.len().max()).format(col))

                elif header_alignment in ['centre', 'center', 'c']:
                    header.append('{{:^{}s}}'.format(frame[col].str.len().max()).format(col))

                elif header_alignment in ['', 'right', 'r']:
                    header.append('  {{:>{}s}}'.format(frame[col].str.len().max()).format(col))

                else:
                    error = "Unexpected value for header alignment: {}"
                    raise ValueError(error.format(header_alignment))

                # ---------- ---------- ---------- ---------- ---------- ---------- content alignnment
                values_alignment = column_alignment.pop('values', '').lower()

                if values_alignment in ['left', 'l']:
                    # formatters[col] = lambda value: "{{:<{}s}}".format(frame[col].str.len().max()).format(value)
                    formatters[col] = left_justified(col)

                elif values_alignment in ['centre', 'center', 'c']:
                    # formatters[col] = lambda value: "{{:^{}s}}".format(frame[col].str.len().max()).format(value)
                    formatters[col] = centre_justified(col)

                elif values_alignment in ['', 'right', 'r']:
                    # formatters[col] = lambda value: "{{:>{}s}}".format(frame[col].str.len().max()).format(value)
                    formatters[col] = right_justified(col)

                else:
                    error = "Unexpected value for header alignment: {}"
                    raise ValueError(error.format(header_alignment))

            else:
                header.append(col)

        frame = frame.to_string(header=header,
                                formatters=formatters,
                                index=index,
                                max_colwidth=max_colwidth,
                                max_rows=max_rows)

        # ---------- ---------- ---------- ---------- ---------- ----------

        lines = frame.split('\n')

        # if not index:
        #     lines = [line.strip() for line in lines]

        lines[0] = Representable._format_as_property(lines[0])

        frame = '\n'.join(lines)

        return frame

    @staticmethod
    def _create_formatted_form(data: dict[str, Any],
                               order: Optional[list[str]] = None,
                               min_gap: int = 4,
                               uppercase: bool = False,
                               capitalise: bool = False,
                               capitalize: bool = False) -> str:
        """Creates a :py:class:`string <str>` representation of a form

        Parameters
        ----------
        data : :py:class:`dict`
            Data to be represented as form.

        order : :py:class:`list` of :py:class:`str` | :py:obj:`None`
            List of field names in the desired order.

        min_gap : :py:class:`int`
            Minimum number of white spaces between field names and values.

        uppercase : :py:class:`bool`
            Uppercase the field names.

        capitalise : :py:class:`bool`
            Capitalise the field names.

        Returns
        -------
        out : :py:class:`str`
            The formatted form.

        """

        # ---------- ---------- ---------- ---------- ---------- ---------- formatting keys

        if order is None:

            if uppercase:
                data = {Representable._format_as_property(key.upper()): value for key, value in data.items()}

            elif capitalise or capitalize:
                data = {Representable._format_as_property(key.capitalize()): value for key, value in data.items()}

            else:
                data = {Representable._format_as_property(key): value for key, value in data.items()}

        else:

            ordered_data = collections.OrderedDict()

            if uppercase:
                for key in order:
                    ordered_data[Representable._format_as_property(key.upper())] = data[key]

            elif capitalise or capitalize:
                for key in order:
                    ordered_data[Representable._format_as_property(key.capitalize())] = data[key]

            else:
                for key in order:
                    ordered_data[Representable._format_as_property(key)] = data[key]

            data = ordered_data

        # ----------  this is a nice implementation, but it doesn't work somehow due the formatting chars
        # longest_key_length = max(len(key) for key in data)
        # template = "{{key:>{max_len}s}}:{min_gap}{{value}}".format(max_len=longest_key_length, min_gap=min_gap*' ')
        # return '\n'.join(template.format(key=Representable._format_as_property(k), value=v) for k, v in data.items())

        # ---------- ---------- ---------- ---------- ---------- I didn't like this implementation, but it works
        gap = max(len(key) for key in data) + min_gap

        template = "{key}:{gap}{value}"

        return '\n'.join(
            template.format(key=key, value=value, gap=' ' * (gap - len(key))) for key, value in data.items())

    @abstractmethod
    def _get_header(self) -> str:
        """
        Returns
        -------
        out: :py:class:`str`
            The header of the report representation

        """
        raise NotImplementedError()

    @abstractmethod
    def _get_body(self) -> str:
        """

        Returns
        -------
        out: :py:class:`str`
            The body of the report representation
        """
        raise NotImplementedError()

    # ========== ========== ========== ========== ========== ========== public methods
    @staticmethod
    def parse_color(color: str) -> str:
        """Parses color name"""
        if color.lower() in Representable._available_colors:
            return color.lower()

        ValueError("There is no color named {} available".format(color))

    # ---------- ---------- ---------- ---------- ---------- ---------- properties
    ...