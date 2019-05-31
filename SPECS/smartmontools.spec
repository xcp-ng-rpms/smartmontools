Summary:	Tools for monitoring SMART capable hard disks
Name:		smartmontools
Version:	6.5
Release:	1.1%{?dist}
Epoch:		1
Group:		System Environment/Base
License:	GPLv2+
URL:		https://www.smartmontools.org/
Source0:	https://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz
Source2:	smartmontools.sysconf
Source4:	smartdnotify

#fedora/rhel specific
Patch1:		smartmontools-5.38-defaultconf.patch
Patch2:         smartmontools-6.2-up2datedrivedb.patch

BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
Requires:	fileutils mailx
#new rpm does not handle this (yet?)
#Requires(triggerun):	systemd-units
Requires(post):		systemd-units
Requires(preun):	systemd-units
Requires(postun):	systemd-units
BuildRequires:	readline-devel ncurses-devel automake util-linux groff gettext
BuildRequires:	libselinux-devel libcap-ng-devel
BuildRequires:	systemd-units

%description
The smartmontools package contains two utility programs (smartctl
and smartd) to control and monitor storage systems using the Self-
Monitoring, Analysis and Reporting Technology system (SMART) built
into most modern ATA/SATA, SCSI/SAS and NVMe disks. In many cases,
these utilities will provide advanced warning of disk degradation
and failure.

%prep
%setup -q 
%patch1 -p1 -b .defaultconf
%patch2 -p1 -b .up2datedrivedb

# fix encoding
for fe in AUTHORS ChangeLog
do
  iconv -f iso-8859-1 -t utf-8 <$fe >$fe.new
  touch -r $fe $fe.new
  mv -f $fe.new $fe
done

%build
autoreconf -i
%configure --with-selinux --with-libcap-ng=yes --with-systemdsystemunitdir=%{_unitdir} --sysconfdir=%{_sysconfdir}/%name/
%ifarch sparc64
make CXXFLAGS="$RPM_OPT_FLAGS -fPIE" LDFLAGS="-pie -Wl,-z,relro,-z,now"
%else
make CXXFLAGS="$RPM_OPT_FLAGS -fpie" LDFLAGS="-pie -Wl,-z,relro,-z,now"
%endif

sed -i 's|/etc/smartmontools/sysconfig|/etc/sysconfig|g' smartd.service

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install

