from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/monitor-loop-protection.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_monitor_loop_protection = resolve('monitor_loop_protection')
    try:
        t_1 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_1((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection)):
        pass
        yield '!\nmonitor loop-protection\n'
        if t_1(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'enabled'), True):
            pass
            yield '   no shutdown\n'
        elif t_1(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'enabled'), False):
            pass
            yield '   shutdown\n'
        if t_1(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'protect_vlan')):
            pass
            yield '   protect vlan '
            yield str(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'protect_vlan'))
            yield '\n'
        if t_1(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'rate_limit')):
            pass
            yield '   rate-limit '
            yield str(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'rate_limit'))
            yield '\n'
        if t_1(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'transmit_interval')):
            pass
            yield '   transmit-interval '
            yield str(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'transmit_interval'))
            yield '\n'
        if t_1(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'disabled_time')):
            pass
            yield '   disabled-time '
            yield str(environment.getattr((undefined(name='monitor_loop_protection') if l_0_monitor_loop_protection is missing else l_0_monitor_loop_protection), 'disabled_time'))
            yield '\n'

blocks = {}
debug_info = '7=18&10=21&12=24&15=27&16=30&18=32&19=35&21=37&22=40&24=42&25=45'