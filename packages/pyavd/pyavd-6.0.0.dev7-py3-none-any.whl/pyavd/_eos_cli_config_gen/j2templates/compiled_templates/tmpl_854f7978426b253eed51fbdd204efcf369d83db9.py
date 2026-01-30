from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/all-community-lists.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_ip_community_lists = resolve('ip_community_lists')
    l_0_ip_extcommunity_lists = resolve('ip_extcommunity_lists')
    l_0_ip_extcommunity_lists_regexp = resolve('ip_extcommunity_lists_regexp')
    l_0_ip_large_community_lists = resolve('ip_large_community_lists')
    try:
        t_1 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if (((t_1((undefined(name='ip_community_lists') if l_0_ip_community_lists is missing else l_0_ip_community_lists)) or t_1((undefined(name='ip_extcommunity_lists') if l_0_ip_extcommunity_lists is missing else l_0_ip_extcommunity_lists))) or t_1((undefined(name='ip_extcommunity_lists_regexp') if l_0_ip_extcommunity_lists_regexp is missing else l_0_ip_extcommunity_lists_regexp))) or t_1((undefined(name='ip_large_community_lists') if l_0_ip_large_community_lists is missing else l_0_ip_large_community_lists))):
        pass
        yield '!\n'
        template = environment.get_template('eos/ip-community-lists.j2', 'eos/all-community-lists.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        template = environment.get_template('eos/ip-extcommunity-lists.j2', 'eos/all-community-lists.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        template = environment.get_template('eos/ip-extcommunity-lists-regexp.j2', 'eos/all-community-lists.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        template = environment.get_template('eos/ip-large-community-lists.j2', 'eos/all-community-lists.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()

blocks = {}
debug_info = '6=21&12=24&14=30&16=36&18=42'