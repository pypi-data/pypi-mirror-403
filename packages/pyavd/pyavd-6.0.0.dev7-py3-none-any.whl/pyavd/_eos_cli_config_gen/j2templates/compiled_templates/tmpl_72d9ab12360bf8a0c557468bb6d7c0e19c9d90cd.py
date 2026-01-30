from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/router-multicast.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_router_multicast = resolve('router_multicast')
    try:
        t_1 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_2 = environment.filters['list']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'list' found.")
    try:
        t_3 = environment.filters['rejectattr']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'rejectattr' found.")
    try:
        t_4 = environment.filters['selectattr']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No filter named 'selectattr' found.")
    try:
        t_5 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_5(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_5((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast)):
        pass
        yield '!\nrouter multicast\n'
        if t_5(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv4')):
            pass
            yield '   ipv4\n'
            for l_1_rpf_route in t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv4'), 'rpf'), 'routes'), 'source_prefix'):
                l_1_dest_with_dis = l_1_default_dest = missing
                _loop_vars = {}
                pass
                l_1_dest_with_dis = t_2(context.eval_ctx, t_4(context, t_1(environment.getattr(l_1_rpf_route, 'destinations'), sort_key='nexthop'), 'distance', 'arista.avd.defined'))
                _loop_vars['dest_with_dis'] = l_1_dest_with_dis
                l_1_default_dest = t_2(context.eval_ctx, t_3(context, t_1(environment.getattr(l_1_rpf_route, 'destinations'), sort_key='nexthop'), 'distance', 'arista.avd.defined'))
                _loop_vars['default_dest'] = l_1_default_dest
                for l_2_destination in (undefined(name='default_dest') if l_1_default_dest is missing else l_1_default_dest):
                    _loop_vars = {}
                    pass
                    yield '      rpf route '
                    yield str(environment.getattr(l_1_rpf_route, 'source_prefix'))
                    yield ' '
                    yield str(environment.getattr(l_2_destination, 'nexthop'))
                    yield '\n'
                l_2_destination = missing
                for l_2_destination in (undefined(name='dest_with_dis') if l_1_dest_with_dis is missing else l_1_dest_with_dis):
                    _loop_vars = {}
                    pass
                    yield '      rpf route '
                    yield str(environment.getattr(l_1_rpf_route, 'source_prefix'))
                    yield ' '
                    yield str(environment.getattr(l_2_destination, 'nexthop'))
                    yield ' '
                    yield str(environment.getattr(l_2_destination, 'distance'))
                    yield '\n'
                l_2_destination = missing
            l_1_rpf_route = l_1_dest_with_dis = l_1_default_dest = missing
            if t_5(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv4'), 'counters'), 'rate_period_decay')):
                pass
                yield '      counters rate period decay '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv4'), 'counters'), 'rate_period_decay'))
                yield ' seconds\n'
            if t_5(environment.getattr(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv4'), 'activity_polling_interval')):
                pass
                yield '      activity polling-interval '
                yield str(environment.getattr(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv4'), 'activity_polling_interval'))
                yield '\n'
            if t_5(environment.getattr(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv4'), 'routing'), True):
                pass
                yield '      routing\n'
            if t_5(environment.getattr(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv4'), 'multipath')):
                pass
                yield '      multipath '
                yield str(environment.getattr(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv4'), 'multipath'))
                yield '\n'
            if t_5(environment.getattr(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv4'), 'software_forwarding')):
                pass
                yield '      software-forwarding '
                yield str(environment.getattr(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv4'), 'software_forwarding'))
                yield '\n'
        if t_5(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv6')):
            pass
            yield '   !\n   ipv6\n'
            if t_5(environment.getattr(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv6'), 'activity_polling_interval')):
                pass
                yield '      activity polling-interval '
                yield str(environment.getattr(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'ipv6'), 'activity_polling_interval'))
                yield '\n'
        for l_1_vrf in t_1(environment.getattr((undefined(name='router_multicast') if l_0_router_multicast is missing else l_0_router_multicast), 'vrfs'), 'name', ignore_case=False):
            _loop_vars = {}
            pass
            yield '   !\n   vrf '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield '\n'
            if t_5(environment.getattr(l_1_vrf, 'ipv4')):
                pass
                yield '      ipv4\n'
            if t_5(environment.getattr(environment.getattr(l_1_vrf, 'ipv4'), 'routing'), True):
                pass
                yield '         routing\n'
        l_1_vrf = missing

blocks = {}
debug_info = '7=42&10=45&12=48&13=52&14=54&15=56&16=60&18=65&19=69&22=77&23=80&25=82&26=85&28=87&31=90&32=93&34=95&35=98&38=100&41=103&42=106&45=108&47=112&48=114&51=117'