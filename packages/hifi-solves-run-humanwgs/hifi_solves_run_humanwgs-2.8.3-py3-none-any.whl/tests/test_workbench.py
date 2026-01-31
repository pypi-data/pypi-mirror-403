#!/usr/bin/env python3
"""
Integration tests for workbench functions.

These tests require the user to be logged in to Workbench via `omics auth login`.
Tests use the user's default namespace and create workflows prefixed with "TEST-"
to avoid conflicts with real workflows.

To run these tests:
    omics auth login
    python -m pytest tests/test_workbench.py -v
"""

import json
import os
import subprocess
import unittest

from hifi_solves_run_humanwgs.workbench import (
    _register_or_retrieve_workflow,
    _register_workflow_version,
    _register_workflow_defaults,
    _register_workflow_transformations,
    configure_workflow,
)
from hifi_solves_run_humanwgs.logger import logger


# Check if user is logged in to Workbench
auth_status = subprocess.run(
    ["omics", "auth", "status"],
    capture_output=True,
    text=True,
)
if auth_status.returncode != 0:
    logger.error("Not logged in to Workbench. Run 'omics auth login' first.")
    raise SystemExit(1)


# Test workflow prefix to avoid conflicts with real workflows
TEST_PREFIX = "TEST-"


def delete_test_workflows():
    """Delete all workflows with the TEST- prefix."""
    result = subprocess.run(
        [
            "omics", "workbench", "workflows", "list",
            "--source", "PRIVATE",
            "--search", TEST_PREFIX,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        try:
            workflows = json.loads(result.stdout)
            for workflow in workflows:
                if workflow["name"].startswith(TEST_PREFIX):
                    subprocess.run(
                        [
                            "omics", "workbench", "workflows", "delete",
                            "-f",
                            workflow["internalId"],
                        ],
                        capture_output=True,
                        text=True,
                    )
        except json.JSONDecodeError:
            pass  # No workflows found or invalid response


class TestRegisterOrRetrieveWorkflow(unittest.TestCase):
    namespace = None  # Use default namespace
    workflow_name = f"{TEST_PREFIX}Workflow (hifisolves-ingest tests)"
    workflow_version = "v0.0.1-test"
    entrypoint_path = "/tmp/test_workflow.wdl"
    entrypoint_content = """
version 1.0

workflow test_workflow {
    input {
        String test_input
    }
    output {
        String result = test_input
    }
}
"""

    @classmethod
    def setUpClass(cls):
        with open(cls.entrypoint_path, "w") as f:
            f.write(cls.entrypoint_content)
        delete_test_workflows()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.entrypoint_path):
            os.remove(cls.entrypoint_path)
        delete_test_workflows()

    def test_creates_new_workflow(self):
        workflow_id = _register_or_retrieve_workflow(
            self.workflow_name,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )

        self.assertIsNotNone(workflow_id)
        self.assertIsInstance(workflow_id, str)
        self.assertGreater(len(workflow_id), 0)

    def test_retrieves_existing_workflow(self):
        workflow_id_1 = _register_or_retrieve_workflow(
            self.workflow_name,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )

        workflow_id_2 = _register_or_retrieve_workflow(
            self.workflow_name,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )

        self.assertEqual(workflow_id_1, workflow_id_2)


class TestRegisterWorkflowVersion(unittest.TestCase):
    namespace = None
    workflow_name = f"{TEST_PREFIX}Workflow Version (hifisolves-ingest tests)"
    workflow_version = "v0.0.1-test"
    entrypoint_path = "/tmp/test_workflow.wdl"
    entrypoint_content = """
version 1.0

workflow test_workflow {
    input {
        String test_input
    }
    output {
        String result = test_input
    }
}
"""

    @classmethod
    def setUpClass(cls):
        with open(cls.entrypoint_path, "w") as f:
            f.write(cls.entrypoint_content)
        delete_test_workflows()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.entrypoint_path):
            os.remove(cls.entrypoint_path)
        delete_test_workflows()

    def test_registers_version(self):
        workflow_id = _register_or_retrieve_workflow(
            self.workflow_name,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )

        _register_workflow_version(
            workflow_id,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )

        result = subprocess.run(
            [
                "omics", "workbench", "workflows", "versions", "list",
                "--workflow", workflow_id,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        versions = json.loads(result.stdout)
        version_ids = [v["id"] for v in versions]
        self.assertIn(self.workflow_version, version_ids)


class TestRegisterWorkflowDefaults(unittest.TestCase):
    namespace = None
    workflow_name = f"{TEST_PREFIX}Workflow Defaults (hifisolves-ingest tests)"
    workflow_version = "v0.0.1-test"
    backend = "GCP"
    region = "us-central1"
    static_inputs = {"test_input": "test_value"}
    entrypoint_path = "/tmp/test_workflow.wdl"
    entrypoint_content = """
version 1.0

workflow test_workflow {
    input {
        String test_input
    }
    output {
        String result = test_input
    }
}
"""

    @classmethod
    def setUpClass(cls):
        with open(cls.entrypoint_path, "w") as f:
            f.write(cls.entrypoint_content)
        delete_test_workflows()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.entrypoint_path):
            os.remove(cls.entrypoint_path)
        delete_test_workflows()

    def test_registers_defaults(self):
        workflow_id = _register_or_retrieve_workflow(
            self.workflow_name,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )
        _register_workflow_version(
            workflow_id,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )

        _register_workflow_defaults(
            workflow_id,
            self.workflow_version,
            self.backend,
            self.region,
            self.static_inputs,
            self.namespace,
        )

        result = subprocess.run(
            [
                "omics", "workbench", "workflows", "versions", "defaults", "list",
                "--workflow", workflow_id,
                "--version", self.workflow_version,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        defaults = json.loads(result.stdout)
        self.assertGreater(len(defaults), 0)

        matching_defaults = [
            d for d in defaults
            if d["selector"]["provider"] == self.backend
            and d["selector"]["region"] == self.region
        ]
        self.assertEqual(len(matching_defaults), 1)
        self.assertEqual(matching_defaults[0]["values"], self.static_inputs)

    def test_updates_existing_defaults(self):
        workflow_id = _register_or_retrieve_workflow(
            self.workflow_name,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )
        _register_workflow_version(
            workflow_id,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )

        _register_workflow_defaults(
            workflow_id,
            self.workflow_version,
            self.backend,
            self.region,
            self.static_inputs,
            self.namespace,
        )

        updated_inputs = {"test_input": "updated_value", "new_input": "new_value"}
        _register_workflow_defaults(
            workflow_id,
            self.workflow_version,
            self.backend,
            self.region,
            updated_inputs,
            self.namespace,
        )

        result = subprocess.run(
            [
                "omics", "workbench", "workflows", "versions", "defaults", "list",
                "--workflow", workflow_id,
                "--version", self.workflow_version,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        defaults = json.loads(result.stdout)

        matching_defaults = [
            d for d in defaults
            if d["selector"]["provider"] == self.backend
            and d["selector"]["region"] == self.region
        ]
        self.assertEqual(len(matching_defaults), 1)
        self.assertEqual(matching_defaults[0]["values"], updated_inputs)

    def test_registers_defaults_with_engine(self):
        workflow_name = f"{TEST_PREFIX}Workflow Defaults Engine (hifisolves-ingest tests)"
        engine = "test-engine"

        workflow_id = _register_or_retrieve_workflow(
            workflow_name,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )
        _register_workflow_version(
            workflow_id,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )

        _register_workflow_defaults(
            workflow_id,
            self.workflow_version,
            self.backend,
            self.region,
            self.static_inputs,
            self.namespace,
            engine=engine,
        )

        result = subprocess.run(
            [
                "omics", "workbench", "workflows", "versions", "defaults", "list",
                "--workflow", workflow_id,
                "--version", self.workflow_version,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        defaults = json.loads(result.stdout)
        self.assertGreater(len(defaults), 0)

        matching_defaults = [
            d for d in defaults
            if d["selector"]["provider"] == self.backend
            and d["selector"]["region"] == self.region
            and d["selector"]["engine"] == engine
        ]
        self.assertEqual(len(matching_defaults), 1)
        self.assertEqual(matching_defaults[0]["values"], self.static_inputs)


class TestRegisterWorkflowTransformations(unittest.TestCase):
    namespace = None
    workflow_name = f"{TEST_PREFIX}Workflow Transformations (hifisolves-ingest tests)"
    workflow_version = "v0.0.1-test"
    labels = ["test-label"]
    transformation_js = "(context) => { return {}; }"
    transformation_path = "/tmp/test_transformation.js"
    entrypoint_path = "/tmp/test_workflow.wdl"
    entrypoint_content = """
version 1.0

workflow test_workflow {
    input {
        String test_input
    }
    output {
        String result = test_input
    }
}
"""

    @classmethod
    def setUpClass(cls):
        with open(cls.entrypoint_path, "w") as f:
            f.write(cls.entrypoint_content)
        with open(cls.transformation_path, "w") as f:
            f.write(cls.transformation_js)
        delete_test_workflows()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.entrypoint_path):
            os.remove(cls.entrypoint_path)
        if os.path.exists(cls.transformation_path):
            os.remove(cls.transformation_path)
        delete_test_workflows()

    def test_registers_transformation(self):
        workflow_id = _register_or_retrieve_workflow(
            self.workflow_name,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )
        _register_workflow_version(
            workflow_id,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )

        _register_workflow_transformations(
            workflow_id,
            self.workflow_version,
            self.namespace,
            self.labels,
            self.transformation_path,
        )

        result = subprocess.run(
            [
                "omics", "workbench", "workflows", "versions", "transformations", "list",
                "--workflow", workflow_id,
                "--version", self.workflow_version,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        transformations = json.loads(result.stdout)
        self.assertEqual(len(transformations), 1)
        self.assertEqual(transformations[0]["script"], self.transformation_js)

    def test_updates_existing_transformation(self):
        workflow_id = _register_or_retrieve_workflow(
            self.workflow_name,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )
        _register_workflow_version(
            workflow_id,
            self.workflow_version,
            self.namespace,
            self.entrypoint_path,
        )

        _register_workflow_transformations(
            workflow_id,
            self.workflow_version,
            self.namespace,
            self.labels,
            self.transformation_path,
        )

        updated_js = "(context) => { return { updated: true }; }"
        with open(self.transformation_path, "w") as f:
            f.write(updated_js)

        _register_workflow_transformations(
            workflow_id,
            self.workflow_version,
            self.namespace,
            self.labels,
            self.transformation_path,
        )

        result = subprocess.run(
            [
                "omics", "workbench", "workflows", "versions", "transformations", "list",
                "--workflow", workflow_id,
                "--version", self.workflow_version,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        transformations = json.loads(result.stdout)
        self.assertEqual(len(transformations), 1)
        self.assertEqual(transformations[0]["script"], updated_js)


class TestConfigureWorkflow(unittest.TestCase):
    namespace = None
    workflow_version = "v0.0.1-test"
    backend = "GCP"
    region = "us-central1"
    static_inputs = {"test_input": "test_value"}
    labels = ["test-label"]
    transformation_js = "(context) => { return {}; }"
    transformation_path = "/tmp/test_transformation.js"
    entrypoint_path = "/tmp/test_workflow.wdl"
    entrypoint_content = """
version 1.0

workflow test_workflow {
    input {
        String test_input
    }
    output {
        String result = test_input
    }
}
"""

    @classmethod
    def setUpClass(cls):
        with open(cls.entrypoint_path, "w") as f:
            f.write(cls.entrypoint_content)
        with open(cls.transformation_path, "w") as f:
            f.write(cls.transformation_js)
        delete_test_workflows()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.entrypoint_path):
            os.remove(cls.entrypoint_path)
        if os.path.exists(cls.transformation_path):
            os.remove(cls.transformation_path)
        delete_test_workflows()

    def test_configure_workflow_full(self):
        workflow_name = f"{TEST_PREFIX}Workflow Full (hifisolves-ingest tests)"

        workflow_id = configure_workflow(
            workflow_name=workflow_name,
            workflow_version=self.workflow_version,
            backend=self.backend,
            region=self.region,
            static_inputs=self.static_inputs,
            namespace=self.namespace,
            labels=self.labels,
            transformation_path=self.transformation_path,
            entrypoint_path=self.entrypoint_path,
        )

        self.assertIsNotNone(workflow_id)
        self.assertIsInstance(workflow_id, str)

        result = subprocess.run(
            [
                "omics", "workbench", "workflows", "list",
                "--source", "PRIVATE",
                "--search", workflow_name,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        workflows = json.loads(result.stdout)
        matching = [w for w in workflows if w["name"] == workflow_name]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["internalId"], workflow_id)

    def test_configure_workflow_idempotent(self):
        workflow_name = f"{TEST_PREFIX}Workflow Idempotent (hifisolves-ingest tests)"

        workflow_id_1 = configure_workflow(
            workflow_name=workflow_name,
            workflow_version=self.workflow_version,
            backend=self.backend,
            region=self.region,
            static_inputs=self.static_inputs,
            namespace=self.namespace,
            labels=self.labels,
            transformation_path=self.transformation_path,
            entrypoint_path=self.entrypoint_path,
        )

        workflow_id_2 = configure_workflow(
            workflow_name=workflow_name,
            workflow_version=self.workflow_version,
            backend=self.backend,
            region=self.region,
            static_inputs=self.static_inputs,
            namespace=self.namespace,
            labels=self.labels,
            transformation_path=self.transformation_path,
            entrypoint_path=self.entrypoint_path,
        )

        self.assertEqual(workflow_id_1, workflow_id_2)


if __name__ == "__main__":
    unittest.main()
