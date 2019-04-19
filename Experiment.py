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
from abc import ABCMeta, abstractmethod


class Experiment():
    __metaclass__ = ABCMeta

    RANGE_START = 10
    RANGE_END = 22
    LAUNCH_WAIT = 20
    BATCH_SZ = 10
    VIRT = NotImplemented
    APT = spawn.find_executable("apt-get")
    CONTAINER = NotImplemented

    def __init__(self, exp_dir=None):
        parser = argparse.ArgumentParser(description="Configures and runs Ken's PhD Experiment")
        parser.add_argument("--clean", action="store_true", default=False, dest="clean",
                            help="Removes all generated files and directories")
        parser.add_argument("--configure", action="store_true", default=False, dest="configure",
                            help="Generates the config files and directories")
        parser.add_argument("-v", action="store_true", default=False, dest="verbose",
                            help="Print experiment activity info")
        parser.add_argument("--range", action="store", dest="range",
                            help="Specifies the experiment start and end range in format #,#")
        parser.add_argument("--run", action="store_true", default=False, dest="run",
                            help="Runs the currently configured experiment")
        parser.add_argument("--end", action="store_true", default=False, dest="end",
                            help="End the currently running experiment")
        parser.add_argument("-info", action="store_true", default=False, dest="info",
                            help="Displays the current experiment configuration")
        parser.add_argument("--setup", action="store_true", default=False, dest="setup",
                            help="Installs software requirements. Requires run as root.")
        parser.add_argument("--pull", action="store_true", default=False, dest="pull",
                            help="Pulls the kcratie/ringroute:0.1 image from docker hub")
        parser.add_argument("--lxd", action="store_true", default=False, dest="lxd",
                            help="Uses LXC containers")
        parser.add_argument("--dkr", action="store_true", default=False, dest="dkr",
                            help="Use docker containers")

        self.args = parser.parse_args()
        self.range_end = Experiment.RANGE_END
        self.range_start = Experiment.RANGE_START
        if self.args.range:
            rng = self.args.range.rsplit(",", 2)
            self.range_end = int(rng[1])
            self.range_start = int(rng[0])

        self.total_inst = self.range_end - self.range_start
        self.seq_list = [None] * self.total_inst
        self.exp_dir = exp_dir
        if not self.exp_dir:
            self.exp_dir = os.path.abspath(".")
        self.template_file = "{0}/template-config.json".format(self.exp_dir)
        self.config_dir = "{0}/config".format(self.exp_dir)
        self.cores_dir = "{0}/cores".format(self.exp_dir)
        self.logs_dir = "{0}/log".format(self.exp_dir)
        self.config_file_base = "{0}/config-".format(self.config_dir)
        self.seq_file = "{0}/startup.list".format(self.exp_dir)

    @classmethod
    def runshell(cls, cmd):
        """ Run a shell command. if fails, raise an exception. """
        if cmd[0] is None:
            raise ValueError("No executable specified to run")
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p

    @property
    @abstractmethod
    def gen_config(self, range_start, range_end):
        pass

    @property
    @abstractmethod
    def start_instance(self, instance):
        pass

    @property
    @abstractmethod
    def end(self):
        pass

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

    def configure(self):
        self.gen_config(self.range_start, self.range_end)
        self.gen_rand_seq(self.range_start, self.range_end)

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
            self.gen_rand_seq(self.range_start, self.range_end)

    def start_all(self, num, wait, mode="random"):
        cnt = 0
        sequence = self.seq_list
        if mode == "seqential":
            sequence = range(self.range_start, self.range_end)
        elif mode == "reversed":
            sequence = range(self.range_end, self.range_start, -1)
        for inst in sequence:
            self.start_instance(inst)
            cnt += 1
            if cnt % num == 0 and cnt < len(sequence):
                time.sleep(wait)
        if self.args.verbose:
            print("{0} container(s) instantiated".format(len(self.seq_list)))

    def run(self):
        if not os.path.isdir(self.config_dir):
            self.gen_config(self.range_start, self.range_end)

        if os.path.isfile(self.seq_file):
            self.load_seq_list()
        else:
            self.gen_rand_seq(self.range_start, self.range_end)

        if os.path.isdir(self.logs_dir):
            shutil.rmtree(self.logs_dir)

        self.start_all(Experiment.BATCH_SZ, Experiment.LAUNCH_WAIT, "random")

    def display_current_config(self):
        print("----Experiment Configuration----")
        print("{0} instances range {1}-{2}".format(self.total_inst, self.range_start,
                                                   self.range_end))
        print("Config files are {0}".format(self.config_dir))
        print("".format())

    def setup_system(self):
        setup_cmds = [["./setup-system.sh"]]
        for cmd_list in setup_cmds:
            resp = Experiment.runshell(cmd_list)
            if self.args.verbose:
                print(cmd_list)
                print(resp.stdout.decode("utf-8") if resp.returncode == 0 else
                      resp.stderr.decode("utf-8"))


