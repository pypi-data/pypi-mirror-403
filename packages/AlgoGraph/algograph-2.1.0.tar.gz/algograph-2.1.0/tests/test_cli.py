"""
Tests for AlgoGraph CLI entry point.
"""

import pytest
import sys
import tempfile
import os
from io import StringIO
from unittest.mock import patch, MagicMock

from AlgoGraph.shell.cli import main, _create_sample_graph
from AlgoGraph import Graph, Vertex, Edge, save_graph


class TestSampleGraph:
    """Tests for sample graph creation."""

    def test_create_sample_graph(self):
        """Test that sample graph is created correctly."""
        graph = _create_sample_graph()

        assert graph.vertex_count == 4
        assert graph.edge_count == 4
        assert graph.has_vertex('A')
        assert graph.has_vertex('B')
        assert graph.has_vertex('C')
        assert graph.has_vertex('D')
        assert graph.has_edge('A', 'B')
        assert graph.has_edge('A', 'C')
        assert graph.has_edge('B', 'D')
        assert graph.has_edge('C', 'D')

    def test_sample_graph_vertex_attrs(self):
        """Test that sample graph vertices have attributes."""
        graph = _create_sample_graph()

        v_a = graph.get_vertex('A')
        assert v_a is not None
        assert v_a.get('value') == 1

        v_d = graph.get_vertex('D')
        assert v_d is not None
        assert v_d.get('value') == 4


class TestCLIInteractiveMode:
    """Tests for interactive mode startup."""

    def test_main_interactive_mode(self):
        """Test that main() starts shell in interactive mode."""
        with patch.object(sys, 'argv', ['algograph']):
            with patch('AlgoGraph.shell.cli.GraphShell') as mock_shell_class:
                mock_shell = MagicMock()
                mock_shell_class.return_value = mock_shell

                main()

                mock_shell_class.assert_called_once()
                mock_shell.run.assert_called_once()


class TestCLICommandMode:
    """Tests for one-off command execution."""

    def test_main_with_command(self):
        """Test that main() executes command in one-off mode."""
        with patch.object(sys, 'argv', ['algograph', 'ls']):
            with patch('AlgoGraph.shell.cli.GraphShell') as mock_shell_class:
                mock_shell = MagicMock()
                mock_shell_class.return_value = mock_shell

                main()

                mock_shell_class.assert_called_once()
                mock_shell.execute_command.assert_called_once_with('ls')
                mock_shell.run.assert_not_called()

    def test_main_with_command_and_args(self):
        """Test that main() passes command arguments correctly."""
        with patch.object(sys, 'argv', ['algograph', 'cd', 'A']):
            with patch('AlgoGraph.shell.cli.GraphShell') as mock_shell_class:
                mock_shell = MagicMock()
                mock_shell_class.return_value = mock_shell

                main()

                mock_shell.execute_command.assert_called_once_with('cd A')


class TestCLIGraphLoading:
    """Tests for graph file loading."""

    def test_load_graph_file(self):
        """Test loading graph from file with -g option."""
        # Create a temporary graph file
        graph = Graph.builder().add_vertex('X').add_vertex('Y').add_edge('X', 'Y').build()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            save_graph(graph, f.name)
            temp_file = f.name

        try:
            with patch.object(sys, 'argv', ['algograph', '-g', temp_file, 'ls']):
                with patch('AlgoGraph.shell.cli.GraphShell') as mock_shell_class:
                    mock_shell = MagicMock()
                    mock_shell_class.return_value = mock_shell

                    # Capture output
                    with patch('sys.stdout', new_callable=StringIO):
                        main()

                    # Verify the shell was created with a context
                    mock_shell_class.assert_called_once()
                    call_args = mock_shell_class.call_args
                    context = call_args[0][0]

                    # Verify the loaded graph has the expected structure
                    assert context.graph.has_vertex('X')
                    assert context.graph.has_vertex('Y')
        finally:
            os.unlink(temp_file)

    def test_load_nonexistent_file(self):
        """Test that missing file falls back to sample graph."""
        with patch.object(sys, 'argv', ['algograph', '-g', '/nonexistent/path.json', 'ls']):
            with patch('AlgoGraph.shell.cli.GraphShell') as mock_shell_class:
                mock_shell = MagicMock()
                mock_shell_class.return_value = mock_shell

                # Capture stderr
                with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                    with patch('sys.stdout', new_callable=StringIO):
                        main()

                    # Verify error message was printed
                    assert 'not found' in mock_stderr.getvalue()

                # Verify shell was still created (with sample graph)
                mock_shell_class.assert_called_once()
                call_args = mock_shell_class.call_args
                context = call_args[0][0]

                # Should be sample graph
                assert context.graph.vertex_count == 4

    def test_load_invalid_file(self):
        """Test that invalid file falls back to sample graph."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            temp_file = f.name

        try:
            with patch.object(sys, 'argv', ['algograph', '-g', temp_file, 'ls']):
                with patch('AlgoGraph.shell.cli.GraphShell') as mock_shell_class:
                    mock_shell = MagicMock()
                    mock_shell_class.return_value = mock_shell

                    # Capture stderr
                    with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                        with patch('sys.stdout', new_callable=StringIO):
                            main()

                        # Verify error message was printed
                        assert 'Error loading graph' in mock_stderr.getvalue()

                    # Verify shell was still created (with sample graph)
                    mock_shell_class.assert_called_once()
        finally:
            os.unlink(temp_file)


class TestCLIArgParse:
    """Tests for argument parsing."""

    def test_help_argument(self):
        """Test that --help works correctly."""
        with patch.object(sys, 'argv', ['algograph', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # argparse exits with 0 for --help
            assert exc_info.value.code == 0

    def test_graph_option_short(self):
        """Test -g short option for graph file."""
        with patch.object(sys, 'argv', ['algograph', '-g', '/some/path.json']):
            with patch('AlgoGraph.shell.cli.GraphShell') as mock_shell_class:
                mock_shell = MagicMock()
                mock_shell_class.return_value = mock_shell

                with patch('sys.stderr', new_callable=StringIO):
                    with patch('sys.stdout', new_callable=StringIO):
                        main()

                # Should have tried to load the file and fallen back
                mock_shell_class.assert_called_once()

    def test_graph_option_long(self):
        """Test --graph long option for graph file."""
        with patch.object(sys, 'argv', ['algograph', '--graph', '/some/path.json']):
            with patch('AlgoGraph.shell.cli.GraphShell') as mock_shell_class:
                mock_shell = MagicMock()
                mock_shell_class.return_value = mock_shell

                with patch('sys.stderr', new_callable=StringIO):
                    with patch('sys.stdout', new_callable=StringIO):
                        main()

                # Should have tried to load the file and fallen back
                mock_shell_class.assert_called_once()
