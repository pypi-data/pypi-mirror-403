from unittest import mock

import pytest

from .. import main

pytest.importorskip('ezdag')

from ..tools import condor  # noqa: E402


@pytest.mark.parametrize('subcommand,extra_args', [['q', ('-nobatch',)]])
@mock.patch('os.execvp', side_effect=SystemExit(0))
def test_condor_subcommand(mock_execvp, subcommand, extra_args):
    """Test Condor subcommands that include all jobs in constraints."""
    try:
        main(['gwcelery', 'condor', subcommand])
    except SystemExit as e:
        assert e.code == 0

    cmd = 'condor_' + subcommand
    mock_execvp.assert_called_once_with(
        cmd, (cmd, *extra_args, *condor.get_constraints()))


@pytest.mark.parametrize('subcommand', ['hold', 'release'])
@mock.patch('os.execvp', side_effect=SystemExit(0))
def test_condor_subcommand_ignore_dagman(mock_execvp, subcommand):
    """Test Condor subcommands that exclude DAGMan job from constraints."""
    try:
        main(['gwcelery', 'condor', subcommand])
    except SystemExit as e:
        assert e.code == 0

    cmd = 'condor_' + subcommand
    mock_execvp.assert_called_once_with(
        cmd, (cmd, *condor.get_constraints(ignore_dagman=True)))


@mock.patch('os.execvp', side_effect=SystemExit(0))
def test_condor_rm(mock_execvp):
    """Test that rm command only targets the DAGMan coordinator job."""
    try:
        main(['gwcelery', 'condor', 'rm'])
    except SystemExit as e:
        assert e.code == 0

    mock_execvp.assert_called_once_with(
        'condor_rm', ('condor_rm', *condor.get_constraints(only_dagman=True)))


@mock.patch('subprocess.check_output', return_value=b'<classads></classads>')
@mock.patch('gwcelery.tools.condor.generate_dag_and_submit_files')
def test_condor_submit_not_yet_running(mock_generate_dag, mock_check_output):
    """Test starting the Condor job."""
    try:
        main(['gwcelery', 'condor', 'submit'])
    except SystemExit as e:
        assert e.code == 0

    mock_check_output.assert_called_once_with(
        ('condor_q', '-xml', *condor.get_constraints()))
    mock_generate_dag.assert_called_once()


@mock.patch('subprocess.check_output',
            return_value=b'<classads><c></c></classads>')
@mock.patch('gwcelery.tools.condor.generate_dag_and_submit_files')
def test_condor_submit_already_running(mock_generate_dag, mock_check_output):
    """Test that we don't start the condor jobs if they are already running."""
    try:
        main(['gwcelery', 'condor', 'submit'])
    except SystemExit as e:
        assert e.code == 1

    mock_check_output.assert_called_once_with(
        ('condor_q', '-xml', *condor.get_constraints()))
    mock_generate_dag.assert_not_called()


class MockMonotonic:
    """Mock :meth:`time.monotonic` to speed up the apparent passage of time."""

    def __init__(self):
        self._t = 0.0

    def __call__(self):
        self._t += 1.0
        return self._t


@mock.patch('time.sleep')
@mock.patch('time.monotonic', new_callable=MockMonotonic)
@mock.patch('subprocess.check_output',
            return_value=b'<classads><c></c></classads>')
@mock.patch('subprocess.check_call')
def test_condor_resubmit_fail(mock_check_call, _, __, ___):
    """Test that ``gwcelery condor resubmit`` fails if we are unable to
    ``condor_rm`` the DAGMan coordinator job.
    """
    try:
        main(['gwcelery', 'condor', 'resubmit'])
    except SystemExit as e:
        assert e.code == 1
    mock_check_call.assert_called_with(
        ('condor_rm', *condor.get_constraints(only_dagman=True)))


@mock.patch('subprocess.check_output',
            return_value=b'<classads></classads>')
@mock.patch('subprocess.check_call')
@mock.patch('gwcelery.tools.condor.generate_dag_and_submit_files')
def test_condor_resubmit_succeeds(mock_generate_dag, mock_check_call, _):
    """Test that ``gwcelery condor resubmit`` succeeds when no jobs are
    running.
    """
    try:
        main(['gwcelery', 'condor', 'resubmit'])
    except SystemExit as e:
        assert e.code == 0
    mock_check_call.assert_not_called()
    mock_generate_dag.assert_called_once()
