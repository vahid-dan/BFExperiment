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
import time

class Experiment():

    RANGE_START = 10
    RANGE_END = 20
    LAUNCH_WAIT = 18
    DOCKER = spawn.find_executable("docker")
    APT = spawn.find_executable("apt-get")
    CONTAINER = "ipop-dkr{0}"

    def __init__(self, exp_dir=None):
        parser = argparse.ArgumentParser(description="Configures and runs Ken's PhD Experiment")
        parser.add_argument("-clean", action="store_true", default=False, dest="clean",
                            help="Removes all generated files and directories")
        parser.add_argument("-configure", action="store_true", default=False, dest="configure",
                            help="Generates the config files and directories")
        parser.add_argument("-v", action="store_true", default=False, dest="verbose",
                            help="Print on screen activity report")
        parser.add_argument("-run", action="store_true", default=False, dest="run",
                            help="Runs the currently configured experiment")
        parser.add_argument("-end", action="store_true", default=False, dest="end",
                            help="End the currently running experiment")
        parser.add_argument("-info", action="store_true", default=False, dest="info",
                            help="Displays the current experiment configuration")
        parser.add_argument("-setup", action="store_true", default=False, dest="setup",
                            help="Displays the current experiment configuration")
        parser.add_argument("-pullimage", action="store_true", default=False, dest="pull_image",
                            help="Pulls the kcratie/ringroute:0.1 image from docker hub")

        self.args = parser.parse_args()
        self.total_inst = Experiment.RANGE_END - Experiment.RANGE_START
        self.seq_list = [None] * self.total_inst
        self.exp_dir = exp_dir
        if not self.exp_dir:
            self.exp_dir = os.path.abspath(".")
        self.template_file = "{0}/template-config.json".format(self.exp_dir)
        self.config_dir = "{0}/config".format(self.exp_dir)
        self.cores_dir = "{0}/cores".format(self.exp_dir)
        self.logs_dir = "{0}/log".format(self.exp_dir)
        self.config_file_base = "{0}/config-dkr".format(self.config_dir)
        self.seq_file = "{0}/startup.list".format(self.exp_dir)

    @classmethod
    def runshell(cls, cmd):
        """ Run a shell command. if fails, raise an exception. """
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #if p.returncode != 0:
        #    err = "Subprocess: \"{0}\" failed, std err = {1}".format(str(cmd), str(p.stderr))
        #    raise RuntimeError(err)
        return p

    def gen_config(self, range_start, range_end):
        with open(self.template_file) as fd:
            template = json.load(fd)
        node_id = template["CFx"].get("NodeId", "a0000##0eb6040628e5fb7e70b046f##")
        node_name = template["OverlayVisualizer"].get("NodeName", "dkr##")
        node_ip = template["BridgeController"]["Overlays"]["101000F"].get("IP4", "10.10.100.##")

        for val in range(range_start, range_end):
            rng_str = str(val)
            cfg_file = "{0}{1}.json".format(self.config_file_base, val)
            node_id = "{0}{1}{2}{1}{3}".format(node_id[:5], rng_str, node_id[7:30], node_id[32:])
            node_name = "{0}{1}".format(node_name[:3], rng_str)
            node_ip = "{0}{1}".format(node_ip[:10], rng_str)

            template["CFx"]["NodeId"] = node_id
            template["OverlayVisualizer"]["NodeName"] = node_name
            template["BridgeController"]["Overlays"]["101000F"]["IP4"] = node_ip
            os.makedirs(self.config_dir, exist_ok=True)
            with open(cfg_file, "w") as f:
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
            print("Startup sequence generated, {0} entries, {1} total attempts\n{2}"
                  .format(self.total_inst, total_attempts, self.seq_list))

    def load_seq_list(self):
        if os.path.isfile(self.seq_file):
            with open(self.seq_file, "rb") as fd:
                self.seq_list = pickle.load(fd)
                if len(self.seq_list) != self.total_inst:
                    print("Warning: the number of entries in sequence list does not match the "
                          "configured experiment range. {0}!={1}".
                          format(len(self.seq_list), self.total_inst))
            if self.args.verbose:
                print("Sequence list loaded from existing file -  {0} entries\n{1}".
                      format(len(self.seq_list), self.seq_list))
        else:
            self.gen_rand_seq(Experiment.RANGE_START, Experiment.RANGE_END)


    def start_instance(self, instance):
        container = Experiment.CONTAINER.format(instance)
        log_dir = "{0}/dkr{1}".format(self.logs_dir, instance)
        os.makedirs(log_dir, exist_ok=True)

        cfg_file = "{0}{1}.json".format(self.config_file_base, instance)
        if not os.path.isfile(cfg_file):
            self.gen_config(instance, instance+1)

        core_dir = "{0}/{1}/".format(self.cores_dir, container)
        os.makedirs(core_dir, exist_ok=True)

        mount_cfg = "{0}:/etc/opt/ipop-vpn/config.json".format(cfg_file)
        mount_log = "{0}/:/var/log/ipop-vpn/".format(log_dir)
        mount_core = "{0}:/var/cores/".format(core_dir)
        args = ["--rm", "--privileged"]
        opts = "-d"
        img = "kcratie/ringroute:0.1"
        cmd = "/sbin/init"

        cmd_list = [Experiment.DOCKER, "run", opts, "-v", mount_cfg, "-v", mount_log,
                    "-v", mount_core, args[0], args[1], "--name", container, img, cmd]

        resp = Experiment.runshell(cmd_list)
        if self.args.verbose:
            print(cmd_list)
            print(resp.stdout.decode("utf-8") if resp.returncode == 0 \
                else resp.stderr.decode("utf-8"))

    def start_all(self, num, wait, mode="random"):
        cnt = 1
        sequence = self.seq_list
        if mode == "seqential":
            sequence = range(Experiment.RANGE_START, Experiment.RANGE_END)
        elif mode == "reversed":
            sequence = range(Experiment.RANGE_END, Experiment.RANGE_START, -1)
        for inst in sequence:
            if cnt % num == 0:
                time.sleep(wait)
            self.start_instance(inst)
            cnt += 1
        if self.args.verbose:
            print("{0} docker container(s) instantiated".format(len(self.seq_list)))

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
        if os.path.isdir(self.logs_dir):
            shutil.rmtree(self.logs_dir)
            if self.args.verbose:
                print("Removed dir {}".format(self.logs_dir))
        if os.path.isdir(self.cores_dir):
            shutil.rmtree(self.cores_dir)
            if self.args.verbose:
                print("Removed dir {}".format(self.cores_dir))

    def run(self):
        if not os.path.isdir(self.config_dir):
            self.gen_config(Experiment.RANGE_START, Experiment.RANGE_END)

        if os.path.isfile(self.seq_file):
            self.load_seq_list()
        else:
            self.gen_rand_seq(Experiment.RANGE_START, Experiment.RANGE_END)

        if os.path.isdir(self.logs_dir):
            shutil.rmtree(self.logs_dir)

        self.start_all(3, Experiment.LAUNCH_WAIT, "random")

    def stop_all_containers(self):
        cmd_list = [Experiment.DOCKER, "stop"]
        for inst in range(Experiment.RANGE_START, Experiment.RANGE_END):
            container = Experiment.CONTAINER.format(inst)
            cmd_list.append(container)
        resp = Experiment.runshell(cmd_list)
        if self.args.verbose:
            print(cmd_list)
            print(resp.stdout.decode("utf-8") if resp.returncode == 0 else \
                resp.stderr.decode("utf-8"))

    def display_current_config(self):
        print("----Experiment Configuration----")
        print("{0} instances range {1}-{2}".format(self.total_inst, Experiment.RANGE_START, Experiment.RANGE_END))
        print("Config files are {0}".format(self.config_dir))
        print("".format())

    def setup_system(self):
        setup_cmds = [["./setup-python.sh"], ["./setup-docker.sh"]]
        for cmd_list in setup_cmds:
            resp = Experiment.runshell(cmd_list)
            if self.args.verbose:
                print(cmd_list)
                print(resp.stdout.decode("utf-8") if resp.returncode == 0 else \
                    resp.stderr.decode("utf-8"))

    def docker_pull_image(self):
        cmd_list = [Experiment.DOCKER, "pull", "kcratie/ringroute:0.1"]
        resp = Experiment.runshell(cmd_list)
        if self.args.verbose:
            print(resp)


def main():
    exp = Experiment()
    if exp.args.run and exp.args.end:
        print("Error! Both run and end were specified.")
        return

    if exp.args.info:
        exp.display_current_config()
        return

    if exp.args.setup:
        exp.setup_system()

    if exp.args.pull_image:
        exp.docker_pull_image()

    if exp.args.clean:
        exp.make_clean()

    if Experiment.RANGE_END - Experiment.RANGE_START <= 0:
        print("Invalid range, please fix RANGE_START={0} RANGE_END={1}".
              format(Experiment.RANGE_START, Experiment.RANGE_END))
        return

    if exp.args.configure:
        exp.clean_config()
        exp.gen_config(Experiment.RANGE_START, Experiment.RANGE_END)
        exp.gen_rand_seq(Experiment.RANGE_START, Experiment.RANGE_END)


    if exp.args.run:
        exp.run()
        return

    if exp.args.end:
        exp.stop_all_containers()
        return

if __name__ == "__main__":
    main()