class LxdExperiment(Experiment):
    VIRT = spawn.find_executable("lxd")
    CONTAINER = "ipop-lxd{0}"

    def __init__(self, exp_dir=None):
        super().__init__(exp_dir=exp_dir)

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

    def start_instance(self, instance):
        container = LxdExperiment.CONTAINER.format(instance)
        cfg_file = "{0}{1}.json".format(self.config_file_base, instance)
        if not os.path.isfile(cfg_file):
            self.gen_config(instance, instance+1)

        dst = "{0}/etc/opt/ipop-vpn/config.json".format(container)
        cmd_list = [LxdExperiment.VIRT, "file", "push", cfg_file, dst]

        # resp = Experiment.runshell(cmd_list)
        if self.args.verbose:
            print(cmd_list)
         #   print(resp.stdout.decode("utf-8") if resp.returncode == 0 \
         #       else resp.stderr.decode("utf-8"))

        cmd_list = [LxdExperiment.VIRT, "start", container]

        #resp = Experiment.runshell(cmd_list)
        if self.args.verbose:
            print(cmd_list)
        #    print(resp.stdout.decode("utf-8") if resp.returncode == 0 \
        #        else resp.stderr.decode("utf-8"))

    def end(self):
        pass


class DockerExperiment(Experiment):
    VIRT = spawn.find_executable("docker")
    CONTAINER = "ipop-dkr{0}"

    def __init__(self, exp_dir=None):
        super().__init__(exp_dir=exp_dir)

    #def configure(self):
    #    super().configure()
    #    self.pull_image()

    def gen_config(self, range_start, range_end):
        with open(self.template_file) as fd:
            template = json.load(fd)
        node_id = template["CFx"].get("NodeId", "a000###feb6040628e5fb7e70b04f###")
        node_name = template["OverlayVisualizer"].get("NodeName", "dkr###")
        node_ip = template["BridgeController"]["Overlays"]["101000F"].get("IP4", "10.10.100.###")

        for val in range(range_start, range_end):
            rng_str = "{0:03}".format(val)
            cfg_file = "{0}{1}.json".format(self.config_file_base, rng_str)
            node_id = "{0}{1}{2}{1}{3}".format(node_id[:4], rng_str, node_id[7:29], node_id[32:])
            node_name = "{0}{1}".format(node_name[:3], rng_str)
            node_ip = "{0}{1}".format(node_ip[:10], val)

            template["CFx"]["NodeId"] = node_id
            template["OverlayVisualizer"]["NodeName"] = node_name
            template["BridgeController"]["Overlays"]["101000F"]["IP4"] = node_ip
            os.makedirs(self.config_dir, exist_ok=True)
            with open(cfg_file, "w") as f:
                json.dump(template, f, indent=2)
                f.flush()
        if self.args.verbose:
            print("{0} config file(s) generated".format(range_end-range_start))

    def start_instance(self, instance):
        instance = "{0:03}".format(instance)
        container = DockerExperiment.CONTAINER.format(instance)
        log_dir = "{0}/dkr{1}".format(self.logs_dir, instance)
        os.makedirs(log_dir, exist_ok=True)

        cfg_file = "{0}{1}.json".format(self.config_file_base, instance)
        if not os.path.isfile(cfg_file):
            self.gen_config(instance, instance+1)

        mount_cfg = "{0}:/etc/opt/ipop-vpn/config.json".format(cfg_file)
        mount_log = "{0}/:/var/log/ipop-vpn/".format(log_dir)
        args = ["--rm", "--privileged"]
        opts = "-d"
        img = "kcratie/ringroute:0.1"
        cmd = "/sbin/init"

        cmd_list = [DockerExperiment.VIRT, "run", opts, "-v", mount_cfg, "-v", mount_log,
                    args[0], args[1], "--name", container, img, cmd]

        resp = Experiment.runshell(cmd_list)
        if self.args.verbose:
            print(cmd_list)
            print(resp.stdout.decode("utf-8") if resp.returncode == 0
                  else resp.stderr.decode("utf-8"))

    def pull_image(self):
        cmd_list = [DockerExperiment.VIRT, "pull", "kcratie/ringroute:0.1"]
        resp = Experiment.runshell(cmd_list)
        if self.args.verbose:
            print(resp)

    def stop_all_containers(self):
        cmd_list = [DockerExperiment.VIRT, "stop"]
        for inst in range(self.range_start, self.range_end):
            inst = "{0:03}".format(inst)
            container = DockerExperiment.CONTAINER.format(inst)
            cmd_list.append(container)
        resp = Experiment.runshell(cmd_list)
        if self.args.verbose:
            print(cmd_list)
            print(resp.stdout.decode("utf-8") if resp.returncode == 0 else
                  resp.stderr.decode("utf-8"))

    def end(self):
        self.stop_all_containers()


def main():
    exp = DockerExperiment()
    if exp.args.lxd:
        exp = LxdExperiment()

    if exp.args.run and exp.args.end:
        print("Error! Both run and end were specified.")
        return

    if exp.args.info:
        exp.display_current_config()
        return

    if exp.args.setup:
        exp.setup_system()

    if exp.args.pull:
        exp.pull_image()

    if exp.args.clean:
        exp.make_clean()

    if exp.range_end - exp.range_start <= 0:
        print("Invalid range, please fix RANGE_START={0} RANGE_END={1}".
              format(exp.range_start, exp.range_end))
        return

    if exp.args.configure:
        exp.configure()

    if exp.args.run:
        exp.run()
        return

    if exp.args.end:
        exp.end()
        return


if __name__ == "__main__":
    main()
