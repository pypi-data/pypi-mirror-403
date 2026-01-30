"""Override the open method to provide a file-like object or STDIN/STDOUT.
Also, provide writing via a temp file if needed. The `open` function is
available from the root i.e. `stdin.open`.
"""
from contextlib import contextmanager
from pathlib import PosixPath
import builtins
import sys
import shutil
import tempfile
import os


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@contextmanager
def open(filename, mode='rt', method=builtins.open, use_tmp=False,
         tmpdir=None, keep_tmp=False, **kwargs):
    """Provide either an opened file or STDIN/STDOUT if filename is not a file.
    This must be used as a context manager.

    Parameters
    ----------
    filename : `str` or `NoneType` or `iterator`
        The filename to open. If ``-``, ``''`` or ``NoneType`` then either
        `sys.stdin` or `sys.stdout` is yielded (depending on ``mode``).
        Otherwise the file is opened with ``method``. If the filename is an
        iterator (or can be made into one), then it is simply passed through
        and returned.
    mode : `str` optional, default: `rt`
        Should be the usual ``w/wt/wb/r/rt/rb``. A ``''`` is interpreted as
        read as is ``NoneType``.
    method : `function`, optional, default: `builtins.open`
        The open method to use if filename is not using ``STDIN`` or
        ``STDOUT``.
    use_temp : `bool`, optional, default: False
        Use a temp file for writing instead of the output file. Then move the
        temp file to the output file location upon successful closing, or
        delete if there is an error (unless ``keep_tmp`` is ``True``.
    tmpdir : `str` or `NoneType`, optional, default: `NoneType`
        The location to write any temp files, if ``NoneType`` then it
        defaults to the system temp
    keep_tmp : `bool`, optional, default: `False`
        If the contextmanager exits with an error then do not delete the
        temp file after closing (might be useful for debugging - if you
        can id the file).
    **kwargs
        Any other kwargs passed to ``method``.

    Yields
    ------
    fobj : `File` or `sys.stdin` or `sys.stdout`
        A place to read or write depending on ``filename`` and ``mode``

    Raises
    ------
    ValueError
        If the mode can't be identified.
    """
    # Reading
    if has_read(mode):
        if is_std(filename) is False and \
           isinstance(filename, (PosixPath, str)) is False:
            # Not a filename or STDIN
            if hasattr(filename, '__iter__'):
                yield filename
            else:
                yield iter(filename)
        else:
            fobj = _input_open(filename, mode, method, **kwargs)
            yield fobj
            fobj.close()
    elif has_write(mode):
        fobj, tmp_name = _output_open(filename, mode, method, use_tmp,
                                      tmpdir=tmpdir, **kwargs)

        try:
            # We are relocating a temp file, so we get the temp name
            # from the file object. However, some moethods do not have
            # the name attribute so we will default to what was created
            # as a fall back. In theory we could use this anyway but I
            # prefer to get it first hand if possible
            n = fobj.name
        except AttributeError:
            n = tmp_name

        if n is None:
            raise IOError("can't ID file name, this is probably a bug")

        try:
            yield fobj
            fobj.close()
        except Exception:
            fobj.close()
            if is_std(filename) is False and use_tmp is True and \
               keep_tmp is False:
                os.unlink(n)
            raise
        if is_std(filename) is False and use_tmp is True:
            shutil.move(n, filename)
    else:
        raise ValueError("unknown mode: {0}".format(mode))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def _output_open(filename, mode, method, use_tmp, *args, tmpdir=None,
                 **kwargs):
    """Provide either an opened file for writing or STDOUT if filename is not
    a file path.

    Parameters
    ----------
    filename : `str` or `NoneType`
        The filename to open. If ``-``, ``''`` or ``NoneType`` then either
        `sys.stdin` or `sys.stdout` is yielded (depending on ``mode``).
        Otherwise the file is opened with ``method``.
    mode : `str`
        Should be the usual ``w/wt/wb`` or appends.
    method : `function`
        The open method to use if filename is not using ``STDOUT``.
    use_temp : `bool`
        Use a temp file for writing instead of the output file. This will
        open the tempfile and returnt he file object (if not writing to
        STDOUT).
    *args
        Any arguments to ``method``.
    tmpdir : `str` or `NoneType`, optional, default: `NoneType`
        The location to write any temp files, if ``NoneType`` then it
        defaults to the system temp
    **kwargs
        Any other kwargs passed to ``method``.

    Returns
    -------
    fobj : `File` or `sys.stdout`
        A place to write depending on ``filename``

    Raises
    ------
    ValueError
        If the mode can't be identified.
    """
    if is_std(filename) is False:
        if use_tmp is True:
            filename = get_tmp_file(dir=tmpdir)

        try:
            return method(filename, mode, *args, **kwargs), filename
        except Exception:
            if use_tmp is True:
                os.unlink(filename)
            raise
    else:
        # Writing to STDOUT
        if has_binary(mode):
            return sys.stdout.buffer, None
        else:
            try:
                encoding = kwargs['encoding']
                sys.stdout.reconfigure(encoding=encoding)
            except KeyError:
                pass
            return sys.stdout, None


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def _input_open(filename, mode, method, *args, **kwargs):
    """Provide either an opened file or STDIN/STDOUT if filename is not a file.

    Parameters
    ----------
    filename : `str` or `NoneType`
        The filename to open. If `sys.stdin`, '-', '' or `NoneType` then
        `sys.stdin` is yielded otherwise the file is opened with `method`
    mode : `str`
        Should be the usual ``r/rt/rb``.
    method : `function`, optional, default: `open`
        The open method to use (uses the standard `open` as a default) but the
        user can supplied things like `gzip.open` here if required.
    *args
        Arguments to ``method``
    **kwargs
        Any other kwargs passed to ``method``.

    Yields
    ------
    fobj : `File` or `sys.stdin`
        A place to read the file from
    """
    # Want to read in from a file and not STDIN
    if is_std(filename) is False:
        return method(filename, mode, *args, **kwargs)
    else:
        stdin_obj = sys.stdin
        if has_binary(mode) is True:
            stdin_obj = sys.stdin.buffer

        try:
            # If the encoding has been supplied then modify STDIN to accept the
            # new encoding
            # This is because pytest was being silly!?
            encoding = kwargs['encoding']
            stdin_obj.reconfigure(encoding=encoding)
        except KeyError:
            pass
    return stdin_obj


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def get_tmp_file(**kwargs):
    """Initialise a temp file to work with. This differs from
    `tempfile.mkstemp` as the tmp file is closed and the file name is returned.

    Parameters
    ----------
    **kwargs
        Any arguments usually passed to `tempfile.mkstemp`

    Returns
    -------
    temp_file_name : `str`
        The name of a temp file that has been created with the requested
        parameters.
    """
    tmp_file_obj, tmp_file_name = tempfile.mkstemp(**kwargs)
    os.close(tmp_file_obj)
    return tmp_file_name


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def has_binary(mode):
    """Does the mode have binary flag ``b``.

    Parameters
    ----------
    mode : `str`
        The mode string

    Returns
    -------
    has_flag : `bool`
        ``True`` if it contains the flag ``False`` if not.
    """
    return 'b' in mode


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def has_read(mode):
    """Does the mode have read flag ``r``.

    Parameters
    ----------
    mode : `str`
        The mode string

    Returns
    -------
    has_flag : `bool`
        ``True`` if it contains the flag ``False`` if not.
    """
    return mode is None or 'r' in mode or mode == ''


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def has_write(mode):
    """Does the mode have write flag ``w`` or ``a``.

    Parameters
    ----------
    mode : `str`
        The mode string

    Returns
    -------
    has_flag : `bool`
        ``True`` if it contains the flag ``False`` if not.
    """
    # Handle a potential error state
    if mode is None:
        return False
    return 'w' in mode or 'a' in mode


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def is_std(filename):
    """Id the filename consistant with wanting input from stdin, stdout or
    stderr.

    Parameters
    ----------
    filename : `sys.stdin` or `sys.stdout` or `str` or `NoneType`
        If `sys.stdin` or `sys.stdout`, NoneType, ``'-'`` or ``''`` then it
        is.

    Returns
    -------
    has_std_flag : `bool`
        ``True`` if it contains the flag ``False`` if not.
    """
    return filename in [sys.stdin, sys.stdout, sys.stderr, '-', '', None]
