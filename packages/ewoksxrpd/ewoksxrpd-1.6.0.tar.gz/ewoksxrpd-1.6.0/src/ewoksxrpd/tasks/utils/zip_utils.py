import io
import os
import zipfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator
from typing import Union


@contextmanager
def open_in_zipfile(
    zipf: zipfile.ZipFile, filename: Union[str, Path], **kwargs
) -> Generator[io.BufferedIOBase, None, None]:
    """Same as `zipfile.ZipFile.open` but with a fixed `name` argument that
    ensures the file timestamp and permissions would be equivalent as with
    python's `open` function when creating a file.
    """
    filename = str(filename).replace("\\", "/")

    info = zipfile.ZipInfo(filename)
    info.date_time = datetime.now().timetuple()[:6]

    current_umask = os.umask(0)
    os.umask(current_umask)
    file_permissions = 0o666 & ~current_umask
    info.external_attr = file_permissions << 16

    with zipf.open(info, **kwargs) as zipio:
        yield zipio
