# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path


class TestExecuteQueryProtos:
    def test_request_results_from_json(self):
        from google.cloud.bigtable_v2.types.bigtable import ExecuteQueryResponse

        dir = Path(__file__).parent.resolve()
        response = ExecuteQueryResponse.from_json(
            (dir / "execute-query-response-example-1.json").read_text()
        )
        assert "metadata" not in response
        assert "results" in response

    def test_request_metadata_from_json(self):
        from google.cloud.bigtable_v2.types.bigtable import ExecuteQueryResponse

        dir = Path(__file__).parent.resolve()
        response = ExecuteQueryResponse.from_json(
            (dir / "execute-query-response-example-2.json").read_text()
        )
        assert "metadata" in response
        assert "results" not in response

    def test_proto_rows_from_json(self):
        from google.cloud.bigtable_v2.types.data import ProtoRows

        dir = Path(__file__).parent.resolve()
        rows = ProtoRows.from_json(
            (dir / "execute-query-proto-rows-example-1.json").read_text()
        )
        assert len(rows.values) == 10
        assert len(rows.values[0].raw_value) > 0
        assert rows.values[1].raw_timestamp_micros == 12345
        assert len(rows.values[2].bytes_value) > 0
        assert rows.values[3].string_value == "deadbeef"
        assert rows.values[4].int_value == 123
        assert rows.values[5].bool_value
        assert rows.values[6].float_value == 12.31e-3
        assert rows.values[7].date_value.day == 0
        assert rows.values[7].date_value.month == 11
        assert rows.values[7].date_value.year == 1021
        assert (
            rows.values[8].timestamp_value.strftime("%Y-%m-%dT%H:%M:%S")
            == "2020-05-01T23:31:12"
        )
        assert rows.values[8].timestamp_value.nanosecond == 0
        assert len(rows.values[9].array_value.values) == 2
        assert rows.values[9].array_value.values[0].int_value == 123
        assert rows.values[9].array_value.values[1].int_value == 412
