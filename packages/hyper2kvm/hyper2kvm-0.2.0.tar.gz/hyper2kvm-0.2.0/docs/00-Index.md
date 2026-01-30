# 📚 hyper2kvm Documentation Index

> **Complete migration toolkit: VMware/Hyper-V → KVM/QEMU** \
> Built for the Enterprise Linux ecosystem (Fedora, RHEL, CentOS Stream)

---

## 🎯 Quick Navigation

### 🚀 Getting Started
- **[📦 02-Installation](02-Installation.md)** - Install hyper2kvm on Fedora, RHEL, Ubuntu, macOS, Windows
- **[🚀 03-Quick-Start](03-Quick-Start.md)** - 5-minute quick start guide
- **[🖥️ 25-TUI-Quickstart](25-TUI-Quickstart.md)** - Interactive Terminal UI guide (NEW!)
- **[⚙️ 04-CLI-Reference](04-CLI-Reference.md)** - Complete command-line reference
- **[📝 05-YAML-Examples](05-YAML-Examples.md)** - Configuration file examples
- **[🤝 CONTRIBUTING](CONTRIBUTING.md)** - Contributing guidelines, GitLab mirror info

### 🏗️ Architecture & Design
- **[🏗️ 01-Architecture](01-Architecture.md)** - System architecture and design
- **[🚀 09-VMCraft](09-VMCraft.md)** - VMCraft Platform (307+ methods, AI/ML intelligence)
- **[🎨 07-vSphere-Design](07-vSphere-Design.md)** - vSphere integration (powered by hypersdk)

### 👨‍🍳 Recipes & Workflows
- **[📖 06-Cookbook](06-Cookbook.md)** - Common migration recipes
- **[⚙️ 14-Configuration-Injection-Guide](14-Configuration-Injection-Guide.md)** - Pre-boot VM customization
- **[☁️ 30-vSphere-Export](30-vSphere-Export.md)** - vSphere to KVM workflows

---

## 🪟 Windows Migration

Windows VMs require special handling due to driver dependencies and registry configuration.

| Guide | Description |
|-------|-------------|
| **[🪟 10-Windows-Guide](10-Windows-Guide.md)** | Complete Windows migration guide |
| **[🔄 11-Windows-Boot-Cycle](11-Windows-Boot-Cycle.md)** | Understanding Windows boot on KVM |
| **[🔧 12-Windows-Troubleshooting](12-Windows-Troubleshooting.md)** | Windows migration troubleshooting |
| **[🌐 13-Windows-Networking](13-Windows-Networking.md)** | Windows networking & VirtIO drivers |

### Windows Features
- ✅ **VirtIO driver injection** - Offline injection into offline Windows VMs
- ✅ **Registry modification** - BOOT_START service configuration
- ✅ **Two-phase boot** - Bootstrap with SATA, finalize with VirtIO
- ✅ **Windows 10 & 11** - Full support including UEFI, Secure Boot, TPM 2.0

---

## 🐧 Linux Distributions

Linux migrations are generally more straightforward, but each distro has specific requirements.

| Distribution | Guide | Key Features |
|--------------|-------|--------------|
| **🎩 RHEL / Fedora / CentOS** | [20-RHEL-10](20-RHEL-10.md) | Dracut, SELinux, NetworkManager |
| **🌟 VMware Photon OS** | [21-Photon-OS](21-Photon-OS.md) | systemd-networkd, RPM-based |
| **🐧 Ubuntu / Debian** | [22-Ubuntu-24.04](22-Ubuntu-24.04.md) | update-initramfs, netplan |
| **🦎 openSUSE / SUSE** | [23-SUSE](23-SUSE.md) | YaST, zypper, SUSE-specific |

### Linux Migration Features
- ✅ **Automatic initramfs regeneration** - Dracut or update-initramfs
- ✅ **UUID-based fstab** - Stable device references ([11-Fstab-Stabilization](11-Fstab-Stabilization.md))
- ✅ **Enhanced chroot for bootloader** - Reliable GRUB regeneration ([24-Enhanced-Chroot](24-Enhanced-Chroot.md))
- ✅ **GRUB root= fixing** - Kernel parameters
- ✅ **Network config migration** - NetworkManager, netplan, systemd-networkd

---

## ☁️ vSphere Integration

