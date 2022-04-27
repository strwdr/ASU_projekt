import argparse
import pathlib
import hashlib
from enum import Enum
import json
import stat
import shutil

EMPTY_MD5SUM = "d41d8cd98f00b204e9800998ecf8427e"
DEFAULT_CONFIG_PATH = str(pathlib.Path.home()) + "/.clean_files"
config = {
    "temp_files_extensions": [".TEMP", "~", ".tmp", ".temp"],
    "bad_permissions": [
        "777",
    ],
    "bad_permissions_auto_replacement": "644",
    "bad_characters": [":", "\"", ",", ";", "*", "?", "$", "#", "'", "|", "\\"],
    "bad_characters_auto_replacement": "_",
}


def init_config(config_path):
    """
    :param config_path:
        string - path to a config file
    :return:
        config dict
    :return:
    """
    global config

    json_config = json.dumps(config, indent=3)
    config_file = open(config_path, "a")
    config_file.write(json_config)
    config_file.close()

    return config


def load_config(config_path):
    """
    :param config_path:
        string - path to a config file
    :return:
        config dict
    """
    global config

    try:
        config_file = open(config_path, "r")
        config = json.loads(config_file.read())
        config_file.close()
    except FileNotFoundError:
        print("Initializing new config in '" + config_path + "'...")
        config = init_config(config_path)

    return config


class Mode(Enum):
    FIND_DUPLICATES = 1
    FIND_EMPTY = 2
    FIND_TEMP = 3
    FIND_SAME_NAME = 4
    FIND_BAD_PERMISSION = 5
    FIND_BAD_CHARACTER = 6
    FIND_X_NONEXISTENT = 7


def get_modification_date(file):
    return file.lstat().st_mtime


def mode_to_str(mode):
    if mode == Mode.FIND_DUPLICATES:
        return "'find duplicate files'"
    elif mode == Mode.FIND_EMPTY:
        return "'find empty files'"
    elif mode == Mode.FIND_TEMP:
        return "'find temp files'"
    elif mode == Mode.FIND_SAME_NAME:
        return "'find same name files'"
    elif mode == Mode.FIND_BAD_PERMISSION:
        return "'find bad permission'"
    elif mode == Mode.FIND_BAD_CHARACTER:
        return "'find bad character files'"
    elif mode == Mode.FIND_X_NONEXISTENT:
        return "'find X-nonexistent files in Y dirs'"

    return "UNKNOWN_MODE"


def select_from_list(sel_list):
    while True:
        print("> ", end="")
        selection = input()
        try:
            if 1 <= int(selection) <= len(sel_list):
                return sel_list[int(selection) - 1]
            else:
                print("Please provide proper number")
        except ValueError:
            print("Please provide proper number")


def manual_select_mode():
    print("Available modes:")
    print("\t1.\tFind duplicate files")
    print("\t2.\tFind empty files")
    print("\t3.\tFind temp files")
    print("\t4.\tFind same name files")
    print("\t5.\tFind bad permission files")
    print("\t6.\tFind bad character files")
    print("\t7.\tFind X-directory nonexistent \n\t\tfiles (hashes) in Y directories")

    selected_mode = None

    good_selection = False

    while not good_selection:
        print("> ", end="")
        selection = input()
        good_selection = True
        if selection == "1":
            selected_mode = Mode.FIND_DUPLICATES
        elif selection == "2":
            selected_mode = Mode.FIND_EMPTY
        elif selection == "3":
            selected_mode = Mode.FIND_TEMP
        elif selection == "4":
            selected_mode = Mode.FIND_SAME_NAME
        elif selection == "5":
            selected_mode = Mode.FIND_BAD_PERMISSION
        elif selection == "6":
            selected_mode = Mode.FIND_BAD_CHARACTER
        elif selection == "7":
            selected_mode = Mode.FIND_X_NONEXISTENT
        else:
            good_selection = False
            print("Please provide proper number")
    return selected_mode


def gen_files_set(directories):
    """
    :param directories:
        tuple of:
            - x_directory: string - X directory
            - y_directories: list of strings - Y directories
    :return:
    x_files_set, y_files_set - set of tuples (pathlib_path, md5sum string of file),
    hash_count_dict - dict of md5sum's counts
    """
    x_files_set = set()
    y_files_set = set()
    hash_count_dict = dict()

    x_directory = directories[0]
    y_directories = directories[1:]

    def mini_gen_files_set(root_directory, files_set):
        for p in pathlib.Path(root_directory).rglob("*"):
            if p.is_file():
                hash_file = hashlib.md5(open(p.absolute(), 'rb').read()).hexdigest()
                files_set.add((p, hash_file))
                if not hash_count_dict.get(hash_file):
                    hash_count_dict[hash_file] = 1
                else:
                    hash_count_dict[hash_file] += 1

    mini_gen_files_set(x_directory, x_files_set)

    for y_directory in y_directories:
        mini_gen_files_set(y_directory, y_files_set)

    return x_files_set, y_files_set, hash_count_dict


