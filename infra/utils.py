# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for OSS-Fuzz infrastructure."""

import os
import re
import sys

import helper

ALLOWED_FUZZ_TARGET_EXTENSIONS = ['', '.exe']
FUZZ_TARGET_SEARCH_STRING = 'LLVMFuzzerTestOneInput'
VALID_TARGET_NAME = re.compile(r'^[a-zA-Z0-9_-]+$')


def is_fuzz_target_local(file_path, file_handle=None):
  """Returns whether |file_path| is a fuzz target binary (local path)."""
  filename, file_extension = os.path.splitext(os.path.basename(file_path))
  if not VALID_TARGET_NAME.match(filename):
    # Check fuzz target has a valid name (without any special chars).
    return False

  if file_extension not in ALLOWED_FUZZ_TARGET_EXTENSIONS:
    # Ignore files with disallowed extensions (to prevent opening e.g. .zips).
    return False

  if not file_handle and not os.path.exists(file_path):
    # Ignore non-existant files for cases when we don't have a file handle.
    return False

  if filename.endswith('_fuzzer'):
    return True

  # TODO(aarya): Remove this optimization if it does not show up significant
  # savings in profiling results.
  fuzz_target_name_regex = environment.get_value('FUZZER_NAME_REGEX')
  if fuzz_target_name_regex:
    return bool(re.match(fuzz_target_name_regex, filename))

  if os.path.exists(file_path) and not stat.S_ISREG(os.stat(file_path).st_mode):
    # Don't read special files (eg: /dev/urandom).
    logs.log_warn('Tried to read from non-regular file: %s.' % file_path)
    return False

  # Use already provided file handle or open the file.
  local_file_handle = file_handle or open(file_path, 'rb')

  # TODO(metzman): Bound this call so we don't read forever if something went
  # wrong.
  result = utils.search_string_in_file(FUZZ_TARGET_SEARCH_STRING,
                                       local_file_handle)

  if not file_handle:
    # If this local file handle is owned by our function, close it now.
    # Otherwise, it is caller's responsibility.
    local_file_handle.close()

  return result


def get_project_fuzz_targets(project_name):
  """Get list of fuzz targets for a specific OSS-Fuzz project.

  Args:
    project_name: The name of the OSS-Fuzz in question.

  Returns:
    A list of paths to fuzzers or an empty list if None.
  """

  if not helper.check_project_exists(project_name):
    print('Error: Project {0} does not exist in OSS-Fuzz.'.format(project_name), file=sys.stderr)
    return []
  fuzz_target_paths = []
  path = os.path.join(helper.BUILD_DIR, 'out', project_name)

  for root, _, files in os.walk(path):
    for filename in files:
      file_path = os.path.join(root, filename)
      if is_fuzz_target_local(file_path):
        fuzz_target_paths.append(file_path)

  return fuzz_target_paths
