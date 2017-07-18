#!/usr/bin/env python

import argparse
import copy
from jinja2 import Environment, FileSystemLoader
import os
import shutil
import yaml
from sklearn.model_selection import ParameterGrid
import hashlib
import subprocess

def create_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configs_dir", help="configs dir", type=str, required=True)
    parser.add_argument("-w", "--working_dir", help="working dir", type=str, required=True)
    return parser


def build_working_dir_core(configs_dir, working_dir, ret):
    for f in os.listdir(configs_dir):
        next_configs_f = os.path.join(configs_dir, f)
        next_working_f = os.path.join(working_dir, f)
        if os.path.isfile(next_configs_f) and f == 'config.yml':
            origin_path = os.path.join(working_dir, 'origin')
            if os.path.exists(origin_path) :
                shutil.rmtree(origin_path)
            shutil.copytree(configs_dir, os.path.join(working_dir, 'origin'))
            ret.append({"config_dir": configs_dir, "working_dir":working_dir})
        elif os.path.isdir(next_configs_f):
            if not os.path.exists(next_working_f):
                os.makedirs(next_working_f)
            build_working_dir_core(next_configs_f, next_working_f, ret)


def build_working_dir(configs_dir, working_dir):
    ret = []
    build_working_dir_core(configs_dir, working_dir, ret)
    return ret

def validate_config(config):
    if not 'order' in config:
        raise RuntimeError('invalid config order')


def render_each_parameter_and_run(config, parameter):
    config_dir = config['config_dir']
    env = Environment(loader=FileSystemLoader(config_dir, encoding='utf8'))
    h = hashlib.md5(str(parameter).encode('utf-8')).hexdigest()
    print('hash:', h)
    print('parameter:', parameter)
    working_dir = os.path.join(config['working_dir'], h)
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    shutil.copytree(config_dir, working_dir)
    if config['data']['templates'] is not None :
        for template_path in config['data']['templates']:
            output_path = os.path.join(working_dir, template_path)
            template = env.get_template(template_path)
            rendered_file_str = template.render(parameter)

            with open(output_path, 'w') as f:
                f.write(rendered_file_str)
    print('start to run.sh')
    command = ['./run.sh']
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd=working_dir)
    outs, _ = proc.communicate()
    print(outs)
    print('finish run.sh')

def render_and_run(config):
    config_dir = config['config_dir']
    if config['data']['template_parameters'] is None:
        render_each_parameter_and_run(config, None)
    else:
        parameters = ParameterGrid(config['data']['template_parameters'])
        for parameter in parameters:
            render_each_parameter_and_run(config, parameter)

def main():
    parser = create_argparse()
    args = parser.parse_args()
    if not os.path.exists(args.working_dir):
        os.makedirs(args.working_dir)
    config_dirs = build_working_dir(args.configs_dir, args.working_dir)

    configs = []
    for dirs in config_dirs:
        with open(os.path.join(dirs['config_dir'], 'config.yml'), 'r') as f:
            config = copy.deepcopy(dirs)
            data = yaml.load(f)
            validate_config(data)
            config["data"] = data
            configs.append(config)

    for i, config in enumerate(sorted(configs, key=lambda x: x['data']['order'])):
        print(i, config['config_dir'])
        render_and_run(config)



if __name__ == '__main__':
    main()
