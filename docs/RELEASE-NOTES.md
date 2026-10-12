# Linux preview 0.1.0

Native Qt Widgets edition, preserving the Windows Delphi source and ripDZL stability history through `93d0fb4`. This is a preview, with documented differences from the original Windows interaction model.

Downloads: x86_64 AppImage, Ubuntu 24.04/Debian 13 compatible `.deb`, Freedesktop 25.08 Flatpak, and portable tarball. AppImage/portable require glibc 2.39 or later and OpenGL/EGL. Void musl users should use Flatpak; musl was not tested. The project is not published on Flathub.

Validation: 48 pytest tests; packaged format/editing checks and startup on Ubuntu 24.04, Debian 13, Fedora 44, Arch and Void glibc containers; actual .deb installation in Ubuntu; AppImage extraction/startup; Flatpak installation and runtime checks. No full desktop validation on all distributions, physical printer test, real Wayland test or wallpaper portal test. Windows 11 remains unverified.

ClamAV final scan: 647 files, zero detections. Python dependency audit: no known vulnerabilities. These checks are not a malware-free or bug-free guarantee.

`SHA256SUMS` covers the release assets. `validation-logs.tar.gz` contains test logs and OCI image digests. `dependencies.cdx.json` contains the Python dependency inventory. `third-party-sources-0.1.0-x86_64.tar.gz` mirrors third-party sources; bundled notices describe dynamic-library replacement and licensing. One unavailable source mirror for permissively licensed Kerberos is documented in the source inventory; its complete notices are included.

Read [installation instructions](https://github.com/xXKuroiKenshiXx/mspaint-rewritten-linux#readme), [feature coverage](https://github.com/xXKuroiKenshiXx/mspaint-rewritten-linux/blob/main/docs/PORTING.md), [Windows review](https://github.com/xXKuroiKenshiXx/mspaint-rewritten-linux/blob/main/docs/UPSTREAM-REVIEW.md), and [validation report](https://github.com/xXKuroiKenshiXx/mspaint-rewritten-linux/blob/main/docs/VALIDATION.md).
