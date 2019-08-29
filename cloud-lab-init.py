"""
Single bare-metal amd64 Ubuntu 18.04 node running RingRoute in Docker
containers.

Instructions:
As root (sudo su), run the update-limits.sh script and reboot before starting
containers. Update the template-config with your current Signal and Visualizer
server addresses.
To run an experiment from the workspace/experiment directory perform the
following steps:
source exp-venv/bin/activate
python ./Experiment.py --clean --configure --pull --run --range 10,35
You can set the range to values between 1 and 255 but each system can
handle only about 25 containers. """


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
node.disk_image = 'urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU18-64-OSNM-Q'

# Set the Site
node.Site('Site 1')

# Print the generated rspec
pc.printRequestRSpec(request)