def find_same_hash_files(directories):
    found_files_groups_list = []

    files_set_x, files_set_y, hash_count_dict = gen_files_set(directories)
    files_set = files_set_x | files_set_y

    for key in hash_count_dict:
        if hash_count_dict[key] >= 1:
            file_group = []
            for (file, hash_file) in files_set:
                if hash_file == key:
                    file_group.append(file)
            found_files_groups_list.append(file_group)

    return found_files_groups_list


def find_empty_files(directories):
    found_files_groups_list = []

    files_set_x, files_set_y, hash_count_dict = gen_files_set(directories)
    files_set = files_set_x | files_set_y

    for (file, hash_file) in files_set:
        if hash_file == EMPTY_MD5SUM:
            found_files_groups_list.append([file])
    return found_files_groups_list


def find_same_name_files(directories):
    found_files_groups_list = []

    files_set_x, files_set_y, hash_count_dict = gen_files_set(directories)
    files_set = files_set_x | files_set_y

    processed_filenames = set()

    for (file, hash_file) in files_set:
        if file.name not in processed_filenames:
            processed_filenames.add(file.name)
            file_group = [file]
            found_any_duplicate = False
            for (file_snd, hash_file_snd) in files_set:
                if file != file_snd and file.name == file_snd.name:
                    file_group.append(file_snd)
                    found_any_duplicate = True
            if found_any_duplicate:
                found_files_groups_list.append(file_group)

    return found_files_groups_list


def is_temp_file(filename):
    global config
    for temp_extension in config["temp_files_extensions"]:
        if filename.endswith(temp_extension):
            return True
    return False


def find_temp_files(directories):
    found_files_groups_list = []

    files_set_x, files_set_y, hash_count_dict = gen_files_set(directories)
    files_set = files_set_x | files_set_y

    for (file, hash_file) in files_set:
        if is_temp_file(file.name):
            found_files_groups_list.append([file])

    return found_files_groups_list


def get_file_permission(file):
    return str(oct(file.stat().st_mode))[5:]


def get_file_permission_hr(file):
    return stat.filemode(file.stat().st_mode)[1:]


def find_bad_permission_files(directories):
    global config

    found_files_groups_list = []

    files_set_x, files_set_y, hash_count_dict = gen_files_set(directories)
    files_set = files_set_x | files_set_y

    for (file, hash_file) in files_set:
        if get_file_permission(file) in config['bad_permissions']:
            found_files_groups_list.append([file])

    return found_files_groups_list


def find_x_nonexistent_files(directories):
    files_set_x, files_set_y, hash_count_dict = gen_files_set(directories)
    found_files_groups_list = []

    # generate set of X directory files hashes
    x_hashes = set()
    for (file, hash_file) in files_set_x:
        x_hashes.add(hash_file)

    for (file, hash_file) in files_set_y:
        if hash_file not in x_hashes:
            found_files_groups_list.append([file])

    return found_files_groups_list


def find_bad_name_files(directories):
    global config

    found_files_groups_list = []

    files_set_x, files_set_y, hash_count_dict = gen_files_set(directories)
    files_set = files_set_x | files_set_y

    for (file, hash_file) in files_set:
        if any(x in file.name for x in config['bad_characters']):
            found_files_groups_list.append([file])

    return found_files_groups_list


def run_mode_function(mode, directories):
    files_groups_list = None
    if mode == Mode.FIND_EMPTY:
        files_groups_list = find_empty_files(directories)
    elif mode == Mode.FIND_TEMP:
        files_groups_list = find_temp_files(directories)
    elif mode == Mode.FIND_SAME_NAME:
        files_groups_list = find_same_name_files(directories)
    elif mode == Mode.FIND_BAD_PERMISSION:
        files_groups_list = find_bad_permission_files(directories)
    elif mode == Mode.FIND_BAD_CHARACTER:
        files_groups_list = find_bad_name_files(directories)
    elif mode == Mode.FIND_DUPLICATES:
        files_groups_list = find_same_hash_files(directories)
    elif mode == Mode.FIND_X_NONEXISTENT:
        files_groups_list = find_x_nonexistent_files(directories)
    return files_groups_list


class Action(Enum):
    DELETE = 1
    SKIP = 2
    KEEP_NEWEST = 3
    AUTO_FIX_MOD = 4
    AUTO_FIX_CHARACTERS = 5
    MANUAL_CHANGE_NAME = 6
    REPLACE_OLD_WITH_NEW = 7
    KEEP_SELECTED = 8
    MOVE_TO_X = 9
    COPY_TO_X = 10


