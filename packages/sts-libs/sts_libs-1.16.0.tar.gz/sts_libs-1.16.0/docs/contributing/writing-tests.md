# Writing and Running STS Tests

This guide explains how to write test cases using the STS framework and run them with TMT and Testing-Farm.

## Writing a Test Case

STS test cases follow pytest conventions with additional storage-specific fixtures and utilities.
Here's a complete example based on `tests/examples/basic-example/`:

### 1. Create the Test File

We create a Python file to define the actual test logic, utilizing sts-libs fixtures (like loop_devices) to automate
storage setup. Clone the repo and create a Python test file (e.g., `test_my_storage.py`) in the
`tests/examples/example` directory:

```python
# Copyright: Contributors to the sts project
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import pytest
from sts.fio.fio import FIO
from sts.utils.cmdline import run

@pytest.mark.parametrize('loop_devices', [1], indirect=True)
def test_example(loop_devices: list[str]) -> None:
    """Test example using sts-libs features.

    This test demonstrates:
    1. Using loop_devices fixture to get a test device
    2. Verifying device exists using run()
    3. Running I/O test using FIO
    """
    device = loop_devices[0]
    logging.info(f'Starting test with device {device}')

    # Verify device exists
    result = run(f'lsblk {device}')
    assert result.succeeded, 'lsblk command failed'
    assert device.split('/')[-1] in result.stdout

    # Run I/O test
    fio = FIO(filename=device)
    assert fio.run()
```

### 2. Create the FMF Metadata File

This file is the bridge for TMT. It allows the framework to discover the test and defines attributes like component
and tier that don't exist in the Python code. Create a `main.fmf` file to define test metadata in dir
tests/examples/example:

```yaml
summary: My storage test example
description: |
  Detailed description of what the test validates.
  Include test setup, test steps, expected result and cleanup.
framework: shell
test: pytest test_my_storage.py
# or enable pytest debug which is helpful for error analysis:
# test: pytest -o log_cli_level='debug' -vrA test_my_storage.py
component:
  - kernel
tag:
  - my-example
  - storage
tier: 1
duration: 10m
```

### 3. Create a TMT Test Plan

While Step 2 describes the test, the Plan defines the environment and selection logic. For example, the filter
section uses the tier or component tags defined in Step 2 to determine which tests to include in a specific run.
Create a test plan file (e.g., `example-plan.fmf`) that defines how tests are discovered and executed. Save it under
`plans/examples/`:

```yaml
summary: My storage test plan
description: Plan for running my storage tests
discover:
  - how: fmf
    filter:
      - tag:my-example
      - tag:storage
provision:
  how: virtual
  image: fedora
execute:
  how: tmt
```

#### Alternative Plan Configurations

**For container testing:**

```yaml
summary: Container-based test plan
discover:
  - how: fmf
    filter: tag:my-example
provision:
  how: container
  image: centos:stream10
execute:
  how: tmt
```

**For specific hardware requirements:**

```yaml
summary: Hardware-specific test plan
discover:
  - how: fmf
    filter: tag:storage
provision:
  how: beaker
  image: RHEL-9%
  hardware:
    disk:
      - size: '>= 10 GB'
    memory: '>= 4 GB'
execute:
  how: tmt
```

## Running Tests Locally

### Using TMT (Recommended)

For common TMT usage, see:

```bash
tldr tmt
```

