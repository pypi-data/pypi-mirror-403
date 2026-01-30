from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/ip-name-server.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_ip_name_server = resolve('ip_name_server')
    l_0_flattened_name_servers = missing
    try:
        t_1 = environment.filters['arista.avd.default']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.default' found.")
    try:
        t_2 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_3 = environment.filters['int']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'int' found.")
    try:
        t_4 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    l_0_flattened_name_servers = []
    context.vars['flattened_name_servers'] = l_0_flattened_name_servers
    context.exported_vars.add('flattened_name_servers')
    for l_1_vrf in t_1(environment.getattr((undefined(name='ip_name_server') if l_0_ip_name_server is missing else l_0_ip_name_server), 'vrfs'), []):
        _loop_vars = {}
        pass
        for l_2_name_server in environment.getattr(l_1_vrf, 'servers'):
            l_2_server = missing
            _loop_vars = {}
            pass
            l_2_server = {'vrf': environment.getattr(l_1_vrf, 'name'), 'ip_address': environment.getattr(l_2_name_server, 'ip_address')}
            _loop_vars['server'] = l_2_server
            if (t_4(environment.getattr(l_2_name_server, 'priority')) and (t_3(environment.getattr(l_2_name_server, 'priority')) > 0)):
                pass
                context.call(environment.getattr((undefined(name='server') if l_2_server is missing else l_2_server), 'update'), {'priority': environment.getattr(l_2_name_server, 'priority')}, _loop_vars=_loop_vars)
            context.call(environment.getattr((undefined(name='flattened_name_servers') if l_0_flattened_name_servers is missing else l_0_flattened_name_servers), 'append'), (undefined(name='server') if l_2_server is missing else l_2_server), _loop_vars=_loop_vars)
        l_2_name_server = l_2_server = missing
    l_1_vrf = missing
    for l_1_server in t_2(t_2(t_2((undefined(name='flattened_name_servers') if l_0_flattened_name_servers is missing else l_0_flattened_name_servers), 'ip_address'), sort_key='vrf', ignore_case=False), 'priority', default_value='0'):
        l_1_name_server_cli = missing
        _loop_vars = {}
        pass
        l_1_name_server_cli = str_join(('ip name-server vrf ', environment.getattr(l_1_server, 'vrf'), ' ', environment.getattr(l_1_server, 'ip_address'), ))
        _loop_vars['name_server_cli'] = l_1_name_server_cli
        if t_4(environment.getattr(l_1_server, 'priority')):
            pass
            l_1_name_server_cli = str_join(((undefined(name='name_server_cli') if l_1_name_server_cli is missing else l_1_name_server_cli), ' priority ', environment.getattr(l_1_server, 'priority'), ))
            _loop_vars['name_server_cli'] = l_1_name_server_cli
        yield str((undefined(name='name_server_cli') if l_1_name_server_cli is missing else l_1_name_server_cli))
        yield '\n'
    l_1_server = l_1_name_server_cli = missing

blocks = {}
debug_info = '8=37&9=40&10=43&11=47&12=49&13=51&15=52&18=55&19=59&20=61&21=63&23=65'