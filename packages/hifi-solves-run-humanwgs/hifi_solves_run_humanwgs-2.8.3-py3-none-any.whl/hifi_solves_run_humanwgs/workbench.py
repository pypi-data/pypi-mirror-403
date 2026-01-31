"""
Functions for interacting with DNAstack Workbench to configure workflows.
"""

import json
import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)


def configure_workbench(workbench_url):
    """
    Configure the workbench URL for omics CLI. This will also ask the user to authenticate interactively if they are not already logged in.

    Args:
        workbench_url (str): The workbench URL to use

    Raises:
        SystemExit: If configuration fails
    """
    logger.info("Configuring workbench")
    workbench_config = subprocess.run(["omics", "use", workbench_url])
    if workbench_config.returncode != 0:
        logger.error(f"Failed to configure workbench URL '{workbench_url}'")
        raise SystemExit(1)
    logger.debug("\t✓ Workbench configured")


def get_latest_workflow_version(workflow_id, namespace=None):
    """
    Get the latest version of a workflow.

    Args:
        workflow_id (str): The workflow's internal ID
        namespace (str): Optional namespace to search in

    Returns:
        version_id (str): The latest version ID, or None if no versions found
    """
    list_versions_args = [
        "omics",
        "workbench",
        "workflows",
        "versions",
        "list",
        "--workflow",
        workflow_id,
    ]

    if namespace is not None:
        list_versions_args += ["--namespace", namespace]

    versions_list = subprocess.run(
        list_versions_args,
        capture_output=True,
        text=True,
    )

    if versions_list.returncode == 0:
        try:
            versions_list_json = json.loads(versions_list.stdout)
            if len(versions_list_json) > 0:
                # First version in list is the latest
                return versions_list_json[0]["id"]
            return None
        except json.JSONDecodeError as e:
            logger.error(f"\t✗ Error parsing JSON: {e}\n{versions_list.stderr}")
            raise SystemExit(1)
    else:
        logger.error(
            f"\t✗ Something went wrong when listing workflow versions\n{versions_list.stderr}"
        )
        raise SystemExit(1)


def get_workflow_id_by_name(workflow_name, namespace=None, source=None):
    list_wf_args = [
        "omics",
        "workbench",
        "workflows",
        "list",
        "--search",
        workflow_name,
    ]

    if source is not None:
        list_wf_args += ["--source", source]

    if namespace is not None:
        list_wf_args += ["--namespace", namespace]

    workflow_list = subprocess.run(
        list_wf_args,
        capture_output=True,
        text=True,
    )

    if workflow_list.returncode == 0:
        try:
            workflow_list_json = json.loads(workflow_list.stdout)
            for workflow in workflow_list_json:
                if workflow["name"] == workflow_name:
                    return workflow["internalId"]
            return None
        except json.JSONDecodeError as e:
            logger.error(f"\t✗ Error parsing JSON: {e}\n{workflow_list.stderr}")
            raise SystemExit(1)
    else:
        logger.error(
            f"\t✗ Something went wrong when listing workflows\n{workflow_list.stderr}"
        )
        raise SystemExit(1)


def _register_or_retrieve_workflow(
    workflow_name, workflow_version, namespace, entrypoint_path
):
    """
    Register or retrieve a workflow from Workbench

    Args:
        workflow_name (str): Name of the workflow
        workflow_version (str): Workflow version
        namespace (str): Optional namespace to use; by default, will be derived from the user's context
        entrypoint_path (str): Path to the main WDL file for the workflow

    Returns:
        workflow_id (str): Workflow ID for the workflow
    """

    def _register_workflow(workflow_name, workflow_version):
        create_wf_args = [
            "omics",
            "workbench",
            "workflows",
            "create",
            "--name",
            workflow_name,
            "--version-name",
            workflow_version,
            "--entrypoint",
            entrypoint_path,
        ]

        if namespace is not None:
            create_wf_args += ["--namespace", namespace]

        workflow_info = subprocess.run(
            create_wf_args,
            capture_output=True,
            text=True,
        )
        if workflow_info.returncode == 0:
            try:
                workflow_info_json = json.loads(workflow_info.stdout)
                workflow_id = workflow_info_json["internalId"]
                logger.debug("\t✓ Registered workflow")
                return workflow_id
            except json.JSONDecodeError as e:
                logger.error(f"\t✗ Error parsing JSON: {e}")
                raise SystemExit(1)
        else:
            logger.error(
                f"\t✗ Something went wrong when attempting to register the workflow\n{workflow_info.stderr}"
            )
            raise SystemExit(1)

    # See if the workflow exists
    workflow_id = get_workflow_id_by_name(workflow_name, namespace, source="PRIVATE")
    if workflow_id is None:
        logger.debug("\tWorkflow not found in Workbench; registering workflow")
        workflow_id = _register_workflow(workflow_name, workflow_version)

    return workflow_id


