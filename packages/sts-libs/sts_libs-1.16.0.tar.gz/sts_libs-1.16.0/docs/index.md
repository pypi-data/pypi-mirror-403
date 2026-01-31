# STS - Storage Testing

## Comprehensive Linux storage testing framework for Fedora, CentOS Stream, and RHEL

STS makes storage testing easy with pytest-based libraries, extensive fixtures, and TMT integration.
Whether you're testing iSCSI, LVM, multipath, or other storage technologies, STS provides the tools you need.

It consists of two main components:

- **📦 sts-libs**: Python testing library with storage-specific APIs and fixtures
- **🧪 Test Suite**: Collection of storage tests and TMT plans

Supported APIs and Tests:

- **iSCSI**: Initiator and target testing
- **LVM**: Volume management and thin provisioning
- **Multipath**: Device mapper multipath
- **NVMe**: NVMe device operations
- **Fibre Channel**: FC HBA testing
- **SCSI**: SCSI device testing
- **Stratis**: Stratis storage management
- **RDMA**: RDMA storage protocols
- **VDO**: Virtual Data Optimizer
- **And more**: Actively expanding support for additional storage technologies

## Quick Start

### 1. Install sts-libs

**From PyPI:**

```bash
pip install sts-libs
```

**From Fedora/EPEL:**

```bash
dnf copr enable packit/gitlab.com-rh-kernel-stqe-sts-releases
dnf install -y python3-sts-libs
```

### 2. Write Your First Test

For detailed guidance on writing and running tests, see [Writing and Running STS Tests](contributing/writing-tests.md).

## Requirements

- **Python**: 3.9 or later
- **Operating Systems**: Fedora, CentOS Stream 9+, RHEL 8+
- **Dependencies**: pytest, pytest-testinfra

## Project Architecture

```bash
sts/
├── sts_libs/              # Core Python library
│   ├── src/sts/           # Library source code  
│   │   ├── base.py        # Base device classes
│   │   ├── fixtures/      # Pytest fixtures
│   │   ├── utils/         # Utility modules
│   │   └── [storage]/     # Storage technology modules
│   └── tests/             # Library unit tests
├── tests/                 # Storage functional tests
├── plans/                 # TMT test plans (.fmf files)
├── docs/                  # Documentation source
└── pyproject.toml         # Project configuration
```

## Community & Support

- **Documentation**: [Complete docs](https://rh-kernel-stqe.gitlab.io/sts)
- **Source Code**: [GitLab Repository](https://gitlab.com/rh-kernel-stqe/sts)
- **Issues**: [Issue Tracker](https://gitlab.com/rh-kernel-stqe/sts/-/issues)
- **TMT Support**: [TMT Documentation](https://tmt.readthedocs.io/)
