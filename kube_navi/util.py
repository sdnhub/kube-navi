import subprocess
import logging
import yaml
import os


class Utilities(object):
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.m_logger = logging.getLogger(__name__)

    def cmd_execute(self, host_to_ssh='', cmd_to_execute='', local_host=True):
        '''
        This method ssh into the passwordless accessible host and execute any command
        :param host_to_ssh: Host IP or FDN
        :param cmd_to_execute: Command to be executed in the host
        :param local_host: "True" if cmd_to_execute should be done on local host, else "False"
        :return: "True" if ssh and cmd execution is successful, else "False"
        '''

        cmd_status = False
        if local_host:
            ssh_cmd_execute = subprocess.Popen(['%s' % cmd_to_execute], shell=True, stdout=subprocess.PIPE,
                                               stderr=subprocess.STDOUT)
        else:
            ssh_cmd_execute = subprocess.Popen(['ssh', '%s' % host_to_ssh, cmd_to_execute], stdout=subprocess.PIPE,
                                               stderr=subprocess.STDOUT)
        ssh_cmd_execute.wait()
        cmd_stdout = ssh_cmd_execute.stdout
        cmd_stderr = ssh_cmd_execute.stderr

        if ssh_cmd_execute.returncode:
            cmd_output = cmd_stderr.readlines() if cmd_stderr else cmd_stdout.readlines()
            self.m_logger.error('CMD RETURNCODE FOR %s : %s' % (cmd_to_execute, ssh_cmd_execute.returncode))
            self.m_logger.error('CMD OUTPUT FOR %s : %s' % (cmd_to_execute, cmd_output))
        else:
            cmd_output = cmd_stdout.readlines() if cmd_stdout else ssh_cmd_execute.returncode
            self.m_logger.debug('CMD OUTPUT FOR %s : %s' % (cmd_to_execute, cmd_output))
            cmd_status = True

        return cmd_status, cmd_output

    def get_yaml_dict(self, yml_file):
        '''
        This method will generate the yml_dict from a given yml_file
        :param yml_file: fullpath of the yml_file
        :return: yml_dict
        '''
        with open(yml_file) as des_yml:
            yml_file_dict = yaml.load(des_yml)
        des_yml.close()
        return yml_file_dict

    def is_yaml_file_a_descriptor(self, yml_file):
        '''
        This method will return True if yml_file is a descriptor, else False
        :param yml_file: yml_file: fullpath of the yml_file
        :return: True, if yml_file is a Descriptor, False, if it is not a descriptor
        '''
        is_descriptor = False
        with open(yml_file) as des_yml:
            for line in des_yml:
                if line.strip().startswith('kind'):
                    is_descriptor = True
                    break
        des_yml.close()
        return is_descriptor

    def get_yaml_files_list(self, yml_location):
        '''
        This method gets the yml_location_list and get all the yml files into a single list yml_files
        :param yml_location_list: full path yml location/dir
        :return: yml_files
        '''
        yml_files = [os.path.join(root, file_name) for root, dirs, files in os.walk(yml_location)
                     for file_name in files if file_name.endswith(('.yaml', '.yml'))]
        return yml_files
