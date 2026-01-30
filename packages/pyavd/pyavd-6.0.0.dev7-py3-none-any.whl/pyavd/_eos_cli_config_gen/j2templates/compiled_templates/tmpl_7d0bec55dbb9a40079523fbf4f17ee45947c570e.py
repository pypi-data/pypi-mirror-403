from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/ethernet-interfaces.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_ethernet_interfaces = resolve('ethernet_interfaces')
    l_0_POE_CLASS_MAP = missing
    try:
        t_1 = environment.filters['arista.avd.default']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.default' found.")
    try:
        t_2 = environment.filters['arista.avd.hide_passwords']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.hide_passwords' found.")
    try:
        t_3 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_4 = environment.filters['arista.avd.range_expand']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.range_expand' found.")
    try:
        t_5 = environment.filters['float']
    except KeyError:
        @internalcode
        def t_5(*unused):
            raise TemplateRuntimeError("No filter named 'float' found.")
    try:
        t_6 = environment.filters['format']
    except KeyError:
        @internalcode
        def t_6(*unused):
            raise TemplateRuntimeError("No filter named 'format' found.")
    try:
        t_7 = environment.filters['indent']
    except KeyError:
        @internalcode
        def t_7(*unused):
            raise TemplateRuntimeError("No filter named 'indent' found.")
    try:
        t_8 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_8(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
    try:
        t_9 = environment.filters['list']
    except KeyError:
        @internalcode
        def t_9(*unused):
            raise TemplateRuntimeError("No filter named 'list' found.")
    try:
        t_10 = environment.filters['rejectattr']
    except KeyError:
        @internalcode
        def t_10(*unused):
            raise TemplateRuntimeError("No filter named 'rejectattr' found.")
    try:
        t_11 = environment.filters['replace']
    except KeyError:
        @internalcode
        def t_11(*unused):
            raise TemplateRuntimeError("No filter named 'replace' found.")
    try:
        t_12 = environment.filters['selectattr']
    except KeyError:
        @internalcode
        def t_12(*unused):
            raise TemplateRuntimeError("No filter named 'selectattr' found.")
    try:
        t_13 = environment.filters['sort']
    except KeyError:
        @internalcode
        def t_13(*unused):
            raise TemplateRuntimeError("No filter named 'sort' found.")
    try:
        t_14 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_14(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    l_0_POE_CLASS_MAP = {0: '15.40', 1: '4.00', 2: '7.00', 3: '15.40', 4: '30.00', 5: '45.00', 6: '60.00', 7: '75.00', 8: '90.00'}
    context.vars['POE_CLASS_MAP'] = l_0_POE_CLASS_MAP
    context.exported_vars.add('POE_CLASS_MAP')
    for l_1_ethernet_interface in t_3((undefined(name='ethernet_interfaces') if l_0_ethernet_interfaces is missing else l_0_ethernet_interfaces), sort_key='name'):
        l_1_encapsulation_dot1q_cli = resolve('encapsulation_dot1q_cli')
        l_1_client_encapsulation = resolve('client_encapsulation')
        l_1_network_flag = resolve('network_flag')
        l_1_encapsulation_cli = resolve('encapsulation_cli')
        l_1_network_encapsulation = resolve('network_encapsulation')
        l_1_address_locking_cli = resolve('address_locking_cli')
        l_1_dfe_algo_cli = resolve('dfe_algo_cli')
        l_1_dfe_hold_time_cli = resolve('dfe_hold_time_cli')
        l_1_non_default_vrf = resolve('non_default_vrf')
        l_1_default_vrf = resolve('default_vrf')
        l_1_host_proxy_cli = resolve('host_proxy_cli')
        l_1_tcp_mss_ceiling_cli = resolve('tcp_mss_ceiling_cli')
        l_1_interface_ip_nat = resolve('interface_ip_nat')
        l_1_hide_passwords = resolve('hide_passwords')
        l_1_poe_link_down_action_cli = resolve('poe_link_down_action_cli')
        l_1_poe_limit_cli = resolve('poe_limit_cli')
        l_1_sorted_vlans_cli = resolve('sorted_vlans_cli')
        l_1_isis_auth_cli = resolve('isis_auth_cli')
        l_1_both_key_ids = resolve('both_key_ids')
        l_1_rate_limit_count = resolve('rate_limit_count')
        l_1_backup_link_cli = resolve('backup_link_cli')
        l_1_tap_identity_cli = resolve('tap_identity_cli')
        l_1_tap_mac_address_cli = resolve('tap_mac_address_cli')
        l_1_tap_truncation_cli = resolve('tap_truncation_cli')
        l_1_tool_groups = resolve('tool_groups')
        l_1_frequency_cli = resolve('frequency_cli')
        l_1_aaa_config = resolve('aaa_config')
        l_1_actions = resolve('actions')
        l_1_host_mode_cli = resolve('host_mode_cli')
        l_1_auth_cli = resolve('auth_cli')
        l_1_auth_failure_fallback_mba = resolve('auth_failure_fallback_mba')
        _loop_vars = {}
        pass
        yield '!\ninterface '
        yield str(environment.getattr(l_1_ethernet_interface, 'name'))
        yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'comment')):
            pass
            for l_2_comment_line in t_1(context.call(environment.getattr(environment.getattr(l_1_ethernet_interface, 'comment'), 'splitlines'), _loop_vars=_loop_vars), []):
                _loop_vars = {}
                pass
                yield '   !! '
                yield str(l_2_comment_line)
                yield '\n'
            l_2_comment_line = missing
        if t_14(environment.getattr(l_1_ethernet_interface, 'profile')):
            pass
            yield '   profile '
            yield str(environment.getattr(l_1_ethernet_interface, 'profile'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'description')):
            pass
            yield '   description '
            yield str(environment.getattr(l_1_ethernet_interface, 'description'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'shutdown'), True):
            pass
            yield '   shutdown\n'
        elif t_14(environment.getattr(l_1_ethernet_interface, 'shutdown'), False):
            pass
            yield '   no shutdown\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'load_interval')):
            pass
            yield '   load-interval '
            yield str(environment.getattr(l_1_ethernet_interface, 'load_interval'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'mtu')):
            pass
            yield '   mtu '
            yield str(environment.getattr(l_1_ethernet_interface, 'mtu'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'logging'), 'event'), 'link_status'), True):
            pass
            yield '   logging event link-status\n'
        elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'logging'), 'event'), 'link_status'), False):
            pass
            yield '   no logging event link-status\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_policy'), 'input')):
            pass
            yield '   traffic-policy input '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_policy'), 'input'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_policy'), 'output')):
            pass
            yield '   traffic-policy output '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_policy'), 'output'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'bgp'), 'session_tracker')):
            pass
            yield '   bgp session tracker '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'bgp'), 'session_tracker'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'l2_protocol'), 'forwarding_profile')):
            pass
            yield '   l2-protocol forwarding profile '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'l2_protocol'), 'forwarding_profile'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'flowcontrol'), 'received')):
            pass
            yield '   flowcontrol receive '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'flowcontrol'), 'received'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'l2_mtu')):
            pass
            yield '   l2 mtu '
            yield str(environment.getattr(l_1_ethernet_interface, 'l2_mtu'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'l2_mru')):
            pass
            yield '   l2 mru '
            yield str(environment.getattr(l_1_ethernet_interface, 'l2_mru'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'logging'), 'event'), 'congestion_drops'), True):
            pass
            yield '   logging event congestion-drops\n'
        elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'logging'), 'event'), 'congestion_drops'), False):
            pass
            yield '   no logging event congestion-drops\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'speed')):
            pass
            yield '   speed '
            yield str(environment.getattr(l_1_ethernet_interface, 'speed'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'error_correction_encoding'), 'enabled'), False):
            pass
            yield '   no error-correction encoding\n'
        else:
            pass
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'error_correction_encoding'), 'fire_code'), True):
                pass
                yield '   error-correction encoding fire-code\n'
            elif t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'error_correction_encoding'), 'fire_code'), False):
                pass
                yield '   no error-correction encoding fire-code\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'error_correction_encoding'), 'reed_solomon'), True):
                pass
                yield '   error-correction encoding reed-solomon\n'
            elif t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'error_correction_encoding'), 'reed_solomon'), False):
                pass
                yield '   no error-correction encoding reed-solomon\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'trunk'), 'private_vlan_secondary'), True):
            pass
            yield '   switchport trunk private-vlan secondary\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'pvlan_mapping')):
            pass
            yield '   switchport pvlan mapping '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'pvlan_mapping'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'access_vlan')):
            pass
            yield '   switchport access vlan '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'access_vlan'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'trunk'), 'native_vlan_tag'), True):
            pass
            yield '   switchport trunk native vlan tag\n'
        elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'trunk'), 'native_vlan')):
            pass
            yield '   switchport trunk native vlan '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'trunk'), 'native_vlan'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'phone'), 'vlan')):
            pass
            yield '   switchport phone vlan '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'phone'), 'vlan'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'phone'), 'trunk')):
            pass
            yield '   switchport phone trunk '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'phone'), 'trunk'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'vlan_translations'), 'in_required'), True):
            pass
            yield '   switchport vlan translation in required\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'vlan_translations'), 'out_required'), True):
            pass
            yield '   switchport vlan translation out required\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'dot1q'), 'vlan_tag')):
            pass
            yield '   switchport dot1q vlan tag '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'dot1q'), 'vlan_tag'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'trunk'), 'allowed_vlan')):
            pass
            yield '   switchport trunk allowed vlan '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'trunk'), 'allowed_vlan'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'mode')):
            pass
            yield '   switchport mode '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'mode'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'dot1q'), 'ethertype')):
            pass
            yield '   switchport dot1q ethertype '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'dot1q'), 'ethertype'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'vlan_forwarding_accept_all'), True):
            pass
            yield '   switchport vlan forwarding accept all\n'
        for l_2_trunk_group in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'trunk'), 'groups'), ignore_case=False):
            _loop_vars = {}
            pass
            yield '   switchport trunk group '
            yield str(l_2_trunk_group)
            yield '\n'
        l_2_trunk_group = missing
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'enabled'), True):
            pass
            yield '   switchport\n'
        elif t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'enabled'), False):
            pass
            yield '   no switchport\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_dot1q'), 'vlan')):
            pass
            l_1_encapsulation_dot1q_cli = str_join(('encapsulation dot1q vlan ', environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_dot1q'), 'vlan'), ))
            _loop_vars['encapsulation_dot1q_cli'] = l_1_encapsulation_dot1q_cli
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_dot1q'), 'inner_vlan')):
                pass
                l_1_encapsulation_dot1q_cli = str_join(((undefined(name='encapsulation_dot1q_cli') if l_1_encapsulation_dot1q_cli is missing else l_1_encapsulation_dot1q_cli), ' inner ', environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_dot1q'), 'inner_vlan'), ))
                _loop_vars['encapsulation_dot1q_cli'] = l_1_encapsulation_dot1q_cli
            yield '   '
            yield str((undefined(name='encapsulation_dot1q_cli') if l_1_encapsulation_dot1q_cli is missing else l_1_encapsulation_dot1q_cli))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'vlan_id')):
            pass
            yield '   vlan id '
            yield str(environment.getattr(l_1_ethernet_interface, 'vlan_id'))
            yield '\n'
        if (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'encapsulation')) and (not t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_dot1q'), 'vlan')))):
            pass
            l_1_client_encapsulation = environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'encapsulation')
            _loop_vars['client_encapsulation'] = l_1_client_encapsulation
            l_1_network_flag = False
            _loop_vars['network_flag'] = l_1_network_flag
            if ((undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation) in ['dot1q', 'dot1ad']):
                pass
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'vlan')):
                    pass
                    l_1_encapsulation_cli = str_join(('client ', (undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation), ' ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'vlan'), ))
                    _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                elif (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'outer_vlan')) and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'inner_vlan'))):
                    pass
                    if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'inner_encapsulation')):
                        pass
                        l_1_encapsulation_cli = str_join(('client ', (undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation), ' outer ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'outer_vlan'), ' inner ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'inner_encapsulation'), ' ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'inner_vlan'), ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    else:
                        pass
                        l_1_encapsulation_cli = str_join(('client ', (undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation), ' outer ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'outer_vlan'), ' inner ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'inner_vlan'), ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    if (t_1(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'encapsulation')) == 'client inner'):
                        pass
                        l_1_network_flag = True
                        _loop_vars['network_flag'] = l_1_network_flag
                        l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' network ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'encapsulation'), ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
            elif ((undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation) in ['untagged', 'unmatched']):
                pass
                l_1_encapsulation_cli = str_join(('client ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'client'), 'encapsulation'), ))
                _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
            if t_14((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli)):
                pass
                if ((((undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation) in ['dot1q', 'dot1ad', 'untagged']) and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'encapsulation'))) and (not (undefined(name='network_flag') if l_1_network_flag is missing else l_1_network_flag))):
                    pass
                    l_1_network_encapsulation = environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'encapsulation')
                    _loop_vars['network_encapsulation'] = l_1_network_encapsulation
                    if ((undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation) in ['dot1q', 'dot1ad']):
                        pass
                        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'vlan')):
                            pass
                            l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' network ', (undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation), ' ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'vlan'), ))
                            _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                        elif (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'outer_vlan')) and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'inner_vlan'))):
                            pass
                            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'inner_encapsulation')):
                                pass
                                l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' network ', (undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation), ' outer ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'outer_vlan'), ' inner ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'inner_encapsulation'), ' ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'inner_vlan'), ))
                                _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                            else:
                                pass
                                l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' network ', (undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation), ' outer ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'outer_vlan'), ' inner ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'encapsulation_vlan'), 'network'), 'inner_vlan'), ))
                                _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    elif (((undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation) == 'untagged') and ((undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation) == 'untagged')):
                        pass
                        l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' network untagged', ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    elif (((undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation) == 'client') and ((undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation) != 'untagged')):
                        pass
                        l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' network client', ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                yield '   encapsulation vlan\n      '
                yield str((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli))
                yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'source_interface')):
            pass
            yield '   switchport source-interface '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'source_interface'))
            yield '\n'
        for l_2_vlan_translation in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'vlan_translations'), 'direction_both'), sort_key='from'):
            l_2_vlan_translation_both_cli = missing
            _loop_vars = {}
            pass
            l_2_vlan_translation_both_cli = str_join(('switchport vlan translation ', environment.getattr(l_2_vlan_translation, 'from'), ))
            _loop_vars['vlan_translation_both_cli'] = l_2_vlan_translation_both_cli
            if t_14(environment.getattr(l_2_vlan_translation, 'dot1q_tunnel'), True):
                pass
                l_2_vlan_translation_both_cli = str_join(((undefined(name='vlan_translation_both_cli') if l_2_vlan_translation_both_cli is missing else l_2_vlan_translation_both_cli), ' dot1q-tunnel', ))
                _loop_vars['vlan_translation_both_cli'] = l_2_vlan_translation_both_cli
            elif t_14(environment.getattr(l_2_vlan_translation, 'inner_vlan_from')):
                pass
                l_2_vlan_translation_both_cli = str_join(((undefined(name='vlan_translation_both_cli') if l_2_vlan_translation_both_cli is missing else l_2_vlan_translation_both_cli), ' inner ', environment.getattr(l_2_vlan_translation, 'inner_vlan_from'), ))
                _loop_vars['vlan_translation_both_cli'] = l_2_vlan_translation_both_cli
                if t_14(environment.getattr(l_2_vlan_translation, 'network'), True):
                    pass
                    l_2_vlan_translation_both_cli = str_join(((undefined(name='vlan_translation_both_cli') if l_2_vlan_translation_both_cli is missing else l_2_vlan_translation_both_cli), ' network', ))
                    _loop_vars['vlan_translation_both_cli'] = l_2_vlan_translation_both_cli
            l_2_vlan_translation_both_cli = str_join(((undefined(name='vlan_translation_both_cli') if l_2_vlan_translation_both_cli is missing else l_2_vlan_translation_both_cli), ' ', environment.getattr(l_2_vlan_translation, 'to'), ))
            _loop_vars['vlan_translation_both_cli'] = l_2_vlan_translation_both_cli
            yield '   '
            yield str((undefined(name='vlan_translation_both_cli') if l_2_vlan_translation_both_cli is missing else l_2_vlan_translation_both_cli))
            yield '\n'
        l_2_vlan_translation = l_2_vlan_translation_both_cli = missing
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'vlan_translations'), 'direction_in')):
            pass
            for l_2_vlan_translation in environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'vlan_translations'), 'direction_in'):
                l_2_vlan_translation_in_cli = missing
                _loop_vars = {}
                pass
                l_2_vlan_translation_in_cli = str_join(('switchport vlan translation in ', environment.getattr(l_2_vlan_translation, 'from'), ))
                _loop_vars['vlan_translation_in_cli'] = l_2_vlan_translation_in_cli
                if t_14(environment.getattr(l_2_vlan_translation, 'dot1q_tunnel'), True):
                    pass
                    l_2_vlan_translation_in_cli = str_join(((undefined(name='vlan_translation_in_cli') if l_2_vlan_translation_in_cli is missing else l_2_vlan_translation_in_cli), ' dot1q-tunnel', ))
                    _loop_vars['vlan_translation_in_cli'] = l_2_vlan_translation_in_cli
                elif t_14(environment.getattr(l_2_vlan_translation, 'inner_vlan_from')):
                    pass
                    l_2_vlan_translation_in_cli = str_join(((undefined(name='vlan_translation_in_cli') if l_2_vlan_translation_in_cli is missing else l_2_vlan_translation_in_cli), ' inner ', environment.getattr(l_2_vlan_translation, 'inner_vlan_from'), ))
                    _loop_vars['vlan_translation_in_cli'] = l_2_vlan_translation_in_cli
                l_2_vlan_translation_in_cli = str_join(((undefined(name='vlan_translation_in_cli') if l_2_vlan_translation_in_cli is missing else l_2_vlan_translation_in_cli), ' ', environment.getattr(l_2_vlan_translation, 'to'), ))
                _loop_vars['vlan_translation_in_cli'] = l_2_vlan_translation_in_cli
                yield '   '
                yield str((undefined(name='vlan_translation_in_cli') if l_2_vlan_translation_in_cli is missing else l_2_vlan_translation_in_cli))
                yield '\n'
            l_2_vlan_translation = l_2_vlan_translation_in_cli = missing
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'vlan_translations'), 'direction_out')):
            pass
            for l_2_vlan_translation in environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'vlan_translations'), 'direction_out'):
                l_2_vlan_translation_out_cli = resolve('vlan_translation_out_cli')
                _loop_vars = {}
                pass
                if t_14(environment.getattr(l_2_vlan_translation, 'dot1q_tunnel_to')):
                    pass
                    l_2_vlan_translation_out_cli = str_join(('switchport vlan translation out ', environment.getattr(l_2_vlan_translation, 'from'), ' dot1q-tunnel ', environment.getattr(l_2_vlan_translation, 'dot1q_tunnel_to'), ))
                    _loop_vars['vlan_translation_out_cli'] = l_2_vlan_translation_out_cli
                elif t_14(environment.getattr(l_2_vlan_translation, 'to')):
                    pass
                    l_2_vlan_translation_out_cli = str_join(('switchport vlan translation out ', environment.getattr(l_2_vlan_translation, 'from'), ' ', environment.getattr(l_2_vlan_translation, 'to'), ))
                    _loop_vars['vlan_translation_out_cli'] = l_2_vlan_translation_out_cli
                    if t_14(environment.getattr(l_2_vlan_translation, 'inner_vlan_to')):
                        pass
                        l_2_vlan_translation_out_cli = str_join(((undefined(name='vlan_translation_out_cli') if l_2_vlan_translation_out_cli is missing else l_2_vlan_translation_out_cli), ' inner ', environment.getattr(l_2_vlan_translation, 'inner_vlan_to'), ))
                        _loop_vars['vlan_translation_out_cli'] = l_2_vlan_translation_out_cli
                if t_14((undefined(name='vlan_translation_out_cli') if l_2_vlan_translation_out_cli is missing else l_2_vlan_translation_out_cli)):
                    pass
                    yield '   '
                    yield str((undefined(name='vlan_translation_out_cli') if l_2_vlan_translation_out_cli is missing else l_2_vlan_translation_out_cli))
                    yield '\n'
            l_2_vlan_translation = l_2_vlan_translation_out_cli = missing
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'l2_protocol'), 'encapsulation_dot1q_vlan')):
            pass
            yield '   l2-protocol encapsulation dot1q vlan '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'l2_protocol'), 'encapsulation_dot1q_vlan'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'mac_timestamp')):
            pass
            yield '   mac timestamp '
            yield str(environment.getattr(l_1_ethernet_interface, 'mac_timestamp'))
            yield '\n'
        if ((t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'address_locking'), 'address_family'), 'ipv4')) or t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'address_locking'), 'address_family'), 'ipv6'))) or t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'address_locking'), 'ipv4_enforcement_disabled'), True)):
            pass
            yield '   !\n   address locking\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'address_locking'), 'address_family'), 'ipv4'), True):
                pass
                yield '      address-family ipv4\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'address_locking'), 'address_family'), 'ipv6'), True):
                pass
                yield '      address-family ipv6\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'address_locking'), 'address_family'), 'ipv4'), False):
                pass
                yield '      address-family ipv4 disabled\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'address_locking'), 'address_family'), 'ipv6'), False):
                pass
                yield '      address-family ipv6 disabled\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'address_locking'), 'ipv4_enforcement_disabled'), True):
                pass
                yield '      locked-address ipv4 enforcement disabled\n'
        elif (t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'address_locking'), 'ipv4'), True) or t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'address_locking'), 'ipv6'), True)):
            pass
            l_1_address_locking_cli = 'address locking'
            _loop_vars['address_locking_cli'] = l_1_address_locking_cli
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'address_locking'), 'ipv4'), True):
                pass
                l_1_address_locking_cli = ((undefined(name='address_locking_cli') if l_1_address_locking_cli is missing else l_1_address_locking_cli) + ' ipv4')
                _loop_vars['address_locking_cli'] = l_1_address_locking_cli
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'address_locking'), 'ipv6'), True):
                pass
                l_1_address_locking_cli = ((undefined(name='address_locking_cli') if l_1_address_locking_cli is missing else l_1_address_locking_cli) + ' ipv6')
                _loop_vars['address_locking_cli'] = l_1_address_locking_cli
            yield '   '
            yield str((undefined(name='address_locking_cli') if l_1_address_locking_cli is missing else l_1_address_locking_cli))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment')):
            pass
            yield '   !\n   evpn ethernet-segment\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'identifier')):
                pass
                yield '      identifier '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'identifier'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'redundancy')):
                pass
                yield '      redundancy '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'redundancy'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election')):
                pass
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'algorithm'), 'modulus'):
                    pass
                    yield '      designated-forwarder election algorithm modulus\n'
                elif (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'algorithm'), 'preference') and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'preference_value'))):
                    pass
                    l_1_dfe_algo_cli = str_join(('designated-forwarder election algorithm preference ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'preference_value'), ))
                    _loop_vars['dfe_algo_cli'] = l_1_dfe_algo_cli
                    if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'dont_preempt'), True):
                        pass
                        l_1_dfe_algo_cli = str_join(((undefined(name='dfe_algo_cli') if l_1_dfe_algo_cli is missing else l_1_dfe_algo_cli), ' dont-preempt', ))
                        _loop_vars['dfe_algo_cli'] = l_1_dfe_algo_cli
                    yield '      '
                    yield str((undefined(name='dfe_algo_cli') if l_1_dfe_algo_cli is missing else l_1_dfe_algo_cli))
                    yield '\n'
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'hold_time')):
                    pass
                    l_1_dfe_hold_time_cli = str_join(('designated-forwarder election hold-time ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'hold_time'), ))
                    _loop_vars['dfe_hold_time_cli'] = l_1_dfe_hold_time_cli
                    if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'subsequent_hold_time')):
                        pass
                        l_1_dfe_hold_time_cli = str_join(((undefined(name='dfe_hold_time_cli') if l_1_dfe_hold_time_cli is missing else l_1_dfe_hold_time_cli), ' subsequent-hold-time ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'subsequent_hold_time'), ))
                        _loop_vars['dfe_hold_time_cli'] = l_1_dfe_hold_time_cli
                    yield '      '
                    yield str((undefined(name='dfe_hold_time_cli') if l_1_dfe_hold_time_cli is missing else l_1_dfe_hold_time_cli))
                    yield '\n'
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'candidate_reachability_required'), True):
                    pass
                    yield '      designated-forwarder election candidate reachability required\n'
                elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'candidate_reachability_required'), False):
                    pass
                    yield '      no designated-forwarder election candidate reachability required\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'mpls'), 'tunnel_flood_filter_time')):
                pass
                yield '      mpls tunnel flood filter time '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'mpls'), 'tunnel_flood_filter_time'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'mpls'), 'shared_index')):
                pass
                yield '      mpls shared index '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'mpls'), 'shared_index'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'route_target')):
                pass
                yield '      route-target import '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'evpn_ethernet_segment'), 'route_target'))
                yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'flow_tracker'), 'hardware')):
            pass
            yield '   flow tracker hardware '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'flow_tracker'), 'hardware'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'flow_tracker'), 'sampled')):
            pass
            yield '   flow tracker sampled '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'flow_tracker'), 'sampled'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'snmp_trap_link_change'), False):
            pass
            yield '   no snmp trap link-change\n'
        elif t_14(environment.getattr(l_1_ethernet_interface, 'snmp_trap_link_change'), True):
            pass
            yield '   snmp trap link-change\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'vrf')):
            pass
            yield '   vrf '
            yield str(environment.getattr(l_1_ethernet_interface, 'vrf'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ip_address')):
            pass
            yield '   ip address '
            yield str(environment.getattr(l_1_ethernet_interface, 'ip_address'))
            yield '\n'
            for l_2_ip_address_secondary in t_3(environment.getattr(l_1_ethernet_interface, 'ip_address_secondaries')):
                _loop_vars = {}
                pass
                yield '   ip address '
                yield str(l_2_ip_address_secondary)
                yield ' secondary\n'
            l_2_ip_address_secondary = missing
        if t_14(environment.getattr(l_1_ethernet_interface, 'ip_proxy_arp'), True):
            pass
            yield '   ip proxy-arp\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'arp_gratuitous_accept'), True):
            pass
            yield '   arp gratuitous accept\n'
        if (t_14(environment.getattr(l_1_ethernet_interface, 'ip_address'), 'dhcp') and t_14(environment.getattr(l_1_ethernet_interface, 'dhcp_client_accept_default_route'), True)):
            pass
            yield '   dhcp client accept default-route\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ip_verify_unicast_source_reachable_via')):
            pass
            yield '   ip verify unicast source reachable-via '
            yield str(environment.getattr(l_1_ethernet_interface, 'ip_verify_unicast_source_reachable_via'))
            yield '\n'
        if ((t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'bfd'), 'interval')) and t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'bfd'), 'min_rx'))) and t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'bfd'), 'multiplier'))):
            pass
            yield '   bfd interval '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'bfd'), 'interval'))
            yield ' min-rx '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'bfd'), 'min_rx'))
            yield ' multiplier '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'bfd'), 'multiplier'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'bfd'), 'echo'), True):
            pass
            yield '   bfd echo\n'
        elif t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'bfd'), 'echo'), False):
            pass
            yield '   no bfd echo\n'
        for l_2_ip_helper in t_3(environment.getattr(l_1_ethernet_interface, 'ip_helpers'), sort_key='ip_helper'):
            l_2_ip_helper_cli = missing
            _loop_vars = {}
            pass
            l_2_ip_helper_cli = str_join(('ip helper-address ', environment.getattr(l_2_ip_helper, 'ip_helper'), ))
            _loop_vars['ip_helper_cli'] = l_2_ip_helper_cli
            if t_14(environment.getattr(l_2_ip_helper, 'vrf')):
                pass
                l_2_ip_helper_cli = str_join(((undefined(name='ip_helper_cli') if l_2_ip_helper_cli is missing else l_2_ip_helper_cli), ' vrf ', environment.getattr(l_2_ip_helper, 'vrf'), ))
                _loop_vars['ip_helper_cli'] = l_2_ip_helper_cli
            if t_14(environment.getattr(l_2_ip_helper, 'source_interface')):
                pass
                l_2_ip_helper_cli = str_join(((undefined(name='ip_helper_cli') if l_2_ip_helper_cli is missing else l_2_ip_helper_cli), ' source-interface ', environment.getattr(l_2_ip_helper, 'source_interface'), ))
                _loop_vars['ip_helper_cli'] = l_2_ip_helper_cli
            yield '   '
            yield str((undefined(name='ip_helper_cli') if l_2_ip_helper_cli is missing else l_2_ip_helper_cli))
            yield '\n'
        l_2_ip_helper = l_2_ip_helper_cli = missing
        if t_14(environment.getattr(l_1_ethernet_interface, 'ipv6_dhcp_relay_destinations')):
            pass
            l_1_non_default_vrf = t_9(context.eval_ctx, t_10(context, t_12(context, environment.getattr(l_1_ethernet_interface, 'ipv6_dhcp_relay_destinations'), 'vrf', 'arista.avd.defined'), 'vrf', 'equalto', 'default'))
            _loop_vars['non_default_vrf'] = l_1_non_default_vrf
            l_1_default_vrf = (t_9(context.eval_ctx, t_10(context, environment.getattr(l_1_ethernet_interface, 'ipv6_dhcp_relay_destinations'), 'vrf', 'arista.avd.defined')) + t_9(context.eval_ctx, t_12(context, t_12(context, environment.getattr(l_1_ethernet_interface, 'ipv6_dhcp_relay_destinations'), 'vrf', 'arista.avd.defined'), 'vrf', 'equalto', 'default')))
            _loop_vars['default_vrf'] = l_1_default_vrf
            for l_2_destination in (t_3((undefined(name='default_vrf') if l_1_default_vrf is missing else l_1_default_vrf), sort_key='address') + t_3(t_3((undefined(name='non_default_vrf') if l_1_non_default_vrf is missing else l_1_non_default_vrf), sort_key='address'), sort_key='vrf', ignore_case=False)):
                l_2_destination_cli = missing
                _loop_vars = {}
                pass
                l_2_destination_cli = str_join(('ipv6 dhcp relay destination ', environment.getattr(l_2_destination, 'address'), ))
                _loop_vars['destination_cli'] = l_2_destination_cli
                if t_14(environment.getattr(l_2_destination, 'vrf')):
                    pass
                    l_2_destination_cli = str_join(((undefined(name='destination_cli') if l_2_destination_cli is missing else l_2_destination_cli), ' vrf ', environment.getattr(l_2_destination, 'vrf'), ))
                    _loop_vars['destination_cli'] = l_2_destination_cli
                if t_14(environment.getattr(l_2_destination, 'local_interface')):
                    pass
                    l_2_destination_cli = str_join(((undefined(name='destination_cli') if l_2_destination_cli is missing else l_2_destination_cli), ' local-interface ', environment.getattr(l_2_destination, 'local_interface'), ))
                    _loop_vars['destination_cli'] = l_2_destination_cli
                elif t_14(environment.getattr(l_2_destination, 'source_address')):
                    pass
                    l_2_destination_cli = str_join(((undefined(name='destination_cli') if l_2_destination_cli is missing else l_2_destination_cli), ' source-address ', environment.getattr(l_2_destination, 'source_address'), ))
                    _loop_vars['destination_cli'] = l_2_destination_cli
                if t_14(environment.getattr(l_2_destination, 'link_address')):
                    pass
                    l_2_destination_cli = str_join(((undefined(name='destination_cli') if l_2_destination_cli is missing else l_2_destination_cli), ' link-address ', environment.getattr(l_2_destination, 'link_address'), ))
                    _loop_vars['destination_cli'] = l_2_destination_cli
                yield '   '
                yield str((undefined(name='destination_cli') if l_2_destination_cli is missing else l_2_destination_cli))
                yield '\n'
            l_2_destination = l_2_destination_cli = missing
        if t_14(environment.getattr(l_1_ethernet_interface, 'dhcp_server_ipv4'), True):
            pass
            yield '   dhcp server ipv4\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'dhcp_server_ipv6'), True):
            pass
            yield '   dhcp server ipv6\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ip_igmp_host_proxy'), 'enabled'), True):
            pass
            l_1_host_proxy_cli = 'ip igmp host-proxy'
            _loop_vars['host_proxy_cli'] = l_1_host_proxy_cli
            yield '   '
            yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
            yield '\n'
            for l_2_proxy_group in t_1(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ip_igmp_host_proxy'), 'groups'), []):
                _loop_vars = {}
                pass
                if (t_14(environment.getattr(l_2_proxy_group, 'exclude')) or t_14(environment.getattr(l_2_proxy_group, 'include'))):
                    pass
                    if t_14(environment.getattr(l_2_proxy_group, 'include')):
                        pass
                        for l_3_include_source in environment.getattr(l_2_proxy_group, 'include'):
                            _loop_vars = {}
                            pass
                            yield '   '
                            yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
                            yield ' '
                            yield str(environment.getattr(l_2_proxy_group, 'group'))
                            yield ' include '
                            yield str(environment.getattr(l_3_include_source, 'source'))
                            yield '\n'
                        l_3_include_source = missing
                    if t_14(environment.getattr(l_2_proxy_group, 'exclude')):
                        pass
                        for l_3_exclude_source in environment.getattr(l_2_proxy_group, 'exclude'):
                            _loop_vars = {}
                            pass
                            yield '   '
                            yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
                            yield ' '
                            yield str(environment.getattr(l_2_proxy_group, 'group'))
                            yield ' exclude '
                            yield str(environment.getattr(l_3_exclude_source, 'source'))
                            yield '\n'
                        l_3_exclude_source = missing
                elif t_14(environment.getattr(l_2_proxy_group, 'group')):
                    pass
                    yield '   '
                    yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
                    yield ' '
                    yield str(environment.getattr(l_2_proxy_group, 'group'))
                    yield '\n'
            l_2_proxy_group = missing
            for l_2_access_list in t_1(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ip_igmp_host_proxy'), 'access_lists'), []):
                _loop_vars = {}
                pass
                yield '   '
                yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
                yield ' access-list '
                yield str(environment.getattr(l_2_access_list, 'name'))
                yield '\n'
            l_2_access_list = missing
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ip_igmp_host_proxy'), 'report_interval')):
                pass
                yield '   '
                yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
                yield ' report-interval '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ip_igmp_host_proxy'), 'report_interval'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ip_igmp_host_proxy'), 'version')):
                pass
                yield '   '
                yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
                yield ' version '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ip_igmp_host_proxy'), 'version'))
                yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ipv6_enable'), True):
            pass
            yield '   ipv6 enable\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ipv6_address')):
            pass
            yield '   ipv6 address '
            yield str(environment.getattr(l_1_ethernet_interface, 'ipv6_address'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ipv6_address_link_local')):
            pass
            yield '   ipv6 address '
            yield str(environment.getattr(l_1_ethernet_interface, 'ipv6_address_link_local'))
            yield ' link-local\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ipv6_nd_ra_disabled'), True):
            pass
            yield '   ipv6 nd ra disabled\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ipv6_nd_managed_config_flag'), True):
            pass
            yield '   ipv6 nd managed-config-flag\n'
        for l_2_prefix in t_3(environment.getattr(l_1_ethernet_interface, 'ipv6_nd_prefixes'), 'ipv6_prefix'):
            l_2_ipv6_nd_prefix_cli = missing
            _loop_vars = {}
            pass
            l_2_ipv6_nd_prefix_cli = str_join(('ipv6 nd prefix ', environment.getattr(l_2_prefix, 'ipv6_prefix'), ))
            _loop_vars['ipv6_nd_prefix_cli'] = l_2_ipv6_nd_prefix_cli
            if t_14(environment.getattr(l_2_prefix, 'valid_lifetime')):
                pass
                l_2_ipv6_nd_prefix_cli = str_join(((undefined(name='ipv6_nd_prefix_cli') if l_2_ipv6_nd_prefix_cli is missing else l_2_ipv6_nd_prefix_cli), ' ', environment.getattr(l_2_prefix, 'valid_lifetime'), ))
                _loop_vars['ipv6_nd_prefix_cli'] = l_2_ipv6_nd_prefix_cli
                if t_14(environment.getattr(l_2_prefix, 'preferred_lifetime')):
                    pass
                    l_2_ipv6_nd_prefix_cli = str_join(((undefined(name='ipv6_nd_prefix_cli') if l_2_ipv6_nd_prefix_cli is missing else l_2_ipv6_nd_prefix_cli), ' ', environment.getattr(l_2_prefix, 'preferred_lifetime'), ))
                    _loop_vars['ipv6_nd_prefix_cli'] = l_2_ipv6_nd_prefix_cli
            if t_14(environment.getattr(l_2_prefix, 'no_autoconfig_flag'), True):
                pass
                l_2_ipv6_nd_prefix_cli = str_join(((undefined(name='ipv6_nd_prefix_cli') if l_2_ipv6_nd_prefix_cli is missing else l_2_ipv6_nd_prefix_cli), ' no-autoconfig', ))
                _loop_vars['ipv6_nd_prefix_cli'] = l_2_ipv6_nd_prefix_cli
            yield '   '
            yield str((undefined(name='ipv6_nd_prefix_cli') if l_2_ipv6_nd_prefix_cli is missing else l_2_ipv6_nd_prefix_cli))
            yield '\n'
        l_2_prefix = l_2_ipv6_nd_prefix_cli = missing
        if (t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'tcp_mss_ceiling'), 'ipv4')) or t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'tcp_mss_ceiling'), 'ipv6'))):
            pass
            l_1_tcp_mss_ceiling_cli = 'tcp mss ceiling'
            _loop_vars['tcp_mss_ceiling_cli'] = l_1_tcp_mss_ceiling_cli
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'tcp_mss_ceiling'), 'ipv4')):
                pass
                l_1_tcp_mss_ceiling_cli = str_join(((undefined(name='tcp_mss_ceiling_cli') if l_1_tcp_mss_ceiling_cli is missing else l_1_tcp_mss_ceiling_cli), ' ipv4 ', environment.getattr(environment.getattr(l_1_ethernet_interface, 'tcp_mss_ceiling'), 'ipv4'), ))
                _loop_vars['tcp_mss_ceiling_cli'] = l_1_tcp_mss_ceiling_cli
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'tcp_mss_ceiling'), 'ipv6')):
                pass
                l_1_tcp_mss_ceiling_cli = str_join(((undefined(name='tcp_mss_ceiling_cli') if l_1_tcp_mss_ceiling_cli is missing else l_1_tcp_mss_ceiling_cli), ' ipv6 ', environment.getattr(environment.getattr(l_1_ethernet_interface, 'tcp_mss_ceiling'), 'ipv6'), ))
                _loop_vars['tcp_mss_ceiling_cli'] = l_1_tcp_mss_ceiling_cli
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'tcp_mss_ceiling'), 'direction')):
                pass
                l_1_tcp_mss_ceiling_cli = str_join(((undefined(name='tcp_mss_ceiling_cli') if l_1_tcp_mss_ceiling_cli is missing else l_1_tcp_mss_ceiling_cli), ' ', environment.getattr(environment.getattr(l_1_ethernet_interface, 'tcp_mss_ceiling'), 'direction'), ))
                _loop_vars['tcp_mss_ceiling_cli'] = l_1_tcp_mss_ceiling_cli
            yield '   '
            yield str((undefined(name='tcp_mss_ceiling_cli') if l_1_tcp_mss_ceiling_cli is missing else l_1_tcp_mss_ceiling_cli))
            yield '\n'
        if (t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'channel_group'), 'id')) and t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'channel_group'), 'mode'))):
            pass
            yield '   channel-group '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'channel_group'), 'id'))
            yield ' mode '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'channel_group'), 'mode'))
            yield '\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'lacp_timer'), 'mode')):
                pass
                yield '   lacp timer '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'lacp_timer'), 'mode'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'lacp_timer'), 'multiplier')):
                pass
                yield '   lacp timer multiplier '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'lacp_timer'), 'multiplier'))
                yield '\n'
            if t_14(environment.getattr(l_1_ethernet_interface, 'lacp_port_priority')):
                pass
                yield '   lacp port-priority '
                yield str(environment.getattr(l_1_ethernet_interface, 'lacp_port_priority'))
                yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'access_group_in')):
            pass
            yield '   ip access-group '
            yield str(environment.getattr(l_1_ethernet_interface, 'access_group_in'))
            yield ' in\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'access_group_out')):
            pass
            yield '   ip access-group '
            yield str(environment.getattr(l_1_ethernet_interface, 'access_group_out'))
            yield ' out\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ipv6_access_group_in')):
            pass
            yield '   ipv6 access-group '
            yield str(environment.getattr(l_1_ethernet_interface, 'ipv6_access_group_in'))
            yield ' in\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ipv6_access_group_out')):
            pass
            yield '   ipv6 access-group '
            yield str(environment.getattr(l_1_ethernet_interface, 'ipv6_access_group_out'))
            yield ' out\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'mac_access_group_in')):
            pass
            yield '   mac access-group '
            yield str(environment.getattr(l_1_ethernet_interface, 'mac_access_group_in'))
            yield ' in\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'mac_access_group_out')):
            pass
            yield '   mac access-group '
            yield str(environment.getattr(l_1_ethernet_interface, 'mac_access_group_out'))
            yield ' out\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'mpls'), 'ldp'), 'igp_sync'), True):
            pass
            yield '   mpls ldp igp sync\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'mpls'), 'ldp'), 'interface'), True):
            pass
            yield '   mpls ldp interface\n'
        elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'mpls'), 'ldp'), 'interface'), False):
            pass
            yield '   no mpls ldp interface\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'lldp'), 'transmit'), False):
            pass
            yield '   no lldp transmit\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'lldp'), 'receive'), False):
            pass
            yield '   no lldp receive\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'lldp'), 'ztp_vlan')):
            pass
            yield '   lldp tlv transmit ztp vlan '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'lldp'), 'ztp_vlan'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'loop_protection'), False):
            pass
            yield '   no loop-protection\n'
        elif t_14(environment.getattr(l_1_ethernet_interface, 'loop_protection'), True):
            pass
            yield '   loop-protection\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'mac_security'), 'profile')):
            pass
            yield '   mac security profile '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'mac_security'), 'profile'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'multicast')):
            pass
            for l_2_boundary in t_1(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'multicast'), 'ipv4'), 'boundaries'), []):
                l_2_boundary_cli = missing
                _loop_vars = {}
                pass
                l_2_boundary_cli = str_join(('multicast ipv4 boundary ', environment.getattr(l_2_boundary, 'boundary'), ))
                _loop_vars['boundary_cli'] = l_2_boundary_cli
                if t_14(environment.getattr(l_2_boundary, 'out'), True):
                    pass
                    l_2_boundary_cli = str_join(((undefined(name='boundary_cli') if l_2_boundary_cli is missing else l_2_boundary_cli), ' out', ))
                    _loop_vars['boundary_cli'] = l_2_boundary_cli
                yield '   '
                yield str((undefined(name='boundary_cli') if l_2_boundary_cli is missing else l_2_boundary_cli))
                yield '\n'
            l_2_boundary = l_2_boundary_cli = missing
            for l_2_boundary in t_1(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'multicast'), 'ipv6'), 'boundaries'), []):
                _loop_vars = {}
                pass
                yield '   multicast ipv6 boundary '
                yield str(environment.getattr(l_2_boundary, 'boundary'))
                yield ' out\n'
            l_2_boundary = missing
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'multicast'), 'ipv4'), 'static'), True):
                pass
                yield '   multicast ipv4 static\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'multicast'), 'ipv6'), 'static'), True):
                pass
                yield '   multicast ipv6 static\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'mpls'), 'ip'), True):
            pass
            yield '   mpls ip\n'
        elif t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'mpls'), 'ip'), False):
            pass
            yield '   no mpls ip\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ip_nat')):
            pass
            l_1_interface_ip_nat = environment.getattr(l_1_ethernet_interface, 'ip_nat')
            _loop_vars['interface_ip_nat'] = l_1_interface_ip_nat
            template = environment.get_template('eos/interface-ip-nat.j2', 'eos/ethernet-interfaces.j2')
            gen = template.root_render_func(template.new_context(context.get_all(), True, {'aaa_config': l_1_aaa_config, 'actions': l_1_actions, 'address_locking_cli': l_1_address_locking_cli, 'auth_cli': l_1_auth_cli, 'auth_failure_fallback_mba': l_1_auth_failure_fallback_mba, 'backup_link_cli': l_1_backup_link_cli, 'both_key_ids': l_1_both_key_ids, 'client_encapsulation': l_1_client_encapsulation, 'default_vrf': l_1_default_vrf, 'dfe_algo_cli': l_1_dfe_algo_cli, 'dfe_hold_time_cli': l_1_dfe_hold_time_cli, 'encapsulation_cli': l_1_encapsulation_cli, 'encapsulation_dot1q_cli': l_1_encapsulation_dot1q_cli, 'ethernet_interface': l_1_ethernet_interface, 'frequency_cli': l_1_frequency_cli, 'host_mode_cli': l_1_host_mode_cli, 'host_proxy_cli': l_1_host_proxy_cli, 'interface_ip_nat': l_1_interface_ip_nat, 'isis_auth_cli': l_1_isis_auth_cli, 'network_encapsulation': l_1_network_encapsulation, 'network_flag': l_1_network_flag, 'non_default_vrf': l_1_non_default_vrf, 'poe_limit_cli': l_1_poe_limit_cli, 'poe_link_down_action_cli': l_1_poe_link_down_action_cli, 'rate_limit_count': l_1_rate_limit_count, 'sorted_vlans_cli': l_1_sorted_vlans_cli, 'tap_identity_cli': l_1_tap_identity_cli, 'tap_mac_address_cli': l_1_tap_mac_address_cli, 'tap_truncation_cli': l_1_tap_truncation_cli, 'tcp_mss_ceiling_cli': l_1_tcp_mss_ceiling_cli, 'tool_groups': l_1_tool_groups, 'POE_CLASS_MAP': l_0_POE_CLASS_MAP}))
            try:
                for event in gen:
                    yield event
            finally: gen.close()
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ip_nat'), 'service_profile')):
                pass
                yield '   ip nat service-profile '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ip_nat'), 'service_profile'))
                yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ntp_serve')):
            pass
            if environment.getattr(l_1_ethernet_interface, 'ntp_serve'):
                pass
                yield '   ntp serve\n'
            else:
                pass
                yield '   no ntp serve\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ospf_cost')):
            pass
            yield '   ip ospf cost '
            yield str(environment.getattr(l_1_ethernet_interface, 'ospf_cost'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ospf_network_point_to_point'), True):
            pass
            yield '   ip ospf network point-to-point\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ospf_authentication'), 'simple'):
            pass
            yield '   ip ospf authentication\n'
        elif t_14(environment.getattr(l_1_ethernet_interface, 'ospf_authentication'), 'message-digest'):
            pass
            yield '   ip ospf authentication message-digest\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ospf_authentication_key')):
            pass
            yield '   ip ospf authentication-key '
            yield str(t_1(environment.getattr(l_1_ethernet_interface, 'ospf_authentication_key_type'), '7'))
            yield ' '
            yield str(t_2(environment.getattr(l_1_ethernet_interface, 'ospf_authentication_key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'ospf_area')):
            pass
            yield '   ip ospf area '
            yield str(environment.getattr(l_1_ethernet_interface, 'ospf_area'))
            yield '\n'
        for l_2_ospf_message_digest_key in t_3(environment.getattr(l_1_ethernet_interface, 'ospf_message_digest_keys'), sort_key='id'):
            _loop_vars = {}
            pass
            if (t_14(environment.getattr(l_2_ospf_message_digest_key, 'hash_algorithm')) and t_14(environment.getattr(l_2_ospf_message_digest_key, 'key'))):
                pass
                yield '   ip ospf message-digest-key '
                yield str(environment.getattr(l_2_ospf_message_digest_key, 'id'))
                yield ' '
                yield str(environment.getattr(l_2_ospf_message_digest_key, 'hash_algorithm'))
                yield ' '
                yield str(t_1(environment.getattr(l_2_ospf_message_digest_key, 'key_type'), '7'))
                yield ' '
                yield str(t_2(environment.getattr(l_2_ospf_message_digest_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                yield '\n'
        l_2_ospf_message_digest_key = missing
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'service_policy'), 'pbr'), 'input')):
            pass
            yield '   service-policy type pbr input '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'service_policy'), 'pbr'), 'input'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'pim'), 'ipv4'), 'sparse_mode'), True):
            pass
            yield '   pim ipv4 sparse-mode\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'pim'), 'ipv4'), 'bidirectional'), True):
            pass
            yield '   pim ipv4 bidirectional\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'pim'), 'ipv4'), 'border_router'), True):
            pass
            yield '   pim ipv4 border-router\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'pim'), 'ipv4'), 'hello'), 'interval')):
            pass
            yield '   pim ipv4 hello interval '
            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'pim'), 'ipv4'), 'hello'), 'interval'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'pim'), 'ipv4'), 'hello'), 'count')):
            pass
            yield '   pim ipv4 hello count '
            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'pim'), 'ipv4'), 'hello'), 'count'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'pim'), 'ipv4'), 'dr_priority')):
            pass
            yield '   pim ipv4 dr-priority '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'pim'), 'ipv4'), 'dr_priority'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'pim'), 'ipv4'), 'neighbor_filter')):
            pass
            yield '   pim ipv4 neighbor filter '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'pim'), 'ipv4'), 'neighbor_filter'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'pim'), 'ipv4'), 'bfd'), True):
            pass
            yield '   pim ipv4 bfd\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'priority')):
            pass
            yield '   poe priority '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'priority'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'reboot'), 'action')):
            pass
            yield '   poe reboot action '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'reboot'), 'action'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'link_down'), 'action')):
            pass
            l_1_poe_link_down_action_cli = str_join(('poe link down action ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'link_down'), 'action'), ))
            _loop_vars['poe_link_down_action_cli'] = l_1_poe_link_down_action_cli
            if (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'link_down'), 'power_off_delay')) and (environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'link_down'), 'action') == 'power-off')):
                pass
                l_1_poe_link_down_action_cli = str_join(((undefined(name='poe_link_down_action_cli') if l_1_poe_link_down_action_cli is missing else l_1_poe_link_down_action_cli), ' ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'link_down'), 'power_off_delay'), ' seconds', ))
                _loop_vars['poe_link_down_action_cli'] = l_1_poe_link_down_action_cli
            yield '   '
            yield str((undefined(name='poe_link_down_action_cli') if l_1_poe_link_down_action_cli is missing else l_1_poe_link_down_action_cli))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'shutdown'), 'action')):
            pass
            yield '   poe shutdown action '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'shutdown'), 'action'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'disabled'), True):
            pass
            yield '   poe disabled\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'limit')):
            pass
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'limit'), 'class')):
                pass
                l_1_poe_limit_cli = str_join(('poe limit ', environment.getitem((undefined(name='POE_CLASS_MAP') if l_0_POE_CLASS_MAP is missing else l_0_POE_CLASS_MAP), environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'limit'), 'class')), ' watts', ))
                _loop_vars['poe_limit_cli'] = l_1_poe_limit_cli
            elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'limit'), 'watts')):
                pass
                l_1_poe_limit_cli = str_join(('poe limit ', t_6('%.2f', t_5(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'limit'), 'watts'))), ' watts', ))
                _loop_vars['poe_limit_cli'] = l_1_poe_limit_cli
            if (t_14((undefined(name='poe_limit_cli') if l_1_poe_limit_cli is missing else l_1_poe_limit_cli)) and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'limit'), 'fixed'), True)):
                pass
                l_1_poe_limit_cli = str_join(((undefined(name='poe_limit_cli') if l_1_poe_limit_cli is missing else l_1_poe_limit_cli), ' fixed', ))
                _loop_vars['poe_limit_cli'] = l_1_poe_limit_cli
            yield '   '
            yield str((undefined(name='poe_limit_cli') if l_1_poe_limit_cli is missing else l_1_poe_limit_cli))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'negotiation_lldp'), False):
            pass
            yield '   poe negotiation lldp disabled\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'poe'), 'legacy_detect'), True):
            pass
            yield '   poe legacy detect\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security')):
            pass
            if (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'enabled'), True) or t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'violation'), 'mode'), 'shutdown')):
                pass
                yield '   switchport port-security\n'
            elif t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'violation'), 'mode'), 'protect'):
                pass
                if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'violation'), 'protect_log'), True):
                    pass
                    yield '   switchport port-security violation protect log\n'
                else:
                    pass
                    yield '   switchport port-security violation protect\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'mac_address_maximum'), 'disabled'), True):
                pass
                yield '   switchport port-security mac-address maximum disabled\n'
            elif t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'mac_address_maximum'), 'disabled'), False):
                pass
                yield '   no switchport port-security mac-address maximum disabled\n'
            elif t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'mac_address_maximum'), 'limit')):
                pass
                yield '   switchport port-security mac-address maximum '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'mac_address_maximum'), 'limit'))
                yield '\n'
            if (not t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'violation'), 'mode'), 'protect')):
                pass
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'vlans')):
                    pass
                    l_1_sorted_vlans_cli = []
                    _loop_vars['sorted_vlans_cli'] = l_1_sorted_vlans_cli
                    for l_2_vlan in environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'vlans'):
                        _loop_vars = {}
                        pass
                        for l_3_id in t_4(environment.getattr(l_2_vlan, 'range')):
                            l_3_port_sec_cli = missing
                            _loop_vars = {}
                            pass
                            l_3_port_sec_cli = str_join(('switchport port-security vlan ', l_3_id, ' mac-address maximum ', environment.getattr(l_2_vlan, 'mac_address_maximum'), ))
                            _loop_vars['port_sec_cli'] = l_3_port_sec_cli
                            context.call(environment.getattr((undefined(name='sorted_vlans_cli') if l_1_sorted_vlans_cli is missing else l_1_sorted_vlans_cli), 'append'), (undefined(name='port_sec_cli') if l_3_port_sec_cli is missing else l_3_port_sec_cli), _loop_vars=_loop_vars)
                        l_3_id = l_3_port_sec_cli = missing
                    l_2_vlan = missing
                    for l_2_vlan_cli in t_3((undefined(name='sorted_vlans_cli') if l_1_sorted_vlans_cli is missing else l_1_sorted_vlans_cli)):
                        _loop_vars = {}
                        pass
                        yield '   '
                        yield str(l_2_vlan_cli)
                        yield '\n'
                    l_2_vlan_cli = missing
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'vlan_default_mac_address_maximum')):
                    pass
                    yield '   switchport port-security vlan default mac-address maximum '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'port_security'), 'vlan_default_mac_address_maximum'))
                    yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'enable'), True):
            pass
            yield '   ptp enable\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'announce'), 'interval')):
            pass
            yield '   ptp announce interval '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'announce'), 'interval'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'announce'), 'timeout')):
            pass
            yield '   ptp announce timeout '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'announce'), 'timeout'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'delay_mechanism')):
            pass
            yield '   ptp delay-mechanism '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'delay_mechanism'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'delay_req')):
            pass
            yield '   ptp delay-req interval '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'delay_req'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'profile'), 'g8275_1'), 'destination_mac_address')):
            pass
            yield '   ptp profile g8275.1 destination mac-address '
            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'profile'), 'g8275_1'), 'destination_mac_address'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'role')):
            pass
            yield '   ptp role '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'role'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'sync_message'), 'interval')):
            pass
            yield '   ptp sync-message interval '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'sync_message'), 'interval'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'transport')):
            pass
            yield '   ptp transport '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'transport'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'vlan')):
            pass
            yield '   ptp vlan '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'ptp'), 'vlan'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'service_policy'), 'qos'), 'input')):
            pass
            yield '   service-policy type qos input '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'service_policy'), 'qos'), 'input'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'service_profile')):
            pass
            yield '   service-profile '
            yield str(environment.getattr(l_1_ethernet_interface, 'service_profile'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'qos'), 'trust')):
            pass
            if (environment.getattr(environment.getattr(l_1_ethernet_interface, 'qos'), 'trust') == 'disabled'):
                pass
                yield '   no qos trust\n'
            else:
                pass
                yield '   qos trust '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'qos'), 'trust'))
                yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'qos'), 'cos')):
            pass
            yield '   qos cos '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'qos'), 'cos'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'qos'), 'dscp')):
            pass
            yield '   qos dscp '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'qos'), 'dscp'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'shape'), 'rate')):
            pass
            yield '   shape rate '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'shape'), 'rate'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'priority_flow_control'), 'enabled'), True):
            pass
            yield '   priority-flow-control on\n'
        elif t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'priority_flow_control'), 'enabled'), False):
            pass
            yield '   no priority-flow-control\n'
        for l_2_priority_block in t_3(environment.getattr(environment.getattr(l_1_ethernet_interface, 'priority_flow_control'), 'priorities'), sort_key='priority'):
            _loop_vars = {}
            pass
            if t_14(environment.getattr(l_2_priority_block, 'no_drop'), True):
                pass
                yield '   priority-flow-control priority '
                yield str(environment.getattr(l_2_priority_block, 'priority'))
                yield ' no-drop\n'
            elif t_14(environment.getattr(l_2_priority_block, 'no_drop'), False):
                pass
                yield '   priority-flow-control priority '
                yield str(environment.getattr(l_2_priority_block, 'priority'))
                yield ' drop\n'
        l_2_priority_block = missing
        for l_2_tx_queue in t_3(environment.getattr(l_1_ethernet_interface, 'tx_queues'), sort_key='id'):
            _loop_vars = {}
            pass
            template = environment.get_template('eos/ethernet-interface-tx-queues.j2', 'eos/ethernet-interfaces.j2')
            gen = template.root_render_func(template.new_context(context.get_all(), True, {'tx_queue': l_2_tx_queue, 'aaa_config': l_1_aaa_config, 'actions': l_1_actions, 'address_locking_cli': l_1_address_locking_cli, 'auth_cli': l_1_auth_cli, 'auth_failure_fallback_mba': l_1_auth_failure_fallback_mba, 'backup_link_cli': l_1_backup_link_cli, 'both_key_ids': l_1_both_key_ids, 'client_encapsulation': l_1_client_encapsulation, 'default_vrf': l_1_default_vrf, 'dfe_algo_cli': l_1_dfe_algo_cli, 'dfe_hold_time_cli': l_1_dfe_hold_time_cli, 'encapsulation_cli': l_1_encapsulation_cli, 'encapsulation_dot1q_cli': l_1_encapsulation_dot1q_cli, 'ethernet_interface': l_1_ethernet_interface, 'frequency_cli': l_1_frequency_cli, 'host_mode_cli': l_1_host_mode_cli, 'host_proxy_cli': l_1_host_proxy_cli, 'interface_ip_nat': l_1_interface_ip_nat, 'isis_auth_cli': l_1_isis_auth_cli, 'network_encapsulation': l_1_network_encapsulation, 'network_flag': l_1_network_flag, 'non_default_vrf': l_1_non_default_vrf, 'poe_limit_cli': l_1_poe_limit_cli, 'poe_link_down_action_cli': l_1_poe_link_down_action_cli, 'rate_limit_count': l_1_rate_limit_count, 'sorted_vlans_cli': l_1_sorted_vlans_cli, 'tap_identity_cli': l_1_tap_identity_cli, 'tap_mac_address_cli': l_1_tap_mac_address_cli, 'tap_truncation_cli': l_1_tap_truncation_cli, 'tcp_mss_ceiling_cli': l_1_tcp_mss_ceiling_cli, 'tool_groups': l_1_tool_groups, 'POE_CLASS_MAP': l_0_POE_CLASS_MAP}))
            try:
                for event in gen:
                    yield event
            finally: gen.close()
        l_2_tx_queue = missing
        for l_2_uc_tx_queue in t_3(environment.getattr(l_1_ethernet_interface, 'uc_tx_queues'), sort_key='id'):
            _loop_vars = {}
            pass
            template = environment.get_template('eos/ethernet-interface-uc-tx-queues.j2', 'eos/ethernet-interfaces.j2')
            gen = template.root_render_func(template.new_context(context.get_all(), True, {'uc_tx_queue': l_2_uc_tx_queue, 'aaa_config': l_1_aaa_config, 'actions': l_1_actions, 'address_locking_cli': l_1_address_locking_cli, 'auth_cli': l_1_auth_cli, 'auth_failure_fallback_mba': l_1_auth_failure_fallback_mba, 'backup_link_cli': l_1_backup_link_cli, 'both_key_ids': l_1_both_key_ids, 'client_encapsulation': l_1_client_encapsulation, 'default_vrf': l_1_default_vrf, 'dfe_algo_cli': l_1_dfe_algo_cli, 'dfe_hold_time_cli': l_1_dfe_hold_time_cli, 'encapsulation_cli': l_1_encapsulation_cli, 'encapsulation_dot1q_cli': l_1_encapsulation_dot1q_cli, 'ethernet_interface': l_1_ethernet_interface, 'frequency_cli': l_1_frequency_cli, 'host_mode_cli': l_1_host_mode_cli, 'host_proxy_cli': l_1_host_proxy_cli, 'interface_ip_nat': l_1_interface_ip_nat, 'isis_auth_cli': l_1_isis_auth_cli, 'network_encapsulation': l_1_network_encapsulation, 'network_flag': l_1_network_flag, 'non_default_vrf': l_1_non_default_vrf, 'poe_limit_cli': l_1_poe_limit_cli, 'poe_link_down_action_cli': l_1_poe_link_down_action_cli, 'rate_limit_count': l_1_rate_limit_count, 'sorted_vlans_cli': l_1_sorted_vlans_cli, 'tap_identity_cli': l_1_tap_identity_cli, 'tap_mac_address_cli': l_1_tap_mac_address_cli, 'tap_truncation_cli': l_1_tap_truncation_cli, 'tcp_mss_ceiling_cli': l_1_tcp_mss_ceiling_cli, 'tool_groups': l_1_tool_groups, 'POE_CLASS_MAP': l_0_POE_CLASS_MAP}))
            try:
                for event in gen:
                    yield event
            finally: gen.close()
        l_2_uc_tx_queue = missing
        if t_14(environment.getattr(l_1_ethernet_interface, 'sflow')):
            pass
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'sflow'), 'enable'), True):
                pass
                yield '   sflow enable\n'
            elif t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'sflow'), 'enable'), False):
                pass
                yield '   no sflow enable\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'sflow'), 'egress'), 'enable'), True):
                pass
                yield '   sflow egress enable\n'
            elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'sflow'), 'egress'), 'enable'), False):
                pass
                yield '   no sflow egress enable\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'sflow'), 'egress'), 'unmodified_enable'), True):
                pass
                yield '   sflow egress unmodified enable\n'
            elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'sflow'), 'egress'), 'unmodified_enable'), False):
                pass
                yield '   no sflow egress unmodified enable\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'isis_enable')):
            pass
            yield '   isis enable '
            yield str(environment.getattr(l_1_ethernet_interface, 'isis_enable'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'isis_bfd'), True):
            pass
            yield '   isis bfd\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'isis_circuit_type')):
            pass
            yield '   isis circuit-type '
            yield str(environment.getattr(l_1_ethernet_interface, 'isis_circuit_type'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'isis_metric')):
            pass
            yield '   isis metric '
            yield str(environment.getattr(l_1_ethernet_interface, 'isis_metric'))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'isis_passive'), True):
            pass
            yield '   isis passive\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'isis_hello_padding'), False):
            pass
            yield '   no isis hello padding\n'
        elif t_14(environment.getattr(l_1_ethernet_interface, 'isis_hello_padding'), True):
            pass
            yield '   isis hello padding\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'isis_network_point_to_point'), True):
            pass
            yield '   isis network point-to-point\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'isis_authentication')):
            pass
            if (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'mode')) and (((environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'mode') in ['md5', 'text']) or ((environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'mode') == 'sha') and t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'sha'), 'key_id')))) or ((environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'mode') == 'shared-secret') and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'shared_secret'))))):
                pass
                l_1_isis_auth_cli = str_join(('isis authentication mode ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'mode'), ))
                _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                if (environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'mode') == 'sha'):
                    pass
                    l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' key-id ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'sha'), 'key_id'), ))
                    _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                elif (environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'mode') == 'shared-secret'):
                    pass
                    l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' profile ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'shared_secret'), 'profile'), ' algorithm ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'shared_secret'), 'algorithm'), ))
                    _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'rx_disabled'), True):
                    pass
                    l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' rx-disabled', ))
                    _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                yield '   '
                yield str((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli))
                yield '\n'
            else:
                pass
                if (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'mode')) and (((environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'mode') in ['md5', 'text']) or ((environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'mode') == 'sha') and t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'sha'), 'key_id')))) or ((environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'mode') == 'shared-secret') and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'shared_secret'))))):
                    pass
                    l_1_isis_auth_cli = str_join(('isis authentication mode ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'mode'), ))
                    _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    if (environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'mode') == 'sha'):
                        pass
                        l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' key-id ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'sha'), 'key_id'), ))
                        _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    elif (environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'mode') == 'shared-secret'):
                        pass
                        l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' profile ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'shared_secret'), 'profile'), ' algorithm ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'shared_secret'), 'algorithm'), ))
                        _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'rx_disabled'), True):
                        pass
                        l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' rx-disabled', ))
                        _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    yield '   '
                    yield str((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli))
                    yield ' level-1\n'
                if (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'mode')) and (((environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'mode') in ['md5', 'text']) or ((environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'mode') == 'sha') and t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'sha'), 'key_id')))) or ((environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'mode') == 'shared-secret') and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'shared_secret'))))):
                    pass
                    l_1_isis_auth_cli = str_join(('isis authentication mode ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'mode'), ))
                    _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    if (environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'mode') == 'sha'):
                        pass
                        l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' key-id ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'sha'), 'key_id'), ))
                        _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    elif (environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'mode') == 'shared-secret'):
                        pass
                        l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' profile ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'shared_secret'), 'profile'), ' algorithm ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'shared_secret'), 'algorithm'), ))
                        _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'rx_disabled'), True):
                        pass
                        l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' rx-disabled', ))
                        _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    yield '   '
                    yield str((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli))
                    yield ' level-2\n'
            l_1_both_key_ids = []
            _loop_vars['both_key_ids'] = l_1_both_key_ids
            for l_2_auth_key in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'key_ids'), sort_key='id'):
                _loop_vars = {}
                pass
                context.call(environment.getattr((undefined(name='both_key_ids') if l_1_both_key_ids is missing else l_1_both_key_ids), 'append'), environment.getattr(l_2_auth_key, 'id'), _loop_vars=_loop_vars)
                if t_14(environment.getattr(l_2_auth_key, 'rfc_5310'), True):
                    pass
                    yield '   isis authentication key-id '
                    yield str(environment.getattr(l_2_auth_key, 'id'))
                    yield ' algorithm '
                    yield str(environment.getattr(l_2_auth_key, 'algorithm'))
                    yield ' rfc-5310 key '
                    yield str(environment.getattr(l_2_auth_key, 'key_type'))
                    yield ' '
                    yield str(t_2(environment.getattr(l_2_auth_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                    yield '\n'
                else:
                    pass
                    yield '   isis authentication key-id '
                    yield str(environment.getattr(l_2_auth_key, 'id'))
                    yield ' algorithm '
                    yield str(environment.getattr(l_2_auth_key, 'algorithm'))
                    yield ' key '
                    yield str(environment.getattr(l_2_auth_key, 'key_type'))
                    yield ' '
                    yield str(t_2(environment.getattr(l_2_auth_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                    yield '\n'
            l_2_auth_key = missing
            for l_2_auth_key in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'key_ids'), sort_key='id'):
                _loop_vars = {}
                pass
                if (environment.getattr(l_2_auth_key, 'id') not in (undefined(name='both_key_ids') if l_1_both_key_ids is missing else l_1_both_key_ids)):
                    pass
                    if t_14(environment.getattr(l_2_auth_key, 'rfc_5310'), True):
                        pass
                        yield '   isis authentication key-id '
                        yield str(environment.getattr(l_2_auth_key, 'id'))
                        yield ' algorithm '
                        yield str(environment.getattr(l_2_auth_key, 'algorithm'))
                        yield ' rfc-5310 key '
                        yield str(environment.getattr(l_2_auth_key, 'key_type'))
                        yield ' '
                        yield str(t_2(environment.getattr(l_2_auth_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                        yield ' level-1\n'
                    else:
                        pass
                        yield '   isis authentication key-id '
                        yield str(environment.getattr(l_2_auth_key, 'id'))
                        yield ' algorithm '
                        yield str(environment.getattr(l_2_auth_key, 'algorithm'))
                        yield ' key '
                        yield str(environment.getattr(l_2_auth_key, 'key_type'))
                        yield ' '
                        yield str(t_2(environment.getattr(l_2_auth_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                        yield ' level-1\n'
            l_2_auth_key = missing
            for l_2_auth_key in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'key_ids'), sort_key='id'):
                _loop_vars = {}
                pass
                if (environment.getattr(l_2_auth_key, 'id') not in (undefined(name='both_key_ids') if l_1_both_key_ids is missing else l_1_both_key_ids)):
                    pass
                    if t_14(environment.getattr(l_2_auth_key, 'rfc_5310'), True):
                        pass
                        yield '   isis authentication key-id '
                        yield str(environment.getattr(l_2_auth_key, 'id'))
                        yield ' algorithm '
                        yield str(environment.getattr(l_2_auth_key, 'algorithm'))
                        yield ' rfc-5310 key '
                        yield str(environment.getattr(l_2_auth_key, 'key_type'))
                        yield ' '
                        yield str(t_2(environment.getattr(l_2_auth_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                        yield ' level-2\n'
                    else:
                        pass
                        yield '   isis authentication key-id '
                        yield str(environment.getattr(l_2_auth_key, 'id'))
                        yield ' algorithm '
                        yield str(environment.getattr(l_2_auth_key, 'algorithm'))
                        yield ' key '
                        yield str(environment.getattr(l_2_auth_key, 'key_type'))
                        yield ' '
                        yield str(t_2(environment.getattr(l_2_auth_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                        yield ' level-2\n'
            l_2_auth_key = missing
            if (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'key_type')) and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'key'))):
                pass
                yield '   isis authentication key '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'key_type'))
                yield ' '
                yield str(t_2(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'both'), 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                yield '\n'
            else:
                pass
                if (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'key_type')) and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'key'))):
                    pass
                    yield '   isis authentication key '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'key_type'))
                    yield ' '
                    yield str(t_2(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_1'), 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                    yield ' level-1\n'
                if (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'key_type')) and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'key'))):
                    pass
                    yield '   isis authentication key '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'key_type'))
                    yield ' '
                    yield str(t_2(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'isis_authentication'), 'level_2'), 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                    yield ' level-2\n'
        for l_2_section in t_3(environment.getattr(l_1_ethernet_interface, 'storm_control')):
            _loop_vars = {}
            pass
            if (t_14(environment.getattr(environment.getitem(environment.getattr(l_1_ethernet_interface, 'storm_control'), l_2_section), 'level')) and (l_2_section != 'all')):
                pass
                if t_14(environment.getattr(environment.getitem(environment.getattr(l_1_ethernet_interface, 'storm_control'), l_2_section), 'unit'), 'pps'):
                    pass
                    yield '   storm-control '
                    yield str(t_11(context.eval_ctx, l_2_section, '_', '-'))
                    yield ' level pps '
                    yield str(environment.getattr(environment.getitem(environment.getattr(l_1_ethernet_interface, 'storm_control'), l_2_section), 'level'))
                    yield '\n'
                else:
                    pass
                    yield '   storm-control '
                    yield str(t_11(context.eval_ctx, l_2_section, '_', '-'))
                    yield ' level '
                    yield str(environment.getattr(environment.getitem(environment.getattr(l_1_ethernet_interface, 'storm_control'), l_2_section), 'level'))
                    yield '\n'
        l_2_section = missing
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'storm_control'), 'all'), 'level')):
            pass
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'storm_control'), 'all'), 'unit'), 'pps'):
                pass
                yield '   storm-control all level pps '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'storm_control'), 'all'), 'level'))
                yield '\n'
            else:
                pass
                yield '   storm-control all level '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'storm_control'), 'all'), 'level'))
                yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'logging'), 'event'), 'storm_control_discards'), True):
            pass
            yield '   logging event storm-control discards\n'
        elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'logging'), 'event'), 'storm_control_discards'), False):
            pass
            yield '   no logging event storm-control discards\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'spanning_tree_portfast'), 'edge'):
            pass
            yield '   spanning-tree portfast\n'
        elif t_14(environment.getattr(l_1_ethernet_interface, 'spanning_tree_portfast'), 'network'):
            pass
            yield '   spanning-tree portfast network\n'
        if (t_14(environment.getattr(l_1_ethernet_interface, 'spanning_tree_bpduguard')) and (environment.getattr(l_1_ethernet_interface, 'spanning_tree_bpduguard') in [True, 'True', 'enabled'])):
            pass
            yield '   spanning-tree bpduguard enable\n'
        elif t_14(environment.getattr(l_1_ethernet_interface, 'spanning_tree_bpduguard'), 'disabled'):
            pass
            yield '   spanning-tree bpduguard disable\n'
        if (t_14(environment.getattr(l_1_ethernet_interface, 'spanning_tree_bpdufilter')) and (environment.getattr(l_1_ethernet_interface, 'spanning_tree_bpdufilter') in [True, 'True', 'enabled'])):
            pass
            yield '   spanning-tree bpdufilter enable\n'
        elif t_14(environment.getattr(l_1_ethernet_interface, 'spanning_tree_bpdufilter'), 'disabled'):
            pass
            yield '   spanning-tree bpdufilter disable\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'spanning_tree_guard')):
            pass
            if (environment.getattr(l_1_ethernet_interface, 'spanning_tree_guard') == 'disabled'):
                pass
                yield '   spanning-tree guard none\n'
            else:
                pass
                yield '   spanning-tree guard '
                yield str(environment.getattr(l_1_ethernet_interface, 'spanning_tree_guard'))
                yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'spanning_tree_bpduguard_rate_limit'), 'enabled'), True):
            pass
            yield '   spanning-tree bpduguard rate-limit enable\n'
        elif t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'spanning_tree_bpduguard_rate_limit'), 'enabled'), False):
            pass
            yield '   spanning-tree bpduguard rate-limit disable\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'spanning_tree_bpduguard_rate_limit'), 'count')):
            pass
            l_1_rate_limit_count = str_join(('spanning-tree bpduguard rate-limit count ', environment.getattr(environment.getattr(l_1_ethernet_interface, 'spanning_tree_bpduguard_rate_limit'), 'count'), ))
            _loop_vars['rate_limit_count'] = l_1_rate_limit_count
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'spanning_tree_bpduguard_rate_limit'), 'interval')):
                pass
                l_1_rate_limit_count = str_join(((undefined(name='rate_limit_count') if l_1_rate_limit_count is missing else l_1_rate_limit_count), ' interval ', environment.getattr(environment.getattr(l_1_ethernet_interface, 'spanning_tree_bpduguard_rate_limit'), 'interval'), ))
                _loop_vars['rate_limit_count'] = l_1_rate_limit_count
            yield '   '
            yield str((undefined(name='rate_limit_count') if l_1_rate_limit_count is missing else l_1_rate_limit_count))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'logging'), 'event'), 'spanning_tree'), True):
            pass
            yield '   logging event spanning-tree\n'
        elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'logging'), 'event'), 'spanning_tree'), False):
            pass
            yield '   no logging event spanning-tree\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup_link'), 'interface')):
            pass
            l_1_backup_link_cli = str_join(('switchport backup-link ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup_link'), 'interface'), ))
            _loop_vars['backup_link_cli'] = l_1_backup_link_cli
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup_link'), 'prefer_vlan')):
                pass
                l_1_backup_link_cli = str_join(((undefined(name='backup_link_cli') if l_1_backup_link_cli is missing else l_1_backup_link_cli), ' prefer vlan ', environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup_link'), 'prefer_vlan'), ))
                _loop_vars['backup_link_cli'] = l_1_backup_link_cli
            yield '   '
            yield str((undefined(name='backup_link_cli') if l_1_backup_link_cli is missing else l_1_backup_link_cli))
            yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup'), 'preemption_delay')):
                pass
                yield '   switchport backup preemption-delay '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup'), 'preemption_delay'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup'), 'mac_move_burst')):
                pass
                yield '   switchport backup mac-move-burst '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup'), 'mac_move_burst'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup'), 'mac_move_burst_interval')):
                pass
                yield '   switchport backup mac-move-burst-interval '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup'), 'mac_move_burst_interval'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup'), 'initial_mac_move_delay')):
                pass
                yield '   switchport backup initial-mac-move-delay '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup'), 'initial_mac_move_delay'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup'), 'dest_macaddr')):
                pass
                yield '   switchport backup dest-macaddr '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'backup'), 'dest_macaddr'))
                yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'sync_e'), 'enable'), True):
            pass
            yield '   !\n   sync-e\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'sync_e'), 'priority')):
                pass
                yield '      priority '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'sync_e'), 'priority'))
                yield '\n'
        if (t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap')) or t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'))):
            pass
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'native_vlan')):
                pass
                yield '   switchport tap native vlan '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'native_vlan'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'identity'), 'id')):
                pass
                l_1_tap_identity_cli = str_join(('switchport tap identity ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'identity'), 'id'), ))
                _loop_vars['tap_identity_cli'] = l_1_tap_identity_cli
                if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'identity'), 'inner_vlan')):
                    pass
                    l_1_tap_identity_cli = str_join(((undefined(name='tap_identity_cli') if l_1_tap_identity_cli is missing else l_1_tap_identity_cli), ' inner ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'identity'), 'inner_vlan'), ))
                    _loop_vars['tap_identity_cli'] = l_1_tap_identity_cli
                yield '   '
                yield str((undefined(name='tap_identity_cli') if l_1_tap_identity_cli is missing else l_1_tap_identity_cli))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'mac_address'), 'destination')):
                pass
                l_1_tap_mac_address_cli = str_join(('switchport tap mac-address dest ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'mac_address'), 'destination'), ))
                _loop_vars['tap_mac_address_cli'] = l_1_tap_mac_address_cli
                if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'mac_address'), 'source')):
                    pass
                    l_1_tap_mac_address_cli = str_join(((undefined(name='tap_mac_address_cli') if l_1_tap_mac_address_cli is missing else l_1_tap_mac_address_cli), ' src ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'mac_address'), 'source'), ))
                    _loop_vars['tap_mac_address_cli'] = l_1_tap_mac_address_cli
                yield '   '
                yield str((undefined(name='tap_mac_address_cli') if l_1_tap_mac_address_cli is missing else l_1_tap_mac_address_cli))
                yield '\n'
            if (t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'encapsulation'), 'vxlan_strip'), True) and (not t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'mpls_pop_all'), True))):
                pass
                yield '   switchport tap encapsulation vxlan strip\n'
            for l_2_protocol in t_3(environment.getattr(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'encapsulation'), 'gre'), 'protocols'), sort_key='protocol'):
                l_2_tap_encapsulation_cli = resolve('tap_encapsulation_cli')
                _loop_vars = {}
                pass
                if t_14(environment.getattr(l_2_protocol, 'strip'), True):
                    pass
                    l_2_tap_encapsulation_cli = str_join(('switchport tap encapsulation gre protocol ', environment.getattr(l_2_protocol, 'protocol'), ))
                    _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                    if t_14(environment.getattr(l_2_protocol, 'feature_header_length')):
                        pass
                        l_2_tap_encapsulation_cli = str_join(((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli), ' feature header length ', environment.getattr(l_2_protocol, 'feature_header_length'), ))
                        _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                    l_2_tap_encapsulation_cli = str_join(((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli), ' strip', ))
                    _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                    if t_14(environment.getattr(l_2_protocol, 're_encapsulation_ethernet_header'), True):
                        pass
                        l_2_tap_encapsulation_cli = str_join(((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli), ' re-encapsulation ethernet', ))
                        _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                    yield '   '
                    yield str((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli))
                    yield '\n'
            l_2_protocol = l_2_tap_encapsulation_cli = missing
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'encapsulation'), 'gre'), 'strip'), True):
                pass
                yield '   switchport tap encapsulation gre strip\n'
            for l_2_destination in t_3(environment.getattr(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'encapsulation'), 'gre'), 'destinations'), sort_key='destination'):
                l_2_tap_encapsulation_cli = missing
                _loop_vars = {}
                pass
                l_2_tap_encapsulation_cli = str_join(('switchport tap encapsulation gre destination ', environment.getattr(l_2_destination, 'destination'), ))
                _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                if t_14(environment.getattr(l_2_destination, 'source')):
                    pass
                    l_2_tap_encapsulation_cli = str_join(((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli), ' source ', environment.getattr(l_2_destination, 'source'), ))
                    _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                for l_3_destination_protocol in t_3(environment.getattr(l_2_destination, 'protocols'), sort_key='protocol'):
                    l_3_tap_encapsulation_protocol_cli = resolve('tap_encapsulation_protocol_cli')
                    _loop_vars = {}
                    pass
                    if t_14(environment.getattr(l_3_destination_protocol, 'strip'), True):
                        pass
                        l_3_tap_encapsulation_protocol_cli = str_join(((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli), ' protocol ', environment.getattr(l_3_destination_protocol, 'protocol'), ))
                        _loop_vars['tap_encapsulation_protocol_cli'] = l_3_tap_encapsulation_protocol_cli
                        if t_14(environment.getattr(l_3_destination_protocol, 'feature_header_length')):
                            pass
                            l_3_tap_encapsulation_protocol_cli = str_join(((undefined(name='tap_encapsulation_protocol_cli') if l_3_tap_encapsulation_protocol_cli is missing else l_3_tap_encapsulation_protocol_cli), ' feature header length ', environment.getattr(l_3_destination_protocol, 'feature_header_length'), ))
                            _loop_vars['tap_encapsulation_protocol_cli'] = l_3_tap_encapsulation_protocol_cli
                        l_3_tap_encapsulation_protocol_cli = str_join(((undefined(name='tap_encapsulation_protocol_cli') if l_3_tap_encapsulation_protocol_cli is missing else l_3_tap_encapsulation_protocol_cli), ' strip', ))
                        _loop_vars['tap_encapsulation_protocol_cli'] = l_3_tap_encapsulation_protocol_cli
                        if t_14(environment.getattr(l_3_destination_protocol, 're_encapsulation_ethernet_header'), True):
                            pass
                            l_3_tap_encapsulation_protocol_cli = str_join(((undefined(name='tap_encapsulation_protocol_cli') if l_3_tap_encapsulation_protocol_cli is missing else l_3_tap_encapsulation_protocol_cli), ' re-encapsulation ethernet', ))
                            _loop_vars['tap_encapsulation_protocol_cli'] = l_3_tap_encapsulation_protocol_cli
                        yield '   '
                        yield str((undefined(name='tap_encapsulation_protocol_cli') if l_3_tap_encapsulation_protocol_cli is missing else l_3_tap_encapsulation_protocol_cli))
                        yield '\n'
                l_3_destination_protocol = l_3_tap_encapsulation_protocol_cli = missing
                if t_14(environment.getattr(l_2_destination, 'strip'), True):
                    pass
                    l_2_tap_encapsulation_cli = str_join(((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli), ' strip', ))
                    _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                    yield '   '
                    yield str((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli))
                    yield '\n'
            l_2_destination = l_2_tap_encapsulation_cli = missing
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'mpls_pop_all'), True):
                pass
                yield '   switchport tap mpls pop all\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'mpls_pop_all'), True):
                pass
                yield '   switchport tool mpls pop all\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'encapsulation'), 'vn_tag_strip'), True):
                pass
                yield '   switchport tool encapsulation vn-tag strip\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'encapsulation'), 'dot1br_strip'), True):
                pass
                yield '   switchport tool encapsulation dot1br strip\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'allowed_vlan')):
                pass
                yield '   switchport tap allowed vlan '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'allowed_vlan'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'allowed_vlan')):
                pass
                yield '   switchport tool allowed vlan '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'allowed_vlan'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'identity'), 'tag')):
                pass
                yield '   switchport tool identity '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'identity'), 'tag'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'identity'), 'dot1q_dzgre_source')):
                pass
                yield '   switchport tool identity dot1q source dzgre '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'identity'), 'dot1q_dzgre_source'))
                yield '\n'
            elif t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'identity'), 'qinq_dzgre_source')):
                pass
                yield '   switchport tool identity qinq source dzgre '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'identity'), 'qinq_dzgre_source'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'truncation'), 'enabled'), True):
                pass
                l_1_tap_truncation_cli = 'switchport tap truncation'
                _loop_vars['tap_truncation_cli'] = l_1_tap_truncation_cli
                if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'truncation'), 'size')):
                    pass
                    l_1_tap_truncation_cli = str_join(((undefined(name='tap_truncation_cli') if l_1_tap_truncation_cli is missing else l_1_tap_truncation_cli), ' ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'truncation'), 'size'), ))
                    _loop_vars['tap_truncation_cli'] = l_1_tap_truncation_cli
                yield '   '
                yield str((undefined(name='tap_truncation_cli') if l_1_tap_truncation_cli is missing else l_1_tap_truncation_cli))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'default'), 'groups')):
                pass
                yield '   switchport tap default group '
                yield str(t_8(context.eval_ctx, t_3(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'default'), 'groups'), ignore_case=False), ' group '))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'default'), 'nexthop_groups')):
                pass
                yield '   switchport tap default nexthop-group '
                yield str(t_8(context.eval_ctx, t_3(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'default'), 'nexthop_groups'), ignore_case=False), ' '))
                yield '\n'
            for l_2_interface in t_3(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tap'), 'default'), 'interfaces')):
                _loop_vars = {}
                pass
                yield '   switchport tap default interface '
                yield str(l_2_interface)
                yield '\n'
            l_2_interface = missing
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'groups')):
                pass
                l_1_tool_groups = t_8(context.eval_ctx, t_3(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'groups'), ignore_case=False), ' ')
                _loop_vars['tool_groups'] = l_1_tool_groups
                yield '   switchport tool group set '
                yield str((undefined(name='tool_groups') if l_1_tool_groups is missing else l_1_tool_groups))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'dot1q_remove_outer_vlan_tag')):
                pass
                yield '   switchport tool dot1q remove outer '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'dot1q_remove_outer_vlan_tag'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'switchport'), 'tool'), 'dzgre_preserve'), True):
                pass
                yield '   switchport tool dzgre preserve\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'enabled'), True):
            pass
            yield '   traffic-engineering\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'bandwidth')):
            pass
            yield '   traffic-engineering bandwidth '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'bandwidth'), 'number'))
            yield ' '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'bandwidth'), 'unit'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'administrative_groups')):
            pass
            yield '   traffic-engineering administrative-group '
            yield str(t_8(context.eval_ctx, environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'administrative_groups'), ','))
            yield '\n'
        for l_2_srlg in t_3(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'srlgs'), ignore_case=False):
            _loop_vars = {}
            pass
            yield '   traffic-engineering srlg '
            yield str(l_2_srlg)
            yield '\n'
        l_2_srlg = missing
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'metric')):
            pass
            yield '   traffic-engineering metric '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'metric'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'min_delay_static')):
            pass
            yield '   traffic-engineering min-delay static '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'min_delay_static'), 'number'))
            yield ' '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'min_delay_static'), 'unit'))
            yield '\n'
        elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'min_delay_dynamic'), 'twamp_light_fallback')):
            pass
            yield '   traffic-engineering min-delay dynamic twamp-light fallback '
            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'min_delay_dynamic'), 'twamp_light_fallback'), 'number'))
            yield ' '
            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'traffic_engineering'), 'min_delay_dynamic'), 'twamp_light_fallback'), 'unit'))
            yield '\n'
        for l_2_link_tracking_group in t_1(environment.getattr(l_1_ethernet_interface, 'link_tracking_groups'), []):
            _loop_vars = {}
            pass
            yield '   link tracking group '
            yield str(environment.getattr(l_2_link_tracking_group, 'name'))
            yield ' '
            yield str(environment.getattr(l_2_link_tracking_group, 'direction'))
            yield '\n'
        l_2_link_tracking_group = missing
        if (t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'link_tracking'), 'direction')) and t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'link_tracking'), 'groups'))):
            pass
            for l_2_group_name in environment.getattr(environment.getattr(l_1_ethernet_interface, 'link_tracking'), 'groups'):
                _loop_vars = {}
                pass
                yield '   link tracking group '
                yield str(l_2_group_name)
                yield ' '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'link_tracking'), 'direction'))
                yield '\n'
            l_2_group_name = missing
        if t_14(environment.getattr(l_1_ethernet_interface, 'vmtracer'), True):
            pass
            yield '   vmtracer vmware-esx\n'
        for l_2_vrid in t_3(environment.getattr(l_1_ethernet_interface, 'vrrp_ids'), sort_key='id'):
            l_2_delay_cli = resolve('delay_cli')
            l_2_peer_auth_cli = resolve('peer_auth_cli')
            _loop_vars = {}
            pass
            if t_14(environment.getattr(l_2_vrid, 'priority_level')):
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' priority-level '
                yield str(environment.getattr(l_2_vrid, 'priority_level'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(l_2_vrid, 'advertisement'), 'interval')):
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' advertisement interval '
                yield str(environment.getattr(environment.getattr(l_2_vrid, 'advertisement'), 'interval'))
                yield '\n'
            if (t_14(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'enabled'), True) and (t_14(environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'delay'), 'minimum')) or t_14(environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'delay'), 'reload')))):
                pass
                l_2_delay_cli = str_join(('vrrp ', environment.getattr(l_2_vrid, 'id'), ' preempt delay', ))
                _loop_vars['delay_cli'] = l_2_delay_cli
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'delay'), 'minimum')):
                    pass
                    l_2_delay_cli = str_join(((undefined(name='delay_cli') if l_2_delay_cli is missing else l_2_delay_cli), ' minimum ', environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'delay'), 'minimum'), ))
                    _loop_vars['delay_cli'] = l_2_delay_cli
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'delay'), 'reload')):
                    pass
                    l_2_delay_cli = str_join(((undefined(name='delay_cli') if l_2_delay_cli is missing else l_2_delay_cli), ' reload ', environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'delay'), 'reload'), ))
                    _loop_vars['delay_cli'] = l_2_delay_cli
                yield '   '
                yield str((undefined(name='delay_cli') if l_2_delay_cli is missing else l_2_delay_cli))
                yield '\n'
            elif t_14(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'enabled'), False):
                pass
                yield '   no vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' preempt\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'timers'), 'delay'), 'reload')):
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' timers delay reload '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'timers'), 'delay'), 'reload'))
                yield '\n'
            if t_14(environment.getattr(l_2_vrid, 'peer_authentication')):
                pass
                l_2_peer_auth_cli = str_join(('vrrp ', environment.getattr(l_2_vrid, 'id'), ' peer authentication', ))
                _loop_vars['peer_auth_cli'] = l_2_peer_auth_cli
                if (environment.getattr(environment.getattr(l_2_vrid, 'peer_authentication'), 'mode') == 'ietf-md5'):
                    pass
                    l_2_peer_auth_cli = str_join(((undefined(name='peer_auth_cli') if l_2_peer_auth_cli is missing else l_2_peer_auth_cli), ' ietf-md5 key-string', ))
                    _loop_vars['peer_auth_cli'] = l_2_peer_auth_cli
                else:
                    pass
                    l_2_peer_auth_cli = str_join(((undefined(name='peer_auth_cli') if l_2_peer_auth_cli is missing else l_2_peer_auth_cli), ' text', ))
                    _loop_vars['peer_auth_cli'] = l_2_peer_auth_cli
                if t_14(environment.getattr(environment.getattr(l_2_vrid, 'peer_authentication'), 'key_type')):
                    pass
                    l_2_peer_auth_cli = str_join(((undefined(name='peer_auth_cli') if l_2_peer_auth_cli is missing else l_2_peer_auth_cli), ' ', environment.getattr(environment.getattr(l_2_vrid, 'peer_authentication'), 'key_type'), ))
                    _loop_vars['peer_auth_cli'] = l_2_peer_auth_cli
                l_2_peer_auth_cli = str_join(((undefined(name='peer_auth_cli') if l_2_peer_auth_cli is missing else l_2_peer_auth_cli), ' ', t_2(environment.getattr(environment.getattr(l_2_vrid, 'peer_authentication'), 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)), ))
                _loop_vars['peer_auth_cli'] = l_2_peer_auth_cli
                yield '   '
                yield str((undefined(name='peer_auth_cli') if l_2_peer_auth_cli is missing else l_2_peer_auth_cli))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'address')):
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' ipv4 '
                yield str(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'address'))
                yield '\n'
            for l_3_secondary_ip in t_3(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'secondary_addresses')):
                _loop_vars = {}
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' ipv4 '
                yield str(l_3_secondary_ip)
                yield ' secondary\n'
            l_3_secondary_ip = missing
            if t_14(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'version')):
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' ipv4 version '
                yield str(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'version'))
                yield '\n'
            for l_3_ipv6_address in t_3(environment.getattr(environment.getattr(l_2_vrid, 'ipv6'), 'addresses')):
                _loop_vars = {}
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' ipv6 '
                yield str(l_3_ipv6_address)
                yield '\n'
            l_3_ipv6_address = missing
            for l_3_tracked_obj in t_3(environment.getattr(l_2_vrid, 'tracked_object'), sort_key='name', ignore_case=False):
                l_3_tracked_obj_cli = resolve('tracked_obj_cli')
                _loop_vars = {}
                pass
                if t_14(environment.getattr(l_3_tracked_obj, 'name')):
                    pass
                    l_3_tracked_obj_cli = str_join(('vrrp ', environment.getattr(l_2_vrid, 'id'), ' tracked-object ', environment.getattr(l_3_tracked_obj, 'name'), ))
                    _loop_vars['tracked_obj_cli'] = l_3_tracked_obj_cli
                    if t_14(environment.getattr(l_3_tracked_obj, 'decrement')):
                        pass
                        l_3_tracked_obj_cli = str_join(((undefined(name='tracked_obj_cli') if l_3_tracked_obj_cli is missing else l_3_tracked_obj_cli), ' decrement ', environment.getattr(l_3_tracked_obj, 'decrement'), ))
                        _loop_vars['tracked_obj_cli'] = l_3_tracked_obj_cli
                    elif t_14(environment.getattr(l_3_tracked_obj, 'shutdown'), True):
                        pass
                        l_3_tracked_obj_cli = str_join(((undefined(name='tracked_obj_cli') if l_3_tracked_obj_cli is missing else l_3_tracked_obj_cli), ' shutdown', ))
                        _loop_vars['tracked_obj_cli'] = l_3_tracked_obj_cli
                    yield '   '
                    yield str((undefined(name='tracked_obj_cli') if l_3_tracked_obj_cli is missing else l_3_tracked_obj_cli))
                    yield '\n'
            l_3_tracked_obj = l_3_tracked_obj_cli = missing
        l_2_vrid = l_2_delay_cli = l_2_peer_auth_cli = missing
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'media'), 'override')):
            pass
            yield '   transceiver media override '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'media'), 'override'))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'power'), 'ignore'), True):
            pass
            yield '   transceiver power ignore\n'
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'application_override')):
            pass
            yield '   transceiver application override '
            yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'application_override'))
            yield '\n'
        for l_2_application_override in t_1(environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'application_override_lanes'), []):
            l_2_application_override_cli = missing
            _loop_vars = {}
            pass
            l_2_application_override_cli = str_join(('transceiver application override ', environment.getattr(l_2_application_override, 'override'), ' lanes start ', environment.getattr(l_2_application_override, 'first_lane'), ))
            _loop_vars['application_override_cli'] = l_2_application_override_cli
            if t_14(environment.getattr(l_2_application_override, 'last_lane')):
                pass
                l_2_application_override_cli = str_join(((undefined(name='application_override_cli') if l_2_application_override_cli is missing else l_2_application_override_cli), ' end ', environment.getattr(l_2_application_override, 'last_lane'), ))
                _loop_vars['application_override_cli'] = l_2_application_override_cli
            yield '   '
            yield str((undefined(name='application_override_cli') if l_2_application_override_cli is missing else l_2_application_override_cli))
            yield '\n'
        l_2_application_override = l_2_application_override_cli = missing
        if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'frequency')):
            pass
            l_1_frequency_cli = str_join(('transceiver frequency ', t_6('%.3f', t_5(environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'frequency'))), ))
            _loop_vars['frequency_cli'] = l_1_frequency_cli
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'frequency_unit')):
                pass
                l_1_frequency_cli = str_join(((undefined(name='frequency_cli') if l_1_frequency_cli is missing else l_1_frequency_cli), ' ', environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'frequency_unit'), ))
                _loop_vars['frequency_cli'] = l_1_frequency_cli
            yield '   '
            yield str((undefined(name='frequency_cli') if l_1_frequency_cli is missing else l_1_frequency_cli))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'transmitter'), 'signal_power')):
            pass
            yield '   transceiver transmitter signal-power '
            yield str(t_6('%.2f', t_5(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'transmitter'), 'signal_power'))))
            yield '\n'
        if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'transceiver'), 'transmitter'), 'disabled'), True):
            pass
            yield '   transceiver transmitter disabled\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'dot1x')):
            pass
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'pae'), 'mode'), 'authenticator'):
                pass
                yield '   dot1x pae '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'pae'), 'mode'))
                yield '\n'
            elif (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'pae'), 'mode'), 'supplicant') and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'pae'), 'supplicant_profile'))):
                pass
                yield '   dot1x pae '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'pae'), 'mode'))
                yield ' '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'pae'), 'supplicant_profile'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'authentication_failure')):
                pass
                if (t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'authentication_failure'), 'action'), 'allow') and t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'authentication_failure'), 'allow_vlan'))):
                    pass
                    yield '   dot1x authentication failure action traffic allow vlan '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'authentication_failure'), 'allow_vlan'))
                    yield '\n'
                elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'authentication_failure'), 'action'), 'drop'):
                    pass
                    yield '   dot1x authentication failure action traffic drop\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'aaa'), 'unresponsive')):
                pass
                l_1_aaa_config = 'dot1x aaa unresponsive'
                _loop_vars['aaa_config'] = l_1_aaa_config
                l_1_actions = environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'aaa'), 'unresponsive')
                _loop_vars['actions'] = l_1_actions
                for l_2_action in t_13(environment, (undefined(name='actions') if l_1_actions is missing else l_1_actions), reverse=True):
                    l_2_aaa_action_config = resolve('aaa_action_config')
                    l_2_action_apply_config = resolve('action_apply_config')
                    _loop_vars = {}
                    pass
                    if (l_2_action == 'phone_action'):
                        pass
                        l_2_aaa_action_config = str_join(((undefined(name='aaa_config') if l_1_aaa_config is missing else l_1_aaa_config), ' phone action', ))
                        _loop_vars['aaa_action_config'] = l_2_aaa_action_config
                    elif (l_2_action == 'action'):
                        pass
                        l_2_aaa_action_config = str_join(((undefined(name='aaa_config') if l_1_aaa_config is missing else l_1_aaa_config), ' action', ))
                        _loop_vars['aaa_action_config'] = l_2_aaa_action_config
                    if t_14((undefined(name='aaa_action_config') if l_2_aaa_action_config is missing else l_2_aaa_action_config)):
                        pass
                        if t_14(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'apply_cached_results'), True):
                            pass
                            l_2_action_apply_config = 'apply cached-results'
                            _loop_vars['action_apply_config'] = l_2_action_apply_config
                            if (t_14(environment.getattr(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'cached_results_timeout'), 'time_duration')) and t_14(environment.getattr(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'cached_results_timeout'), 'time_duration_unit'))):
                                pass
                                l_2_aaa_action_config = str_join(((undefined(name='aaa_action_config') if l_2_aaa_action_config is missing else l_2_aaa_action_config), ' ', (undefined(name='action_apply_config') if l_2_action_apply_config is missing else l_2_action_apply_config), ' timeout ', environment.getattr(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'cached_results_timeout'), 'time_duration'), ' ', environment.getattr(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'cached_results_timeout'), 'time_duration_unit'), ))
                                _loop_vars['aaa_action_config'] = l_2_aaa_action_config
                        if t_14(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow'), True):
                            pass
                            if t_14(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'apply_alternate'), True):
                                pass
                                l_2_aaa_action_config = str_join(((undefined(name='aaa_action_config') if l_2_aaa_action_config is missing else l_2_aaa_action_config), ' else traffic allow', ))
                                _loop_vars['aaa_action_config'] = l_2_aaa_action_config
                            else:
                                pass
                                l_2_aaa_action_config = str_join(((undefined(name='aaa_action_config') if l_2_aaa_action_config is missing else l_2_aaa_action_config), ' traffic allow', ))
                                _loop_vars['aaa_action_config'] = l_2_aaa_action_config
                        else:
                            pass
                            if (t_14(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow_vlan')) and t_14(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow_access_list'))):
                                pass
                                if t_14(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'apply_alternate'), True):
                                    pass
                                    l_2_aaa_action_config = str_join(((undefined(name='aaa_action_config') if l_2_aaa_action_config is missing else l_2_aaa_action_config), ' else traffic allow vlan ', environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow_vlan'), ' access-list ', environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow_access_list'), ))
                                    _loop_vars['aaa_action_config'] = l_2_aaa_action_config
                                else:
                                    pass
                                    l_2_aaa_action_config = str_join(((undefined(name='aaa_action_config') if l_2_aaa_action_config is missing else l_2_aaa_action_config), ' traffic allow vlan ', environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow_vlan'), ' access-list ', environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow_access_list'), ))
                                    _loop_vars['aaa_action_config'] = l_2_aaa_action_config
                            else:
                                pass
                                if t_14(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow_vlan')):
                                    pass
                                    if t_14(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'apply_alternate'), True):
                                        pass
                                        l_2_aaa_action_config = str_join(((undefined(name='aaa_action_config') if l_2_aaa_action_config is missing else l_2_aaa_action_config), ' else traffic allow vlan ', environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow_vlan'), ))
                                        _loop_vars['aaa_action_config'] = l_2_aaa_action_config
                                    else:
                                        pass
                                        l_2_aaa_action_config = str_join(((undefined(name='aaa_action_config') if l_2_aaa_action_config is missing else l_2_aaa_action_config), ' traffic allow vlan ', environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow_vlan'), ))
                                        _loop_vars['aaa_action_config'] = l_2_aaa_action_config
                                if t_14(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow_access_list')):
                                    pass
                                    if t_14(environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'apply_alternate'), True):
                                        pass
                                        l_2_aaa_action_config = str_join(((undefined(name='aaa_action_config') if l_2_aaa_action_config is missing else l_2_aaa_action_config), ' else traffic allow access list ', environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow_access_list'), ))
                                        _loop_vars['aaa_action_config'] = l_2_aaa_action_config
                                    else:
                                        pass
                                        l_2_aaa_action_config = str_join(((undefined(name='aaa_action_config') if l_2_aaa_action_config is missing else l_2_aaa_action_config), ' traffic allow access list ', environment.getattr(environment.getitem((undefined(name='actions') if l_1_actions is missing else l_1_actions), l_2_action), 'traffic_allow_access_list'), ))
                                        _loop_vars['aaa_action_config'] = l_2_aaa_action_config
                        yield '   '
                        yield str((undefined(name='aaa_action_config') if l_2_aaa_action_config is missing else l_2_aaa_action_config))
                        yield '\n'
                l_2_action = l_2_aaa_action_config = l_2_action_apply_config = missing
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'aaa'), 'unresponsive'), 'eap_response')):
                pass
                yield '   '
                yield str((undefined(name='aaa_config') if l_1_aaa_config is missing else l_1_aaa_config))
                yield ' eap response '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'aaa'), 'unresponsive'), 'eap_response'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'reauthentication'), True):
                pass
                yield '   dot1x reauthentication\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'port_control')):
                pass
                yield '   dot1x port-control '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'port_control'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'port_control_force_authorized_phone'), True):
                pass
                yield '   dot1x port-control force-authorized phone\n'
            elif t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'port_control_force_authorized_phone'), False):
                pass
                yield '   no dot1x port-control force-authorized phone\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'host_mode')):
                pass
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'host_mode'), 'mode'), 'single-host'):
                    pass
                    yield '   dot1x host-mode single-host\n'
                elif t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'host_mode'), 'mode'), 'multi-host'):
                    pass
                    l_1_host_mode_cli = 'dot1x host-mode multi-host'
                    _loop_vars['host_mode_cli'] = l_1_host_mode_cli
                    if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'host_mode'), 'multi_host_authenticated'), True):
                        pass
                        l_1_host_mode_cli = str_join(((undefined(name='host_mode_cli') if l_1_host_mode_cli is missing else l_1_host_mode_cli), ' authenticated', ))
                        _loop_vars['host_mode_cli'] = l_1_host_mode_cli
                    yield '   '
                    yield str((undefined(name='host_mode_cli') if l_1_host_mode_cli is missing else l_1_host_mode_cli))
                    yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'eapol'), 'disabled'), True):
                pass
                yield '   dot1x eapol disabled\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'mac_based_access_list'), True):
                pass
                yield '   dot1x mac based access-list\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'mac_based_authentication'), 'enabled'), True):
                pass
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'mac_based_authentication'), 'host_mode_common'), True):
                    pass
                    yield '   dot1x mac based authentication host-mode common\n'
                    if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'mac_based_authentication'), 'always'), True):
                        pass
                        yield '   dot1x mac based authentication always\n'
                else:
                    pass
                    l_1_auth_cli = 'dot1x mac based authentication'
                    _loop_vars['auth_cli'] = l_1_auth_cli
                    if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'mac_based_authentication'), 'always'), True):
                        pass
                        l_1_auth_cli = str_join(((undefined(name='auth_cli') if l_1_auth_cli is missing else l_1_auth_cli), ' always', ))
                        _loop_vars['auth_cli'] = l_1_auth_cli
                    yield '   '
                    yield str((undefined(name='auth_cli') if l_1_auth_cli is missing else l_1_auth_cli))
                    yield '\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'timeout')):
                pass
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'timeout'), 'quiet_period')):
                    pass
                    yield '   dot1x timeout quiet-period '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'timeout'), 'quiet_period'))
                    yield '\n'
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'timeout'), 'reauth_timeout_ignore'), True):
                    pass
                    yield '   dot1x timeout reauth-timeout-ignore always\n'
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'timeout'), 'tx_period')):
                    pass
                    yield '   dot1x timeout tx-period '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'timeout'), 'tx_period'))
                    yield '\n'
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'timeout'), 'reauth_period')):
                    pass
                    yield '   dot1x timeout reauth-period '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'timeout'), 'reauth_period'))
                    yield '\n'
                if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'timeout'), 'idle_host')):
                    pass
                    yield '   dot1x timeout idle-host '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'timeout'), 'idle_host'))
                    yield ' seconds\n'
            if t_14(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'reauthorization_request_limit')):
                pass
                yield '   dot1x reauthorization request limit '
                yield str(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'reauthorization_request_limit'))
                yield '\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'unauthorized'), 'access_vlan_membership_egress'), True):
                pass
                yield '   dot1x unauthorized access vlan membership egress\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'unauthorized'), 'native_vlan_membership_egress'), True):
                pass
                yield '   dot1x unauthorized native vlan membership egress\n'
            if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'eapol'), 'authentication_failure_fallback_mba'), 'enabled'), True):
                pass
                l_1_auth_failure_fallback_mba = 'dot1x eapol authentication failure fallback mba'
                _loop_vars['auth_failure_fallback_mba'] = l_1_auth_failure_fallback_mba
                if t_14(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'eapol'), 'authentication_failure_fallback_mba'), 'timeout')):
                    pass
                    l_1_auth_failure_fallback_mba = str_join(((undefined(name='auth_failure_fallback_mba') if l_1_auth_failure_fallback_mba is missing else l_1_auth_failure_fallback_mba), ' timeout ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_ethernet_interface, 'dot1x'), 'eapol'), 'authentication_failure_fallback_mba'), 'timeout'), ))
                    _loop_vars['auth_failure_fallback_mba'] = l_1_auth_failure_fallback_mba
                yield '   '
                yield str((undefined(name='auth_failure_fallback_mba') if l_1_auth_failure_fallback_mba is missing else l_1_auth_failure_fallback_mba))
                yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'monitor_link_flap_profiles')):
            pass
            yield '   monitor link-flap profiles '
            yield str(t_8(context.eval_ctx, t_3(environment.getattr(l_1_ethernet_interface, 'monitor_link_flap_profiles'), ignore_case=False), ' '))
            yield '\n'
        if t_14(environment.getattr(l_1_ethernet_interface, 'eos_cli')):
            pass
            yield '   '
            yield str(t_7(environment.getattr(l_1_ethernet_interface, 'eos_cli'), 3, False))
            yield '\n'
    l_1_ethernet_interface = l_1_encapsulation_dot1q_cli = l_1_client_encapsulation = l_1_network_flag = l_1_encapsulation_cli = l_1_network_encapsulation = l_1_address_locking_cli = l_1_dfe_algo_cli = l_1_dfe_hold_time_cli = l_1_non_default_vrf = l_1_default_vrf = l_1_host_proxy_cli = l_1_tcp_mss_ceiling_cli = l_1_interface_ip_nat = l_1_hide_passwords = l_1_poe_link_down_action_cli = l_1_poe_limit_cli = l_1_sorted_vlans_cli = l_1_isis_auth_cli = l_1_both_key_ids = l_1_rate_limit_count = l_1_backup_link_cli = l_1_tap_identity_cli = l_1_tap_mac_address_cli = l_1_tap_truncation_cli = l_1_tool_groups = l_1_frequency_cli = l_1_aaa_config = l_1_actions = l_1_host_mode_cli = l_1_auth_cli = l_1_auth_failure_fallback_mba = missing