def action_name_to_str(action):
    if action == Action.DELETE:
        return "Delete file(s)"
    elif action == Action.SKIP:
        return "Skip"
    elif action == Action.KEEP_NEWEST:
        return "Keep newest"
    elif action == Action.AUTO_FIX_MOD:
        return "Automatic chmod (" + config["bad_permissions_auto_replacement"] + ")"
    elif action == Action.AUTO_FIX_CHARACTERS:
        return "Automatic rename (replace bad characters with '" + config["bad_characters_auto_replacement"] + "')"
    elif action == Action.MANUAL_CHANGE_NAME:
        return "Manual rename"
    elif action == Action.REPLACE_OLD_WITH_NEW:
        return "Replace old version(s) with new"
    elif action == Action.KEEP_SELECTED:
        return "Manual select file to keep"
    elif action == Action.MOVE_TO_X:
        return "Move file to X directory"
    elif action == Action.COPY_TO_X:
        return "Copy file to X directory"
    return "UNKNOWN_ACTION"


# actions
def delete_files(files):
    for file in files:
        print("Deleting file " + str(file.absolute()))
        file.unlink()


def move_file(file_path, file_dest_path):
    file_path_str = str(file_path.absolute())
    file_dest_path_str = str(file_dest_path.absolute())
    print("Moving file " + str(file_path.absolute()) + " to " + file_dest_path_str)
    shutil.move(file_path_str, file_dest_path_str)


def copy_file(file_path, file_dest_path):
    file_path_str = str(file_path.absolute())
    file_dest_path_str = str(file_dest_path.absolute())
    print("Copying file " + str(file_path.absolute()) + " to " + file_dest_path_str)
    shutil.copy(file_path_str, file_dest_path_str)


def fix_bad_permissions(file):
    chmod_val = config["bad_permissions_auto_replacement"]
    print("Changing " + str(file.absolute()) + " permissions to " + chmod_val)
    bnum = bin(int(chmod_val, 8))  # octal to binary
    dec = int(bnum, 2)  # binary to decimal
    file.chmod(dec)


def rename_file(file, new_name):
    print("Renaming " + str(file.absolute()) + " to " + new_name + "...")
    file.rename(new_name)


def fix_bad_name(file):
    global config
    old_file_name = file.name
    new_file_name = ""
    for i in range(len(old_file_name)):
        if old_file_name[i] in set(config["bad_characters"]):
            new_file_name += config["bad_characters_auto_replacement"]
        else:
            new_file_name += old_file_name[i]

    rename_file(file, new_file_name)


def manual_change_name(file):
    print("Please provide new name for file " + str(file.absolute()))
    print("> ", end="")
    new_name = input()
    print("Renaming " + file.name + " to " + new_name + "...")
    rename_file(file, new_name)


def replace_old_with_new(files):
    newest_file = get_newest_file(files)
    for file in files:
        if file != newest_file:
            copy_file(newest_file.absolute(), file.absolute())


def delete_files_but_keep(files, file_to_keep):
    print("Keeping file " + str(file_to_keep.absolute()))
    files_to_delete = []
    for file in files:
        if file != file_to_keep:
            files_to_delete.append(file)
    delete_files(files_to_delete)


def get_newest_file(files):
    max_mod_date = -1
    max_mod_date_file = None
    for file in files:
        mod_date = get_modification_date(file)
        max_mod_date = max(max_mod_date, mod_date)
        max_mod_date_file = file
    return max_mod_date_file


def remove_prefix(prefix, s):
    return s[len(prefix):] if s.startswith(prefix) else None


def get_same_path_relative_to_root_in_x(x_root, y_roots, y_dir):
    p_x_root = pathlib.Path(x_root)
    x_root_abs_str = str(p_x_root.absolute())
    for y_root in y_roots:
        p_y_root = pathlib.Path(y_root)
        y_root_abs_str = str(p_y_root.absolute())
        root_relative_path = remove_prefix(y_root_abs_str, y_dir)
        if root_relative_path is not None:
            return x_root_abs_str + "/" + root_relative_path


