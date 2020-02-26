#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 19:23:39 2020

@author: trent
"""
import psutil
import readline
import shlex
import subprocess

def list_active_processes():
    """
    List all running processes in the system.
    @return: list[Process]
    """
    return psutil.process_iter()


class ProcessAffinityTuner(object):
    def __init__(self):
        self.selection = []
        self.cmd_map = {
            "autobind": self.handle_autobind,
            "fullbind": self.handle_fullbind,
            "bind": self.handle_bind,
            "exit": self.handle_exit,
            "help": self.handle_help,
            "pgrep": self.handle_pgrep,
            "ps": self.handle_ps,
            "quit": self.handle_exit,
            "reset": self.handle_reset,
            "select": self.handle_select,
            "threads": self.handle_threads,
        }
        
    def handle_help(self, items):
        """
        Show usage.
        """
        if not items:
            print("Available commands:")
            for k in self.cmd_map.keys():
                doc = self.cmd_map[k].__doc__
                short_doc = doc.strip().split("\n")[0]
                print("  {:<10} {}".format(k, short_doc))
        else:
            for k in items:
                cmds = [x for x in self.cmd_map.keys() if x.startswith(items[0])]
                for cmd in cmds:
                    print("{}{}".format(cmd, self.cmd_map[cmd].__doc__))
        return True
        
    def handle_exit(self, items):
        """
        Exit the program.
        """
        return False
    
    def print_process_list(self, items, long=False, threads=False):
        cpu_count = psutil.cpu_count()
        f = "{:<6} {:^" + str(cpu_count) + "} {}"
        print(f.format("PID", "AFNT", "CMD"))
        for p in items:
            affinity = p.cpu_affinity()
            a = [0] * cpu_count
            for x in affinity:
                a[x] = 1
            affinity_str = ''.join(str(x) for x in reversed(a))
            process = p.name()
            if long:
                process = ' '.join(p.cmdline())
            line = f.format(p.pid, affinity_str, process)
            print(line)
    
    def find_processes(self, items):
        result = []
        procs = psutil.process_iter()
        for p in procs:
            match = False
            cmd = ' '.join(p.cmdline())
            cmd_upper = cmd.upper()
            for x in items:
                if x.upper() in cmd_upper or x == str(p.pid):
                    match = True
            if match:
                result.append(p)
        return result

    def handle_pgrep(self, items):
        """
        Search for processes with given key words
        Usage:
            pgrep [word...]
        """
        result = self.find_processes(items)
        self.print_process_list(result, True)
        return True
        
    def handle_ps(self, items):
        """
        Print all currently running processes
        """
        result = psutil.process_iter()
        self.print_process_list(result)
        
        return True
        
    def handle_reset(self, items):
        """
        Reset selection.
        """
        self.selection = []
        return True
    
    def handle_select(self, items):
        """
        Add processes to selection.
        Usage:
            select [pid...]
        """
        result = self.find_processes(items)
        self.print_process_list(result)
        self.selection += result
        
        # clean up selection, delete items if they no longer exist
        self.selection = [x for x in self.selection if psutil.pid_exists(x.pid)]
        
        return True

    def get_threads_for_processes(self, items):
        result = []
        for x in items:
            if isinstance(x, psutil.Process):
                pid = x.pid
            else:
                pid = int(x)
            if psutil.pid_exists(pid):
                threads = psutil.Process(pid).threads()
                for t in threads:
                    result.append(psutil.Process(t[0]))
        return result
    
    def handle_threads(self, items):
        """
        Print threads in processes.
        
        Usage:
            threads [pid...]
            
        If pid is not specified, current selection is used
        """
        if items:
            procs = self.find_processes(items)
        else:
            procs = self.selection
        result = self.get_threads_for_processes(procs)
        self.print_process_list(result)
        return True
    
    def handle_bind(self, items):
        """
        Bind a process to a few cpus.
        
        Usage:
            bind 12345 0,1,2,3,4
        """
        pid = items[0]
        cpus = items[1]
        cmd = ["/usr/bin/taskset", "-pc", cpus, pid]
        subprocess.call(cmd)
        return True

    def handle_autobind(self, items):
        """
        Bind selected threads to CPUs evenly.

        Usage:
            autobind [process...]
        """
        if not items:
            items = self.selection
        else:
            items = self.find_processes(items)
        threads = self.get_threads_for_processes(items)
        cpu_count = psutil.cpu_count()
        cpu = 0
        for p in threads:
            args = [str(p.pid), str(cpu)]
            self.handle_bind(args)
            cpu = (cpu + 1) % cpu_count
        return True

    def handle_fullbind(self, items):
        """
        Bind selected threads to all CPUs.

        Usage:
            fullbind [process...]
        """

        if not items:
            items = self.selection
        else:
            items = self.find_processes(items)
        threads = self.get_threads_for_processes(items)
        cpu_count = psutil.cpu_count()
        cpus = ','.join(str(x) for x in range(cpu_count))
        for p in threads:
            args = [str(p.pid), cpus]
            self.handle_bind(args)
        return True
            
    def run(self):
        while True:
            try:
                line = input("cmd: ")
            except EOFError:
                break
            items = shlex.split(line)
            if not items:
                continue
            cmds = [x for x in self.cmd_map.keys() if x.startswith(items[0])]
            if len(cmds) == 1:
                if not self.cmd_map[cmds[0]](items[1:]):
                    break
            elif len(cmds) == 0:
                print("Unknown command")
                self.handle_help([])
            else:
                print("Ambiguous commands", cmds)
        print("Bye")


if __name__ == '__main__':
    tuner = ProcessAffinityTuner()
    tuner.run()
    