Full documentation for tmt is available at [tmt.readthedocs.io](https://tmt.readthedocs.io/en/stable/).
tmt Matrix room is available at [#tmt:fedora.im](https://matrix.to/#/#tmt:fedora.im).

**Run using your test plan:**

```bash
# Run the test plan
TMT_SHOW_TRACEBACK=full tmt run plan --name plans/examples/example-plan -dddvvv
```

### Using Pytest Directly

SSH into the SUT, then:

```bash
# Install dependencies first
dnf install -y python3-pip
pip install sts-libs

# Run tests directly
pytest test_my_storage.py -v
pytest -o log_cli_level='debug' -vrA test_my_storage.py
```

## Running Tests with Testing-Farm

Testing Farm is a reliable and scalable Testing System as a Service.

### Basic Testing-Farm Commands

**Submit a test job:**

```bash
testing-farm request \
  --context distro=rhel-9 \
  --compose RHEL-9.7.0-Nightly \
  --git-url https://gitlab.com/rh-kernel-stqe/sts \
  --plan /plans/examples/example-plan \
  --arch x86_64,aarch64
```

**Run tests from your branch:**

```bash
testing-farm request \
  --compose Fedora-Rawhide \
  --git-url https://gitlab.com/your-username/sts \
  --git-ref your-feature-branch \
  --plan /plans/your-test-plan
```

**Run with specific hardware pool:**

```bash
testing-farm request \
  --context distro=rhel-9 \
  --compose RHEL-9.7.0-Nightly \
  --pool beaker-kernel-qe-storage \
  --git-url https://gitlab.com/rh-kernel-stqe/sts \
  --plan /plans/iscsi/offload/qedi
```

## Good Practices

### Test Category

- **sanity**: Quick verification tests
- **functional**: Core feature testing
- **integration**: Cross-component tests
- **performance**: Benchmarking tests
- **bugs**: Bug reproduction tests
- **security**: Security-focused tests
- **stress** Load/endurance tests

### Test Structure

- **Use descriptive names**: Test functions should clearly indicate what they test
- **Include docstrings**: Explain the test purpose and steps
- **Use appropriate fixtures**: Leverage STS fixtures for common storage setups
- **Add proper error handling**: Validate intermediate steps and provide clear failure messages

### FMF Metadata

Include:

- **Summary**: Short summary of the test
- **Description**: Provide detailed test description
- **Appropriate duration**: Set realistic test duration estimates
- **Proper components**: Tag tests with relevant storage components
- **Proper tags**: Use tags to categorize tests
- **Proper tiers**: Assign tests to appropriate tiers

### Execution

- **Start local**: Test locally with `tmt run` before submitting to Testing-Farm
- **Use verbose mode**: Add `TMT_SHOW_TRACEBACK=full` and `-dddvvv` for debugging issues
- **Check logs**: Review TMT and test logs for failures

## Common Patterns

### Using STS Fixtures

STS provides many pytest fixtures for common storage scenarios, e.g.,

```python
# Loop devices
@pytest.mark.parametrize('loop_devices', [2], indirect=True)
def test_with_loop_devices(loop_devices):
    device1, device2 = loop_devices
    # Test with multiple loop devices

# LVM setup with loop devices
@pytest.mark.parametrize('loop_devices', [1], indirect=True)
def test_with_lvm(setup_loopdev_vg):
    vg_name = setup_loopdev_vg
    # Test LVM operations with volume group

# iSCSI target setup
@pytest.mark.parametrize('iscsi_target_setup',
                         [{'t_iqn': 'iqn.test', 'n_luns': 1}],
                         indirect=True)
def test_iscsi_target(iscsi_target_setup):
    # Test iSCSI target functionality
```

## Troubleshooting

### Common Issues

**Test discovery fails:**

- Check FMF metadata syntax
- Verify test tags match plan filters
- Ensure test files are in correct locations

**Provisioning fails:**

- Verify image names and availability
- Check hardware requirements
- Review network connectivity

**Test execution fails:**

- Check test dependencies
- Review log files for detailed errors
- Verify environment setup

### Debug Commands

```bash
# Check fmf syntax
tmt lint

# Enable detailed traceback and run with maximum verbosity
TMT_SHOW_TRACEBACK=full tmt run ... -dddvvv

# Enable interactive shell session when test failure or error
tmt run login --when fail --when error plans --name /plans/examples/example-plan

# Run until a specific stage
tmt run --until discover plans --name /plans/examples/example-plan

# Show what would be executed without running
tmt run --dry

# Show discovered tests
tmt run discover --dry

# Run steps individually for debugging
tmt run discover
tmt run provision -h container
tmt run prepare
tmt run execute

# Check tests discovery
tmt tests ls
tmt tests show

# Check plans discovery
tmt plans ls
tmt plans show

# Clean workdirs, guests and images
tmt clean
```
