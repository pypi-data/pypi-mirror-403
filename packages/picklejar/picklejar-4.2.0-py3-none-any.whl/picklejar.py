"""PickleJar is a python module that allows you to work with multiple pickles inside a single file (I call it a "jar")!
"""
# Copyright (C) 2015-2026 Jesse Almanrode
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Lesser General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Lesser General Public License for more details.
#
#     You should have received a copy of the GNU Lesser General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Imports
import contextlib
import os
from typing import Any

import dill

# Constants
DILL_PROTOCOL = dill.HIGHEST_PROTOCOL


class Jar:
    """A file containing multiple pickle objects

    :param filepath: Path to the file
    :type filepath: str, required
    :return: None
    :rtype: None
    """
    def __init__(self, filepath: str) -> None:
        self.jar = os.path.abspath(os.path.expanduser(filepath))

    def __enter__(self):
        """Context manager entry

        :return: Self
        :rtype: Jar
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit

        :param exc_type: Exception type
        :param exc_val: Exception value
        :param exc_tb: Exception traceback
        :return: None
        :rtype: None
        """
        return None

    def exists(self) -> bool:
        """Does the Jar exist

        :return: True or False
        :rtype: bool
        """
        return os.path.exists(self.jar)

    def remove(self) -> bool:
        """Remove the current jar file if it exists

        :return: True
        :rtype: bool
        """
        with contextlib.suppress(FileNotFoundError):
            os.remove(self.jar)
        return True

    def load(self, always_list: bool = False) -> Any:
        """Loads all the pickles out of the file/jar

        :param always_list: Ensure that Jars with single pickle return as a list (Default: False)
        :type always_list: bool, optional
        :return: List of de-pickled objects or de-pickled object if always_list is False and pickled object is not list
        :rtype: Any
        :raises OSError: If the jar file does not exist
        """
        items = list()
        if not self.exists():
            raise OSError(f'File does not exist: {self.jar}')
        with open(self.jar, 'rb') as jar:
            while True:
                try:
                    items.append(dill.load(jar))
                except EOFError:
                    break
        if len(items) == 1:
            if always_list:
                return items
            else:
                return items[0]
        else:
            return items

    def dump(self, items: Any, new_jar: bool = False, collapse: bool = False) -> bool:
        """Write a Pickle to the file/jar.

        :param items: Item or list of items to pickle
        :type items: Any
        :param new_jar: Start a new jar (Default: False)
        :type new_jar: bool, optional
        :param collapse: If items is a list write list as single pickle
        :type collapse: bool, optional
        :return: True on file write
        :rtype: bool
        :raises IOError: If file cannot be written
        """
        try:
            writemode = 'wb' if new_jar else 'ab'
            with open(self.jar, writemode) as jar:
                if collapse:
                    dill.dump(items, jar, DILL_PROTOCOL)
                else:
                    if isinstance(items, list):
                        for item in items:
                            dill.dump(item, jar, DILL_PROTOCOL)
                    else:
                        dill.dump(items, jar, DILL_PROTOCOL)
            return True
        except OSError as e:
            raise OSError(f'Failed to write to jar file {self.jar}: {e}') from e


