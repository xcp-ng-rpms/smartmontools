%global package_speccommit edaa4d38205d4ad8fa3e6e74090f109e185b437c
%global usver 7.4
%global xsver 2
%global xsrel %{xsver}%{?xscount}%{?xshash}
# xsrel setup is automatic, see the Packaging Guidelines for details:
# https://info.citrite.net/display/xenserver/RPM+Packaging+Guidelines

# defining macros needed by SELinux
%global with_selinux 0
%global selinuxtype targeted
%global moduletype contrib
%global modulename smartmon

Summary:	Tools for monitoring SMART capable hard disks
Name:		smartmontools
Version:	7.4
Release:        %{?xsrel}%{?dist}
# RHEL7/XS8 smartmontools use epoch 1. Epoch 1 is required to update it.
%if 0%{?xenserver} < 9
Epoch: 1
%endif
License:	GPL-2.0-or-later
URL:		http://smartmontools.sourceforge.net/
Source0: smartmontools-7.4.tar.gz
Source2: smartmontools.sysconf
Source4: smartdnotify
Patch0: smartmontools-5.38-defaultconf.patch
#semi-automatic update of drivedb.h
%global		UrlSource5	https://sourceforge.net/p/smartmontools/code/HEAD/tree/trunk/smartmontools/drivedb.h?format=raw
Source5: drivedb.h
Source6: smartmon.te
Source7: smartmon.if
Source8: smartmon.fc

BuildRequires: make
BuildRequires:	gcc-c++ readline-devel ncurses-devel automake util-linux groff gettext
%if 0%{?xsrel:1} && 0%{?xenserver} < 9
BuildRequires:  devtoolset-11-gcc-c++
%endif
BuildRequires:	libselinux-devel libcap-ng-devel
BuildRequires:	systemd systemd-devel
%if 0%{?with_selinux}
# This ensures that the *-selinux package and all it’s dependencies are not pulled
# into containers and other systems that do not use SELinux
Requires:	(%{name}-selinux if selinux-policy-%{selinuxtype})
%endif

%description
The smartmontools package contains two utility programs (smartctl
and smartd) to control and monitor storage systems using the Self-
Monitoring, Analysis and Reporting Technology System (SMART) built
into most modern ATA and SCSI hard disks. In many cases, these
utilities will provide advanced warning of disk degradation and
failure.

%if 0%{?with_selinux}
%package selinux
Summary:	SELinux policies for smartmontools
BuildArch:	noarch
Requires:	selinux-policy-%{selinuxtype}
Requires(post):	selinux-policy-%{selinuxtype}
BuildRequires:	selinux-policy-devel
%{?selinux_requires}

%description selinux
Custom SELinux policy module for smartmontools
%endif

%prep
%autosetup -p1
cp %{SOURCE5} .
%if 0%{?with_selinux}
mkdir selinux
cp -p %{SOURCE6} %{SOURCE7} %{SOURCE8} selinux/
%endif

%build
%if 0%{?xsrel:1} && 0%{?xenserver} < 9
source /opt/rh/devtoolset-11/enable
%endif
autoreconf -i
%configure --without-selinux --with-libcap-ng=yes --with-libsystemd --with-systemdsystemunitdir=%{_unitdir} --sysconfdir=%{_sysconfdir}/%{name}/ --with-systemdenvfile=%{_sysconfdir}/sysconfig/%{name}

# update SOURCE5 on maintainer's machine prior commiting, there's no internet connection on builders
%make_build update-smart-drivedb
./update-smart-drivedb -s - -u sf drivedb.h ||:
cp drivedb.h ../drivedb.h ||:

%make_build CXXFLAGS="$RPM_OPT_FLAGS -fpie" LDFLAGS="-pie -Wl,-z,relro,-z,now"

%if 0%{?with_selinux}
make -f %{_datadir}/selinux/devel/Makefile %{modulename}.pp
bzip2 -9 %{modulename}.pp
%endif

%if 0%{?xsrel:1}

# XenServer:
# ----------
# Fix the startup of the systemd service for smartd on XS9:
#
# The new systemd unit configues smartd to not run in VMs using
# ConditionVirtualization=no, which the systemd in XS9 Dom0 honors.
#
# In Dom0, continue to start the smartd service in order to log disk warnings
# and to call disk warning handler scripts that may have been added/installed:
#
sed -i 's/ConditionVirtualization=/# &/' smartd.service

