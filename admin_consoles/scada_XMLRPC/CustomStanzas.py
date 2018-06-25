from sleekxmpp.xmlstream import ElementBase


class ADMMStepOverview(ElementBase):
    """
      A stanza class for XML content of the form:
      <admm_step_overview xmlns="sleekxmpp:custom:admm_step_overviews">
        <iteration>X</iteration>
        <opt_time>X</opt_time>
        <wait_time>X</wait_time>
        <x_opt>X</x_opt>
        <beta>X</beta>
        <nu>X</nu>
        <z>X</z>
      </admm_step_overview>
      """
    name = 'admm_step_overview'
    namespace = 'sleekxmpp:custom:admm_step_overviews'
    plugin_attrib = 'admm_step_overview'
    interfaces = set(('iteration', 'opt_time', 'wait_time', 'x_opt', 'beta', 'nu', 'z'))
    sub_interfaces = interfaces
