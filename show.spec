%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           show
Version:        0.2
Release:        1%{?dist}
Summary:        "show" is a SQL-like interface for the command line

Group:          Development/Languages
License:        LGPLv2.1
URL:            https://fedorahosted.org/show
Source0:        show-0.2.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel

%description
show is a SQL-like interface for the command line.

%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
mv $RPM_BUILD_ROOT/%{_bindir}/show.py $RPM_BUILD_ROOT/%{_bindir}/show
mkdir -p $RPM_BUILD_ROOT/%{_docdir}/%{name}-%{version}
install -m 644 README $RPM_BUILD_ROOT/%{_docdir}/%{name}-%{version}

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc %{_docdir}/%{name}-%{version}
%{python_sitelib}/*
%{_bindir}/show


%changelog
* Sun Mar 22 2009 David Malcolm <dmalcolm@redhat.com> - 0.2-1
- 0.2

* Sun Mar 22 2009 David Malcolm <dmalcolm@redhat.com> - 0.1.1-1
- 0.1.1
- fix license header

* Sun Mar 22 2009 David Malcolm <dmalcolm@redhat.com> - 0.1-1
- initial packaging


