"""
velmu.models.file
~~~~~~~~~~~~~~~~~

Wrapper for file uploads.
"""
import os
import io

class File:
    """Represents a file to be uploaded to Velmu.

    Attributes
    ----------
    fp : Union[str, bytes, os.PathLike, io.BufferedIOBase]
        The file path, binary data, or file-like object to upload.
    filename : Optional[str]
        The filename to use for the upload. If not specified, tries to guess from fp.
    """

    def __init__(self, fp, filename=None, spoiler=False):
        self.fp = fp
        self.filename = filename or getattr(fp, 'name', None)
        self.spoiler = spoiler

        if self.filename is None:
            self.filename = 'untitled'
        
        if self.spoiler and not self.filename.startswith('SPOILER_'):
            self.filename = 'SPOILER_' + self.filename

        self._close_on_exit = False

    def close(self):
        if hasattr(self.fp, 'close') and self._close_on_exit:
            self.fp.close()

    def reset(self, seek=True):
        if seek and hasattr(self.fp, 'seek') and hasattr(self.fp, 'tell'):
            self.fp.seek(0)