def _register_workflow_version(
    workflow_id, workflow_version, namespace, entrypoint_path
):
    """
    Register a workflow version in Workbench, if it does not already exist

    Args:
        workflow_id (str): The ID of the workflow registered in Workbench to version
        workflow_version (str): The verison of the workflow to register
        namespace (str): Optional namespace to use; by default, will be derived from the user's context
        entrypoint_path (str): Path to the main WDL file for the workflow
    """

    def _register_version(workflow_id, workflow_version):
        register_version_args = [
            "omics",
            "workbench",
            "workflows",
            "versions",
            "create",
            "--workflow",
            workflow_id,
            "--name",
            workflow_version,
            "--entrypoint",
            entrypoint_path,
        ]

        if namespace is not None:
            register_version_args += ["--namespace", namespace]

        version_info = subprocess.run(
            register_version_args,
            capture_output=True,
            text=True,
        )

        if version_info.returncode == 0:
            logger.debug("\t✓ Registered workflow version")
        else:
            logger.error(
                f"\t✗ Something went wrong when attempting to register a workflow version\n{version_info.stderr}"
            )
            raise SystemExit(1)

    # See if the workflow version exists
    list_versions_args = [
        "omics",
        "workbench",
        "workflows",
        "versions",
        "list",
        "--workflow",
        workflow_id,
    ]

    if namespace is not None:
        list_versions_args += ["--namespace", namespace]

    versions_list = subprocess.run(
        list_versions_args,
        capture_output=True,
        text=True,
    )

    if versions_list.returncode == 0:
        try:
            versions_list_json = json.loads(versions_list.stdout)
            all_versions = [v["id"] for v in versions_list_json]
            if workflow_version not in all_versions:
                _register_version(workflow_id, workflow_version)
        except json.JSONDecodeError as e:
            logger.error(f"\t✗ Error parsing JSON: {e}\n{versions_list.stderr}")
            raise SystemExit(1)
    else:
        logger.error(
            f"\t✗ Something went wrong when listing workflow versions\n{versions_list.stderr}"
        )
        raise SystemExit(1)


