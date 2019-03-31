try:
    import simplejson as json
except ImportError:
    import json
import os
import subprocess
import math
import random
from distutils import spawn
import pickle
import argparse
import shutil

class Experiment():

    RANGE_START=10
    RANGE_END=20
    DOCKER = spawn.find_executable("docker")

    def __init__(self, exp_dir=None):
        parser = argparse.ArgumentParser(description="Configures and runs Ken's PhD Experiment")
        parser.add_argument("-clean", action="store_true", default=False, dest="clean",
                            help="Removes all generated files and directories")
        parser.add_argument("-configure", action="store_true", default=False, dest="configure",
                            help="Generates the config files and directories")
        parser.add_argument("-v", action="store_true", default=False, dest="verbose",
                            help="Print on screen activity report")
        parser.add_argument("-run", action="store_true", default=True, dest="run",
                            help="Runs the currently configured experiment")

        self.args = parser.parse_args()
        self.total_inst = Experiment.RANGE_END - Experiment.RANGE_START
        self.seq_list = [None] * self.total_inst
        self.exp_dir = exp_dir
        if not self.exp_dir:
            self.exp_dir = os.path.abspath(".")
        self.template_file="{0}/template-config.json".format(self.exp_dir)
        self.config_dir="{0}/config".format(self.exp_dir)
        self.log_dir="{0}/log".format(self.exp_dir)
        self.config_file="{0}/config/config-dkr".format(self.exp_dir)
        self.seq_file = "{0}/startup.list".format(self.exp_dir)

    @classmethod
    def runshell(cls, cmd):
        """ Run a shell command. if fails, raise an exception. """
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode != 0:
            err = "Subprocess: \"{0}\" failed, std err = {1}".format(str(cmd), str(p.stderr))
            raise RuntimeError(err)
        return p


    def gen_config(self, range_start, range_end):
        with open(self.template_file) as fd:
            template = json.load(fd)
        node_id = template["CFx"].get("NodeId", "a0000##0eb6040628e5fb7e70b046f##")
        node_name = template["OverlayVisualizer"].get("NodeName", "dkr##")
        node_ip = template["BridgeController"]["Overlays"]["101000F"].get("IP4", "10.10.100.##")

        for val in range(range_start, range_end):
            rng_str = str(val)
            filename = "{0}{1}.json".format(self.config_file, val)
            node_id = "{0}{1}{2}{3}{4}".format(node_id[:5], rng_str, node_id[7:30],
                                                   rng_str, node_id[32:])
            node_name = "{0}{1}".format(node_name[:3], rng_str)
            node_ip = "{0}{1}".format(node_ip[:10], rng_str)

            template["CFx"]["NodeId"] = node_id
            template["OverlayVisualizer"]["NodeName"] = node_name
            template["BridgeController"]["Overlays"]["101000F"]["IP4"] = node_ip
            os.makedirs(self.config_dir, exist_ok=True)
            with open(filename, "w") as f:
                json.dump(template, f, indent=2)
                f.flush()
        if self.args.verbose:
            print("{0} config file(s) generated".format(range_end-range_start))

    def gen_rand_seq(self, range_start, range_end):
        count = 0
        total_attempts = 0
        while count < self.total_inst:
            total_attempts += 1
            inst = math.floor(random.uniform(range_start, range_end))
            if inst not in self.seq_list:
                self.seq_list[count] = inst
                count += 1

        with open(self.seq_file, "wb") as fd:
            pickle.dump(self.seq_list, fd)
            fd.flush()
        if self.args.verbose:
            print("Startup sequence generated, {0} entries, {1} total attempts"
                  .format(self.total_inst, total_attempts))

    def load_seq_list(self):
        if os.path.isfile(self.seq_file):
            with open(self.seq_file, "rb") as fd:
                self.seq_list = pickle.load(fd)
            if self.args.verbose:
                print("Sequence list loaded from existing file ", self.seq_file)
        else:
            self.gen_rand_seq(Experiment.RANGE_START, Experiment.RANGE_END)

    def create_docker_image(self):
        cmd_list = [Experiment.DOCKER, "build", "-t", "kcratie/ringroute:0.0", "."]
        resp = Experiment.runshell(cmd_list)
        if self.args.verbose:
            print(resp)

    def random_start_all(self):
        args = ["--rm", "--privileged"]
        opts = "-itd"
        img = "kcratie/ringroute:0.0"
        cmd = "/sbin/init"
        for inst in self.seq_list:
            os.makedirs(self.log_dir+"/dkr{0}".format(inst), exist_ok=True)
            cfg_file = "{0}/config/config-dkr{1}.json".format(self.exp_dir, inst)
            if not os.path.isfile(cfg_file):
                self.gen_config(inst, inst+1)
            continer = "ipop-dkr{0}".format(inst)
            mount_cfg = "{0}/config/config-dkr{1}.json:/etc/opt/ipop-vpn/config.json".\
                format(self.exp_dir, inst)
            mount_log = "{0}/log/dkr{1}/:/var/log/ipop-vpn/".format(self.exp_dir, inst)
            cmd_list = [Experiment.DOCKER, "run", opts, "-v", mount_cfg, "-v", mount_log, args[0], args[1], "--name", continer, img, cmd]
            resp = Experiment.runshell(cmd_list)
            if self.args.verbose:
                print(resp)
                #print(cmd_list)
        if self.args.verbose:
            print("{} docker container(s) instantiated".format(len(self.seq_list)))

    def clean_config(self):
        if os.path.isdir(self.config_dir):
            shutil.rmtree(self.config_dir)
            if self.args.verbose:
                print("Removed dir {}".format(self.config_dir))
        if os.path.isfile(self.seq_file):
            os.remove(self.seq_file)
            if self.args.verbose:
                print("Removed file {}".format(self.seq_file))

    def make_clean(self):
        self.clean_config()
        if os.path.isdir(self.log_dir):
            shutil.rmtree(self.log_dir)
            if self.args.verbose:
                print("Removed dir {}".format(self.log_dir))

    def run(self):
        #if not os.path.isdir(self.CFG_DIR):
        #    self.gen_config(Experiment.RANGE_START, Experiment.RANGE_END)
        if os.path.isfile(self.seq_file):
            self.load_seq_list()
        else:
            self.gen_rand_seq(Experiment.RANGE_START, Experiment.RANGE_END)
        self.random_start_all()

def main():
    exp = Experiment()
    if exp.args.clean:
        exp.make_clean()
        return

    if Experiment.RANGE_END - Experiment.RANGE_START <= 0:
        print("Invalid range {0}, please fix RANGE_START={1} RANGE_END={2}".\
            format(Experiment.RANGE_START, Experiment.RANGE_END))
        return

    if exp.args.configure:
        exp.clean_config()
        exp.gen_config(Experiment.RANGE_START, Experiment.RANGE_END)
        exp.gen_rand_seq(Experiment.RANGE_START, Experiment.RANGE_END)
        return

    if exp.args.run:
        exp.run()

if __name__ == "__main__":
    main()
