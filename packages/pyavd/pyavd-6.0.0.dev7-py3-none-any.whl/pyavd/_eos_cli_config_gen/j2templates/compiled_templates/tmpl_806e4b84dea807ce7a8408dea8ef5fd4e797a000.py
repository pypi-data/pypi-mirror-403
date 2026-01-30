from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/router-msdp.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_router_msdp = resolve('router_msdp')
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
    if t_2((undefined(name='router_msdp') if l_0_router_msdp is missing else l_0_router_msdp)):
        pass
        yield '!\nrouter msdp\n'
        for l_1_group_limit in t_1(environment.getattr((undefined(name='router_msdp') if l_0_router_msdp is missing else l_0_router_msdp), 'group_limits'), sort_key='source_prefix'):
            _loop_vars = {}
            pass
            yield '   group-limit '
            yield str(environment.getattr(l_1_group_limit, 'limit'))
            yield ' source '
            yield str(environment.getattr(l_1_group_limit, 'source_prefix'))
            yield '\n'
        l_1_group_limit = missing
        if t_2(environment.getattr((undefined(name='router_msdp') if l_0_router_msdp is missing else l_0_router_msdp), 'originator_id_local_interface')):
            pass
            yield '   originator-id local-interface '
            yield str(environment.getattr((undefined(name='router_msdp') if l_0_router_msdp is missing else l_0_router_msdp), 'originator_id_local_interface'))
            yield '\n'
        if t_2(environment.getattr((undefined(name='router_msdp') if l_0_router_msdp is missing else l_0_router_msdp), 'rejected_limit')):
            pass
            yield '   rejected-limit '
            yield str(environment.getattr((undefined(name='router_msdp') if l_0_router_msdp is missing else l_0_router_msdp), 'rejected_limit'))
            yield '\n'
        if t_2(environment.getattr((undefined(name='router_msdp') if l_0_router_msdp is missing else l_0_router_msdp), 'forward_register_packets'), True):
            pass
            yield '   forward register-packets\n'
        if t_2(environment.getattr((undefined(name='router_msdp') if l_0_router_msdp is missing else l_0_router_msdp), 'connection_retry_interval')):
            pass
            yield '   connection retry interval '
            yield str(environment.getattr((undefined(name='router_msdp') if l_0_router_msdp is missing else l_0_router_msdp), 'connection_retry_interval'))
            yield '\n'
        for l_1_peer in t_1(environment.getattr((undefined(name='router_msdp') if l_0_router_msdp is missing else l_0_router_msdp), 'peers'), sort_key='ipv4_address'):
            l_1_default_peer_cli = resolve('default_peer_cli')
            _loop_vars = {}
            pass
            yield '   !\n   peer '
            yield str(environment.getattr(l_1_peer, 'ipv4_address'))
            yield '\n'
            if t_2(environment.getattr(environment.getattr(l_1_peer, 'default_peer'), 'enabled'), True):
                pass
                l_1_default_peer_cli = 'default-peer'
                _loop_vars['default_peer_cli'] = l_1_default_peer_cli
                if t_2(environment.getattr(environment.getattr(l_1_peer, 'default_peer'), 'prefix_list')):
                    pass
                    l_1_default_peer_cli = str_join(((undefined(name='default_peer_cli') if l_1_default_peer_cli is missing else l_1_default_peer_cli), ' prefix-list ', environment.getattr(environment.getattr(l_1_peer, 'default_peer'), 'prefix_list'), ))
                    _loop_vars['default_peer_cli'] = l_1_default_peer_cli
                yield '      '
                yield str((undefined(name='default_peer_cli') if l_1_default_peer_cli is missing else l_1_default_peer_cli))
                yield '\n'
            for l_2_mesh_group in t_1(environment.getattr(l_1_peer, 'mesh_groups'), 'name', ignore_case=False):
                _loop_vars = {}
                pass
                if t_2(environment.getattr(l_2_mesh_group, 'name')):
                    pass
                    yield '      mesh-group '
                    yield str(environment.getattr(l_2_mesh_group, 'name'))
                    yield '\n'
            l_2_mesh_group = missing
            if t_2(environment.getattr(l_1_peer, 'local_interface')):
                pass
                yield '      local-interface '
                yield str(environment.getattr(l_1_peer, 'local_interface'))
                yield '\n'
            if (t_2(environment.getattr(environment.getattr(l_1_peer, 'keepalive'), 'keepalive_timer')) and t_2(environment.getattr(environment.getattr(l_1_peer, 'keepalive'), 'hold_timer'))):
                pass
                yield '      keepalive '
                yield str(environment.getattr(environment.getattr(l_1_peer, 'keepalive'), 'keepalive_timer'))
                yield ' '
                yield str(environment.getattr(environment.getattr(l_1_peer, 'keepalive'), 'hold_timer'))
                yield '\n'
            if t_2(environment.getattr(environment.getattr(l_1_peer, 'sa_filter'), 'in_list')):
                pass
                yield '      sa-filter in list '
                yield str(environment.getattr(environment.getattr(l_1_peer, 'sa_filter'), 'in_list'))
                yield '\n'
            if t_2(environment.getattr(environment.getattr(l_1_peer, 'sa_filter'), 'out_list')):
                pass
                yield '      sa-filter out list '
                yield str(environment.getattr(environment.getattr(l_1_peer, 'sa_filter'), 'out_list'))
                yield '\n'
            if t_2(environment.getattr(l_1_peer, 'description')):
                pass
                yield '      description '
                yield str(environment.getattr(l_1_peer, 'description'))
                yield '\n'
            if t_2(environment.getattr(l_1_peer, 'disabled'), True):
                pass
                yield '      disabled\n'
            if t_2(environment.getattr(l_1_peer, 'sa_limit')):
                pass
                yield '      sa-limit '
                yield str(environment.getattr(l_1_peer, 'sa_limit'))
                yield '\n'
        l_1_peer = l_1_default_peer_cli = missing
        for l_1_vrf in t_1(environment.getattr((undefined(name='router_msdp') if l_0_router_msdp is missing else l_0_router_msdp), 'vrfs'), 'name', ignore_case=False):
            _loop_vars = {}
            pass
            if (environment.getattr(l_1_vrf, 'name') != 'default'):
                pass
                yield '   !\n   vrf '
                yield str(environment.getattr(l_1_vrf, 'name'))
                yield '\n'
                for l_2_group_limit in t_1(environment.getattr(l_1_vrf, 'group_limits'), 'source_prefix'):
                    _loop_vars = {}
                    pass
                    yield '      group-limit '
                    yield str(environment.getattr(l_2_group_limit, 'limit'))
                    yield ' source '
                    yield str(environment.getattr(l_2_group_limit, 'source_prefix'))
                    yield '\n'
                l_2_group_limit = missing
                if t_2(environment.getattr(l_1_vrf, 'originator_id_local_interface')):
                    pass
                    yield '      originator-id local-interface '
                    yield str(environment.getattr(l_1_vrf, 'originator_id_local_interface'))
                    yield '\n'
                if t_2(environment.getattr(l_1_vrf, 'rejected_limit')):
                    pass
                    yield '      rejected-limit '
                    yield str(environment.getattr(l_1_vrf, 'rejected_limit'))
                    yield '\n'
                if t_2(environment.getattr(l_1_vrf, 'forward_register_packets'), True):
                    pass
                    yield '      forward register-packets\n'
                if t_2(environment.getattr(l_1_vrf, 'connection_retry_interval')):
                    pass
                    yield '      connection retry interval '
                    yield str(environment.getattr(l_1_vrf, 'connection_retry_interval'))
                    yield '\n'
                for l_2_peer in t_1(environment.getattr(l_1_vrf, 'peers'), 'ipv4_address'):
                    l_2_default_peer_cli = resolve('default_peer_cli')
                    _loop_vars = {}
                    pass
                    yield '      !\n      peer '
                    yield str(environment.getattr(l_2_peer, 'ipv4_address'))
                    yield '\n'
                    if t_2(environment.getattr(environment.getattr(l_2_peer, 'default_peer'), 'enabled'), True):
                        pass
                        l_2_default_peer_cli = 'default-peer'
                        _loop_vars['default_peer_cli'] = l_2_default_peer_cli
                        if t_2(environment.getattr(environment.getattr(l_2_peer, 'default_peer'), 'prefix_list')):
                            pass
                            l_2_default_peer_cli = str_join(((undefined(name='default_peer_cli') if l_2_default_peer_cli is missing else l_2_default_peer_cli), ' prefix-list ', environment.getattr(environment.getattr(l_2_peer, 'default_peer'), 'prefix_list'), ))
                            _loop_vars['default_peer_cli'] = l_2_default_peer_cli
                        yield '         '
                        yield str((undefined(name='default_peer_cli') if l_2_default_peer_cli is missing else l_2_default_peer_cli))
                        yield '\n'
                    for l_3_mesh_group in t_1(environment.getattr(l_2_peer, 'mesh_groups'), sort_key='name', ignore_case=False):
                        _loop_vars = {}
                        pass
                        yield '         mesh-group '
                        yield str(environment.getattr(l_3_mesh_group, 'name'))
                        yield '\n'
                    l_3_mesh_group = missing
                    if t_2(environment.getattr(l_2_peer, 'local_interface')):
                        pass
                        yield '         local-interface '
                        yield str(environment.getattr(l_2_peer, 'local_interface'))
                        yield '\n'
                    if (t_2(environment.getattr(environment.getattr(l_2_peer, 'keepalive'), 'keepalive_timer')) and t_2(environment.getattr(environment.getattr(l_2_peer, 'keepalive'), 'hold_timer'))):
                        pass
                        yield '         keepalive '
                        yield str(environment.getattr(environment.getattr(l_2_peer, 'keepalive'), 'keepalive_timer'))
                        yield ' '
                        yield str(environment.getattr(environment.getattr(l_2_peer, 'keepalive'), 'hold_timer'))
                        yield '\n'
                    if t_2(environment.getattr(environment.getattr(l_2_peer, 'sa_filter'), 'in_list')):
                        pass
                        yield '         sa-filter in list '
                        yield str(environment.getattr(environment.getattr(l_2_peer, 'sa_filter'), 'in_list'))
                        yield '\n'
                    if t_2(environment.getattr(environment.getattr(l_2_peer, 'sa_filter'), 'out_list')):
                        pass
                        yield '         sa-filter out list '
                        yield str(environment.getattr(environment.getattr(l_2_peer, 'sa_filter'), 'out_list'))
                        yield '\n'
                    if t_2(environment.getattr(l_2_peer, 'description')):
                        pass
                        yield '         description '
                        yield str(environment.getattr(l_2_peer, 'description'))
                        yield '\n'
                    if t_2(environment.getattr(l_2_peer, 'disabled'), True):
                        pass
                        yield '         disabled\n'
                    if t_2(environment.getattr(l_2_peer, 'sa_limit')):
                        pass
                        yield '         sa-limit '
                        yield str(environment.getattr(l_2_peer, 'sa_limit'))
                        yield '\n'
                l_2_peer = l_2_default_peer_cli = missing
        l_1_vrf = missing

blocks = {}
debug_info = '7=24&10=27&11=31&13=36&14=39&16=41&17=44&19=46&22=49&23=52&25=54&27=59&28=61&29=63&30=65&31=67&33=70&35=72&36=75&37=78&40=81&41=84&43=86&44=89&46=93&47=96&49=98&50=101&52=103&53=106&55=108&58=111&59=114&62=117&63=120&65=123&66=125&67=129&69=134&70=137&72=139&73=142&75=144&78=147&79=150&81=152&83=157&84=159&85=161&86=163&87=165&89=168&91=170&92=174&94=177&95=180&97=182&98=185&100=189&101=192&103=194&104=197&106=199&107=202&109=204&112=207&113=210'