def _register_workflow_defaults(
    workflow_id,
    workflow_version,
    backend,
    region,
    static_inputs,
    namespace,
    engine=None,
):
    """
    Define the default (static) values for the workflow inputs, if they don't exist

    Args:
        workflow_id (str): The ID of the workflow registered in Workbench to version
        workflow_version (str): The verison of the workflow to register
        backend (str): The cloud backend where infrastructure will be run; used as a selector for defaults values
        region (str): The cloud region where infrastructure will be run; used a a selector for defaults values
        static_inputs (dict): The set of static inputs for the workflow
        namespace (str): Optional namespace to use; by default, will be derived from the user's context
        engine (str): Optional engine selector for the defaults
    """

    def _get_default_set_by_selector(defaults_list_json, selector):
        for default_set in defaults_list_json:
            if default_set["selector"] == selector:
                return default_set
        return None

    def _register_defaults(
        workflow_id,
        workflow_version,
        backend,
        region,
        defaults_version_id,
        values,
        update=False,
    ):
        if update is True:
            defaults_cmd = "update"
        else:
            defaults_cmd = "create"

        crud_defaults_args = [
            "omics",
            "workbench",
            "workflows",
            "versions",
            "defaults",
            defaults_cmd,
            "--workflow",
            workflow_id,
            "--version",
            workflow_version,
            "--provider",
            backend,
            "--region",
            region,
            "--values",
            json.dumps(values),
        ]

        if engine is not None:
            crud_defaults_args += ["--engine", engine]

        if namespace is not None:
            crud_defaults_args += ["--namespace", namespace]

        # Positional argument must come last
        crud_defaults_args.append(defaults_version_id)

        default_info = subprocess.run(
            crud_defaults_args,
            capture_output=True,
            text=True,
        )

        if default_info.returncode == 0:
            logger.debug("\t✓ Registered workflow defaults")
        else:
            logger.error(
                f"\t✗ Something went wrong when attempting to register workflow defaults\n{default_info.stderr}"
            )
            raise SystemExit(1)

    selector = {"engine": engine, "provider": backend, "region": region}

    # Check if workflow defaults already exist and match the defaults we're trying to set
    # If not, register them
    list_defaults_args = [
        "omics",
        "workbench",
        "workflows",
        "versions",
        "defaults",
        "list",
        "--workflow",
        workflow_id,
        "--version",
        workflow_version,
    ]

    if namespace is not None:
        list_defaults_args += ["--namespace", namespace]

    defaults_list = subprocess.run(
        list_defaults_args,
        capture_output=True,
        text=True,
    )

    if defaults_list.returncode == 0:
        try:
            defaults_list_json = json.loads(defaults_list.stdout)

            existing_default_set = _get_default_set_by_selector(
                defaults_list_json, selector
            )
            if existing_default_set is None:
                # Build defaults version ID from components
                # Using backend, region, and engine as part of the ID means you can configure different defaults for different engine setups
                id_parts = [workflow_version.replace(".", "_"), backend, region]
                if engine is not None:
                    id_parts.append(engine)
                defaults_version_id = "_".join(id_parts)
                # Truncate to 64 characters max (API limit)
                if len(defaults_version_id) > 64:
                    defaults_version_id = defaults_version_id[:64]
                _register_defaults(
                    workflow_id,
                    workflow_version,
                    backend,
                    region,
                    defaults_version_id,
                    static_inputs,
                    update=False,
                )
            else:
                # The existing default already has the correct values
                if existing_default_set["values"] == static_inputs:
                    return
                else:
                    # The existing default has different values; update it
                    _register_defaults(
                        workflow_id,
                        workflow_version,
                        backend,
                        region,
                        existing_default_set["id"],
                        static_inputs,
                        update=True,
                    )

        except json.JSONDecodeError as e:
            logger.error(f"\t✗ Error parsing JSON: {e}\n{defaults_list.stderr}")
            raise SystemExit(1)
    else:
        logger.error(
            f"\t✗ Something went wrong when listing workflow defaults versions\n{defaults_list.stderr}"
        )
        raise SystemExit(1)


