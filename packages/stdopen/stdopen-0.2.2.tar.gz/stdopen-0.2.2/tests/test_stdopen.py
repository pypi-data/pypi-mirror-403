"""Tests for stdopen
"""
from stdopen import stdopen as helpers
import gzip
import stdopen
import pytest
import sys
import os


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@pytest.mark.parametrize(
    'test,result',
    (('rb', True), ('r', False), ('', False), ('wb', True))
)
def test_has_binary(test, result):
    """Test that `stdopen.has_binary` is working correctly.
    """
    test_res = helpers.has_binary(test)
    assert test_res == result


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@pytest.mark.parametrize(
    'test,result',
    (('rb', True), ('r', True), (None, True), ('', True), ('wb', False))
)
def test_has_read(test, result):
    """Test that `stdopen.has_read` is working correctly.
    """
    test_res = helpers.has_read(test)
    assert test_res == result


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@pytest.mark.parametrize(
    'test,result',
    (('rb', False), ('r', False), (None, False), ('', False), ('wb', True),
     ('wt', True), ('w', True))
)
def test_has_write(test, result):
    """Test that `stdopen.has_write` is working correctly.
    """
    test_res = helpers.has_write(test)
    assert test_res == result


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@pytest.mark.parametrize(
    'test,result',
    (('my_file.txt', False), (None, True), ('-', True), (sys.stdin, True),
     (sys.stdout, True), ('', True), (sys.stderr, True))
)
def test_is_std(test, result):
    """Test that `stdopen.is_std is working correctly.
    """
    test_res = helpers.is_std(test)
    assert test_res == result


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def test_get_tmp_file(tmpdir):
    """Test that `stdopen.get_tmp_file` is working correctly.
    """
    test_res = helpers.get_tmp_file(dir=tmpdir)
    assert os.path.exists(test_res)
    assert os.path.dirname(test_res) == tmpdir


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def test__input_open_file(tmpdir):
    """Test that `stdopen._input_open` is working correctly when asked to use
    a regular file
    """
    test_file = os.path.join(tmpdir, "test_file.txt")
    test_data = "this is a test"

    with open(os.path.join(tmpdir, "test_file.txt"), 'wt') as testf:
        testf.writelines(test_data)

    fobj = helpers._input_open(test_file, 'rt', open)
    assert fobj.name == test_file


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def test_open_iter(tmpdir):
    """Test that `stdopen.open` passes through any iterators.
    """
    x = ['A', 'B', 'C']

    with helpers.open(x, 'rt') as infile:
        assert infile == x


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def test__input_open_stdin():
    """Test that `stdopen._input_open` is working correctly when asked to use
    stdin
    """
    fobj = helpers._input_open(None, 'rt', open)
    assert fobj == sys.stdin


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def test__output_open_file(tmpfile):
    """Test that `stdopen._output_open` is working correctly when asked to use
    a regular file.
    """
    tp, tdir, tf = tmpfile
    fobj, fname = helpers._output_open(tp, 'wt', open, False)
    assert fobj.name == tp


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def test__output_open_tmpfile(tmpdir):
    """Test that `stdopen._output_open` is working correctly when asked to use
    a tmp file.
    """
    # For this test the file name just has to be a string as it will not get
    # opened in anyway as we are using tmp files
    fobj, fname = helpers._output_open(
        'anything', 'wt', open, True, tmpdir=tmpdir
    )
    assert os.path.dirname(fobj.name) == tmpdir


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def test__output_open_stdout(tmpdir):
    """Test that `stdopen._output_open` is working correctly when asked to use
    a stdout.
    """
    # For this test the file name just has to be NoneType, or '-'
    fobj, fname = helpers._output_open(None, 'wt', open, False)
    assert fobj == sys.stdout


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@pytest.mark.parametrize(
    'method,use_tmp',
    ((open, False), (gzip.open, False), (open, True), (gzip.open, True))
)
def test_open_write_file(tmpfile, testdata, tmpdir, method, use_tmp):
    """Test that `stdopen.open` is working correctly when asked to write to a
    file.
    """
    # If we are using temp then set the dir to something pytest will know
    # about
    tmppath = None
    if use_tmp is True:
        tmppath = tmpdir

    kwargs = dict(
        method=method, use_tmp=use_tmp, tmpdir=tmppath
    )

    # All outputs will be written to this file, we will make sure it does not
    # exist before we start so we can be sure that we are not writing directly
    # to it when use_tmp is True
    final_file = os.path.join(tmpdir, 'my_test_file.txt')
    try:
        os.unlink(final_file)
    except FileNotFoundError:
        pass

    with stdopen.open(final_file, 'wt', **kwargs) as outfile:
        # The file should or should not exist, depending on use temp
        assert os.path.exists(final_file) is (not use_tmp)
        outfile.writelines(testdata)
    # The file should exist when the contextmanager exists
    assert os.path.exists(final_file) is True

    # Test the content of the file
    _eval_write_test(final_file, testdata, method, 'rt')


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def _eval_write_test(infile_path, expected, method, mode):
    with method(infile_path, mode) as infile:
        indata = infile.read()
    assert indata == expected
