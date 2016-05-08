from __future__ import print_function

from metakernel import MetaKernel

import os

from metakernel_images import (
    extract_image_filenames, display_data_for_image, image_setup_cmd
)

_TEXT_SAVED_PYDOT = "metakernel_bash_kernel: saved pydot data to:"

pydot_setup_cmd = """
pydot () {
    local TMPDIR=${TMPDIR-/tmp}/metakernel_bash_kernel
    [ ! -d $TMPDIR ] && mkdir -p $TMPDIR
    TMPFILE=$(mktemp ${TMPDIR-/tmp}/pydot.XXXXXXXXXX)
    cat > $TMPFILE
""" + """
    echo "%s $TMPFILE" >&2
}
""" % _TEXT_SAVED_PYDOT

source_metakernelrc_cmd = """
[ -f ~/.metakernelrc ] && source ~/.metakernelrc
"""

def extract_pydot_filenames(output):
    output_lines = []
    pydot_filenames = []

    for line in output.split("\n"):
        if line.startswith(_TEXT_SAVED_PYDOT):
            filename = line.rstrip().split(": ")[-1]
            pydot_filenames.append(filename)
        else:
            output_lines.append(line)

    output = "\n".join(output_lines)
    return pydot_filenames, output


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

    functions_sent=False

    root_path_prefix=''
    for cygwin_candidate_path in cygwin_candidate_paths:
        if os.path.exists(cygwin_candidate_path):
            root_path_prefix=cygwin_candidate_path
            break

    def get_usage(self):
        #return "This is the bash kernel."
        return "This is the bash kernel - not a very helpful usage message is it ?"

    def do_execute_direct(self, code):
        if not code.strip():
            return
        #print("code=<<<<" + str(code) + ">>>>")
        #print("type=" + str(type(self)))
        self.log.debug('execute: %s' % code)
        shell_magic = self.line_magics['shell']

        # Send function definitions if not already done:
        if not MetaKernelBash.functions_sent:
            MetaKernelBash.functions_sent=True
            ## print("TEST: " + shell_magic.eval( "date" ))
            ## print("Sending image_setup_cmd<<" + image_setup_cmd + ">>")
            resp = shell_magic.eval(image_setup_cmd)
            ## print("resp=<<" + resp + ">>")
            ## print("TEST: " + shell_magic.eval( "date" ))
            ## print("Sending pydot_setup_cmd<<" + pydot_setup_cmd + ">>")
            resp = shell_magic.eval(pydot_setup_cmd)
            resp = shell_magic.eval(source_metakernelrc_cmd)
            ## print("resp=<<" + resp + ">>")
            ## print("TEST: " + shell_magic.eval( "date" ))

        ## print("Sending code<<" + code.strip() + ">>")
        resp = shell_magic.eval(code.strip())
        #resp = shell_magic.line_shell(code.strip())
        ## print("resp=<<" + resp + ">>")
        ## print("TEST: " + shell_magic.eval( "date" ))

        #--------------------------------
        #if not silent:
        image_filenames, resp = extract_image_filenames(resp)
        pydot_filenames, resp = extract_pydot_filenames(resp)

        # Send standard output
        #print("Sending 'stream_content'")
        # stream_content = {'name': 'stdout', 'text': resp}
        # self.send_response(self.iopub_socket, 'stream', stream_content)

        # Send pydot commands, if any
        for filename in pydot_filenames:
            try:
                # Modify filename path to add cygwin prefix:
                filename = MetaKernelBash.root_path_prefix + filename
                lines = '\n'.join( open(filename, 'r').readlines() )
                #shell_magic = self.line_magics['pydot']
                shell_magic = self.cell_magics['dot']
                ## print("lines->pydot:" + lines) 
                #resp = shell_magic.dot_cell(lines)
                # cell_dot(self)
                # line_dot(self, code)
                resp = shell_magic.line_dot(lines)
                ## print("resp=<<" + resp + ">>")
                #data = display_data_for_image(filename)
                return resp
            except ValueError as e:
                #print("Sending 'stream message'")
                message = {'name': 'stdout', 'text': str(e)}
                self.send_response(self.iopub_socket, 'stream', message)
            #else:
                #print("Sending 'display_data message'")
                #self.send_response(self.iopub_socket, 'display_data', data)

        # Send images, if any
        for filename in image_filenames:
            try:
                # Modify filename path to add cygwin prefix:
                filename = MetaKernelBash.root_path_prefix + filename
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
