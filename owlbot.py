# Copyright 2018 Google LLC
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

"""This script is used to synthesize generated parts of this library."""

from pathlib import Path
import re
from typing import List, Optional

import synthtool as s
from synthtool import gcp
from synthtool.languages import python

common = gcp.CommonTemplates()

# This is a customized version of the s.get_staging_dirs() function from synthtool to
# cater for copying 2 different folders from googleapis-gen
# which are bigtable and bigtable/admin.
# Source https://github.com/googleapis/synthtool/blob/master/synthtool/transforms.py#L280
def get_staging_dirs(
    default_version: Optional[str] = None, sub_directory: Optional[str] = None
) -> List[Path]:
    """Returns the list of directories, one per version, copied from
    https://github.com/googleapis/googleapis-gen. Will return in lexical sorting
    order with the exception of the default_version which will be last (if specified).

    Args:
      default_version (str): the default version of the API. The directory for this version
        will be the last item in the returned list if specified.
      sub_directory (str): if a `sub_directory` is provided, only the directories within the
        specified `sub_directory` will be returned.

    Returns: the empty list if no file were copied.
    """

    staging = Path("owl-bot-staging")

    if sub_directory:
        staging /= sub_directory

    if staging.is_dir():
        # Collect the subdirectories of the staging directory.
        versions = [v.name for v in staging.iterdir() if v.is_dir()]
        # Reorder the versions so the default version always comes last.
        versions = [v for v in versions if v != default_version]
        versions.sort()
        if default_version is not None:
            versions += [default_version]
        dirs = [staging / v for v in versions]
        for dir in dirs:
            s._tracked_paths.add(dir)
        return dirs
    else:
        return []

# This library ships clients for two different APIs,
# BigTable and BigTable Admin
bigtable_default_version = "v2"
bigtable_admin_default_version = "v2"

for library in get_staging_dirs(bigtable_default_version, "bigtable"):
    s.move(library / "google/cloud/bigtable_v2", excludes=["**/gapic_version.py"])
    s.move(library / "tests")
    s.move(library / "scripts")

for library in get_staging_dirs(bigtable_admin_default_version, "bigtable_admin"):
    s.move(library / "google/cloud/bigtable_admin", excludes=["**/gapic_version.py"])
    s.move(library / "google/cloud/bigtable_admin_v2", excludes=["**/gapic_version.py"])
    s.move(library / "tests")
    s.move(library / "scripts")

s.remove_staging_dirs()

# ----------------------------------------------------------------------------
# Add templated files
# ----------------------------------------------------------------------------
templated_files = common.py_library(
    samples=True,  # set to True only if there are samples
    split_system_tests=True,
    microgenerator=True,
    cov_level=99,
    system_test_external_dependencies=[
        "pytest-asyncio==0.21.2",
    ],
)

s.move(templated_files, excludes=[".coveragerc", "README.rst", ".github/release-please.yml", "noxfile.py"])

# ----------------------------------------------------------------------------
# Customize gapics to include PooledBigtableGrpcAsyncIOTransport
# ----------------------------------------------------------------------------
def insert(file, before_line, insert_line, after_line, escape=None):
    target = before_line + "\n" + after_line
    if escape:
        for c in escape:
            target = target.replace(c, '\\' + c)
    replacement = before_line + "\n" + insert_line + "\n" + after_line
    s.replace(file, target, replacement)


insert(
    "google/cloud/bigtable_v2/services/bigtable/client.py",
    "from .transports.grpc_asyncio import BigtableGrpcAsyncIOTransport",
    "from .transports.pooled_grpc_asyncio import PooledBigtableGrpcAsyncIOTransport",
    "from .transports.rest import BigtableRestTransport"
)
insert(
    "google/cloud/bigtable_v2/services/bigtable/client.py",
    '    _transport_registry["grpc_asyncio"] = BigtableGrpcAsyncIOTransport',
    '    _transport_registry["pooled_grpc_asyncio"] = PooledBigtableGrpcAsyncIOTransport',
    '    _transport_registry["rest"] = BigtableRestTransport',
    escape='[]"'
)
insert(
    "google/cloud/bigtable_v2/services/bigtable/transports/__init__.py",
    '_transport_registry["grpc_asyncio"] = BigtableGrpcAsyncIOTransport',
    '_transport_registry["pooled_grpc_asyncio"] = PooledBigtableGrpcAsyncIOTransport',
    '_transport_registry["rest"] = BigtableRestTransport',
    escape='[]"'
)
insert(
    "google/cloud/bigtable_v2/services/bigtable/transports/__init__.py",
    "from .grpc_asyncio import BigtableGrpcAsyncIOTransport",
    "from .pooled_grpc_asyncio import PooledBigtableGrpcAsyncIOTransport",
    "from .rest import BigtableRestTransport"
)
insert(
    "google/cloud/bigtable_v2/services/bigtable/transports/__init__.py",
    '    "BigtableGrpcAsyncIOTransport",',
    '    "PooledBigtableGrpcAsyncIOTransport",',
    '    "BigtableRestTransport",',
    escape='"'
)

# ----------------------------------------------------------------------------
# Patch duplicate routing header: https://github.com/googleapis/gapic-generator-python/issues/2078
# ----------------------------------------------------------------------------
for file in ["client.py", "async_client.py"]:
    s.replace(
        f"google/cloud/bigtable_v2/services/bigtable/{file}",
        "metadata \= tuple\(metadata\) \+ \(",
        """metadata = tuple(metadata)
        if all(m[0] != gapic_v1.routing_header.ROUTING_METADATA_KEY for m in metadata):
            metadata += ("""
    )

# ----------------------------------------------------------------------------
# Samples templates
# ----------------------------------------------------------------------------

python.py_samples(skip_readmes=True)

s.replace(
    "samples/beam/noxfile.py",
    """INSTALL_LIBRARY_FROM_SOURCE \= os.environ.get\("INSTALL_LIBRARY_FROM_SOURCE", False\) in \(
    "True",
    "true",
\)""",
    """# todo(kolea2): temporary workaround to install pinned dep version
INSTALL_LIBRARY_FROM_SOURCE = False""")

s.shell.run(["nox", "-s", "blacken"], hide_output=False)