def _register_workflow_transformations(
    workflow_id,
    workflow_version,
    namespace,
    labels,
    transformation_path,
):
    """
    Define the transformations needed to map samples into workflow inputs, if they don't exist

    Args:
        workflow_id (str): The ID of the workflow registered in Workbench to version
        workflow_version (str): The verison of the workflow to register
        namespace (str): Optional namespace to use; by default, will be derived from the user's context
        labels (list): List of labels to apply to the transformation
        transformation_path (str): Path to the JavaScript transformation file
    """
    with open(transformation_path, "r") as f:
        transformation_js = f.read()

    def _register_transformation(
        workflow_id,
        workflow_version,
        transformation_js,
        transformation_id,
        existing_transformation_id=None,
    ):
        if existing_transformation_id is not None:
            # delete the existing transformation
            delete_transformation_args = [
                "omics",
                "workbench",
                "workflows",
                "versions",
                "transformations",
                "delete",
                "-f",
                "--workflow",
                workflow_id,
                "--version",
                workflow_version,
                existing_transformation_id,
            ]

            if namespace is not None:
                delete_transformation_args += ["--namespace", namespace]

            transformation_deleted_info = subprocess.run(
                delete_transformation_args,
                capture_output=True,
                text=True,
            )

            if transformation_deleted_info.returncode != 0:
                logger.error(
                    f"\t✗ Something went wrong when attempting to delete an existing workflow transformation\n{transformation_deleted_info.stderr}"
                )
                raise SystemExit(1)

        create_transformation_args = [
            "omics",
            "workbench",
            "workflows",
            "versions",
            "transformations",
            "create",
            "--workflow",
            workflow_id,
            "--version",
            workflow_version,
        ]
        for label in labels:
            create_transformation_args += ["--label", label]
        create_transformation_args += [
            "--id",
            transformation_id,
        ]

        if namespace is not None:
            create_transformation_args += ["--namespace", namespace]

        # Add the script as the final positional argument
        create_transformation_args.append(f"@{transformation_path}")

        logger.debug(f"Running: {' '.join(create_transformation_args)}")

        transformation_info = subprocess.run(
            create_transformation_args,
            capture_output=True,
            text=True,
        )

        if transformation_info.returncode == 0:
            logger.debug("\t✓ Registered workflow transformation")
        else:
            logger.error(
                f"\t✗ Something went wrong when attempting to register a workflow transformation\n{transformation_info.stderr}"
            )
            raise SystemExit(1)

    # See if the workflow transformation exists
    list_transformations_args = [
        "omics",
        "workbench",
        "workflows",
        "versions",
        "transformations",
        "list",
        "--workflow",
        workflow_id,
        "--version",
        workflow_version,
    ]

    if namespace is not None:
        list_transformations_args += ["--namespace", namespace]

    transformations_list = subprocess.run(
        list_transformations_args,
        capture_output=True,
        text=True,
    )

    if transformations_list.returncode == 0:
        try:
            transformations_list_json = json.loads(transformations_list.stdout)
            n_transformations = len(transformations_list_json)

            # We'll just use the workflow version as the transformation ID (but no periods allowed)
            transformation_id = workflow_version.replace(".", "_")

            # unlikely to actually have more than 1 transformation, but let's confirm that
            if n_transformations == 0:
                # register a new transformation
                _register_transformation(
                    workflow_id,
                    workflow_version,
                    transformation_js,
                    transformation_id,
                )
            elif n_transformations == 1:
                existing = transformations_list_json[0]
                existing_labels = sorted(existing.get("labels", []))
                desired_labels = sorted(labels)
                script_unchanged = existing["script"] == transformation_js
                labels_unchanged = existing_labels == desired_labels
                if script_unchanged and labels_unchanged:
                    return
                else:
                    _register_transformation(
                        workflow_id,
                        workflow_version,
                        transformation_js,
                        transformation_id,
                        existing["id"],
                    )
            else:
                logger.error(
                    f"Expected exactly one transformation for the workflow; got {n_transformations}"
                )
                raise SystemExit(1)

        except json.JSONDecodeError as e:
            logger.error(f"\t✗ Error parsing JSON: {e}\n{transformations_list.stderr}")
            raise SystemExit(1)

    else:
        logger.error(
            f"\t✗ Something went wrong when listing workflow transformations\n{transformations_list.stderr}"
        )
        raise SystemExit(1)


def configure_workflow(
    workflow_name,
    workflow_version,
    backend,
    region,
    static_inputs,
    namespace,
    labels,
    transformation_path,
    entrypoint_path,
    engine=None,
):
    """
    Register and configure a workflow if it does not exist; get the workflow_id if it does

    Args:
        workflow_name (str): Name of the workflow
        workflow_version (str): Workflow version
        backend (str): The cloud backend where infrastructure will be run; used as a selector for defaults values
        region (str): The cloud region where infrastructure will be run; used as a selector for defaults values
        static_inputs (dict): The set of static inputs for the workflow
        namespace (str): Optional namespace to use; by default, will be derived from the user's context
        labels (list): List of labels to apply to the transformation
        transformation_path (str): Path to the JavaScript transformation file
        entrypoint_path (str): Path to the main WDL file for the workflow
        engine (str): Optional engine selector for the defaults

    Returns:
        workflow_id (str): Workflow ID for the workflow
    """
    workflow_id = _register_or_retrieve_workflow(
        workflow_name, workflow_version, namespace, entrypoint_path
    )
    _register_workflow_version(
        workflow_id, workflow_version, namespace, entrypoint_path
    )
    _register_workflow_defaults(
        workflow_id, workflow_version, backend, region, static_inputs, namespace, engine
    )
    _register_workflow_transformations(
        workflow_id, workflow_version, namespace, labels, transformation_path
    )

    return workflow_id
