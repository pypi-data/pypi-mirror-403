#!/usr/bin/env python3

import json
import unittest
from hifi_solves_run_humanwgs.backends.parameter_override import (
    generate_memory_override_inputs,
)
from hifi_solves_run_humanwgs.upload_and_run import (
    import_backend_module,
    filter_by_families,
    get_tags,
)
from hifi_solves_run_humanwgs.backends.parameter_override import MEMORY_OVERRIDE_KEYS
from hifi_solves_run_humanwgs.logger import logger
import pandas as pd


class TestGenerateInput(unittest.TestCase):
    expected_sample_info = pd.DataFrame.from_records(
        [
            (
                "HG005-fam",
                "HG005",
                ["movie1.bam", "movie2.bam"],
                "HG006",
                "HG007",
                "MALE",
                False,
                0,
            ),
            ("HG005-fam", "HG006", ["movie3.bam"], None, None, "MALE", False, 0),
            ("HG005-fam", "HG007", ["movie4.bam"], None, None, "FEMALE", False, 0),
        ],
        columns=[
            "family_id",
            "sample_id",
            "hifi_reads",
            "father_id",
            "mother_id",
            "sex",
            "affected",
            "total_file_size_bytes",
        ],
    ).set_index("sample_id", drop=False)

    def test_all_memory_override_inputs(self):
        expected_memory_override_inputs = {
            "HumanWGS_wrapper.hiphase_override_mem_gb": 1,
            "HumanWGS_wrapper.merge_bam_stats_override_mem_gb": 2,
            "HumanWGS_wrapper.pbmm2_align_wgs_override_mem_gb": 3,
            "HumanWGS_wrapper.pbstarphase_diplotype_override_mem_gb": 5,
            "HumanWGS_wrapper.pbsv_discover_override_mem_gb": 6,
            "HumanWGS_wrapper.pbsv_call_mem_gb": 7,
        }

        input_memory_override_inputs = {
            "hiphase_override_mem_gb": 1,
            "merge_bam_stats_override_mem_gb": 2,
            "pbmm2_align_wgs_override_mem_gb": 3,
            "pbstarphase_diplotype_override_mem_gb": 5,
            "pbsv_discover_override_mem_gb": 6,
            "pbsv_call_mem_gb": 7,
        }

        test_mem_override_inputs = {}
        test_mem_override_inputs.update(
            generate_memory_override_inputs(input_memory_override_inputs)
        )
        self.assertDictEqual(expected_memory_override_inputs, test_mem_override_inputs)

    def test_partial_memory_override_inputs(self):
        expected_memory_override_inputs = {
            "HumanWGS_wrapper.hiphase_override_mem_gb": 1,
            "HumanWGS_wrapper.pbstarphase_diplotype_override_mem_gb": 5,
        }

        input_memory_override_inputs = {
            "hiphase_override_mem_gb": 1,
            "merge_bam_stats_override_mem_gb": None,
            "pbmm2_align_wgs_override_mem_gb": None,
            "pbstarphase_diplotype_override_mem_gb": 5,
            "pbsv_discover_override_mem_gb": None,
            "pbsv_call_mem_gb": None,
        }

        test_mem_override_inputs = {}
        test_mem_override_inputs.update(
            generate_memory_override_inputs(input_memory_override_inputs)
        )
        self.assertDictEqual(expected_memory_override_inputs, test_mem_override_inputs)

    def test_none_memory_override_inputs(self):
        expected_memory_override_inputs = {}
        input_memory_override_inputs = {
            "hiphase_override_mem_gb": None,
            "merge_bam_stats_override_mem_gb": None,
            "pbmm2_align_wgs_override_mem_gb": None,
            "pbstarphase_diplotype_override_mem_gb": None,
            "pbsv_discover_override_mem_gb": None,
            "pbsv_call_mem_gb": None,
        }

        test_mem_override_inputs = {}
        test_mem_override_inputs.update(
            generate_memory_override_inputs(input_memory_override_inputs)
        )
        self.assertDictEqual(expected_memory_override_inputs, test_mem_override_inputs)

    def test_gcp_generate_inputs(self):
        backend_module = import_backend_module("GCP")
        reference_input_bucket = "testorg-reference-inputs"
        workflow_file_outputs_bucket = "testorg-workflow-file-outputs"
        region = "us-central1-b"
        container_registry = "dnastack"
        expected_workflow_inputs = {
            "HumanWGS_wrapper.family": {
                "family_id": "HG005-fam",
                "samples": [
                    {
                        "sample_id": "HG005",
                        "hifi_reads": ["movie1.bam", "movie2.bam"],
                        "father_id": "HG006",
                        "mother_id": "HG007",
                        "sex": "MALE",
                        "affected": False,
                    },
                    {
                        "sample_id": "HG006",
                        "hifi_reads": ["movie3.bam"],
                        "sex": "MALE",
                        "affected": False,
                    },
                    {
                        "sample_id": "HG007",
                        "hifi_reads": ["movie4.bam"],
                        "sex": "FEMALE",
                        "affected": False,
                    },
                ],
            },
            "HumanWGS_wrapper.ref_map_file": "gs://testorg-reference-inputs/dataset/map_files/GRCh38.ref_map.v2p0p0.gcp.tsv",
            "HumanWGS_wrapper.backend": "GCP",
            "HumanWGS_wrapper.preemptible": True,
            "HumanWGS_wrapper.workflow_outputs_bucket": "gs://testorg-workflow-file-outputs",
            "HumanWGS_wrapper.zones": "us-central1-b-b us-central1-b-c",
            "HumanWGS_wrapper.container_registry": "dnastack",
            "HumanWGS_wrapper.hiphase_override_mem_gb": 1,
            "HumanWGS_wrapper.merge_bam_stats_override_mem_gb": 2,
            "HumanWGS_wrapper.pbmm2_align_wgs_override_mem_gb": 3,
            "HumanWGS_wrapper.pbstarphase_diplotype_override_mem_gb": 5,
            "HumanWGS_wrapper.pbsv_discover_override_mem_gb": 6,
            "HumanWGS_wrapper.pbsv_call_mem_gb": 7,
        }
        input_memory_override_inputs = {
            "hiphase_override_mem_gb": 1,
            "merge_bam_stats_override_mem_gb": 2,
            "pbmm2_align_wgs_override_mem_gb": 3,
            "pbstarphase_diplotype_override_mem_gb": 5,
            "pbsv_discover_override_mem_gb": 6,
            "pbsv_call_mem_gb": 7,
        }
        static_inputs = backend_module.get_static_workflow_inputs(
            reference_inputs_bucket=reference_input_bucket,
            workflow_file_outputs_bucket=workflow_file_outputs_bucket,
            region=region,
            container_registry=container_registry,
        )
        workflow_inputs, engine_params = backend_module.generate_inputs_json(
            self.expected_sample_info,
            reference_input_bucket,
            workflow_file_outputs_bucket,
            region,
            container_registry=container_registry,
            **input_memory_override_inputs
        )
        self.assertDictEqual(workflow_inputs, expected_workflow_inputs)


