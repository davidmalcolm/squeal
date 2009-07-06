%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           squeal
Version:        0.4.1
Release:        1%{?dist}
Summary:        Data manipulation tool for the command line

Group:          Development/Languages
License:        LGPLv2
URL:            https://fedorahosted.org/squeal
Source0:        https://fedorahosted.org/released/squeal/squeal-0.4.1.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel

# Trying to support both Fedora and RHEL:
%if 0%{?fedora}
BuildRequires:  python-setuptools-devel
%else
BuildRequires:  python-setuptools
%endif

Requires:       python-augeas

%description
"squeal" is a tool for manipulating data from the shell, and in shell
pipelines.

It is able to carve up various types of input file, treating them as tabular
data.  It has backends for working with many types of log file, configuration
files, and archive formats.

It accepts a subset of SQL for manipulating the inputs, such as filtering,
sorting and aggregating.

Finally, it can output the results in a number of formats, including a
text-based user interface.


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
%doc README COPYING
%{python_sitelib}/*
%{_bindir}/squeal


%changelog
* Mon Jul  6 2009 David Malcolm <dmalcolm@redhat.com> - 0.4.1-1
- 0.4.1: add MANIFEST.in and COPYING files (LGPLv2.1); fix metadata; add
debug option
- make summary and description convey a better idea of what the software
does

* Thu Jun  4 2009 David Malcolm <dmalcolm@redhat.com> - 0.4-3
- change license tag to "LGPLv2", the approved shortname for LGPLv2.1, as per
Fedora packaging guidelines.  The code is licensed under LGPLv2.1.

* Thu Jun  4 2009 David Malcolm <dmalcolm@redhat.com> - 0.4-2
- add python-setuptools(-devel) to build requirements

* Thu Jun  4 2009 David Malcolm <dmalcolm@redhat.com> - 0.4-1
- 0.4
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


