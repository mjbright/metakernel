from __future__ import print_function

from metakernel import MetaKernel

import os

from metakernel_images import (
    extract_image_filenames, display_data_for_image, image_setup_cmd
)

cygwin_candidate_paths=['c:/cygwin', 'c:/cygwin64', 'c:/tools/cygwin']

class MetaKernelBash(MetaKernel):
    implementation = 'MetaKernel Bash'
    implementation_version = '1.0'
    language = 'bash'
    language_version = '0.1'
    banner = "MetaKernel Bash - interact with bash"
    language_info = {
        'mimetype': 'text/x-bash',
        'name': 'bash',
        # ------ If different from 'language':
        # 'codemirror_mode': {
        #    "version": 2,
        #    "name": "ipython"
        # }
        # 'pygments_lexer': 'language',
        # 'version'       : "x.y.z",
        'file_extension': '.sh',
        'help_links': MetaKernel.help_links,
    }

    image_function_sent=False

    image_path_prefix=''
    for cygwin_candidate_path in cygwin_candidate_paths:
        if os.path.exists(cygwin_candidate_path):
            image_path_prefix=cygwin_candidate_path
            break

    '''
    def __init__(self, **kwargs):
        # Register Bash function to write image data to temporary file
        print("type=" + str(type(self)))
        #shell_magic = self.line_magics['shell']
        #resp = shell_magic.eval(image_setup_cmd)
        return None
    '''

    def get_usage(self):
        #return "This is the bash kernel."
        return "This is the bash kernel - that's not very helpful is it ?"

    def do_execute_direct(self, code):
        if not code.strip():
            return
        #print("type=" + str(type(self)))
        self.log.debug('execute: %s' % code)
        shell_magic = self.line_magics['shell']

        # Send 'display()' definition if not already done:
        if not MetaKernelBash.image_function_sent:
            MetaKernelBash.image_function_sent=True
            shell_magic.eval(image_setup_cmd)

        resp = shell_magic.eval(code.strip())

        #--------------------------------
        #if not silent:
        image_filenames, resp = extract_image_filenames(resp)

        # Send standard output
        #print("Sending 'stream_content'")
        # stream_content = {'name': 'stdout', 'text': resp}
        # self.send_response(self.iopub_socket, 'stream', stream_content)

        # Send images, if any
        for filename in image_filenames:
            try:
                # Modify filename path to add cygwin prefix:
                filename = MetaKernelBash.image_path_prefix + filename
                data = display_data_for_image(filename)
            except ValueError as e:
                #print("Sending 'stream message'")
                message = {'name': 'stdout', 'text': str(e)}
                self.send_response(self.iopub_socket, 'stream', message)
            else:
                #print("Sending 'display_data message'")
                self.send_response(self.iopub_socket, 'display_data', data)
        #--------------------------------

        self.log.debug('execute done')
        return resp.strip()

    def get_completions(self, info):
        shell_magic = self.line_magics['shell']
        return shell_magic.get_completions(info)

    def get_kernel_help_on(self, info, level=0, none_on_fail=False):
        code = info['code'].strip()
        if not code or len(code.split()) > 1:
            if none_on_fail:
                return None
            else:
                return ""
        shell_magic = self.line_magics['shell']
        return shell_magic.get_help_on(info, level, none_on_fail)

    def repr(self, data):
        return data

if __name__ == '__main__':
    try:
        from ipykernel.kernelapp import IPKernelApp
    except ImportError:
        from IPython.kernel.zmq.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=MetaKernelBash)
