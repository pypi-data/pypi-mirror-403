from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/router-isis.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_router_isis = resolve('router_isis')
    l_0_overload_cli = resolve('overload_cli')
    l_0_spf_interval_cli = resolve('spf_interval_cli')
    l_0_wait_hold_interval_unit = resolve('wait_hold_interval_unit')
    l_0_timers_lsp_generation = resolve('timers_lsp_generation')
    l_0_isis_auth_cli = resolve('isis_auth_cli')
    l_0_auth_keys = resolve('auth_keys')
    l_0_both_key_ids = resolve('both_key_ids')
    l_0_lu_cli = resolve('lu_cli')
    l_0_ti_lfa_cli = resolve('ti_lfa_cli')
    l_0_ti_lfa_srlg_cli = resolve('ti_lfa_srlg_cli')
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
        t_3 = environment.filters['indent']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'indent' found.")
    try:
        t_4 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_4(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'instance')):
        pass
        yield '!\nrouter isis '
        yield str(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'instance'))
        yield '\n'
        if t_4(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'net')):
            pass
            yield '   net '
            yield str(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'net'))
            yield '\n'
        if t_4(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'is_hostname')):
            pass
            yield '   is-hostname '
            yield str(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'is_hostname'))
            yield '\n'
        if t_4(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'router_id')):
            pass
            yield '   router-id ipv4 '
            yield str(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'router_id'))
            yield '\n'
        if t_4(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'is_type')):
            pass
            yield '   is-type '
            yield str(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'is_type'))
            yield '\n'
        if t_4(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'log_adjacency_changes'), True):
            pass
            yield '   log-adjacency-changes\n'
        elif t_4(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'log_adjacency_changes'), False):
            pass
            yield '   no log-adjacency-changes\n'
        if t_4(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'mpls_ldp_sync_default'), True):
            pass
            yield '   mpls ldp sync default\n'
        for l_1_redistribute_route in t_2(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'redistribute_routes'), 'source_protocol'):
            l_1_redistribute_route_cli = missing
            _loop_vars = {}
            pass
            l_1_redistribute_route_cli = str_join(('redistribute ', environment.getattr(l_1_redistribute_route, 'source_protocol'), ))
            _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
            if (environment.getattr(l_1_redistribute_route, 'source_protocol') == 'isis'):
                pass
                l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' instance', ))
                _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
            elif (environment.getattr(l_1_redistribute_route, 'source_protocol') == 'ospf'):
                pass
                if t_4(environment.getattr(l_1_redistribute_route, 'include_leaked'), True):
                    pass
                    l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' include leaked', ))
                    _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                if (not t_4(environment.getattr(l_1_redistribute_route, 'ospf_route_type'))):
                    pass
                    continue
                l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' match ', environment.getattr(l_1_redistribute_route, 'ospf_route_type'), ))
                _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
            elif (environment.getattr(l_1_redistribute_route, 'source_protocol') == 'ospfv3'):
                pass
                if (not t_4(environment.getattr(l_1_redistribute_route, 'ospf_route_type'))):
                    pass
                    continue
                l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' match ', environment.getattr(l_1_redistribute_route, 'ospf_route_type'), ))
                _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
            elif (environment.getattr(l_1_redistribute_route, 'source_protocol') in ['static', 'connected']):
                pass
                if t_4(environment.getattr(l_1_redistribute_route, 'include_leaked'), True):
                    pass
                    l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' include leaked', ))
                    _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
            if t_4(environment.getattr(l_1_redistribute_route, 'route_map')):
                pass
                l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' route-map ', environment.getattr(l_1_redistribute_route, 'route_map'), ))
                _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
            yield '   '
            yield str((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli))
            yield '\n'
        l_1_redistribute_route = l_1_redistribute_route_cli = missing
        if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'local_convergence'), 'protected_prefixes'), True):
            pass
            if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'local_convergence'), 'delay')):
                pass
                yield '   timers local-convergence-delay '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'local_convergence'), 'delay'))
                yield ' protected-prefixes\n'
            else:
                pass
                yield '   timers local-convergence-delay protected-prefixes\n'
        if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'set_overload_bit'), 'enabled'), True):
            pass
            l_0_overload_cli = 'set-overload-bit'
            context.vars['overload_cli'] = l_0_overload_cli
            context.exported_vars.add('overload_cli')
            if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'set_overload_bit'), 'on_startup'), 'delay')):
                pass
                l_0_overload_cli = str_join(((undefined(name='overload_cli') if l_0_overload_cli is missing else l_0_overload_cli), ' on-startup ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'set_overload_bit'), 'on_startup'), 'delay'), ))
                context.vars['overload_cli'] = l_0_overload_cli
                context.exported_vars.add('overload_cli')
            elif t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'set_overload_bit'), 'on_startup'), 'wait_for_bgp'), 'enabled'), True):
                pass
                if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'set_overload_bit'), 'on_startup'), 'wait_for_bgp'), 'timeout')):
                    pass
                    l_0_overload_cli = str_join(((undefined(name='overload_cli') if l_0_overload_cli is missing else l_0_overload_cli), ' on-startup wait-for-bgp timeout ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'set_overload_bit'), 'on_startup'), 'wait_for_bgp'), 'timeout'), ))
                    context.vars['overload_cli'] = l_0_overload_cli
                    context.exported_vars.add('overload_cli')
                else:
                    pass
                    l_0_overload_cli = str_join(((undefined(name='overload_cli') if l_0_overload_cli is missing else l_0_overload_cli), ' on-startup wait-for-bgp', ))
                    context.vars['overload_cli'] = l_0_overload_cli
                    context.exported_vars.add('overload_cli')
            yield '   '
            yield str((undefined(name='overload_cli') if l_0_overload_cli is missing else l_0_overload_cli))
            yield '\n'
        if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'advertise'), 'passive_only'), True):
            pass
            yield '   advertise passive-only\n'
        if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'spf_interval'), 'interval')):
            pass
            l_0_spf_interval_cli = str_join(('spf-interval ', environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'spf_interval'), 'interval'), ))
            context.vars['spf_interval_cli'] = l_0_spf_interval_cli
            context.exported_vars.add('spf_interval_cli')
            if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'spf_interval'), 'interval_unit')):
                pass
                l_0_spf_interval_cli = str_join(((undefined(name='spf_interval_cli') if l_0_spf_interval_cli is missing else l_0_spf_interval_cli), ' ', environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'spf_interval'), 'interval_unit'), ))
                context.vars['spf_interval_cli'] = l_0_spf_interval_cli
                context.exported_vars.add('spf_interval_cli')
                l_0_wait_hold_interval_unit = ' milliseconds'
                context.vars['wait_hold_interval_unit'] = l_0_wait_hold_interval_unit
                context.exported_vars.add('wait_hold_interval_unit')
            if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'spf_interval'), 'wait_interval')):
                pass
                l_0_spf_interval_cli = str_join(((undefined(name='spf_interval_cli') if l_0_spf_interval_cli is missing else l_0_spf_interval_cli), ' ', environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'spf_interval'), 'wait_interval'), t_1((undefined(name='wait_hold_interval_unit') if l_0_wait_hold_interval_unit is missing else l_0_wait_hold_interval_unit), ''), ))
                context.vars['spf_interval_cli'] = l_0_spf_interval_cli
                context.exported_vars.add('spf_interval_cli')
                if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'spf_interval'), 'hold_interval')):
                    pass
                    l_0_spf_interval_cli = str_join(((undefined(name='spf_interval_cli') if l_0_spf_interval_cli is missing else l_0_spf_interval_cli), ' ', environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'spf_interval'), 'hold_interval'), t_1((undefined(name='wait_hold_interval_unit') if l_0_wait_hold_interval_unit is missing else l_0_wait_hold_interval_unit), ''), ))
                    context.vars['spf_interval_cli'] = l_0_spf_interval_cli
                    context.exported_vars.add('spf_interval_cli')
            yield '   '
            yield str((undefined(name='spf_interval_cli') if l_0_spf_interval_cli is missing else l_0_spf_interval_cli))
            yield '\n'
        if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'csnp'), 'generation'), 'interval')):
            pass
            yield '   timers csnp generation interval '
            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'csnp'), 'generation'), 'interval'))
            yield ' seconds\n'
        if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'csnp'), 'generation'), 'p2p_disabled'), True):
            pass
            yield '   timers csnp generation p2p disabled\n'
        if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'lsp'), 'out_delay')):
            pass
            yield '   timers lsp out-delay '
            yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'lsp'), 'out_delay'))
            yield '\n'
        if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'lsp'), 'refresh_interval')):
            pass
            yield '   timers lsp refresh '
            yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'lsp'), 'refresh_interval'))
            yield '\n'
        if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'lsp'), 'generation'), 'interval')):
            pass
            l_0_timers_lsp_generation = str_join(('timers lsp generation ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'lsp'), 'generation'), 'interval'), ))
            context.vars['timers_lsp_generation'] = l_0_timers_lsp_generation
            context.exported_vars.add('timers_lsp_generation')
            if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'lsp'), 'generation'), 'initial_wait_time')):
                pass
                l_0_timers_lsp_generation = str_join(((undefined(name='timers_lsp_generation') if l_0_timers_lsp_generation is missing else l_0_timers_lsp_generation), ' ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'lsp'), 'generation'), 'initial_wait_time'), ))
                context.vars['timers_lsp_generation'] = l_0_timers_lsp_generation
                context.exported_vars.add('timers_lsp_generation')
                if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'lsp'), 'generation'), 'wait_time')):
                    pass
                    l_0_timers_lsp_generation = str_join(((undefined(name='timers_lsp_generation') if l_0_timers_lsp_generation is missing else l_0_timers_lsp_generation), ' ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'lsp'), 'generation'), 'wait_time'), ))
                    context.vars['timers_lsp_generation'] = l_0_timers_lsp_generation
                    context.exported_vars.add('timers_lsp_generation')
            yield '   '
            yield str((undefined(name='timers_lsp_generation') if l_0_timers_lsp_generation is missing else l_0_timers_lsp_generation))
            yield '\n'
        if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'lsp'), 'min_remaining_lifetime')):
            pass
            yield '   timers lsp min-remaining-lifetime '
            yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'timers'), 'lsp'), 'min_remaining_lifetime'))
            yield '\n'
        if (t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'mode')) and (((environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'mode') in ['md5', 'text']) or ((environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'mode') == 'sha') and t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'sha'), 'key_id')))) or (((environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'mode') == 'shared-secret') and t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'shared_secret'), 'profile'))) and t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'shared_secret'), 'algorithm'))))):
            pass
            l_0_isis_auth_cli = str_join(('authentication mode ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'mode'), ))
            context.vars['isis_auth_cli'] = l_0_isis_auth_cli
            context.exported_vars.add('isis_auth_cli')
            if (environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'mode') == 'sha'):
                pass
                l_0_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli), ' key-id ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'sha'), 'key_id'), ))
                context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                context.exported_vars.add('isis_auth_cli')
            elif (environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'mode') == 'shared-secret'):
                pass
                l_0_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli), ' profile ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'shared_secret'), 'profile'), ))
                context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                context.exported_vars.add('isis_auth_cli')
                l_0_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli), ' algorithm ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'shared_secret'), 'algorithm'), ))
                context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                context.exported_vars.add('isis_auth_cli')
            if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'rx_disabled'), True):
                pass
                l_0_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli), ' rx-disabled', ))
                context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                context.exported_vars.add('isis_auth_cli')
            yield '   '
            yield str((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli))
            yield '\n'
        else:
            pass
            if (t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'mode')) and (((environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'mode') in ['md5', 'text']) or ((environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'mode') == 'sha') and t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'sha'), 'key_id')))) or (((environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'mode') == 'shared-secret') and t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'shared_secret'), 'profile'))) and t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'shared_secret'), 'algorithm'))))):
                pass
                l_0_isis_auth_cli = str_join(('authentication mode ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'mode'), ))
                context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                context.exported_vars.add('isis_auth_cli')
                if (environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'mode') == 'sha'):
                    pass
                    l_0_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli), ' key-id ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'sha'), 'key_id'), ))
                    context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                    context.exported_vars.add('isis_auth_cli')
                elif (environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'mode') == 'shared-secret'):
                    pass
                    l_0_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli), ' profile ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'shared_secret'), 'profile'), ))
                    context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                    context.exported_vars.add('isis_auth_cli')
                    l_0_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli), ' algorithm ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'shared_secret'), 'algorithm'), ))
                    context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                    context.exported_vars.add('isis_auth_cli')
                if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'rx_disabled'), True):
                    pass
                    l_0_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli), ' rx-disabled', ))
                    context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                    context.exported_vars.add('isis_auth_cli')
                yield '   '
                yield str((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli))
                yield ' level-1\n'
            if (t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'mode')) and (((environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'mode') in ['md5', 'text']) or ((environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'mode') == 'sha') and t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'sha'), 'key_id')))) or (((environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'mode') == 'shared-secret') and t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'shared_secret'), 'profile'))) and t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'shared_secret'), 'algorithm'))))):
                pass
                l_0_isis_auth_cli = str_join(('authentication mode ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'mode'), ))
                context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                context.exported_vars.add('isis_auth_cli')
                if (environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'mode') == 'sha'):
                    pass
                    l_0_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli), ' key-id ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'sha'), 'key_id'), ))
                    context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                    context.exported_vars.add('isis_auth_cli')
                elif (environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'mode') == 'shared-secret'):
                    pass
                    l_0_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli), ' profile ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'shared_secret'), 'profile'), ))
                    context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                    context.exported_vars.add('isis_auth_cli')
                    l_0_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli), ' algorithm ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'shared_secret'), 'algorithm'), ))
                    context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                    context.exported_vars.add('isis_auth_cli')
                if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'rx_disabled'), True):
                    pass
                    l_0_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli), ' rx-disabled', ))
                    context.vars['isis_auth_cli'] = l_0_isis_auth_cli
                    context.exported_vars.add('isis_auth_cli')
                yield '   '
                yield str((undefined(name='isis_auth_cli') if l_0_isis_auth_cli is missing else l_0_isis_auth_cli))
                yield ' level-2\n'
        if t_4(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'graceful_restart')):
            pass
            if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'graceful_restart'), 'enabled'), True):
                pass
                yield '   graceful-restart\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'graceful_restart'), 't2'), 'level_1_wait_time')):
                pass
                yield '   graceful-restart t2 level-1 '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'graceful_restart'), 't2'), 'level_1_wait_time'))
                yield '\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'graceful_restart'), 't2'), 'level_2_wait_time')):
                pass
                yield '   graceful-restart t2 level-2 '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'graceful_restart'), 't2'), 'level_2_wait_time'))
                yield '\n'
            if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'graceful_restart'), 'restart_hold_time')):
                pass
                yield '   graceful-restart restart-hold-time '
                yield str(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'graceful_restart'), 'restart_hold_time'))
                yield '\n'
        if t_4(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication')):
            pass
            l_0_auth_keys = []
            context.vars['auth_keys'] = l_0_auth_keys
            context.exported_vars.add('auth_keys')
            l_0_both_key_ids = []
            context.vars['both_key_ids'] = l_0_both_key_ids
            context.exported_vars.add('both_key_ids')
            for l_1_auth_key in t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'key_ids'), []):
                l_1_dict = resolve('dict')
                l_1_details = missing
                _loop_vars = {}
                pass
                context.call(environment.getattr((undefined(name='both_key_ids') if l_0_both_key_ids is missing else l_0_both_key_ids), 'append'), environment.getattr(l_1_auth_key, 'id'), _loop_vars=_loop_vars)
                l_1_details = context.call((undefined(name='dict') if l_1_dict is missing else l_1_dict), l_1_auth_key, type='', _loop_vars=_loop_vars)
                _loop_vars['details'] = l_1_details
                context.call(environment.getattr((undefined(name='auth_keys') if l_0_auth_keys is missing else l_0_auth_keys), 'append'), (undefined(name='details') if l_1_details is missing else l_1_details), _loop_vars=_loop_vars)
            l_1_auth_key = l_1_dict = l_1_details = missing
            for l_1_auth_key in t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'key_ids'), []):
                l_1_dict = resolve('dict')
                l_1_details = resolve('details')
                _loop_vars = {}
                pass
                if (environment.getattr(l_1_auth_key, 'id') not in (undefined(name='both_key_ids') if l_0_both_key_ids is missing else l_0_both_key_ids)):
                    pass
                    l_1_details = context.call((undefined(name='dict') if l_1_dict is missing else l_1_dict), l_1_auth_key, type=' level-1', _loop_vars=_loop_vars)
                    _loop_vars['details'] = l_1_details
                    context.call(environment.getattr((undefined(name='auth_keys') if l_0_auth_keys is missing else l_0_auth_keys), 'append'), (undefined(name='details') if l_1_details is missing else l_1_details), _loop_vars=_loop_vars)
            l_1_auth_key = l_1_dict = l_1_details = missing
            for l_1_auth_key in t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'key_ids'), []):
                l_1_dict = resolve('dict')
                l_1_details = resolve('details')
                _loop_vars = {}
                pass
                if (environment.getattr(l_1_auth_key, 'id') not in (undefined(name='both_key_ids') if l_0_both_key_ids is missing else l_0_both_key_ids)):
                    pass
                    l_1_details = context.call((undefined(name='dict') if l_1_dict is missing else l_1_dict), l_1_auth_key, type=' level-2', _loop_vars=_loop_vars)
                    _loop_vars['details'] = l_1_details
                    context.call(environment.getattr((undefined(name='auth_keys') if l_0_auth_keys is missing else l_0_auth_keys), 'append'), (undefined(name='details') if l_1_details is missing else l_1_details), _loop_vars=_loop_vars)
            l_1_auth_key = l_1_dict = l_1_details = missing
            for l_1_auth_key in t_2((undefined(name='auth_keys') if l_0_auth_keys is missing else l_0_auth_keys), 'id'):
                _loop_vars = {}
                pass
                if ((t_4(environment.getattr(l_1_auth_key, 'algorithm')) and t_4(environment.getattr(l_1_auth_key, 'key_type'))) and t_4(environment.getattr(l_1_auth_key, 'key'))):
                    pass
                    if t_4(environment.getattr(l_1_auth_key, 'rfc_5310'), True):
                        pass
                        yield '   authentication key-id '
                        yield str(environment.getattr(l_1_auth_key, 'id'))
                        yield ' algorithm '
                        yield str(environment.getattr(l_1_auth_key, 'algorithm'))
                        yield ' rfc-5310 key '
                        yield str(environment.getattr(l_1_auth_key, 'key_type'))
                        yield ' '
                        yield str(environment.getattr(l_1_auth_key, 'key'))
                        yield str(environment.getattr(l_1_auth_key, 'type'))
                        yield '\n'
                    else:
                        pass
                        yield '   authentication key-id '
                        yield str(environment.getattr(l_1_auth_key, 'id'))
                        yield ' algorithm '
                        yield str(environment.getattr(l_1_auth_key, 'algorithm'))
                        yield ' key '
                        yield str(environment.getattr(l_1_auth_key, 'key_type'))
                        yield ' '
                        yield str(environment.getattr(l_1_auth_key, 'key'))
                        yield str(environment.getattr(l_1_auth_key, 'type'))
                        yield '\n'
            l_1_auth_key = missing
            if (t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'key_type')) and t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'key'))):
                pass
                yield '   authentication key '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'key_type'))
                yield ' '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'both'), 'key'))
                yield '\n'
            else:
                pass
                if (t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'key_type')) and t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'key'))):
                    pass
                    yield '   authentication key '
                    yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'key_type'))
                    yield ' '
                    yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_1'), 'key'))
                    yield ' level-1\n'
                if (t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'key_type')) and t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'key'))):
                    pass
                    yield '   authentication key '
                    yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'key_type'))
                    yield ' '
                    yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'authentication'), 'level_2'), 'key'))
                    yield ' level-2\n'
        yield '   !\n'
        if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'enabled'), True):
            pass
            yield '   address-family ipv4 unicast\n'
            if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'maximum_paths')):
                pass
                yield '      maximum-paths '
                yield str(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'maximum_paths'))
                yield '\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'tunnel_source_labeled_unicast'), 'enabled'), True):
                pass
                l_0_lu_cli = 'tunnel source-protocol bgp ipv4 labeled-unicast'
                context.vars['lu_cli'] = l_0_lu_cli
                context.exported_vars.add('lu_cli')
                if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'tunnel_source_labeled_unicast'), 'rcf')):
                    pass
                    l_0_lu_cli = str_join(((undefined(name='lu_cli') if l_0_lu_cli is missing else l_0_lu_cli), ' rcf ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'tunnel_source_labeled_unicast'), 'rcf'), ))
                    context.vars['lu_cli'] = l_0_lu_cli
                    context.exported_vars.add('lu_cli')
                yield '      '
                yield str((undefined(name='lu_cli') if l_0_lu_cli is missing else l_0_lu_cli))
                yield '\n'
            if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'bfd_all_interfaces'), True):
                pass
                yield '      bfd all-interfaces\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'fast_reroute_ti_lfa'), 'mode')):
                pass
                l_0_ti_lfa_cli = str_join(('fast-reroute ti-lfa mode ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'fast_reroute_ti_lfa'), 'mode'), ))
                context.vars['ti_lfa_cli'] = l_0_ti_lfa_cli
                context.exported_vars.add('ti_lfa_cli')
                if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'fast_reroute_ti_lfa'), 'level')):
                    pass
                    l_0_ti_lfa_cli = str_join(((undefined(name='ti_lfa_cli') if l_0_ti_lfa_cli is missing else l_0_ti_lfa_cli), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'fast_reroute_ti_lfa'), 'level'), ))
                    context.vars['ti_lfa_cli'] = l_0_ti_lfa_cli
                    context.exported_vars.add('ti_lfa_cli')
                yield '      '
                yield str((undefined(name='ti_lfa_cli') if l_0_ti_lfa_cli is missing else l_0_ti_lfa_cli))
                yield '\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'fast_reroute_ti_lfa'), 'srlg'), 'enable'), True):
                pass
                l_0_ti_lfa_srlg_cli = 'fast-reroute ti-lfa srlg'
                context.vars['ti_lfa_srlg_cli'] = l_0_ti_lfa_srlg_cli
                context.exported_vars.add('ti_lfa_srlg_cli')
                if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv4'), 'fast_reroute_ti_lfa'), 'srlg'), 'strict'), True):
                    pass
                    l_0_ti_lfa_srlg_cli = str_join(((undefined(name='ti_lfa_srlg_cli') if l_0_ti_lfa_srlg_cli is missing else l_0_ti_lfa_srlg_cli), ' strict', ))
                    context.vars['ti_lfa_srlg_cli'] = l_0_ti_lfa_srlg_cli
                    context.exported_vars.add('ti_lfa_srlg_cli')
                yield '      '
                yield str((undefined(name='ti_lfa_srlg_cli') if l_0_ti_lfa_srlg_cli is missing else l_0_ti_lfa_srlg_cli))
                yield '\n'
            yield '   !\n'
        if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv6'), 'enabled'), True):
            pass
            yield '   address-family ipv6 unicast\n'
            if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv6'), 'bfd_all_interfaces'), True):
                pass
                yield '      bfd all-interfaces\n'
            if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv6'), 'maximum_paths')):
                pass
                yield '      maximum-paths '
                yield str(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv6'), 'maximum_paths'))
                yield '\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv6'), 'fast_reroute_ti_lfa'), 'mode')):
                pass
                l_0_ti_lfa_cli = str_join(('fast-reroute ti-lfa mode ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv6'), 'fast_reroute_ti_lfa'), 'mode'), ))
                context.vars['ti_lfa_cli'] = l_0_ti_lfa_cli
                context.exported_vars.add('ti_lfa_cli')
                if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv6'), 'fast_reroute_ti_lfa'), 'level')):
                    pass
                    l_0_ti_lfa_cli = str_join(((undefined(name='ti_lfa_cli') if l_0_ti_lfa_cli is missing else l_0_ti_lfa_cli), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv6'), 'fast_reroute_ti_lfa'), 'level'), ))
                    context.vars['ti_lfa_cli'] = l_0_ti_lfa_cli
                    context.exported_vars.add('ti_lfa_cli')
                yield '      '
                yield str((undefined(name='ti_lfa_cli') if l_0_ti_lfa_cli is missing else l_0_ti_lfa_cli))
                yield '\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv6'), 'fast_reroute_ti_lfa'), 'srlg'), 'enable'), True):
                pass
                l_0_ti_lfa_srlg_cli = 'fast-reroute ti-lfa srlg'
                context.vars['ti_lfa_srlg_cli'] = l_0_ti_lfa_srlg_cli
                context.exported_vars.add('ti_lfa_srlg_cli')
                if t_4(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'address_family_ipv6'), 'fast_reroute_ti_lfa'), 'srlg'), 'strict'), True):
                    pass
                    l_0_ti_lfa_srlg_cli = str_join(((undefined(name='ti_lfa_srlg_cli') if l_0_ti_lfa_srlg_cli is missing else l_0_ti_lfa_srlg_cli), ' strict', ))
                    context.vars['ti_lfa_srlg_cli'] = l_0_ti_lfa_srlg_cli
                    context.exported_vars.add('ti_lfa_srlg_cli')
                yield '      '
                yield str((undefined(name='ti_lfa_srlg_cli') if l_0_ti_lfa_srlg_cli is missing else l_0_ti_lfa_srlg_cli))
                yield '\n'
            yield '   !\n'
        if t_4(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'segment_routing_mpls')):
            pass
            yield '   segment-routing mpls\n'
            if t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'segment_routing_mpls'), 'enabled'), True):
                pass
                yield '      no shutdown\n'
            elif t_4(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'segment_routing_mpls'), 'enabled'), False):
                pass
                yield '      shutdown\n'
            for l_1_prefix_segment in t_2(environment.getattr(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'segment_routing_mpls'), 'prefix_segments'), 'prefix'):
                _loop_vars = {}
                pass
                if t_4(environment.getattr(l_1_prefix_segment, 'index')):
                    pass
                    yield '      prefix-segment '
                    yield str(environment.getattr(l_1_prefix_segment, 'prefix'))
                    yield ' index '
                    yield str(environment.getattr(l_1_prefix_segment, 'index'))
                    yield '\n'
            l_1_prefix_segment = missing
        if t_4(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'eos_cli')):
            pass
            yield '   '
            yield str(t_3(environment.getattr((undefined(name='router_isis') if l_0_router_isis is missing else l_0_router_isis), 'eos_cli'), 3, False))
            yield '\n'