Migrate VMs directly from VMware vCenter/vSphere using **hypersdk** - VMware's modern, type-safe Python SDK for enterprise-grade API integration.

### Migration Paths

```mermaid
graph LR
    A[vSphere VM] --> B{Export Method}
    B -->|direct export| C[Direct Conversion]
    B -->|govc| D[Download VMDK]
    B -->|OVF Tool| E[Export OVA/OVF]
    C --> F[KVM QCOW2]
    D --> F
    E --> F
```bash

### Export Methods

| Method | Speed | Use Case | Guide |
|--------|-------|----------|-------|
| **direct export + VDDK** | ⚡ Fast | Production, large VMs | [30-vSphere-Export](30-vSphere-Export.md) |
| **govc download** | 🐢 Slow | Small VMs, testing | [07-vSphere-Design](07-vSphere-Design.md) |
| **OVF Tool** | ⚖️ Medium | OVA/OVF export | [30-vSphere-Export](30-vSphere-Export.md#ovftool) |

---

## 🔧 Configuration

### Configuration File Formats

hyper2kvm supports both YAML and JSON configuration files.

**YAML Example:**
```yaml
cmd: local
vmdk: /path/to/vm.vmdk
output_dir: /output
out_format: qcow2
compress: true
fstab_mode: stabilize-all
regen_initramfs: true
```bash

**JSON Example:**
```json
{
  "cmd": "local",
  "vmdk": "/path/to/vm.vmdk",
  "output_dir": "/output",
  "out_format": "qcow2",
  "compress": true
}
```bash

### Configuration Examples

See the `test-confs/` directory for 30+ production-ready configuration examples:
- Local VMDK conversions (01-05)
- vSphere downloads (10-11)
- Direct exports (20-24)
- OVFTool exports (30-31)
- LibVirt XML templates (60-66)

---

## ⚠️ Troubleshooting

### Common Issues

| Issue | Solution | Guide |
|-------|----------|-------|
| **Boot failure after conversion** | Check initramfs, fstab, GRUB | [90-Failure-Modes](90-Failure-Modes.md#boot-failures) |
| **Network not working** | Verify network config migration | [90-Failure-Modes](90-Failure-Modes.md#network-issues) |
| **Windows BSOD 0x7B** | VirtIO driver injection failed | [12-Windows-Troubleshooting](12-Windows-Troubleshooting.md) |
| **Permission denied errors** | Run with appropriate privileges | [90-Failure-Modes](90-Failure-Modes.md#permissions) |

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
hyper2kvm --config config.yaml --verbose 2 local
```bash

Generate detailed report:

```yaml
verbose: 2
log_file: /tmp/hyper2kvm.log
report: /tmp/hyper2kvm-report.md
```bash

---

## 📖 Complete Documentation

### Core Documentation
1. **[🏗️ Architecture](01-Architecture.md)** - System design, components, data flow
2. **[📦 Installation](02-Installation.md)** - Install on Fedora, RHEL, Ubuntu, Arch, macOS, Windows
3. **[🚀 Quick Start](03-Quick-Start.md)** - Get started in 5 minutes
4. **[⚙️ CLI Reference](04-CLI-Reference.md)** - Complete command-line documentation
5. **[📝 YAML Examples](05-YAML-Examples.md)** - Configuration file reference
6. **[👨‍🍳 Cookbook](06-Cookbook.md)** - Common migration recipes
7. **[🎨 vSphere Design](07-vSphere-Design.md)** - vSphere integration architecture
8. **[🐍 Library API](08-Library-API.md)** - Python library API documentation
9. **[🚀 VMCraft Platform](09-VMCraft.md)** - Advanced VM manipulation (307+ methods, AI/ML intelligence)

### Daemon Mode
10. **[⚙️ Daemon Mode](10-Daemon-Mode.md)** - Background processing basics
11. **[📊 Daemon Enhancements](11-Daemon-Enhancements.md)** - Enhanced daemon features
12. **[📖 Enhanced Daemon User Guide](12-Enhanced-Daemon-User-Guide.md)** - Complete daemon guide
13. **[🏗️ Integrated Daemon Architecture](13-Integrated-Daemon-Architecture.md)** - Daemon architecture

### Windows Documentation
10. **[🪟 Windows Guide](10-Windows-Guide.md)** - Complete Windows migration guide
11. **[🔄 Windows Boot Cycle](11-Windows-Boot-Cycle.md)** - Windows boot process on KVM
12. **[🔧 Windows Troubleshooting](12-Windows-Troubleshooting.md)** - Fix Windows migration issues
13. **[🌐 Windows Networking](13-Windows-Networking.md)** - Windows network drivers & configuration

### Linux Distribution Guides
20. **[🎩 RHEL 10](20-RHEL-10.md)** - Red Hat Enterprise Linux migration
21. **[🌟 Photon OS](21-Photon-OS.md)** - VMware Photon OS migration
22. **[🐧 Ubuntu 24.04](22-Ubuntu-24.04.md)** - Ubuntu/Debian migration
23. **[🦎 SUSE](23-SUSE.md)** - openSUSE/SUSE Linux migration
24. **[🔧 Enhanced Chroot](24-Enhanced-Chroot.md)** - Bootloader regeneration with bind mounts
25. **[🖥️ TUI Quickstart](25-TUI-Quickstart.md)** - Interactive Terminal User Interface guide (NEW!)

### Developer Guides
20. **[👨‍💻 TUI Development Guide](20-TUI-Development-Guide.md)** - Complete Textual TUI development reference (NEW!)
21. **[📋 Migration Quick Reference](21-Migration-Quick-Reference.md)** - One-page cheat sheet for common migrations (NEW!)

### Advanced Topics
11. **[🔧 Fstab Stabilization](11-Fstab-Stabilization.md)** - Converting device paths to stable UUIDs
14. **[⚙️ Configuration Injection](14-Configuration-Injection-Guide.md)** - Pre-boot network, user, service, and script injection
20. **[👨‍💻 TUI Development Guide](20-TUI-Development-Guide.md)** - Comprehensive guide for TUI development with Textual (NEW!)
21. **[📋 Migration Quick Reference](21-Migration-Quick-Reference.md)** - One-page quick reference for common migration scenarios (NEW!)
24. **[⚙️ Enhanced Chroot](24-Enhanced-Chroot.md)** - Reliable GRUB regeneration with pseudo-filesystems (NEW!)
30. **[☁️ vSphere Export](30-vSphere-Export.md)** - vSphere to KVM using direct export

### Troubleshooting & Support
90. **[⚠️ Failure Modes](90-Failure-Modes.md)** - Troubleshooting guide
95. **[🧪 Testing Guide](95-Testing-Guide.md)** - Testing infrastructure and best practices
97. **[🌐 Network Resilience](97-Network-Resilience.md)** - Network reliability and recovery
99. **[📦 Optional Dependencies](99-Optional-Dependencies.md)** - Optional packages and features

### Organized Documentation

**[📚 Reference Documentation](reference/)** - API references and technical specs
- [API Reference](reference/API-Reference.md) - Library API reference
- [Integration Contract](reference/Integration-Contract.md) - Integration requirements
- [Manifest Workflow](reference/Manifest-Workflow.md) - Artifact manifests

**[📖 User Guides](guides/)** - Specialized guides and workflows
- [Migration Playbooks](guides/MIGRATION-PLAYBOOKS.md) - Complete migration workflows
- [Batch Migration Guide](guides/Batch-Migration-Features-Guide.md) - Batch operations
- [Enhanced Features](guides/98-Enhanced-Features.md) - Advanced features
- [Security Best Practices](guides/SECURITY-BEST-PRACTICES.md) - Security guidelines
- [Troubleshooting](guides/TROUBLESHOOTING.md) - Common issues

**[🛠️ Development](development/)** - For contributors
- [Contributing](development/CONTRIBUTING.md) - Contribution guidelines
- [Building](development/BUILDING.md) - Build from source
- [Publishing](development/PUBLISHING.md) - Release process

**[📊 Project Information](project/)** - Status and roadmap
- [Project Status](project/PROJECT_STATUS.md) - Current development status
- [Ecosystem](project/ECOSYSTEM.md) - Related projects
- [Priority Features](project/Priority-1-Features.md) - Feature roadmap

---

## 🎓 Learning Path

### Beginner Path
1. Start with **[Quick Start](03-Quick-Start.md)**
2. Read **[Installation](02-Installation.md)**
3. Try a simple local conversion
4. Review **[Cookbook](06-Cookbook.md)** for common recipes

### Intermediate Path
1. Understand **[Architecture](01-Architecture.md)**
2. Explore **[YAML Examples](05-YAML-Examples.md)**
3. Try **[vSphere integration](07-vSphere-Design.md)**
4. Review OS-specific guides (RHEL, Ubuntu, Windows)

### Advanced Path
1. Deep dive into **[vSphere Export](30-vSphere-Export.md)**
2. Master **[Windows migrations](10-Windows-Guide.md)**
3. Handle **[Failure Modes](90-Failure-Modes.md)**
4. Contribute to the project!

---

## 🔗 External Resources

### Related Projects
- **[libguestfs](https://libguestfs.org/)** - Offline VM inspection and modification
- **[virt-v2v](https://libguestfs.org/virt-v2v.1.html)** - Reference VM conversion tool
- **[govc](https://github.com/vmware/govmomi/tree/master/govc)** - vSphere CLI
- **[KVM](https://www.linux-kvm.org/)** - Linux virtualization
- **[QEMU](https://www.qemu.org/)** - Machine emulator & virtualizer

### VMware Resources
- **[VDDK Documentation](https://developer.vmware.com/web/sdk/vddk)** - Virtual Disk Development Kit
- **[OVF Tool](https://developer.vmware.com/web/tool/ovf-tool)** - OVF/OVA import/export
- **[vSphere API](https://developer.vmware.com/apis/vsphere-automation/)** - vSphere automation

---

## 📊 Migration Decision Matrix

| Source Platform | Destination | Best Method | Complexity | Guide |
|----------------|-------------|-------------|------------|-------|
| vSphere → | KVM | direct export + VDDK | ⭐⭐⭐ | [30-vSphere-Export](30-vSphere-Export.md) |
| Local VMDK (Windows) → | KVM | local + VirtIO inject | ⭐⭐⭐⭐ | [10-Windows-Guide](10-Windows-Guide.md) |
| Local VMDK (Linux) → | KVM | local + offline fix | ⭐⭐ | [03-Quick-Start](03-Quick-Start.md) |
| Hyper-V VHD → | KVM | local (WIP) | ⭐⭐⭐ | N/A |
| OVA/OVF → | KVM | extract + local | ⭐⭐ | [06-Cookbook](06-Cookbook.md#ova) |

**Complexity Legend:**
- ⭐ - Easy
- ⭐⭐ - Medium
- ⭐⭐⭐ - Advanced
- ⭐⭐⭐⭐ - Expert

---

## 📝 Contributing

Found an issue or want to improve the documentation?

1. Fork the repository
2. Make your changes
3. Submit a pull request

See the main [README](../README.md) for contribution guidelines.

---

## 📧 Support

- **Issues:** [GitHub Issues](https://github.com/ssahani/hyper2kvm/issues)
- **Discussions:** [GitHub Discussions](https://github.com/ssahani/hyper2kvm/discussions)
- **Email:** ssahani@redhat.com

---

**Last Updated:** 2026-01-26 \
**Documentation Version:** 1.2 \
**hyper2kvm Version:** 0.1.0 \
**VMCraft Version:** v9.0 \
**Maintained by:** Susant Sahani <ssahani@redhat.com>

---

## 🏆 Featured Documentation

### Most Popular Guides
1. **[🚀 Quick Start](03-Quick-Start.md)** - Start here!
2. **[🚀 VMCraft Platform](09-VMCraft.md)** - Advanced VM manipulation (NEW!)
3. **[🪟 Windows Guide](10-Windows-Guide.md)** - Windows migrations
4. **[☁️ vSphere Export](30-vSphere-Export.md)** - vSphere integration
5. **[⚠️ Failure Modes](90-Failure-Modes.md)** - Troubleshooting

### Recently Updated
- **[24-Enhanced-Chroot](24-Enhanced-Chroot.md)** - NEW: Bootloader regeneration with bind mounts (2026-01-26)
- **[09-VMCraft](09-VMCraft.md)** - NEW: VMCraft v9.0 with AI/ML intelligence (307+ methods)
- **[14-Configuration-Injection-Guide](14-Configuration-Injection-Guide.md)** - NEW: Pre-boot VM customization
- **[95-Testing-Guide](95-Testing-Guide.md)** - NEW: Complete testing guide (100% coverage)
- **[README](../README.md)** - Updated with enhanced chroot and VMCraft v9.0 features

---

Happy migrating! 🚀
