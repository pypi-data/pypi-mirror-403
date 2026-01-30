from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/monitor-link-flap-policy.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_monitor_link_flap_policy = resolve('monitor_link_flap_policy')
    try:
        t_1 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_2 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
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
    if ((t_4(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'damping_profiles')) or t_4(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'max_flap_profiles'))) or t_4(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'default_profiles'))):
        pass
        yield '!\nmonitor link-flap policy\n'
        l_1_loop = missing
        for l_1_damping_profile, l_1_loop in LoopContext(t_1(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'damping_profiles'), sort_key='name', ignore_case=False), undefined):
            l_1_monitor_flap_cli = resolve('monitor_flap_cli')
            _loop_vars = {}
            pass
            yield '   profile '
            yield str(environment.getattr(l_1_damping_profile, 'name'))
            yield ' damping\n'
            if (t_4(environment.getattr(l_1_damping_profile, 'penalty_threshold')) and (t_3(environment.getattr(l_1_damping_profile, 'penalty_threshold')) > 0)):
                pass
                l_1_monitor_flap_cli = 'penalty threshold'
                _loop_vars['monitor_flap_cli'] = l_1_monitor_flap_cli
                if t_4(environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_threshold'), 'reuse')):
                    pass
                    l_1_monitor_flap_cli = str_join(((undefined(name='monitor_flap_cli') if l_1_monitor_flap_cli is missing else l_1_monitor_flap_cli), ' reuse ', environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_threshold'), 'reuse'), ))
                    _loop_vars['monitor_flap_cli'] = l_1_monitor_flap_cli
                if t_4(environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_threshold'), 'suppression')):
                    pass
                    l_1_monitor_flap_cli = str_join(((undefined(name='monitor_flap_cli') if l_1_monitor_flap_cli is missing else l_1_monitor_flap_cli), ' suppression ', environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_threshold'), 'suppression'), ))
                    _loop_vars['monitor_flap_cli'] = l_1_monitor_flap_cli
                if t_4(environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_threshold'), 'maximum')):
                    pass
                    l_1_monitor_flap_cli = str_join(((undefined(name='monitor_flap_cli') if l_1_monitor_flap_cli is missing else l_1_monitor_flap_cli), ' maximum ', environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_threshold'), 'maximum'), ))
                    _loop_vars['monitor_flap_cli'] = l_1_monitor_flap_cli
                yield '      '
                yield str((undefined(name='monitor_flap_cli') if l_1_monitor_flap_cli is missing else l_1_monitor_flap_cli))
                yield '\n'
            if t_4(environment.getattr(l_1_damping_profile, 'mac_fault_local_penalty')):
                pass
                yield '      penalty mac fault local '
                yield str(environment.getattr(l_1_damping_profile, 'mac_fault_local_penalty'))
                yield '\n'
            if t_4(environment.getattr(l_1_damping_profile, 'mac_fault_remote_penalty')):
                pass
                yield '      penalty mac fault remote '
                yield str(environment.getattr(l_1_damping_profile, 'mac_fault_remote_penalty'))
                yield '\n'
            if t_4(environment.getattr(l_1_damping_profile, 'penalty_decay')):
                pass
                yield '      penalty decay half-life '
                yield str(environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_decay'), 'half_life'))
                yield ' '
                yield str(environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_decay'), 'units'))
                yield '\n'
            if (not environment.getattr(l_1_loop, 'last')):
                pass
                yield '   !\n'
        l_1_loop = l_1_damping_profile = l_1_monitor_flap_cli = missing
        for l_1_max_flap_profile in t_1(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'max_flap_profiles'), sort_key='name', ignore_case=False):
            l_1_monitor_max_flap_cli = missing
            _loop_vars = {}
            pass
            l_1_monitor_max_flap_cli = str_join(('profile ', environment.getattr(l_1_max_flap_profile, 'name'), ' max-flaps ', environment.getattr(l_1_max_flap_profile, 'max_flaps'), ' time ', environment.getattr(l_1_max_flap_profile, 'time'), ))
            _loop_vars['monitor_max_flap_cli'] = l_1_monitor_max_flap_cli
            if (t_4(environment.getattr(l_1_max_flap_profile, 'violations')) and t_4(environment.getattr(l_1_max_flap_profile, 'intervals'))):
                pass
                l_1_monitor_max_flap_cli = str_join(((undefined(name='monitor_max_flap_cli') if l_1_monitor_max_flap_cli is missing else l_1_monitor_max_flap_cli), ' violations ', environment.getattr(l_1_max_flap_profile, 'violations'), ' intervals ', environment.getattr(l_1_max_flap_profile, 'intervals'), ))
                _loop_vars['monitor_max_flap_cli'] = l_1_monitor_max_flap_cli
            yield '   '
            yield str((undefined(name='monitor_max_flap_cli') if l_1_monitor_max_flap_cli is missing else l_1_monitor_max_flap_cli))
            yield '\n'
        l_1_max_flap_profile = l_1_monitor_max_flap_cli = missing
        if t_4(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'default_profiles')):
            pass
            yield '   default-profiles '
            yield str(t_2(context.eval_ctx, t_1(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'default_profiles'), ignore_case=False), ' '))
            yield '\n'

blocks = {}
debug_info = '7=36&10=40&11=45&12=47&13=49&14=51&15=53&17=55&18=57&20=59&21=61&23=64&25=66&26=69&28=71&29=74&31=76&32=79&34=83&38=87&39=91&40=93&41=95&43=98&45=101&46=104'