blocks = {}
debug_info = '7=46&9=49&10=51&11=54&13=56&14=59&16=61&17=64&19=66&20=69&22=71&24=74&27=77&30=80&31=84&32=86&33=88&34=90&35=92&36=94&38=96&39=98&41=99&42=101&43=103&44=105&46=106&47=108&48=110&49=112&52=114&53=116&55=119&57=122&58=124&59=127&64=132&65=134&66=137&67=139&68=142&69=144&70=146&72=151&75=155&77=157&80=160&81=162&82=165&83=167&84=170&86=173&87=175&88=178&89=180&92=184&94=186&95=189&97=191&100=194&101=197&103=199&104=202&106=204&107=206&108=209&109=211&110=214&111=216&114=220&116=222&117=225&119=227&125=229&126=232&127=234&128=237&129=239&130=242&132=245&133=247&135=251&137=255&143=257&144=260&145=262&146=265&147=267&148=270&150=273&151=275&153=279&155=281&161=283&162=286&163=288&164=291&165=293&166=296&168=299&169=301&171=305&174=307&175=309&178=312&179=315&181=317&182=320&184=322&185=325&188=327&189=329&190=332&191=335&192=340&193=341&194=343&196=345&197=350&198=352&199=354&202=356&203=361&204=363&205=365&208=367&209=370&212=372&213=375&215=387&219=397&220=400&222=406&223=409&225=413&226=416&231=421&233=424&234=427&236=429&237=431&238=434&239=436&241=440&243=442&246=445&247=447&248=450&249=452&251=456&253=458&254=460&255=463&256=465&258=469&262=472&264=475&267=478&268=481&270=483&271=485&272=488&273=490&275=494&277=496&278=498&279=501&280=503&282=507&286=510&288=513&290=516&293=519&294=522&295=525&299=530&300=533'