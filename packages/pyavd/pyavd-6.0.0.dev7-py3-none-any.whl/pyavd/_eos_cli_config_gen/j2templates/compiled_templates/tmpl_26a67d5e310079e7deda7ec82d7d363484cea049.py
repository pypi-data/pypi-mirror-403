from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/ip-client-source-interfaces.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_ip_ftp_client = resolve('ip_ftp_client')
    l_0_ip_http_client = resolve('ip_http_client')
    l_0_ip_ssh_client = resolve('ip_ssh_client')
    l_0_ip_telnet_client = resolve('ip_telnet_client')
    l_0_ip_tftp_client = resolve('ip_tftp_client')
    try:
        t_1 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_2 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if ((((t_2((undefined(name='ip_ftp_client') if l_0_ip_ftp_client is missing else l_0_ip_ftp_client)) or t_2((undefined(name='ip_http_client') if l_0_ip_http_client is missing else l_0_ip_http_client))) or t_2((undefined(name='ip_ssh_client') if l_0_ip_ssh_client is missing else l_0_ip_ssh_client))) or t_2((undefined(name='ip_telnet_client') if l_0_ip_telnet_client is missing else l_0_ip_telnet_client))) or t_2((undefined(name='ip_tftp_client') if l_0_ip_tftp_client is missing else l_0_ip_tftp_client))):
        pass
        yield '!\n'
        if t_2(environment.getattr((undefined(name='ip_ftp_client') if l_0_ip_ftp_client is missing else l_0_ip_ftp_client), 'source_interface')):
            pass
            yield 'ip ftp client source-interface '
            yield str(environment.getattr((undefined(name='ip_ftp_client') if l_0_ip_ftp_client is missing else l_0_ip_ftp_client), 'source_interface'))
            yield '\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='ip_ftp_client') if l_0_ip_ftp_client is missing else l_0_ip_ftp_client), 'vrfs'), 'name', ignore_case=False):
            _loop_vars = {}
            pass
            yield 'ip ftp client source-interface '
            yield str(environment.getattr(l_1_vrf, 'source_interface'))
            yield ' vrf '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield '\n'
        l_1_vrf = missing
        if t_2(environment.getattr((undefined(name='ip_http_client') if l_0_ip_http_client is missing else l_0_ip_http_client), 'source_interface')):
            pass
            yield 'ip http client local-interface '
            yield str(environment.getattr((undefined(name='ip_http_client') if l_0_ip_http_client is missing else l_0_ip_http_client), 'source_interface'))
            yield '\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='ip_http_client') if l_0_ip_http_client is missing else l_0_ip_http_client), 'vrfs'), 'name', ignore_case=False):
            _loop_vars = {}
            pass
            yield 'ip http client local-interface '
            yield str(environment.getattr(l_1_vrf, 'source_interface'))
            yield ' vrf '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield '\n'
        l_1_vrf = missing
        if t_2(environment.getattr((undefined(name='ip_ssh_client') if l_0_ip_ssh_client is missing else l_0_ip_ssh_client), 'source_interface')):
            pass
            yield 'ip ssh client source-interface '
            yield str(environment.getattr((undefined(name='ip_ssh_client') if l_0_ip_ssh_client is missing else l_0_ip_ssh_client), 'source_interface'))
            yield '\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='ip_ssh_client') if l_0_ip_ssh_client is missing else l_0_ip_ssh_client), 'vrfs'), 'name', ignore_case=False):
            _loop_vars = {}
            pass
            yield 'ip ssh client source-interface '
            yield str(environment.getattr(l_1_vrf, 'source_interface'))
            yield ' vrf '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield '\n'
        l_1_vrf = missing
        if t_2(environment.getattr((undefined(name='ip_telnet_client') if l_0_ip_telnet_client is missing else l_0_ip_telnet_client), 'source_interface')):
            pass
            yield 'ip telnet client source-interface '
            yield str(environment.getattr((undefined(name='ip_telnet_client') if l_0_ip_telnet_client is missing else l_0_ip_telnet_client), 'source_interface'))
            yield '\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='ip_telnet_client') if l_0_ip_telnet_client is missing else l_0_ip_telnet_client), 'vrfs'), 'name', ignore_case=False):
            _loop_vars = {}
            pass
            yield 'ip telnet client source-interface '
            yield str(environment.getattr(l_1_vrf, 'source_interface'))
            yield ' vrf '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield '\n'
        l_1_vrf = missing
        if t_2(environment.getattr((undefined(name='ip_tftp_client') if l_0_ip_tftp_client is missing else l_0_ip_tftp_client), 'source_interface')):
            pass
            yield 'ip tftp client source-interface '
            yield str(environment.getattr((undefined(name='ip_tftp_client') if l_0_ip_tftp_client is missing else l_0_ip_tftp_client), 'source_interface'))
            yield '\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='ip_tftp_client') if l_0_ip_tftp_client is missing else l_0_ip_tftp_client), 'vrfs'), 'name', ignore_case=False):
            _loop_vars = {}
            pass
            yield 'ip tftp client source-interface '
            yield str(environment.getattr(l_1_vrf, 'source_interface'))
            yield ' vrf '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield '\n'
        l_1_vrf = missing

blocks = {}
debug_info = '7=28&13=31&14=34&16=36&17=40&19=45&20=48&22=50&23=54&25=59&26=62&28=64&29=68&31=73&32=76&34=78&35=82&37=87&38=90&40=92&41=96'