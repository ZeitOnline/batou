"""Securely edit encrypted secret files."""

from .encryption import EncryptedConfigFile
import argparse
import os
import subprocess
import tempfile


class Editor(object):

    def __init__(self, editor, encrypted_file):
        self.editor = editor
        self.encrypted_file = encrypted_file
        self.original_cleartext = encrypted_file.read()
        self.cleartext = self.original_cleartext

    def main(self):
        cmd = 'edit'
        while cmd != 'quit':
            try:
                self.process_cmd(cmd)
            except Exception, e:
                print
                print "Could not update due to error: {}".format(e)
                print "Your changes are still available. You can try:"
                print "\tedit (opens editor with current data again)"
                print "\tencrypt (tries to encrypt current data again)"
                print "\tquit (quits and looses your changes)"
                cmd = raw_input("> ").strip()
            else:
                break

    def process_cmd(self, cmd):
            if cmd == 'edit':
                self.edit()
                self.encrypt()
            elif cmd == 'encrypt':
                self.encrypt()
            else:
                print "Did not understand command '{}'".format(cmd)

    def encrypt(self):
        if self.cleartext == self.original_cleartext:
            print "No changes from original cleartext. Not updating."
            return
        self.encrypted_file.write(self.cleartext)

    def edit(self):
        with tempfile.NamedTemporaryFile(
                prefix='edit', suffix='.cfg') as clearfile:
            clearfile.write(self.cleartext)
            clearfile.flush()

            subprocess.check_call(
                [self.editor + ' ' + clearfile.name],
                shell=True)

            with open(clearfile.name, 'r') as new_clearfile:
                self.cleartext = new_clearfile.read()


def edit():
    """Secrets editor console script.

    The main focus here is to avoid having unencrypted files accidentally
    ending up in the deployment repository.

    """
    parser = argparse.ArgumentParser(
        description=u"""Encrypted secrets file editor utility. Decrypts file,
        invokes the editor, and encrypts the file again. If called with a
        non-existent file name, a new encrypted file is created.""",
        epilog='Relies on gpg being installed and configured correctly.')
    parser.add_argument('--editor', '-e', metavar='EDITOR',
                        default=os.environ.get('EDITOR', 'vi'),
                        help='Invoke EDITOR to edit (default: $EDITOR or vi)')
    parser.add_argument('filename', metavar='FILE',
                        help='Encrypted secrets file to edit.')
    args = parser.parse_args()

    encrypted = args.filename

    with EncryptedConfigFile(encrypted, write_lock=True) as sf:
        editor = Editor(args.editor, sf)
        editor.main()
