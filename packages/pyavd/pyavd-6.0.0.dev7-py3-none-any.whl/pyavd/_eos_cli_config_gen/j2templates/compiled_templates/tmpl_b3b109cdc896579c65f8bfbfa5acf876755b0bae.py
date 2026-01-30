from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/monitor-loop-protection.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_monitor_loop_protection = resolve('monitor_loop_protection')
    l_0_enabled = resolve('enabled')
    l_0_disabled_time = resolve('disabled_time')
    l_0_protect_vlan = resolve('protect_vlan')
    l_0_rate_limit = resolve('rate_limit')
    l_0_transmit_interval = resolve('transmit_interval')
    l_0_ethernet_interfaces = resolve('ethernet_interfaces')
    l_0_disabled_interfaces = resolve('disabled_interfaces')
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
        t_3 = environment.filters['default']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'default' found.")
    try:
        t_4 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
    try:
        t_5 = environment.filters['map']
    except KeyError:
        @internalcode
        def t_5(*unused):
            raise TemplateRuntimeError("No filter named 'map' found.")
    try:
        t_6 = environment.filters['selectattr']
    except KeyError:
        @internalcode
        def t_6(*unused):
            raise TemplateRuntimeError("No filter named 'selectattr' found.")
    try:
        t_7 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_7(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_7((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection)):
        pass
        yield '\n## Monitor Loop Protection\n\n'
        l_0_enabled = t_1(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'enabled'), '-')
        context.vars['enabled'] = l_0_enabled
        context.exported_vars.add('enabled')
        l_0_disabled_time = t_1(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'disabled_time'), '-')
        context.vars['disabled_time'] = l_0_disabled_time
        context.exported_vars.add('disabled_time')
        l_0_protect_vlan = t_1(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'protect_vlan'), '-')
        context.vars['protect_vlan'] = l_0_protect_vlan
        context.exported_vars.add('protect_vlan')
        l_0_rate_limit = t_1(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'rate_limit'), '-')
        context.vars['rate_limit'] = l_0_rate_limit
        context.exported_vars.add('rate_limit')
        l_0_transmit_interval = t_1(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'transmit_interval'), '-')
        context.vars['transmit_interval'] = l_0_transmit_interval
        context.exported_vars.add('transmit_interval')
        l_0_disabled_interfaces = t_3(t_4(context.eval_ctx, t_2(t_5(context, t_6(context, t_1((undefined(name='ethernet_interfaces') if l_0_ethernet_interfaces is missing else l_0_ethernet_interfaces), []), 'loop_protection', 'arista.avd.defined', False), attribute='name')), '<br/>'), '-', True)
        context.vars['disabled_interfaces'] = l_0_disabled_interfaces
        context.exported_vars.add('disabled_interfaces')
        yield '| Enabled | Disabled-time | Protect vlan | Rate-limit | Transmit-interval | Disabled Interfaces |\n| ------- | ------------- | ------------ | ---------- | ----------------- | ------------------- |\n| '
        yield str((undefined(name='enabled') if l_0_enabled is missing else l_0_enabled))
        yield ' | '
        yield str((undefined(name='disabled_time') if l_0_disabled_time is missing else l_0_disabled_time))
        yield ' | '
        yield str((undefined(name='protect_vlan') if l_0_protect_vlan is missing else l_0_protect_vlan))
        yield ' | '
        yield str((undefined(name='rate_limit') if l_0_rate_limit is missing else l_0_rate_limit))
        yield ' | '
        yield str((undefined(name='transmit_interval') if l_0_transmit_interval is missing else l_0_transmit_interval))
        yield ' | '
        yield str((undefined(name='disabled_interfaces') if l_0_disabled_interfaces is missing else l_0_disabled_interfaces))
        yield ' |\n\n### Monitor Loop Protection Configuration\n\n```eos ####\n'
        template = environment.get_template('eos/monitor-loop-protection.j2', 'documentation/monitor-loop-protection.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {'disabled_interfaces': l_0_disabled_interfaces, 'disabled_time': l_0_disabled_time, 'enabled': l_0_enabled, 'protect_vlan': l_0_protect_vlan, 'rate_limit': l_0_rate_limit, 'transmit_interval': l_0_transmit_interval}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=61&11=64&12=67&13=70&14=73&15=76&16=79&19=83&24=95'