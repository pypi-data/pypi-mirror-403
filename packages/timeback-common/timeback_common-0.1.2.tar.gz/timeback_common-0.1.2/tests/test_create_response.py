"""Tests for CreateResponse and BulkCreateResponse models."""

from timeback_common import BulkCreateResponse, CreateResponse


class TestCreateResponse:
    """Tests for CreateResponse model (single-resource creates)."""

    def test_single_sourced_id_pair_object(self):
        """Single object should be preserved as-is."""
        response = CreateResponse.model_validate(
            {
                "sourcedIdPairs": {
                    "suppliedSourcedId": "supplied-1",
                    "allocatedSourcedId": "allocated-1",
                }
            }
        )
        assert response.sourced_id_pairs.supplied_sourced_id == "supplied-1"
        assert response.sourced_id_pairs.allocated_sourced_id == "allocated-1"

    def test_list_with_one_element_extracts_first(self):
        """List with one element should extract the first (API quirk)."""
        response = CreateResponse.model_validate(
            {
                "sourcedIdPairs": [
                    {
                        "suppliedSourcedId": "supplied-1",
                        "allocatedSourcedId": "allocated-1",
                    }
                ]
            }
        )
        assert response.sourced_id_pairs.supplied_sourced_id == "supplied-1"
        assert response.sourced_id_pairs.allocated_sourced_id == "allocated-1"

    def test_empty_list_returns_empty_pair(self):
        """Empty list should result in empty pair (edge case)."""
        response = CreateResponse.model_validate({"sourcedIdPairs": []})
        assert response.sourced_id_pairs.supplied_sourced_id is None
        assert response.sourced_id_pairs.allocated_sourced_id is None


class TestBulkCreateResponse:
    """Tests for BulkCreateResponse model (bulk creates)."""

    def test_list_of_sourced_id_pairs_preserved(self):
        """All pairs in a list should be preserved."""
        response = BulkCreateResponse.model_validate(
            {
                "sourcedIdPairs": [
                    {
                        "suppliedSourcedId": "supplied-1",
                        "allocatedSourcedId": "allocated-1",
                    },
                    {
                        "suppliedSourcedId": "supplied-2",
                        "allocatedSourcedId": "allocated-2",
                    },
                    {
                        "suppliedSourcedId": "supplied-3",
                        "allocatedSourcedId": "allocated-3",
                    },
                ]
            }
        )
        assert len(response.sourced_id_pairs) == 3
        assert response.sourced_id_pairs[0].supplied_sourced_id == "supplied-1"
        assert response.sourced_id_pairs[1].supplied_sourced_id == "supplied-2"
        assert response.sourced_id_pairs[2].supplied_sourced_id == "supplied-3"

    def test_single_object_wrapped_in_list(self):
        """Single object should be normalized to a list."""
        response = BulkCreateResponse.model_validate(
            {
                "sourcedIdPairs": {
                    "suppliedSourcedId": "supplied-1",
                    "allocatedSourcedId": "allocated-1",
                }
            }
        )
        assert len(response.sourced_id_pairs) == 1
        assert response.sourced_id_pairs[0].supplied_sourced_id == "supplied-1"

    def test_empty_list(self):
        """Empty list should result in empty pairs."""
        response = BulkCreateResponse.model_validate({"sourcedIdPairs": []})
        assert response.sourced_id_pairs == []