class TestGetTags(unittest.TestCase):
    """Tests for the get_tags function, particularly inputs_hash behavior."""

    base_workflow_inputs = {
        "HumanWGS_wrapper.family": {
            "family_id": "test-fam",
            "samples": [
                {
                    "sample_id": "sample-1",
                    "hifi_reads": ["s3://bucket/sample-1.bam"],
                    "sex": "MALE",
                    "affected": False,
                }
            ],
        },
        "HumanWGS_wrapper.ref_map_file": "s3://bucket/ref.tsv",
        "HumanWGS_wrapper.backend": "AWS",
    }

    def test_hash_unchanged_with_memory_overrides(self):
        """Test that adding memory overrides does not change the inputs_hash."""
        tags_without_overrides = get_tags(self.base_workflow_inputs)

        # Add all memory overrides
        inputs_with_overrides = self.base_workflow_inputs.copy()
        inputs_with_overrides["HumanWGS_wrapper.hiphase_override_mem_gb"] = 128
        inputs_with_overrides["HumanWGS_wrapper.merge_bam_stats_override_mem_gb"] = 64
        inputs_with_overrides["HumanWGS_wrapper.pbmm2_align_wgs_override_mem_gb"] = 32

        tags_with_overrides = get_tags(inputs_with_overrides)

        self.assertEqual(
            tags_without_overrides["inputs_hash"],
            tags_with_overrides["inputs_hash"],
            "Hash should be identical regardless of memory overrides",
        )

    def test_hash_unchanged_with_different_override_values(self):
        """Test that different memory override values produce the same hash."""
        inputs_low_mem = self.base_workflow_inputs.copy()
        inputs_low_mem["HumanWGS_wrapper.hiphase_override_mem_gb"] = 64

        inputs_high_mem = self.base_workflow_inputs.copy()
        inputs_high_mem["HumanWGS_wrapper.hiphase_override_mem_gb"] = 256

        tags_low = get_tags(inputs_low_mem)
        tags_high = get_tags(inputs_high_mem)

        self.assertEqual(
            tags_low["inputs_hash"],
            tags_high["inputs_hash"],
            "Hash should be identical regardless of override values",
        )

    def test_hash_changes_with_different_samples(self):
        """Test that changing actual input data does change the hash."""
        tags_original = get_tags(self.base_workflow_inputs)

        # Change the sample data
        different_inputs = {
            "HumanWGS_wrapper.family": {
                "family_id": "test-fam",
                "samples": [
                    {
                        "sample_id": "sample-2",  # Different sample
                        "hifi_reads": ["s3://bucket/sample-2.bam"],
                        "sex": "FEMALE",
                        "affected": False,
                    }
                ],
            },
            "HumanWGS_wrapper.ref_map_file": "s3://bucket/ref.tsv",
            "HumanWGS_wrapper.backend": "AWS",
        }

        tags_different = get_tags(different_inputs)

        self.assertNotEqual(
            tags_original["inputs_hash"],
            tags_different["inputs_hash"],
            "Hash should differ when input data changes",
        )

    def test_all_memory_override_keys_are_excluded(self):
        """Test that all defined memory override keys are properly excluded."""
        tags_base = get_tags(self.base_workflow_inputs)

        # Add all memory override keys
        inputs_with_all_overrides = self.base_workflow_inputs.copy()
        for key in MEMORY_OVERRIDE_KEYS:
            inputs_with_all_overrides[key] = 100

        tags_with_all = get_tags(inputs_with_all_overrides)

        self.assertEqual(
            tags_base["inputs_hash"],
            tags_with_all["inputs_hash"],
            "Hash should be identical even with all memory overrides set",
        )


