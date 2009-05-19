%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           squeal
Version:        0.4
Release:        1%{?dist}
Summary:        "squeal" is a SQL-like interface for the command line

Group:          Development/Languages
License:        LGPLv2.1
URL:            https://fedorahosted.org/show
Source0:        squeal-0.3.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel

Requires:       python-augeas

%description
squeal is a SQL-like interface for the command line.

%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
mv $RPM_BUILD_ROOT/%{_bindir}/squeal.py $RPM_BUILD_ROOT/%{_bindir}/squeal

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc README
%{python_sitelib}/*
%{_bindir}/squeal


%changelog
* Tue May 19 2009 David Malcolm <dmalcolm@redhat.com> - 0.4-1
- rename show -> squeal

* Tue Mar 24 2009 David Malcolm <dmalcolm@redhat.com> - 0.3-1
- 0.3: add horizontal scrolling, syslog handling, and config file handling, using augeas
- specfile cleanup (thanks rathann)
- add dependency on python-augeas for now

* Sun Mar 22 2009 David Malcolm <dmalcolm@redhat.com> - 0.2-1
- 0.2

* Sun Mar 22 2009 David Malcolm <dmalcolm@redhat.com> - 0.1.1-1
- 0.1.1
- fix license header

* Sun Mar 22 2009 David Malcolm <dmalcolm@redhat.com> - 0.1-1
- initial packaging


