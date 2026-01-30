from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/monitor-link-flap-policy.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_monitor_link_flap_policy = resolve('monitor_link_flap_policy')
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
        t_3 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_3((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy)):
        pass
        yield '\n## Monitor Link-Flap\n'
        if t_3(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'damping_profiles')):
            pass
            yield '\n### Damping Link-Flap Profiles\n\n| Profile Name | Penalty Decay Half-Life | Penalty Decay Units | MAC Fault - Local Penalty | MAC Fault - Remote Penalty | Penalty Threshold Max | Penalty Threshold Reuse | Penalty Threshold Suppression |\n| ------------ | ----------------------- | ------------------- | ------------------------- | -------------------------- | --------------------- | ----------------------- | ---------------------------- |\n'
            for l_1_damping_profile in t_2(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'damping_profiles'), sort_key='name', ignore_case=False):
                _loop_vars = {}
                pass
                yield '| '
                yield str(environment.getattr(l_1_damping_profile, 'name'))
                yield ' | '
                yield str(t_1(environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_decay'), 'half_life'), '-'))
                yield ' | '
                yield str(t_1(environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_decay'), 'units'), '-'))
                yield ' | '
                yield str(t_1(environment.getattr(l_1_damping_profile, 'mac_fault_local_penalty'), '-'))
                yield ' | '
                yield str(t_1(environment.getattr(l_1_damping_profile, 'mac_fault_remote_penalty'), '-'))
                yield ' | '
                yield str(t_1(environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_threshold'), 'maximum'), '-'))
                yield ' | '
                yield str(t_1(environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_threshold'), 'reuse'), '-'))
                yield ' | '
                yield str(t_1(environment.getattr(environment.getattr(l_1_damping_profile, 'penalty_threshold'), 'suppression'), '-'))
                yield ' |\n'
            l_1_damping_profile = missing
        if t_3(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'max_flap_profiles')):
            pass
            yield '\n### Max Flap Link Profiles\n\n| Profile Name | Max Flaps | Time | Violations | Intervals |\n| ------------ | --------- | ---- | ---------- | --------- |\n'
            for l_1_max_flap_profile in t_2(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'max_flap_profiles'), sort_key='name', ignore_case=False):
                _loop_vars = {}
                pass
                yield '| '
                yield str(environment.getattr(l_1_max_flap_profile, 'name'))
                yield ' | '
                yield str(t_1(environment.getattr(l_1_max_flap_profile, 'max_flaps'), '-'))
                yield ' | '
                yield str(t_1(environment.getattr(l_1_max_flap_profile, 'time'), '-'))
                yield ' | '
                yield str(t_1(environment.getattr(l_1_max_flap_profile, 'violations'), '-'))
                yield ' | '
                yield str(t_1(environment.getattr(l_1_max_flap_profile, 'intervals'), '-'))
                yield ' |\n'
            l_1_max_flap_profile = missing
        if t_3(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'default_profiles')):
            pass
            yield '\n### Default Profiles\n\nNote that when multiple profiles are assigned, then the monitor is triggered when the conditions in any of the profiles is met.\n\n'
            for l_1_profile in t_2(environment.getattr((undefined(name='monitor_link_flap_policy') if l_0_monitor_link_flap_policy is missing else l_0_monitor_link_flap_policy), 'default_profiles')):
                _loop_vars = {}
                pass
                yield '- '
                yield str(l_1_profile)
                yield '\n'
            l_1_profile = missing
        yield '\n### Monitor Link Flap Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/monitor-link-flap-policy.j2', 'documentation/monitor-link-flap-policy.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=30&10=33&16=36&17=40&20=57&26=60&27=64&30=75&36=78&37=82&44=86'