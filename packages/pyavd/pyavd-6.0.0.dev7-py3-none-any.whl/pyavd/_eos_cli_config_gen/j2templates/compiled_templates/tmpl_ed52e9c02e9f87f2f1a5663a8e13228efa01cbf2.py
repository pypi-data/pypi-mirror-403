from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/router-general.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_router_general = resolve('router_general')
    l_0_delimiter = resolve('delimiter')
    try:
        t_1 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_2 = environment.filters['indent']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'indent' found.")
    try:
        t_3 = environment.filters['length']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'length' found.")
    try:
        t_4 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_4((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general)):
        pass
        yield '!\nrouter general\n'
        if t_4(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'control_functions')):
            pass
            yield '   control-functions\n'
            for l_1_code_unit in t_1(environment.getattr(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'control_functions'), 'code_units'), sort_key='name', ignore_case=False):
                l_1_content = resolve('content')
                _loop_vars = {}
                pass
                if t_4(environment.getattr(l_1_code_unit, 'content')):
                    pass
                    l_1_content = environment.getattr(l_1_code_unit, 'content')
                    _loop_vars['content'] = l_1_content
                    if (not context.call(environment.getattr(context.call(environment.getattr((undefined(name='content') if l_1_content is missing else l_1_content), 'rstrip'), _loop_vars=_loop_vars), 'endswith'), '\nEOF', _loop_vars=_loop_vars)):
                        pass
                        l_1_content = (context.call(environment.getattr((undefined(name='content') if l_1_content is missing else l_1_content), 'rstrip'), _loop_vars=_loop_vars) + '\nEOF')
                        _loop_vars['content'] = l_1_content
                    yield '      code unit '
                    yield str(environment.getattr(l_1_code_unit, 'name'))
                    yield '\n         '
                    yield str(t_2((undefined(name='content') if l_1_content is missing else l_1_content), width=9, first=False))
                    yield '\n'
            l_1_code_unit = l_1_content = missing
            yield '   !\n   exit\n'
        l_0_delimiter = False
        context.vars['delimiter'] = l_0_delimiter
        context.exported_vars.add('delimiter')
        if t_4(environment.getattr(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'router_id'), 'ipv4')):
            pass
            yield '   router-id ipv4 '
            yield str(environment.getattr(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'router_id'), 'ipv4'))
            yield '\n'
            l_0_delimiter = True
            context.vars['delimiter'] = l_0_delimiter
            context.exported_vars.add('delimiter')
        if t_4(environment.getattr(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'router_id'), 'ipv6')):
            pass
            yield '   router-id ipv6 '
            yield str(environment.getattr(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'router_id'), 'ipv6'))
            yield '\n'
            l_0_delimiter = True
            context.vars['delimiter'] = l_0_delimiter
            context.exported_vars.add('delimiter')
        if t_4(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'software_forwarding_hardware_offload_mtu')):
            pass
            yield '   software forwarding hardware offload mtu '
            yield str(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'software_forwarding_hardware_offload_mtu'))
            yield '\n'
            l_0_delimiter = True
            context.vars['delimiter'] = l_0_delimiter
            context.exported_vars.add('delimiter')
        if (t_4((undefined(name='delimiter') if l_0_delimiter is missing else l_0_delimiter), True) and t_4(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'nexthop_fast_failover'), True)):
            pass
            yield '   !\n'
        if t_4(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'nexthop_fast_failover'), True):
            pass
            yield '   hardware next-hop fast-failover\n'
            l_0_delimiter = True
            context.vars['delimiter'] = l_0_delimiter
            context.exported_vars.add('delimiter')
        if (t_4((undefined(name='delimiter') if l_0_delimiter is missing else l_0_delimiter), True) and t_4(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'vrfs'))):
            pass
            yield '   !\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'vrfs'), sort_key='name', ignore_case=False):
            _loop_vars = {}
            pass
            yield '   vrf '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield '\n'
            if t_4(environment.getattr(l_1_vrf, 'software_forwarding_hardware_offload_mtu')):
                pass
                yield '      software forwarding hardware offload mtu '
                yield str(environment.getattr(l_1_vrf, 'software_forwarding_hardware_offload_mtu'))
                yield '\n'
            for l_2_leak_route in t_1(environment.getattr(l_1_vrf, 'leak_routes'), sort_key='source_vrf', ignore_case=False):
                _loop_vars = {}
                pass
                if t_4(environment.getattr(l_2_leak_route, 'subscribe_policy')):
                    pass
                    yield '      leak routes source-vrf '
                    yield str(environment.getattr(l_2_leak_route, 'source_vrf'))
                    yield ' subscribe-policy '
                    yield str(environment.getattr(l_2_leak_route, 'subscribe_policy'))
                    yield '\n'
                elif t_4(environment.getattr(l_2_leak_route, 'subscribe_rcf')):
                    pass
                    yield '      leak routes source-vrf '
                    yield str(environment.getattr(l_2_leak_route, 'source_vrf'))
                    yield ' subscribe rcf '
                    yield str(environment.getattr(l_2_leak_route, 'subscribe_rcf'))
                    yield '\n'
            l_2_leak_route = missing
            for l_2_dynamic_prefix_list in t_1(environment.getattr(environment.getattr(l_1_vrf, 'routes'), 'dynamic_prefix_lists'), sort_key='name', ignore_case=False):
                _loop_vars = {}
                pass
                if t_4(environment.getattr(l_2_dynamic_prefix_list, 'name')):
                    pass
                    yield '      routes dynamic prefix-list '
                    yield str(environment.getattr(l_2_dynamic_prefix_list, 'name'))
                    yield '\n'
            l_2_dynamic_prefix_list = missing
            yield '      exit\n'
            if (t_3(environment.getattr((undefined(name='router_general') if l_0_router_general is missing else l_0_router_general), 'vrfs')) > 1):
                pass
                yield '   !\n'
        l_1_vrf = missing
        yield '   exit\n'

blocks = {}
debug_info = '7=37&10=40&12=43&13=47&14=49&15=51&16=53&18=56&19=58&26=62&27=65&28=68&29=70&31=73&32=76&33=78&35=81&36=84&37=86&39=89&42=92&44=95&46=98&49=101&50=105&51=107&52=110&54=112&55=115&56=118&57=122&58=125&61=130&62=133&63=136&68=140'