# XenServer:
# ----------
# smartd.conf is installed as config(noreplace) /etc/smartmontools/smartd.conf
# This means the config file of existing XS8/XS9 installs is not replaced by
# rpm updates.
#
# But for new installations, the new file would be active:
# It uses "-m root -M exec /usr/libexec/smartmontools/smartdnotify",
# which overrides the built-in config to run the default warning notification
# script of smartd, /etc/smartmontools/smartd_warning.sh.
# It defaults to run the scripts in /etc/smartmontools/smartd_warning.d.
#
# Server customers could rely on it continue to handle disk warnings, and
# this default can also be used to add handling of notifications by default.
#
# Thus, continue to use the existing default warning notification script instead
# by removing the new override in the new default/example smartd.conf file:
#
# These new options to run the  smartdnotify script would instead try to send
# local mail to root and tries to notify local user using the "wall" tool,
# which is not helpful for XS8/XS9 at all:
#
sed -i 's|-m root -M exec /usr/libexec/smartmontools/smartdnotify ||' smartd.conf
%endif


%install
%if 0%{?xsrel:1} && 0%{?xenserver} < 9
source /opt/rh/devtoolset-11/enable
%endif
%make_install

rm -f examplescripts/Makefile*
chmod a-x -R examplescripts/*
install -D -p -m 644 %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/smartmontools
install -D -p -m 755 %{SOURCE4} $RPM_BUILD_ROOT/%{_libexecdir}/%{name}/smartdnotify
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/%{name}/smartd_warning.d
rm -rf $RPM_BUILD_ROOT/etc/{rc.d,init.d}
rm -rf $RPM_BUILD_ROOT%{_docdir}/%{name}
mkdir -p $RPM_BUILD_ROOT%{_sharedstatedir}/%{name}

%if 0%{?with_selinux}
install -D -m 0644 %{modulename}.pp.bz2 %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/%{modulename}.pp.bz2
install -D -p -m 0644 selinux/%{modulename}.if %{buildroot}%{_datadir}/selinux/devel/include/distributed/%{modulename}.if
%endif

%if 0%{?with_selinux}
# SELinux contexts are saved so that only affected files can be
# relabeled after the policy module installation
%pre selinux
%selinux_relabel_pre -s %{selinuxtype}

%post selinux
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/%{modulename}.pp.bz2
%selinux_relabel_post -s %{selinuxtype}

if [ "$1" -le "1" ]; then # First install
   # the daemon needs to be restarted for the custom label to be applied
   %systemd_postun_with_restart smartd.service
fi

%postun selinux
if [ $1 -eq 0 ]; then
    %selinux_modules_uninstall -s %{selinuxtype} %{modulename}
    %selinux_relabel_post -s %{selinuxtype}
    # the daemon needs to be restarted for the custom label to be removed
    %systemd_postun_with_restart smartd.service
fi
%endif

%preun
%systemd_preun smartd.service

%post
%systemd_post smartd.service

%postun
%systemd_postun_with_restart smartd.service

%files
%doc AUTHORS ChangeLog INSTALL NEWS README
%doc TODO examplescripts smartd.conf
%license COPYING
%dir %{_sysconfdir}/%name
%dir %{_sysconfdir}/%name/smartd_warning.d
%config(noreplace) %{_sysconfdir}/%{name}/smartd.conf
%config(noreplace) %{_sysconfdir}/%{name}/smartd_warning.sh
%config(noreplace) %{_sysconfdir}/sysconfig/smartmontools
%{_unitdir}/smartd.service
%{_sbindir}/smartd
%{_sbindir}/update-smart-drivedb
%{_sbindir}/smartctl
%{_mandir}/man?/smart*.*
%{_mandir}/man?/update-smart*.*
%{_libexecdir}/%{name}
%{_datadir}/%{name}
%{_sharedstatedir}/%{name}

%if 0%{?with_selinux}
%files selinux
%license COPYING
%{_datadir}/selinux/packages/%{selinuxtype}/%{modulename}.pp.*
%{_datadir}/selinux/devel/include/distributed/%{modulename}.if
%ghost %verify(not md5 size mode mtime) %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/%{modulename}
%endif

%changelog
* Wed Jul 31 2024 Bernhard Kaindl <bernhard.kaindl@citrix.com> - 7.4-2
- CP-50530: Update smartmontools to support exporting S.M.A.R.T. metrics as JSON
* Mon Sep 04 2023 Lin Liu <lin.liu@citrix.com> - 7.4-1
- First imported release

