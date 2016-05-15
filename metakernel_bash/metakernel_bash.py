from __future__ import print_function

from metakernel import MetaKernel
from IPython.display import HTML

import sys, os
import base64
import imghdr

def get_metakernelrc_path():
    # Location of this script:
    #print('sys.argv[0] =', sys.argv[0])             
    pathname = os.path.dirname(sys.argv[0])        

    #pathname = pathname.replace('\\', '/')
    for root, dirs, files in os.walk(pathname):
        if 'metakernel' in root:
            path = root.split('/')
            #print((len(path) - 1) * '---', os.path.basename(root))
            for file in files:
                if 'metakernelrc' in file:
                    #print(len(path) * '---', file)
                    filepath='/'.join(path)  + '/' + file
                    filepath = filepath.replace('\\', '/')
                    
                    #print(filepath)
                    return(filepath)

    print("ERROR: failed to find package metakernelrc under <{}>".pathname)
    sys.exit(1)

metakernelrc = get_metakernelrc_path()

source_metakernelrc_cmd = """

[ -f {} ]              && source {}
[ -f ~/.metakernelrc ] && source ~/.metakernelrc

""".format( metakernelrc, metakernelrc )

_TEXT_SAVED_EXTENSION = "metakernel_bash_kernel: saved EXTENSION("

def extract_extension_filenames(output):
    output_lines = []
    extensions = []
    extension_filenames = []

    for line in output.split("\n"):
        if line.startswith(_TEXT_SAVED_EXTENSION):
            restpos = line.find( _TEXT_SAVED_EXTENSION ) + len( _TEXT_SAVED_EXTENSION )
            extension = line[ restpos : line.find( ')' ) ]
            extensions.append(extension)

            filename = line.rstrip().split(": ")[-1]
            extension_filenames.append(filename)
        else:
            output_lines.append(line)

    output = "\n".join(output_lines)
    return extensions, extension_filenames, output

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

    def display_data_for_image(self, filename):
        with open(filename, 'rb') as f:
            image = f.read()
        #os.unlink(filename)

        image_data = None
        try:
            image_unencoded=image.decode("utf-8") 
            if str(image_unencoded[:11]) == 'data:image/' and ';base64' in str(image_unencoded[:22]):
                start_type_pos = image_unencoded.find('image/') + 6
                end_type_pos = image_unencoded.find(';base64')
                image_type = str(image_unencoded[ start_type_pos: end_type_pos])
                #print("IMAGE_TYPE=<{}>".format(image_type))
                image_data = image_unencoded[ end_type_pos + 8: ]
        except Exception as e:
            pass

        if image_data == None:
            image_type = imghdr.what(None, image)
            if image_type is None:
                raise ValueError("Not a valid image: %s" % image)

            image_data = base64.b64encode(image).decode('ascii')

        content = {
            'data': {
                'image/' + image_type: image_data
            },
            'metadata': {}
        }
        return content


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
            #resp = shell_magic.eval(image_setup_cmd)
            resp = shell_magic.eval(source_metakernelrc_cmd)

        # Execute shell command
        resp = shell_magic.eval(code.strip())

        #--------------------------------
        #if not silent:
        #image_filenames, resp = extract_image_filenames(resp)
        extensions, extension_filenames, resp = extract_extension_filenames(resp)

        # Detect and process calls to extension functions
        cnt=0
        for filename in extension_filenames:
            try:
                filename = MetaKernelBash.root_path_prefix + filename
                if extensions[cnt] == 'image':
                    display_data = self.display_data_for_image(filename)
                else:
                    lines = '\n'.join( open(filename, 'r').readlines() )

                shell_magic = None
                if extensions[cnt] == 'js':
                    shell_magic = self.cell_magics['javascript']
                    resp = shell_magic.line_javascript(lines)
                elif extensions[cnt] == 'html':
                    shell_magic = self.cell_magics['html']
                    resp = shell_magic.line_html(lines)
                elif extensions[cnt] == 'python':
                    shell_magic = self.cell_magics['python']
                    resp = shell_magic.line_python(lines)
                elif extensions[cnt] == 'pydot':
                    shell_magic = self.cell_magics['dot']
                    resp = shell_magic.line_dot(lines)
                elif extensions[cnt] == 'image':
                    self.send_response(self.iopub_socket, 'display_data', display_data)

                else:
                    print("Unknown extension << {} >>".format( extensions[cnt] ))
                    print("Available cell magics are {}".format( str(self.cell_magics) ))
                    message = {'name': 'stdout', 'text': 'Unknown extension: <<' + extensions[cnt] + '>>'}
                    self.send_response(self.iopub_socket, 'stream', message)
                    resp = None
                    #return

                return resp
            except ValueError as e:
                message = {'name': 'stdout', 'text': str(e)}
                self.send_response(self.iopub_socket, 'stream', message)
            cnt=cnt+1

        #--------------------------------

        self.log.debug('execute done')
        return resp.strip()
        #return HTML("<table><tr><td>" + resp.strip() + "</td></tr></table>")

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
