%global tag v1.3.1
%global pkg_version 1.3.1
%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           ly
Version:        %{pkg_version}
Release:        2%{?dist}
Summary:        A lightweight TUI display manager for Linux and BSD

License:        WTFPL
URL:            https://github.com/fairyglade/ly
Source0:        %{url}/archive/%{tag}/%{name}-%{tag}.tar.gz
Source1:        ly.te

BuildRequires:  zig
BuildRequires:  systemd-devel
BuildRequires:  pam-devel
BuildRequires:  libxcb-devel
BuildRequires:  selinux-policy-devel
BuildRequires:  make
Requires:       pam
Requires:       xauth
Requires:       systemd
Requires(post): policycoreutils, selinux-policy-targeted

%description
Ly is a lightweight TUI display manager. This package includes a 
SELinux policy to allow Ly to manage TTY logins on Fedora.

%prep
%autosetup -n %{name}-%{pkg_version}
cp %{SOURCE1} .

%build
export ZIG_GLOBAL_CACHE_DIR=$(pwd)/.zig-cache
zig build -Doptimize=ReleaseSafe -Dinit_system=systemd --summary all
make -f %{_datadir}/selinux/devel/Makefile ly.pp

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_sysconfdir}/ly
mkdir -p %{buildroot}%{_sysconfdir}/pam.d
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_datadir}/ly
mkdir -p %{buildroot}%{_datadir}/selinux/packages

install -p -m 0755 zig-out/bin/ly %{buildroot}%{_bindir}/ly

install -p -m 0644 res/config.ini %{buildroot}%{_sysconfdir}/ly/config.ini
sed -i -e 's|\$PREFIX_DIRECTORY|%{_prefix}|g' \
       -e 's|\$CONFIG_DIRECTORY|%{_sysconfdir}|g' \
       -e 's|\$PLATFORM_SHUTDOWN_ARG||g' \
       %{buildroot}%{_sysconfdir}/ly/config.ini

install -p -m 0755 res/setup.sh %{buildroot}%{_sysconfdir}/ly/setup.sh

cp res/ly@.service %{buildroot}%{_unitdir}/ly@.service
sed -i -e 's|\$PREFIX_DIRECTORY/bin/\$EXECUTABLE_NAME|%{_bindir}/ly|g' \
       -e 's|@BIN_DIR@|%{_bindir}|g' \
       -e 's|@PACKAGE_NAME@|ly|g' \
       %{buildroot}%{_unitdir}/ly@.service

cp -r res/lang %{buildroot}%{_datadir}/ly/
install -p -m 0644 ly.pp %{buildroot}%{_datadir}/selinux/packages/ly.pp

mkdir -p %{buildroot}%{_sysconfdir}/pam.d
cat << 'EOF' > %{buildroot}%{_sysconfdir}/pam.d/ly
#%PAM-1.0
auth       include      system-auth
account    include      system-auth
password   include      system-auth
session    required     pam_selinux.so close
session    include      system-auth
session    required     pam_loginuid.so
session    required     pam_selinux.so open
session    optional     pam_systemd.so
session    required     pam_env.so
EOF

cat << 'EOF' > %{buildroot}%{_sysconfdir}/pam.d/ly-autologin
#%PAM-1.0
auth       required     pam_permit.so
account    include      system-auth
password   include      system-auth
session    include      system-auth
session    optional     pam_systemd.so
EOF

%post
%systemd_post ly@.service
/usr/sbin/semodule -i %{_datadir}/selinux/packages/ly.pp &> /dev/null || :
/usr/sbin/semanage fcontext -a -t xdm_exec_t '%{_bindir}/ly' 2>/dev/null || :
/usr/sbin/semanage fcontext -a -t xdm_rw_etc_t '%{_sysconfdir}/ly(/.*)?' 2>/dev/null || :
/usr/sbin/restorecon -R %{_bindir}/ly %{_sysconfdir}/ly || :

%preun
%systemd_preun ly@.service

%postun
%systemd_postun_with_restart ly@.service
if [ $1 -eq 0 ]; then
    /usr/sbin/semodule -r ly &> /dev/null || :
    /usr/sbin/semanage fcontext -d -t xdm_exec_t '%{_bindir}/ly' 2>/dev/null || :
    /usr/sbin/semanage fcontext -d -t xdm_rw_etc_t '%{_sysconfdir}/ly(/.*)?' 2>/dev/null || :
fi

%files
%license license.md
%doc readme.md
%{_bindir}/ly
%dir %{_sysconfdir}/ly
%config(noreplace) %{_sysconfdir}/ly/config.ini
%config(noreplace) %{_sysconfdir}/ly/setup.sh
%{_unitdir}/ly@.service
%{_datadir}/ly/
%{_datadir}/selinux/packages/ly.pp
%config(noreplace) %{_sysconfdir}/pam.d/ly
%config(noreplace) %{_sysconfdir}/pam.d/ly-autologin

%changelog
* Sun Feb 01 2026 User <user@example.com> - 1.3.1-2
- Fixed Sway session detection via waylandsessions path
- Fixed config.ini substring replacements for $PREFIX_DIRECTORY
- Fixed service file placeholder resolution
- Added missing setup.sh to installation
