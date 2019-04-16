# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# Import the Emulab specific extensions.
import geni.rspec.emulab as emulab

# Create a portal object,
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# Node node
node = request.RawPC('node')
node.disk_image = 'urn:publicid:IDN+utah.cloudlab.us+image+xos-PG0:Ubuntu18.04-amd64-20190107'

# Install and execute scripts on the node
node.addService(pg.Install(url="https://github.com/kcratie/KenExperiment/releases/download/untagged-8d74e9d9ede5cf9f9393/rr-exp.tar.gz", path="/local"))
node.addService(pg.Execute(shell="bash", command="/local/rr-exp/setup-system.sh"))

# Set the Site
node.Site('Site 1')

# Print the generated rspec
pc.printRequestRSpec(request)