rm -f examplescripts/Makefile*
chmod a-x -R examplescripts/*
install -D -p -m 644 %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/smartmontools
install -D -p -m 755 %{SOURCE4} $RPM_BUILD_ROOT/%{_libexecdir}/%{name}/smartdnotify
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/%{name}/smartd_warning.d
rm -rf $RPM_BUILD_ROOT/etc/{rc.d,init.d}
rm -rf $RPM_BUILD_ROOT/%{_docdir}/%{name}
# symlink to /var/log/smartd so that data is stored in the logs partition
mkdir -p %{buildroot}%{_sharedstatedir}
mkdir -p %{buildroot}/var/log/smartd
ln -s /var/log/smartd %{buildroot}%{_sharedstatedir}/smartmontools

%clean
rm -rf $RPM_BUILD_ROOT

%preun
%systemd_preun smartd.service

%pre
if [ $1 = 2 ] # only during update
then
  # for Fedora 19-22
  if [ -f %{_sysconfdir}/smartd.conf -a ! -e %{_sysconfdir}/%name ]
  then
    mkdir -p %{_sysconfdir}/%{name}
    cp -p %{_sysconfdir}/smartd.conf %{_sysconfdir}/%{name}
  fi
fi

%post
%systemd_post smartd.service

%postun
%systemd_postun_with_restart smartd.service

%files
%defattr(-,root,root,-)
%doc AUTHORS ChangeLog COPYING INSTALL NEWS README
%doc TODO examplescripts smartd.conf
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
%{_mandir}/man8/update-smart-drivedb.8*
%{_libexecdir}/%{name}
%{_datadir}/%{name}
%dir /var/log/smartd
%{_sharedstatedir}/%{name}

%changelog
* Fri May 31 2019 Samuel Verschelde <stormi-xcp@ylix.fr> - 1:6.5-1.1
- Add a /var/log/smartd directory and symlink /var/lib/smartmontools to it
- This allows smartd to write an attribute log

* Wed Oct 11 2017 Michal Hlavinka <mhlavink@redhat.com> - 1:6.5-1
- smartmontools updated to 6.5
- adds support for NVMe devices (#1369731)
- minor spec cleanup (#1463148)

* Sun Mar 26 2017 Michal Hlavinka <mhlavink@redhat.com> - 1:6.2-8
- use up to date drivedb (#1388510)
- less scarry messages reported to users (#1340462)

* Wed Sep 07 2016 Michal Hlavinka <mhlavink@redhat.com> - 1:6.2-7
- add update-smart-drivedb.8 man page (#1367237)
- fix drivedb update url (#1364830)

* Thu May 05 2016 Michal Hlavinka <mhlavink@redhat.com> - 1:6.2-6
- allow to discover more devices (#1294999)

* Mon May 02 2016 Michal Hlavinka <mhlavink@redhat.com> - 1:6.2-5
- do not leak file descriptor when calling mailx (#1212582)

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 1:6.2-4
- Mass rebuild 2014-01-24

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 1:6.2-3
- Mass rebuild 2013-12-27

* Mon Sep 16 2013 Michal Hlavinka <mhlavink@redhat.com> - 1:6.2-2
- smartd service file wrong path to environment file (#1008516)

* Tue Jul 30 2013 Michal Hlavinka <mhlavink@redhat.com> - 1:6.2-1
- smartmontools updated to 6.2

* Mon Jul 22 2013 Michal Hlavinka <mhlavink@redhat.com> - 1:6.1-2
- spec cleanup

* Wed Mar 20 2013 Michal Hlavinka <mhlavink@redhat.com> - 1:6.1-1
- smartmontools updated to 6.1

* Fri Feb 15 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:6.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Oct 11 2012 Michal Hlavinka <mhlavink@redhat.com> - 1:6.0-1
- smartmontools updated to 6.0

* Tue Aug 21 2012 Michal Hlavinka <mhlavink@redhat.com> - 1:5.43-3
- use new systemd rpm macros (#850316)

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:5.43-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jul 02 2012 Michal Hlavinka <mhlavink@redhat.com> - 1:5.43-1
- smartmontools updated to 5.43

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:5.42-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Fri Dec 02 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.42-2
- enable smartd after installation

* Fri Oct 21 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.42-1
- smartmontools updated to 5.42

* Mon Jun 13 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.41-2
- make F-14 (sysv init) -> F-15 (systemd) transition more robust

* Fri Jun 10 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.41-1
- updated to 5.41

* Mon May 16 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-10
- fix path to notify script (#675778)

* Fri Mar 11 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-9
- fix typos in man page

* Fri Mar 04 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-8
- don't call chkconfig add, we use systemd now
 
* Thu Mar 03 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-7
- own %%{_datadir}/%%{name} and %%{_libexecdir}/%%{name} dirs

* Thu Feb 17 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-6
- notify users when disk is failing

* Wed Feb 09 2011 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-5
- move to systemd

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:5.40-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Nov 15 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-3
- megaraid: Fix segfault on non-data commands (#577935)

* Tue Nov 09 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-2
- don't forget to restart smartd service after update (#651211)

* Mon Oct 18 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:5.40-1
- updated to 5.40 final

* Mon Sep 27 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:5.39.1-2.r3169
- updated to r3169
- ddds riverdb support for new devices (#637171)

* Fri Jan 29 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:5.39.1-1
- updated to 5.39.1
- Fix spin-up of SATA drive if '-n standby' is used.

* Wed Jan 20 2010 Michal Hlavinka <mhlavink@redhat.com> - 1:5.39-2
- fix DEVICESCAN -d sat
- fix directive '-l selftest'
- fix option '-q, --quietmode'

* Thu Dec 10 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.39-1
- update to 5.39

* Wed Dec 02 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.39-0.1.rc1
- update to 5.39-rc1

* Wed Nov 25 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-25.20091119svn
- spec cleanup

* Mon Nov 23 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-24.20091119svn
- move powermode option from sysconfig to smartd.conf (#539760)

* Thu Nov 19 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-23.20091119svn
- update to svn snapshot 2009-11-19
- remove upstreamed patches

* Mon Nov 02 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-22
- spec cleanup

* Mon Oct 12 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-21 
- warn about disabled mail only if capabilities are enabled

* Fri Oct 09 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-20
- fix init script for case when no action was specified

* Fri Oct 09 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-19
- make init script lsb compliant (#528016)

* Mon Oct 05 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-18
- bump release for rebuild

* Mon Oct 05 2009 Michal Hlaivnka <mhlavink@redhat.com> - 1:5.38-17
- make capabilities optional
- fix capabilities for 3ware contollers (#526626)

* Wed Aug 26 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-16
- extend capability scanning devices

* Wed Aug 26 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-15
- updated patch for lower capabilities (#517728)
- added buildrequires libcap-ng-devel

* Fri Aug 21 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-14
- drop all unnecessary capabilities (#517728)

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:5.38-13
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Jun 11 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-12
- drop autogen call 

* Sat Apr 11 2009 Dennis Gilmore <dennis@ausil.us> - 1:5.38-11
- remove ExclusiveArch use -fPIE on sparc64  
- tested builds on sparcv9 sparc64 and s390x

* Mon Mar 09 2009 Michal Hlavinka <mhlavink@redhat.com> - 1:5.38-10
- cleanup for merge review

* Fri Feb 27 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 1:5.38-9
- fix ExclusiveArch

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:5.38-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Aug 11 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-7
- fix #458549 - obsolete smartmontools-config
- change the default configuration file

* Fri Aug 08 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-6
- correct CXXFLAGS so the PIE code is produced

* Mon May 12 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-5
- remove config subpackage

* Mon May 05 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-4.1
- add libselinux-devel to BR

* Mon May 05 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-4
- fix #232218 character devices /dev/twa* for 3ware 9000 series RAID
  controllers are not created

* Thu Mar 27 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-3
- don't attempt to query DELL PERC controllers -- they'd go offline

* Tue Mar 18 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-2
- fix FD_CLOEXEC on SCSI device file descriptors not being set

* Mon Mar 10 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.38-1
- new upstream version

* Tue Feb 12 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-8.5
- rebuild (gcc-4.3)

* Tue Jan 15 2008 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-8.4
- change '-d ata' to '-d sat' in the config script for SATA drives

* Wed Dec 12 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-8.3
- fix #375791 - parameter warning for smartd in logwatch output

* Wed Oct 31 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-8.2
- rebuild (one more error in autogen.sh)

* Wed Oct 31 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-8.1
- fix build with new automake

* Wed Oct 31 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-8
- fix #359561 - typo in smartd-conf.py causes smartd to skip all disks

* Mon Oct 15 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-7.1
- improved patch for getaddrinfo

* Fri Oct 12 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-7
- replace gethostbyname with getaddrinfo

* Tue Sep 04 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-6
- fix #271741 - smartd-conf.py should allow customization of parameters
- fix #253753 - service starting by default, perhaps shouldn't
- update initscript (related #247058 - initscript review)

* Mon Aug 20 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-5
- add support for 24 disks on 3ware RAID controllers (related #252055)
- fix #245442 - add %%{arm} to smartmontools's set of build archs
- update license tag

* Thu Jun 21 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-4
- fix #241389 - smartd-conf.py pulls in a big dependency chain, so
  build a separate config package
  
* Tue Jun 05 2007 Tomas Smetana <tsmetana@redhat.com> - 1:5.37-3
- fix #241385 - smartmontools missing dependency on mailx
- fix #241388 - unneeded smartd-conf.py[co] installed in /usr/sbin

* Wed Mar  7 2007 Vitezslav Crhonek <vcrhonek@redhat.com> - 1:5.37-2
- re-add cloexec patch
- re-add one erased changelog entry
- compile with -fpie (instead of -fpic)

* Tue Feb 27 2007 Vitezslav Crhonek <vcrhonek@redhat.com> - 1:5.37-1
- new upstream version

* Thu Feb 22 2007 Tomas Mraz <tmraz@redhat.com> - 1:5.36-8
- enable SMART on disks when smartd-conf.py runs (fix
  by Calvin Ostrum) (#214502)

* Mon Feb 12 2007 Tomas Mraz <tmraz@redhat.com> - 1:5.36-7
- redirect service script output to null (#224566)

* Sun Feb 11 2007 Florian La Roche <laroche@redhat.com> - 1:5.36-6
- make sure the preun script does not fail

* Tue Nov  7 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.36-5
- set cloexec on device descriptor so it doesn't leak to sendmail (#214182)
- fixed minor bug in initscript (#213683)
- backported SATA disk detection from upstream

* Fri Aug 18 2006 Jesse Keating <jkeating@redhat.com> - 1:5.36-3
- rebuilt with latest binutils to pick up 64K -z commonpagesize on ppc*
  (#203001)

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 1:5.36-2.1
- rebuild

* Tue Jun 27 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.36-2
- kudzu is deprecated, replace it with HAL (#195752)
- moved later in the boot process so haldaemon is already running
  when drives are being detected

* Thu May 11 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.36-1
- new upstream version
- included patch with support for cciss controllers (#191288)

* Tue May  2 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.33-8
- regenerate smartd.conf on every startup if the config file
  is autogenerated (#190065)

* Fri Mar 24 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.33-7
- add missing quotes to /etc/sysconfig/smartmontools

* Wed Mar 22 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.33-6
- test SATA drives correctly

* Wed Mar 22 2006 Tomas Mraz <tmraz@redhat.com> - 1:5.33-5
- add default /etc/sysconfig/smartmontools file
- ignore errors on startup (#186130)
- test drive for SMART support before adding it to smartd.conf

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 1:5.33-4.2
- bump again for double-long bug on ppc(64)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 1:5.33-4.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Fri Dec 16 2005 Tomas Mraz <tmraz@redhat.com> 1:5.33-4
- mail should be sent to root not root@localhost (#174252)

* Fri Nov 25 2005 Tomas Mraz <tmraz@redhat.com> 1:5.33-3
- add libata disks with -d ata if the libata version
  is new enough otherwise do not add them (#145859, #174095)

* Thu Nov  3 2005 Tomas Mraz <tmraz@redhat.com> 1:5.33-2
- Spec file cleanup by Robert Scheck <redhat@linuxnetz.de> (#170959)
- manual release numbering
- remove bogus patch of non-installed file
- only non-removable drives should be added to smartd.conf
- smartd.conf should be owned (#171498)

* Tue Oct 25 2005 Dave Jones <davej@redhat.com>
- Add comments to generated smartd.conf (#135397)

* Thu Aug 04 2005 Karsten Hopp <karsten@redhat.de>
- package all python files

* Tue Mar  1 2005 Dave Jones <davej@redhat.com>
- Rebuild for gcc4

* Wed Feb  9 2005 Dave Jones <davej@redhat.com>
- Build on PPC32 too (#147090)

* Sat Dec 18 2004 Dave Jones <davej@redhat.com>
- Initial packaging, based upon kernel-utils.