class TestFilterByFamilies(unittest.TestCase):
    sample_info = pd.DataFrame.from_records(
        [
            ("fam-1", "sample-1a", ["movie1.bam"], None, None, "MALE", False, 0),
            ("fam-1", "sample-1b", ["movie2.bam"], None, None, "FEMALE", False, 0),
            ("fam-2", "sample-2a", ["movie3.bam"], None, None, "MALE", False, 0),
            ("fam-3", "sample-3a", ["movie4.bam"], None, None, "FEMALE", False, 0),
        ],
        columns=[
            "family_id",
            "sample_id",
            "hifi_reads",
            "father_id",
            "mother_id",
            "sex",
            "affected",
            "total_file_size_bytes",
        ],
    ).set_index("sample_id", drop=False)

    def test_filter_single_family(self):
        """Test filtering to a single family."""
        result = filter_by_families(self.sample_info.copy(), "fam-1")
        self.assertEqual(list(result["family_id"].unique()), ["fam-1"])
        self.assertEqual(len(result), 2)

    def test_filter_multiple_families(self):
        """Test filtering to multiple comma-separated families."""
        result = filter_by_families(self.sample_info.copy(), "fam-1,fam-3")
        self.assertEqual(sorted(result["family_id"].unique()), ["fam-1", "fam-3"])
        self.assertEqual(len(result), 3)

    def test_filter_with_whitespace(self):
        """Test that whitespace around family names is trimmed."""
        result = filter_by_families(self.sample_info.copy(), "fam-1 , fam-2")
        self.assertEqual(sorted(result["family_id"].unique()), ["fam-1", "fam-2"])

    def test_no_filter_returns_all(self):
        """Test that passing None returns all families."""
        result = filter_by_families(self.sample_info.copy(), None)
        self.assertEqual(len(result), len(self.sample_info))

    def test_missing_family_raises_error(self):
        """Test that specifying a non-existent family raises SystemExit."""
        with self.assertRaises(SystemExit):
            filter_by_families(self.sample_info.copy(), "fam-1,nonexistent-fam")

    def test_missing_family_error_with_single_family(self):
        """Test that specifying a single non-existent family raises SystemExit."""
        with self.assertRaises(SystemExit):
            filter_by_families(self.sample_info.copy(), "nonexistent-fam")

    def test_case_mismatch_suggests_correction(self):
        """Test that case-mismatched family IDs produce a suggestion."""
        # Create sample info with mixed-case family IDs
        mixed_case_sample_info = pd.DataFrame.from_records(
            [
                ("FAM-1", "sample-1a", ["movie1.bam"], None, None, "MALE", False, 0),
                ("Fam-Two", "sample-2a", ["movie2.bam"], None, None, "MALE", False, 0),
            ],
            columns=[
                "family_id",
                "sample_id",
                "hifi_reads",
                "father_id",
                "mother_id",
                "sex",
                "affected",
                "total_file_size_bytes",
            ],
        ).set_index("sample_id", drop=False)

        with self.assertLogs(logger, level="ERROR") as log_capture, self.assertRaises(
            SystemExit
        ):
            filter_by_families(mixed_case_sample_info.copy(), "fam-1")

        # Verify the suggestion appears in the error log
        log_output = "\n".join(log_capture.output)
        self.assertIn("did you mean", log_output.lower())
        self.assertIn("FAM-1", log_output)

    def test_case_mismatch_no_suggestion_for_truly_missing(self):
        """Test that truly missing families (no case match) don't get suggestions."""
        with self.assertLogs(logger, level="ERROR") as log_capture, self.assertRaises(
            SystemExit
        ):
            filter_by_families(self.sample_info.copy(), "totally-different")

        # Verify no suggestion appears
        log_output = "\n".join(log_capture.output)
        self.assertNotIn("did you mean", log_output.lower())


if __name__ == "__main__":
    unittest.main()


# __END__