def create_directory_path(new_path):
    p = pathlib.Path(new_path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def create_directory_in_x_from_y(x_root, y_roots, y_dir):
    new_path = get_same_path_relative_to_root_in_x(x_root, y_roots, y_dir)
    return create_directory_path(new_path)


def run_action(action, files, directories):
    x_directory = directories[0]
    y_directories = directories[1:]

    if action == Action.DELETE:
        delete_files(files)
    elif action == Action.SKIP:
        print("Skipping...")
    elif action == Action.KEEP_NEWEST:
        file_to_keep = get_newest_file(files)
        delete_files_but_keep(files, file_to_keep)
    elif action == Action.AUTO_FIX_MOD:
        fix_bad_permissions(files[0])
    elif action == Action.AUTO_FIX_CHARACTERS:
        fix_bad_name(files[0])
    elif action == Action.MANUAL_CHANGE_NAME:
        manual_change_name(files[0])
    elif action == Action.REPLACE_OLD_WITH_NEW:
        replace_old_with_new(files)
    elif action == Action.KEEP_SELECTED:
        index = 1
        print("Select file to keep:")
        for file in files:
            print("\t" + str(index) + ". " + str(file.absolute()))
            index += 1

        file_to_keep = select_from_list(files)
        delete_files_but_keep(files, file_to_keep)
    elif action == Action.MOVE_TO_X:
        file = files[0]
        new_path = create_directory_in_x_from_y(x_directory, y_directories, str(file.parent.absolute()))
        move_file(file, new_path)
    elif action == Action.COPY_TO_X:
        file = files[0]
        new_path = create_directory_in_x_from_y(x_directory, y_directories, str(file.parent.absolute()))
        copy_file(file, new_path)


def get_mode_actions(mode):
    """
    :param mode:
        Mode enum
    :return:
    """
    actions = []
    if mode == Mode.FIND_EMPTY:
        actions += [
            Action.DELETE,  # delete only file from set
        ]
    elif mode == Mode.FIND_DUPLICATES:
        actions += [
            Action.DELETE,  # delete all files
            Action.KEEP_NEWEST,
            Action.KEEP_SELECTED,
            Action.REPLACE_OLD_WITH_NEW,
        ]
    elif mode == Mode.FIND_TEMP:
        actions += [
            Action.DELETE,  # delete only file from set
        ]
    elif mode == Mode.FIND_SAME_NAME:
        actions += [
            Action.KEEP_NEWEST,
            Action.KEEP_SELECTED,
            Action.DELETE,  # delete all files from set
        ]
    elif mode == Mode.FIND_BAD_PERMISSION:
        actions += [
            Action.AUTO_FIX_MOD,
            Action.DELETE,  # delete only file from set
        ]
    elif mode == Mode.FIND_BAD_CHARACTER:
        actions += [
            Action.AUTO_FIX_CHARACTERS,
            Action.MANUAL_CHANGE_NAME,
            Action.DELETE,  # delete only file from set
        ]
    elif mode == Mode.FIND_X_NONEXISTENT:
        actions += [
            Action.COPY_TO_X,
            Action.MOVE_TO_X,
            Action.DELETE,  # delete nonexisting file
        ]
    actions += [Action.SKIP]

    return actions


def run_mode(mode, directories):
    """
    :param mode:
        Mode enum
    :param directories:
        tuple of:
            - x_directory: string - X directory
            - y_directories: list of strings - Y directories
    :return:
        pass
    :find_* functions behaviour:
        find_* functions return a list of lists (groups) of files to check
    """

    files_groups_list = run_mode_function(mode, directories)

    if files_groups_list is not None:
        always_action = None
        index = 0
        for files_group in files_groups_list:
            index += 1
            actions = get_mode_actions(mode)
            print("[" + str(index) + "]: " + str(len(files_group)) + " file(s) found in mode " + mode_to_str(mode))
            for pathlib_file in files_group:
                addition_str = ""
                if mode == Mode.FIND_BAD_PERMISSION:
                    addition_str = " (" + str(get_file_permission_hr(pathlib_file)) + ")"
                print("\t - " + str(pathlib_file.absolute()) + addition_str)
            if always_action is None:
                print("Available actions (<index>* to append that action always from now on):")
                i = 1
                for it_action in actions:
                    print("\t" + str(i) + ". " + action_name_to_str(it_action))
                    i += 1
                good_input = False
                select_action_num = 0
                while not good_input:
                    good_input = True
                    print("> ", end="")
                    select_action = input()
                    select_action_num = ord(select_action[0]) - ord('0') - 1
                    if not (0 <= select_action_num < len(actions)):
                        good_input = False
                    if len(select_action) != 1:
                        if len(select_action) != 2 or select_action[1] != "*":
                            good_input = False
                        always_action = select_action_num  # always do that option
                    if not good_input:
                        print("Please provide proper number (with optional *)")
                action = actions[select_action_num]
            else:
                action = actions[always_action]
            run_action(action, files_group, directories)
            print("--------------------------------")


def run():
    parser = argparse.ArgumentParser(description='Process dirs')
    parser.add_argument('directories', metavar='N', type=str, nargs='+',
                        help='directories (first - X dir rest - Y dirs)')

    config_path = DEFAULT_CONFIG_PATH
    load_config(config_path)
    args = parser.parse_args()
    mode = manual_select_mode()
    run_mode(mode, args.directories)


run()
