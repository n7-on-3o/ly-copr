%global tag v1.3.1
%global pkg_version 1.3.1

Name:           ly
Version:        %{pkg_version}
Release:        1%{?dist}
Summary:        A lightweight TUI display manager for Linux and BSD

License:        WTFPL
URL:            https://github.com/fairyglade/ly
Source0:        %{url}/archive/%{tag}/%{name}-%{tag}.tar.gz

BuildRequires:  zig
BuildRequires:  systemd-devel
BuildRequires:  pam-devel
BuildRequires:  libxcb-devel
Requires:       pam
Requires:       xauth
Requires:       systemd

%description
Ly is a lightweight TUI display manager. It relies on zig for its 
build system and provides a minimal, terminal-based login interface.

%prep
%autosetup -n %{name}-%{pkg_version}

%build
zig build -Doptimize=ReleaseSafe -Dinit_system=systemd

%install
DESTDIR=%{buildroot} zig build install --prefix /usr -Dinit_system=systemd

install -D -m 0644 res/config.ini %{buildroot}%{_sysconfdir}/ly/config.ini
install -D -m 0644 res/ly.service %{buildroot}%{_unitdir}/ly.service

%post
%systemd_post ly.service

%preun
%systemd_preun ly.service

%postun
%systemd_postun_with_restart ly.service

%files
%license LICENSE
%doc README.md
%{_bindir}/ly
%dir %{_sysconfdir}/ly
%config(noreplace) %{_sysconfdir}/ly/config.ini
%{_unitdir}/ly.service
%{_datadir}/ly/
