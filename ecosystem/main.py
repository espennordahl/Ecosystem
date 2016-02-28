#!/usr/bin/python

# Copyright (c) 2014, Peregrine Labs, a division of Peregrine Visual Storytelling Ltd. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of Peregrine Visual Storytelling Ltd., Peregrine Labs
#      and any of it's affiliates nor the names of any other contributors
#      to this software may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import glob
import os
import platform
import subprocess
import sys
from environment import Tool, Environment

from settings import MAKE_COMMAND, MAKE_TARGET


def list_available_tools():
    """Reads all of the found .env files, parses the tool name and version creates a list."""
    environment_files = os.path.join(os.getenv('ECO_ENV'), '*.env')
    possible_tools = [Tool(file_name) for file_name in glob.glob(environment_files)]
    tool_names = [new_tool.tool_plus_version for new_tool in possible_tools if new_tool.platform_supported]
    return sorted(list(set(tool_names)))


def call_process(arguments):
    if platform.system().lower() == 'windows':
        subprocess.call(arguments, shell=True)
    else:
        subprocess.call(arguments)


def ecosystem(tools=None, run_application=None, set_environment=False, force_rebuild=False, quick_build=False,
              run_build=False, deploy=False):
    tools = tools or []
    if run_build:
        env = Environment(tools)
        if env.success:
            env.set_env(os.environ)
            build_type = os.getenv('PG_BUILD_TYPE')

            if not quick_build:
                if force_rebuild:
                    try:
                        open('CMakeCache.txt')
                        os.remove('CMakeCache.txt')
                    except IOError:
                        print "Cache doesn't exist..."

                call_process(['cmake', '-DCMAKE_BUILD_TYPE={0}'.format(build_type), '-G', MAKE_TARGET, '..'])

            if deploy:
                MAKE_COMMAND.append("package")

            call_process(MAKE_COMMAND)

    elif run_application:
        env = Environment(tools)
        if env.success:
            env.set_env(os.environ)
            call_process([run_application])

    elif set_environment:
        env = Environment(tools)
        if env.success:
            output = env.get_env()
            if output:
                print output


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    # parse the (command line) arguments; python 2.7+ (or download argparse)
    import argparse
    description = 'Peregrine Ecosystem, environment, build and deploy management toolset v0.1.1'
    parser = argparse.ArgumentParser(prog='ecosystem',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     description=description,
                                     epilog='''
Example:
    python ecosystem.py -t maya2014,vray3.05,yeti1.3.0 -r maya
                                     ''')
    parser.add_argument('-t', '--tools', type=str, default=None,
                        help='specify a list of tools required separated by commas')
    parser.add_argument('-l', '--listtools', action='store_true',
                        help='list the available tools')
    parser.add_argument('-b', '--build', action='store_true',
                        help='run the desired build process')
    parser.add_argument('-d', '--deploy', action='store_true',
                        help='build and package the tool for deployment')
    parser.add_argument('-f', '--force', action='store_true',
                        help='force the full CMake cache to be rebuilt')
    parser.add_argument('-m', '--make', action='store_true',
                        help='just run make')
    parser.add_argument('-r', '--run', type=str, default=None,
                        help='run an application')
    parser.add_argument('-s', '--setenv', action='store_true',
                        help='output setenv statements to be used to set the shells environment')

    args = parser.parse_args(argv)

    if args.listtools:
        for tool in list_available_tools():
            print tool
        return 0

    tools = args.tools.split(',') if args.tools is not None else []
    run_application = args.run
    set_environment = args.setenv
    force_rebuild = args.force
    quick_build = args.make
    run_build = args.build
    deploy = args.deploy
    if deploy:
        force_rebuild = True
        run_build = True
        quick_build = False

    try:
        ecosystem(tools, run_application, set_environment, force_rebuild, quick_build, run_build, deploy)
        return 0
    except Exception, e:
        sys.stderr.write('ERROR: {0:s}'.format(str(e)))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
