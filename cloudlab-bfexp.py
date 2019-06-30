"""This profile allocates two bare metal nodes and connects them together via a Dell or Mellanox switch with layer1 links. 

Instructions:
Click on any node in the topology and choose the `shell` menu item. When your shell window appears, use `ping` to test the link.

You will be able to ping the other node through the switch fabric. We have installed a minimal configuration on your
switches that enables the ports that are in use, and turns on spanning-tree (RSTP) in case you inadvertently created a loop with your topology. All
unused ports are disabled. The ports are in Vlan 1, which effectively gives a single broadcast domain. If you want anything fancier, you will need
to open up a shell window to your switches and configure them yourself.

If your topology has more then a single switch, and you have links between your switches, we will enable those ports too, but we do not put them into
switchport mode or bond them into a single channel, you will need to do that yourself.

If you make any changes to the switch configuration, be sure to write those changes to memory. We will wipe the switches clean and restore a default
configuration when your experiment ends."""

# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# Import the Emulab specific extensions.
import geni.rspec.emulab as emulab

# Create a portal context.
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

pc.defineParameter("phystype", "Switch type",
                   portal.ParameterType.STRING, "dell-s4048",
                   [('mlnx-sn2410', 'Mellanox SN2410'),
                    ('dell-s4048',  'Dell S4048')])

# Retrieve the values the user specifies during instantiation.
params = pc.bindParameters()

# Do not run snmpit
#request.skipVlans()

# Add Switch to the request and give it a couple of interfaces
mysw = request.Switch("mysw");
mysw.hardware_type = params.phystype
swiface1 = mysw.addInterface()
swiface2 = mysw.addInterface()
swiface3 = mysw.addInterface()
swiface4 = mysw.addInterface()

# Add a raw PC to the request and give it an interface.
node1 = request.RawPC("node1")
node1.disk_image = 'urn:publicid:IDN+utah.cloudlab.us+image+xos-PG0:Ubuntu18.04-amd64-20190107'
iface1 = node1.addInterface()
# Specify the IPv4 address
iface1.addAddress(pg.IPv4Address("192.168.1.1", "255.255.255.0"))

# Add another raw PC to the request and give it an interface.
node2 = request.RawPC("node2")
node2.disk_image = 'urn:publicid:IDN+utah.cloudlab.us+image+xos-PG0:Ubuntu18.04-amd64-20190107'
iface2 = node2.addInterface()
# Specify the IPv4 address
iface2.addAddress(pg.IPv4Address("192.168.1.2", "255.255.255.0"))

# Add another raw PC to the request and give it an interface.
node3 = request.RawPC("node3")
node3.disk_image = 'urn:publicid:IDN+utah.cloudlab.us+image+xos-PG0:Ubuntu18.04-amd64-20190107'
iface3 = node3.addInterface()
# Specify the IPv4 address
iface3.addAddress(pg.IPv4Address("192.168.1.3", "255.255.255.0"))

# Add another raw PC to the request and give it an interface.
node4 = request.RawPC("node4")
node4.disk_image = 'urn:publicid:IDN+utah.cloudlab.us+image+xos-PG0:Ubuntu18.04-amd64-20190107'
iface4 = node4.addInterface()
# Specify the IPv4 address
iface4.addAddress(pg.IPv4Address("192.168.1.4", "255.255.255.0"))

# Add L1 link from node1 to mysw
link1 = request.L1Link("link1")
link1.addInterface(iface1)
link1.addInterface(swiface1)

# Add L1 link from node2 to mysw
link2 = request.L1Link("link2")
link2.addInterface(iface2)
link2.addInterface(swiface2)

# Add L1 link from node3 to mysw
link3 = request.L1Link("link3")
link3.addInterface(iface3)
link3.addInterface(swiface3)

# Add L1 link from node4 to mysw
link4 = request.L1Link("link4")
link4.addInterface(iface4)
link4.addInterface(swiface4)

# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)