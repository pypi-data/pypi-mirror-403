from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/ip-name-server.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_ip_name_server = resolve('ip_name_server')
    try:
        t_1 = environment.filters['arista.avd.default']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.default' found.")
    try:
        t_2 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_2((undefined(name='ip_name_server') if l_0_ip_name_server is missing else l_0_ip_name_server)):
        pass
        yield '\n### IP Name Servers\n\n#### IP Name Servers Summary\n\n| Name Server | VRF | Priority |\n| ----------- | --- | -------- |\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='ip_name_server') if l_0_ip_name_server is missing else l_0_ip_name_server), 'vrfs'), []):
            _loop_vars = {}
            pass
            for l_2_name_server in environment.getattr(l_1_vrf, 'servers'):
                _loop_vars = {}
                pass
                yield '| '
                yield str(environment.getattr(l_2_name_server, 'ip_address'))
                yield ' | '
                yield str(environment.getattr(l_1_vrf, 'name'))
                yield ' | '
                yield str(t_1(environment.getattr(l_2_name_server, 'priority'), '-'))
                yield ' |\n'
            l_2_name_server = missing
        l_1_vrf = missing
        yield '\n#### IP Name Servers Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/ip-name-server.j2', 'documentation/ip-name-server.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=24&15=27&16=30&17=34&24=43'