blocks = {}
debug_info = '7=97&8=100&10=135&11=137&12=139&13=143&16=146&17=149&19=151&20=154&22=156&24=159&27=162&28=165&30=167&31=170&33=172&35=175&38=178&39=181&41=183&42=186&44=188&45=191&47=193&48=196&50=198&51=201&53=203&54=206&56=208&57=211&59=213&61=216&64=219&65=222&67=224&70=229&72=232&75=235&77=238&81=241&84=244&85=247&87=249&88=252&90=254&92=257&93=260&95=262&96=265&98=267&99=270&101=272&104=275&107=278&108=281&110=283&111=286&113=288&114=291&116=293&117=296&119=298&122=301&123=305&125=308&127=311&130=314&131=316&132=318&133=320&135=323&137=325&138=328&140=330&141=332&142=334&143=336&144=338&145=340&146=342&147=344&148=346&150=350&152=352&153=354&154=356&157=358&158=360&160=362&161=364&162=366&163=368&164=370&165=372&166=374&167=376&168=378&170=382&173=384&174=386&175=388&176=390&180=393&183=395&184=398&186=400&187=404&188=406&189=408&190=410&191=412&192=414&193=416&196=418&197=421&199=424&200=426&201=430&202=432&203=434&204=436&205=438&207=440&208=443&211=446&212=448&213=452&214=454&215=456&216=458&217=460&218=462&221=464&222=467&226=470&227=473&229=475&230=478&232=480&235=483&238=486&241=489&244=492&247=495&250=498&251=500&252=502&253=504&255=506&256=508&258=511&260=513&263=516&264=519&266=521&267=524&269=526&270=528&272=531&273=533&274=535&275=537&277=540&279=542&280=544&281=546&282=548&284=551&286=553&288=556&292=559&293=562&295=564&296=567&298=569&299=572&302=574&303=577&305=579&306=582&308=584&310=587&313=590&314=593&316=595&317=598&318=600&319=604&322=607&325=610&328=613&331=616&332=619&334=621&337=624&339=630&341=633&344=636&345=640&346=642&347=644&349=646&350=648&352=651&354=654&355=656&356=658&357=660&358=664&359=666&360=668&362=670&363=672&364=674&365=676&367=678&368=680&370=683&373=686&376=689&379=692&380=694&381=697&382=699&383=702&384=704&385=706&386=710&389=717&390=719&391=723&394=730&395=733&398=738&399=742&401=747&402=750&404=754&405=757&408=761&411=764&412=767&414=769&415=772&417=774&420=777&423=780&424=784&425=786&426=788&427=790&428=792&431=794&432=796&434=799&436=802&437=804&438=806&439=808&441=810&442=812&444=814&445=816&447=819&449=821&450=824&451=828&452=831&454=833&455=836&457=838&458=841&461=843&462=846&464=848&465=851&467=853&468=856&470=858&471=861&473=863&474=866&476=868&477=871&479=873&482=876&484=879&487=882&490=885&493=888&494=891&496=893&498=896&501=899&502=902&504=904&505=906&506=910&507=912&508=914&510=917&512=920&513=924&515=927&518=930&522=933&524=936&527=939&528=941&529=943&530=949&531=952&534=954&535=956&541=962&542=965&544=967&547=970&549=973&552=976&553=979&555=983&556=986&558=988&559=991&560=994&563=1003&564=1006&566=1008&569=1011&572=1014&575=1017&576=1020&578=1022&579=1025&581=1027&582=1030&584=1032&585=1035&587=1037&590=1040&591=1043&593=1045&594=1048&596=1050&597=1052&598=1054&599=1056&601=1059&603=1061&604=1064&606=1066&609=1069&610=1071&611=1073&612=1075&613=1077&615=1079&616=1081&618=1084&620=1086&623=1089&626=1092&627=1094&629=1097&630=1099&636=1105&638=1108&640=1111&641=1114&643=1116&644=1118&645=1120&646=1122&647=1125&648=1129&649=1131&652=1134&653=1138&656=1141&657=1144&661=1146&664=1149&665=1152&667=1154&668=1157&670=1159&671=1162&673=1164&674=1167&676=1169&677=1172&679=1174&680=1177&682=1179&683=1182&685=1184&686=1187&688=1189&689=1192&691=1194&692=1197&694=1199&695=1202&697=1204&698=1206&701=1212&704=1214&705=1217&707=1219&708=1222&710=1224&711=1227&713=1229&715=1232&718=1235&719=1238&720=1241&721=1243&722=1246&725=1249&726=1252&728=1259&729=1262&731=1269&732=1271&734=1274&737=1277&739=1280&742=1283&744=1286&748=1289&749=1292&751=1294&754=1297&755=1300&757=1302&758=1305&760=1307&763=1310&765=1313&768=1316&771=1319&772=1321&776=1323&777=1325&778=1327&779=1329&780=1331&782=1333&783=1335&785=1338&787=1342&792=1344&793=1346&794=1348&795=1350&796=1352&798=1354&799=1356&801=1359&803=1361&808=1363&809=1365&810=1367&811=1369&812=1371&814=1373&815=1375&817=1378&820=1380&821=1382&822=1385&823=1386&824=1389&826=1400&829=1409&830=1412&831=1414&832=1417&834=1428&838=1437&839=1440&840=1442&841=1445&843=1456&847=1465&848=1468&850=1474&851=1477&853=1481&854=1484&858=1488&859=1491&860=1493&861=1496&863=1503&867=1508&868=1510&869=1513&871=1518&874=1520&876=1523&879=1526&881=1529&884=1532&886=1535&889=1538&891=1541&894=1544&895=1546&898=1552&901=1554&903=1557&906=1560&907=1562&908=1564&909=1566&911=1569&913=1571&915=1574&918=1577&919=1579&920=1581&921=1583&923=1586&924=1588&925=1591&927=1593&928=1596&930=1598&931=1601&933=1603&934=1606&936=1608&937=1611&940=1613&943=1616&944=1619&947=1621&948=1623&949=1626&951=1628&952=1630&953=1632&954=1634&956=1637&958=1639&959=1641&960=1643&961=1645&963=1648&965=1650&968=1653&969=1657&970=1659&971=1661&972=1663&974=1665&975=1667&976=1669&978=1672&981=1675&984=1678&985=1682&986=1684&987=1686&989=1688&990=1692&991=1694&992=1696&993=1698&995=1700&996=1702&997=1704&999=1707&1002=1710&1003=1712&1004=1715&1007=1718&1010=1721&1013=1724&1016=1727&1019=1730&1020=1733&1022=1735&1023=1738&1025=1740&1026=1743&1028=1745&1029=1748&1030=1750&1031=1753&1033=1755&1034=1757&1035=1759&1036=1761&1038=1764&1040=1766&1041=1769&1043=1771&1044=1774&1046=1776&1047=1780&1049=1783&1050=1785&1051=1788&1053=1790&1054=1793&1057=1795&1061=1798&1064=1801&1065=1804&1067=1808&1068=1811&1070=1813&1071=1817&1073=1820&1074=1823&1076=1825&1077=1828&1078=1832&1079=1835&1081=1839&1082=1843&1084=1848&1085=1850&1086=1854&1089=1859&1092=1862&1093=1867&1094=1870&1096=1874&1097=1877&1099=1881&1102=1883&1103=1885&1104=1887&1106=1889&1107=1891&1109=1894&1110=1896&1111=1899&1113=1901&1114=1904&1116=1908&1117=1910&1118=1912&1119=1914&1121=1918&1123=1920&1124=1922&1126=1924&1127=1927&1129=1929&1130=1932&1132=1936&1133=1940&1135=1945&1136=1948&1138=1952&1139=1956&1141=1961&1142=1965&1143=1967&1144=1969&1145=1971&1146=1973&1147=1975&1149=1978&1153=1982&1154=1985&1156=1987&1159=1990&1160=1993&1162=1995&1163=1999&1164=2001&1165=2003&1167=2006&1169=2009&1170=2011&1171=2013&1172=2015&1174=2018&1176=2020&1177=2023&1179=2025&1182=2028&1183=2030&1184=2033&1185=2035&1186=2038&1188=2042&1189=2044&1191=2047&1192=2049&1196=2052&1197=2054&1198=2056&1199=2058&1200=2063&1201=2065&1202=2067&1203=2069&1205=2071&1206=2073&1207=2075&1208=2077&1209=2079&1212=2081&1213=2083&1214=2085&1216=2089&1219=2093&1220=2095&1221=2097&1223=2101&1226=2105&1227=2107&1228=2109&1230=2113&1233=2115&1234=2117&1235=2119&1237=2123&1242=2126&1246=2129&1247=2132&1249=2136&1252=2139&1253=2142&1255=2144&1257=2147&1260=2150&1261=2152&1263=2155&1264=2157&1265=2159&1266=2161&1268=2164&1271=2166&1274=2169&1277=2172&1278=2174&1280=2177&1284=2182&1285=2184&1286=2186&1288=2189&1291=2191&1292=2193&1293=2196&1295=2198&1298=2201&1299=2204&1301=2206&1302=2209&1304=2211&1305=2214&1308=2216&1309=2219&1311=2221&1314=2224&1317=2227&1318=2229&1319=2231&1320=2233&1322=2236&1325=2238&1326=2241&1328=2243&1329=2246'