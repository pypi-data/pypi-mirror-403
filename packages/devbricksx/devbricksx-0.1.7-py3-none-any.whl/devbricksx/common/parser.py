import os
import filetype
from devbricksx.development.log import *

__ACCEPT_IMAGE_TYPES__ = ['png', 'jpeg', 'bmp']


def append_common_developer_options_to_parse(ap):
    ap.add_argument("-v", "--verbose", action='store_true',
                    default=False,
                    help="print more development information")
    ap.add_argument("-s", "--silent", action='store_true',
                    default=False,
                    help="silent only some critical outputs remained")


def append_common_dir_options_to_parse(ap, required=False, group_required=False):
    if group_required:
        dir_opts_group = ap.add_argument_group('input and output directory arguments')
        dir_opts_group.add_argument("-id", "--input-directory",
                                    required=True,
                                    help="input directory of files")
        dir_opts_group.add_argument("-od", "--output-directory",
                                    help="output directory of files")
    else:
        ap.add_argument("-id", "--input-directory",
                        required=required,
                        help="input directory of files")
        ap.add_argument("-od", "--output-directory",
                        required=required,
                        help="output directory of files")

def append_common_file_options_to_parse(ap, required=False, group_required=False):
    if group_required:
        file_opts_group = ap.add_argument_group('input and output arguments')
        file_opts_group.add_argument("-if", "--input-file",
                                     required=required,
                                     help="input file")
        file_opts_group.add_argument("-of", "--output-file",
                                     required=required,
                                     help="output file")
    else:
        ap.add_argument("-if", "--input-file",
                        required=required,
                        help="input file")
        ap.add_argument("-of", "--output-file",
                        required=required,
                        help="output file")


def check_consistency_of_file_options(args):
    if args.output_directory is not None and args.input_directory is None:
        exit('Invalid arguments: --output_directory should be used with --input_directory')

    if args.output_file is not None and args.input_file is None:
        exit('Invalid arguments: --output_file should be used with --input_file')


def extract_files_from_args(args):
    files = []

    if args.input_directory is not None:
        input_dir = args.input_directory
        debug("selected directories:{}".format(input_dir))
        files_in_dir = os.listdir(input_dir)
        for f in files_in_dir:
            file_path = os.path.join(input_dir, f)

            if os.path.isdir(file_path):
                continue

            kind = filetype.guess(file_path)

            if kind is not None and kind.extension in __ACCEPT_IMAGE_TYPES__:
                files.append(file_path)
            else:
                info('skip file [%s] with file type (%s) is not accepted. It SHOULD be one of [%s].'
                     % (f, kind.extension, ','.join(str(t) for t in __ACCEPT_IMAGE_TYPES__)))
    else:
        debug("selected file:{}".format(args.input_file))
        files.append(args.input_file)

    return files
