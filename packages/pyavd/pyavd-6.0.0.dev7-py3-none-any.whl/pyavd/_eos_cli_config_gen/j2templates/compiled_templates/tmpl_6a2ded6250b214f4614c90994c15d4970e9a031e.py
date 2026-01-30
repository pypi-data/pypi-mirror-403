from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/ip-client-source-interfaces.j2'

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
        t_2 = environment.filters['capitalize']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'capitalize' found.")
    try:
        t_3 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if ((((t_3((undefined(name='ip_ftp_client') if l_0_ip_ftp_client is missing else l_0_ip_ftp_client)) or t_3((undefined(name='ip_http_client') if l_0_ip_http_client is missing else l_0_ip_http_client))) or t_3((undefined(name='ip_ssh_client') if l_0_ip_ssh_client is missing else l_0_ip_ssh_client))) or t_3((undefined(name='ip_telnet_client') if l_0_ip_telnet_client is missing else l_0_ip_telnet_client))) or t_3((undefined(name='ip_tftp_client') if l_0_ip_tftp_client is missing else l_0_ip_tftp_client))):
        pass
        yield '\n### IP Client Source Interfaces\n\n| IP Client | VRF | Source Interface Name |\n| --------- | --- | --------------------- |\n'
        if t_3(environment.getattr((undefined(name='ip_ftp_client') if l_0_ip_ftp_client is missing else l_0_ip_ftp_client), 'source_interface')):
            pass
            yield '| FTP | default | '
            yield str(environment.getattr((undefined(name='ip_ftp_client') if l_0_ip_ftp_client is missing else l_0_ip_ftp_client), 'source_interface'))
            yield ' |\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='ip_ftp_client') if l_0_ip_ftp_client is missing else l_0_ip_ftp_client), 'vrfs'), 'name', ignore_case=False):
            _loop_vars = {}
            pass
            yield '| FTP | '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield ' | '
            yield str(environment.getattr(l_1_vrf, 'source_interface'))
            yield ' |\n'
        l_1_vrf = missing
        if t_3(environment.getattr((undefined(name='ip_http_client') if l_0_ip_http_client is missing else l_0_ip_http_client), 'source_interface')):
            pass
            yield '| HTTP | default | '
            yield str(environment.getattr((undefined(name='ip_http_client') if l_0_ip_http_client is missing else l_0_ip_http_client), 'source_interface'))
            yield ' |\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='ip_http_client') if l_0_ip_http_client is missing else l_0_ip_http_client), 'vrfs'), 'name', ignore_case=False):
            _loop_vars = {}
            pass
            yield '| HTTP | '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield ' | '
            yield str(environment.getattr(l_1_vrf, 'source_interface'))
            yield ' |\n'
        l_1_vrf = missing
        if t_3(environment.getattr((undefined(name='ip_ssh_client') if l_0_ip_ssh_client is missing else l_0_ip_ssh_client), 'source_interface')):
            pass
            yield '| SSH | default | '
            yield str(t_2(environment.getattr((undefined(name='ip_ssh_client') if l_0_ip_ssh_client is missing else l_0_ip_ssh_client), 'source_interface')))
            yield ' |\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='ip_ssh_client') if l_0_ip_ssh_client is missing else l_0_ip_ssh_client), 'vrfs'), 'name', ignore_case=False):
            _loop_vars = {}
            pass
            yield '| SSH | '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield ' | '
            yield str(t_2(environment.getattr(l_1_vrf, 'source_interface')))
            yield ' |\n'
        l_1_vrf = missing
        if t_3(environment.getattr((undefined(name='ip_telnet_client') if l_0_ip_telnet_client is missing else l_0_ip_telnet_client), 'source_interface')):
            pass
            yield '| Telnet | default | '
            yield str(environment.getattr((undefined(name='ip_telnet_client') if l_0_ip_telnet_client is missing else l_0_ip_telnet_client), 'source_interface'))
            yield ' |\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='ip_telnet_client') if l_0_ip_telnet_client is missing else l_0_ip_telnet_client), 'vrfs'), 'name', ignore_case=False):
            _loop_vars = {}
            pass
            yield '| Telnet | '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield ' | '
            yield str(environment.getattr(l_1_vrf, 'source_interface'))
            yield ' |\n'
        l_1_vrf = missing
        if t_3(environment.getattr((undefined(name='ip_tftp_client') if l_0_ip_tftp_client is missing else l_0_ip_tftp_client), 'source_interface')):
            pass
            yield '| TFTP | default | '
            yield str(environment.getattr((undefined(name='ip_tftp_client') if l_0_ip_tftp_client is missing else l_0_ip_tftp_client), 'source_interface'))
            yield ' |\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='ip_tftp_client') if l_0_ip_tftp_client is missing else l_0_ip_tftp_client), 'vrfs'), 'name', ignore_case=False):
            _loop_vars = {}
            pass
            yield '| TFTP | '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield ' | '
            yield str(environment.getattr(l_1_vrf, 'source_interface'))
            yield ' |\n'
        l_1_vrf = missing
        yield '\n#### IP Client Source Interfaces Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/ip-client-source-interfaces.j2', 'documentation/ip-client-source-interfaces.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield ' ```\n'

blocks = {}
debug_info = '7=34&13=37&14=40&16=42&17=46&19=51&20=54&22=56&23=60&25=65&26=68&28=70&29=74&31=79&32=82&34=84&35=88&37=93&38=96&40=98&41=102&47=108'