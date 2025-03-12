#!/usr/bin/env python
"""
Functional test for the monitoring configuration.
This script tests the monitoring_config.json configuration with mock MCP servers.
"""

import os
import sys
import json
import unittest
import subprocess
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_base import BaseMCPTest

class TestMonitoringConfig(BaseMCPTest):
    """Test case for the monitoring configuration."""
    
    def setUp(self):
        """Set up the test case."""
        super().setUp()
        self.config_name = "monitoring_config.json"
        self.query_script = "monitoring_query.py"
        
        # Load the configuration
        self.config = self.load_config(self.config_name)
    
    def test_config_structure(self):
        """Test that the configuration has the expected structure."""
        self.assertIn("mcpServers", self.config, "Configuration missing mcpServers key")
        
        # Check that the configuration has the expected servers
        expected_servers = ["sentry"]
        for server in expected_servers:
            self.assertTrue(self.server_exists(server, self.config), f"Configuration missing {server} server")
    
    def test_mock_servers(self):
        """Test that the mock servers can be started."""
        # Start the monitoring server
        monitoring_server = self.start_mock_server(
            sys.executable,
            [os.path.join(self.config_dir, "tests", "mocks", "mock_server.py"), "--server-type", "monitoring"]
        )
        self.assertIsNotNone(monitoring_server, "Failed to start monitoring server")
    
    def test_query_execution(self):
        """Test that the query script can be executed with mock servers."""
        # Create a temporary configuration file that uses the mock servers
        temp_config = {
            "mcpServers": {
                "sentry": {
                    "command": sys.executable,
                    "args": [os.path.join(self.config_dir, "tests", "mocks", "mock_server.py"), "--server-type", "monitoring"],
                    "env": {}
                }
            }
        }
        
        temp_config_path = os.path.join(self.config_dir, "tests", "temp_monitoring_config.json")
        with open(temp_config_path, "w") as f:
            json.dump(temp_config, f)
        
        try:
            # Execute the query script with the temporary configuration
            result = subprocess.run(
                [sys.executable, os.path.join(self.config_dir, self.query_script), "--project", "test-project", "--status", "unresolved", "--limit", "3", "--config", temp_config_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check that the script executed successfully
            self.assertEqual(result.returncode, 0, f"Query script failed with error: {result.stderr}")
            
            # Check that the output contains expected content
            self.assertIn("sentry issues", result.stdout.lower(), "Output does not contain issues information")
            self.assertIn("performance metrics", result.stdout.lower(), "Output does not contain performance metrics information")
            
            print("Monitoring query executed successfully.")
            print("Output excerpt:")
            print("\n".join(result.stdout.split("\n")[:10]) + "\n...")
            
        except subprocess.CalledProcessError as e:
            self.fail(f"Error executing query: {e}")
        finally:
            # Clean up the temporary configuration file
            if os.path.exists(temp_config_path):
                os.remove(temp_config_path)

if __name__ == "__main__":
    unittest.main()
