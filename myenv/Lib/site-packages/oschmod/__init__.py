# -*- coding: utf-8 -*-
"""oschmod module.

Module for working with file permissions that are consistent across Windows,
macOS, and Linux.

These bitwise permissions from the stat module can be used with this module:
    stat.S_IRWXU   # Mask for file owner permissions
    stat.S_IREAD   # Owner has read permission
    stat.S_IRUSR   # Owner has read permission
    stat.S_IWRITE  # Owner has write permission
    stat.S_IWUSR   # Owner has write permission
    stat.S_IEXEC   # Owner has execute permission
    stat.S_IXUSR   # Owner has execute permission

    stat.S_IRWXG   # Mask for group permissions
    stat.S_IRGRP   # Group has read permission
    stat.S_IWGRP   # Group has write permission
    stat.S_IXGRP   # Group has execute permission

    stat.S_IRWXO   # Mask for permissions for others (not in group)
    stat.S_IROTH   # Others have read permission
    stat.S_IWOTH   # Others have write permission
    stat.S_IXOTH   # Others have execute permission

"""

import os
import platform
import random
import re
import stat
import string

IS_WINDOWS = platform.system() == 'Windows'
HAS_PYWIN32 = False
try:
    import ntsecuritycon  # noqa: F401
    import win32security  # noqa: F401
    from pywintypes import error as pywinerror
    HAS_PYWIN32 = True
except ImportError:
    pass

HAS_PWD = False
try:
    import pwd            # noqa: F401
    import grp            # noqa: F401
    HAS_PWD = True
except ImportError:
    pass

if IS_WINDOWS and not HAS_PYWIN32:
    raise ImportError("win32security and ntsecuritycon required on Windows")

if HAS_PYWIN32:
    W_FLDIR = ntsecuritycon.FILE_LIST_DIRECTORY    # =                        1
    W_FADFL = ntsecuritycon.FILE_ADD_FILE          # =                       10
    W_FADSD = ntsecuritycon.FILE_ADD_SUBDIRECTORY  # =                      100
    W_FRDEA = ntsecuritycon.FILE_READ_EA           # =                     1000
    W_FWREA = ntsecuritycon.FILE_WRITE_EA          # =                    10000
    W_FTRAV = ntsecuritycon.FILE_TRAVERSE          # =                   100000
    W_FDLCH = ntsecuritycon.FILE_DELETE_CHILD      # =                  1000000
    W_FRDAT = ntsecuritycon.FILE_READ_ATTRIBUTES   # =                 10000000
    W_FWRAT = ntsecuritycon.FILE_WRITE_ATTRIBUTES  # =                100000000
    W_DELET = ntsecuritycon.DELETE                 # =        10000000000000000
    W_RDCON = ntsecuritycon.READ_CONTROL           # =       100000000000000000
    W_WRDAC = ntsecuritycon.WRITE_DAC              # =      1000000000000000000
    W_WROWN = ntsecuritycon.WRITE_OWNER            # =     10000000000000000000
    W_SYNCH = ntsecuritycon.SYNCHRONIZE            # =    100000000000000000000
    W_FGNEX = ntsecuritycon.FILE_GENERIC_EXECUTE   # =    100100000000010100000
    W_FGNRD = ntsecuritycon.FILE_GENERIC_READ      # =    100100000000010001001
    W_FGNWR = ntsecuritycon.FILE_GENERIC_WRITE     # =    100100000000100010110
    W_GENAL = ntsecuritycon.GENERIC_ALL         # 10000000000000000000000000000
    W_GENEX = ntsecuritycon.GENERIC_EXECUTE    # 100000000000000000000000000000
    W_GENWR = ntsecuritycon.GENERIC_WRITE     # 1000000000000000000000000000000
    W_GENRD = ntsecuritycon.GENERIC_READ    # -10000000000000000000000000000000

    W_DIRRD = W_FLDIR | W_FRDEA | W_FRDAT | W_RDCON | W_SYNCH
    W_DIRWR = W_FADFL | W_FADSD | W_FWREA | W_FDLCH | W_FWRAT | W_DELET | \
        W_RDCON | W_WRDAC | W_WROWN | W_SYNCH
    W_DIREX = W_FTRAV | W_RDCON | W_SYNCH

    W_FILRD = W_FGNRD
    W_FILWR = W_FDLCH | W_DELET | W_WRDAC | W_WROWN | W_FGNWR
    W_FILEX = W_FGNEX

    WIN_RWX_PERMS = [
        [W_FILRD, W_FILWR, W_FILEX],
        [W_DIRRD, W_DIRWR, W_DIREX]
    ]

    WIN_FILE_PERMISSIONS = (
        "DELETE", "READ_CONTROL", "WRITE_DAC", "WRITE_OWNER",
        "SYNCHRONIZE", "FILE_GENERIC_READ", "FILE_GENERIC_WRITE",
        "FILE_GENERIC_EXECUTE", "FILE_DELETE_CHILD")

    WIN_DIR_PERMISSIONS = (
        "DELETE", "READ_CONTROL", "WRITE_DAC", "WRITE_OWNER",
        "SYNCHRONIZE", "FILE_ADD_SUBDIRECTORY", "FILE_ADD_FILE",
        "FILE_DELETE_CHILD", "FILE_LIST_DIRECTORY", "FILE_TRAVERSE",
        "FILE_READ_ATTRIBUTES", "FILE_WRITE_ATTRIBUTES", "FILE_READ_EA",
        "FILE_WRITE_EA")

    WIN_DIR_INHERIT_PERMISSIONS = (
        "DELETE", "READ_CONTROL", "WRITE_DAC", "WRITE_OWNER",
        "SYNCHRONIZE", "GENERIC_READ", "GENERIC_WRITE", "GENERIC_EXECUTE",
        "GENERIC_ALL")

    WIN_ACE_TYPES = (
        "ACCESS_ALLOWED_ACE_TYPE", "ACCESS_DENIED_ACE_TYPE",
        "SYSTEM_AUDIT_ACE_TYPE", "SYSTEM_ALARM_ACE_TYPE")

    WIN_INHERITANCE_TYPES = (
        "OBJECT_INHERIT_ACE", "CONTAINER_INHERIT_ACE",
        "NO_PROPAGATE_INHERIT_ACE", "INHERIT_ONLY_ACE",
        "INHERITED_ACE", "SUCCESSFUL_ACCESS_ACE_FLAG",
        "FAILED_ACCESS_ACE_FLAG")

    SECURITY_NT_AUTHORITY = ('SYSTEM', 'NT AUTHORITY', 5)

FILE = 0
DIRECTORY = 1

OBJECT_TYPES = [FILE, DIRECTORY]

OWNER = 0
GROUP = 1
OTHER = 2

OWNER_TYPES = [OWNER, GROUP, OTHER]

READ = 0
WRITE = 1
EXECUTE = 2

OPER_TYPES = [READ, WRITE, EXECUTE]

STAT_MODES = [
    [stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR],
    [stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP],
    [stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH]
]

STAT_KEYS = (
    "S_IRUSR",
    "S_IWUSR",
    "S_IXUSR",
    "S_IRGRP",
    "S_IWGRP",
    "S_IXGRP",
    "S_IROTH",
    "S_IWOTH",
    "S_IXOTH"
)

__version__ = "0.3.12"


def get_mode(path):
    """Get bitwise mode (stat) of object (dir or file)."""
    if IS_WINDOWS:
        return win_get_permissions(path)
    return os.stat(path).st_mode & (stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)


def set_mode(path, mode):
    """
    Set bitwise mode (stat) of object (dir or file).

    Three types of modes can be used:
    1. Decimal mode - an integer representation of set bits (eg, 512)
    2. Octal mode - a string expressing an octal number (eg, "777")
    3. Symbolic representation - a string with modifier symbols (eg, "+x")
    """
    new_mode = 0
    if isinstance(mode, int):
        new_mode = mode
    elif isinstance(mode, str):
        if '+' in mode or '-' in mode or '=' in mode:
            new_mode = get_effective_mode(get_mode(path), mode)
        else:
            new_mode = int(mode, 8)

    if IS_WINDOWS:
        return win_set_permissions(path, new_mode)
    return os.chmod(path, new_mode)


def set_mode_recursive(path, mode, dir_mode=None):
    r"""
    Set all file and directory permissions at or under path to modes.

    Args:
    path: (:obj:`str`)
        Object which will have its mode set. If path is a file, only its mode
        is set - no recursion occurs. If path is a directory, its mode and the
        mode of all files and subdirectories below it are set.

    mode: (`int`)
        Mode to be applied to object(s).

    dir_mode: (`int`)
        If provided, this mode is given to all directories only.

    """
    if get_object_type(path) == FILE:
        return set_mode(path, mode)

    if not dir_mode:
        dir_mode = mode

    for root, dirs, files in os.walk(path, topdown=False):
        for one_file in files:
            set_mode(os.path.join(root, one_file), mode)

        for one_dir in dirs:
            set_mode(os.path.join(root, one_dir), dir_mode)

    return set_mode(path, dir_mode)


def _get_effective_mode_multiple(current_mode, modes):
    """Get octal mode, given current mode and symbolic mode modifiers."""
    new_mode = current_mode
    for mode in modes.split(","):
        new_mode = get_effective_mode(new_mode, mode)
    return new_mode


def get_effective_mode(current_mode, symbolic):
    """Get octal mode, given current mode and symbolic mode modifier."""
    if not isinstance(symbolic, str):
        raise AttributeError('symbolic must be a string')

    if "," in symbolic:
        return _get_effective_mode_multiple(current_mode, symbolic)

    result = re.search(r'^\s*([ugoa]*)([-+=])([rwx]*)\s*$', symbolic)
    if result is None:
        raise AttributeError('bad format of symbolic representation modifier')

    whom = result.group(1) or "ugo"
    operation = result.group(2)
    perm = result.group(3)

    if "a" in whom:
        whom = "ugo"

    # bitwise magic
    bit_perm = _get_basic_symbol_to_mode(perm)
    mask_mode = ("u" in whom and bit_perm << 6) | \
        ("g" in whom and bit_perm << 3) | \
        ("o" in whom and bit_perm << 0)

    if operation == "=":
        original = ("u" not in whom and current_mode & 448) | \
            ("g" not in whom and current_mode & 56) | \
            ("o" not in whom and current_mode & 7)
        return mask_mode | original

    if operation == "+":
        return current_mode | mask_mode

    return current_mode & ~mask_mode


def get_object_type(path):
    """Get whether object is file or directory."""
    object_type = DIRECTORY
    if os.path.isfile(path):
        object_type = FILE

    return object_type


def get_owner(path):
    """Get the object owner."""
    if IS_WINDOWS:
        return win32security.LookupAccountSid(None, win_get_owner_sid(path))
    return pwd.getpwuid(os.stat(path).st_uid).pw_name


def get_group(path):
    """Get the object group."""
    if IS_WINDOWS:
        return win32security.LookupAccountSid(None, win_get_group_sid(path))
    return grp.getgrgid(os.stat(path).st_gid).gr_name


def win_get_owner_sid(path):
    """Get the file owner."""
    sec_descriptor = win32security.GetNamedSecurityInfo(
        path, win32security.SE_FILE_OBJECT,
        win32security.OWNER_SECURITY_INFORMATION)
    return sec_descriptor.GetSecurityDescriptorOwner()


def win_get_group_sid(path):
    """Get the file group."""
    sec_descriptor = win32security.GetNamedSecurityInfo(
        path, win32security.SE_FILE_OBJECT,
        win32security.GROUP_SECURITY_INFORMATION)
    return sec_descriptor.GetSecurityDescriptorGroup()


def win_get_other_sid():
    """Get the other SID.

    For now this is the Users builtin account. In the future, probably should
    allow account to be passed in and find any non-owner, non-group account
    currently associated with the file. As a default, it could use Users."""
    return win32security.ConvertStringSidToSid("S-1-5-32-545")


def convert_win_to_stat(win_perm, user_type, object_type):
    """Given Win perm and user type, give stat mode."""
    mode = 0

    for oper in OPER_TYPES:
        if win_perm & WIN_RWX_PERMS[object_type][oper] == \
                WIN_RWX_PERMS[object_type][oper]:
            mode = mode | STAT_MODES[user_type][oper]

    return mode


def convert_stat_to_win(mode, user_type, object_type):
    """Given stat mode, return Win bitwise permissions for user type."""
    win_perm = 0

    for oper in OPER_TYPES:
        if mode & STAT_MODES[user_type][oper] == STAT_MODES[user_type][oper]:
            win_perm = win_perm | WIN_RWX_PERMS[object_type][oper]

    return win_perm


def win_get_user_type(sid, sids):
    """Given object and SIDs, return user type."""
    if sid == sids[OWNER]:
        return OWNER

    if sid == sids[GROUP]:
        return GROUP

    return OTHER


def win_get_object_sids(path):
    """Get the owner, group, other SIDs for an object."""
    return [
        win_get_owner_sid(path),
        win_get_group_sid(path),
        win_get_other_sid()
    ]


def win_get_permissions(path):
    """Get the file or dir permissions."""
    if not os.path.exists(path):
        raise FileNotFoundError('Path %s could not be found.' % path)

    return _win_get_permissions(path, get_object_type(path))


def _get_basic_symbol_to_mode(symbol):
    """Calculate numeric value of set of 'rwx'."""
    return ("r" in symbol and 1 << 2) | \
        ("w" in symbol and 1 << 1) | \
        ("x" in symbol and 1 << 0)


def _win_get_permissions(path, object_type):
    """Get the permissions."""
    sec_des = win32security.GetNamedSecurityInfo(
        path, win32security.SE_FILE_OBJECT,
        win32security.DACL_SECURITY_INFORMATION)
    dacl = sec_des.GetSecurityDescriptorDacl()

    sids = win_get_object_sids(path)
    mode = 0

    for index in range(0, dacl.GetAceCount()):
        ace = dacl.GetAce(index)
        if ace[0][0] == win32security.ACCESS_ALLOWED_ACE_TYPE and \
                win32security.LookupAccountSid(None, ace[2]) != \
                SECURITY_NT_AUTHORITY:
            # Not handling win32security.ACCESS_DENIED_ACE_TYPE
            mode = mode | convert_win_to_stat(
                ace[1],
                win_get_user_type(ace[2], sids),
                object_type)

    return mode


def win_set_permissions(path, mode):
    """Set the file or dir permissions."""
    if not os.path.exists(path):
        raise FileNotFoundError('Path %s could not be found.' % path)

    _win_set_permissions(path, mode, get_object_type(path))


def _win_set_permissions(path, mode, object_type):
    """Set the permissions."""
    # Overview of Windows inheritance:
    # Get/SetNamedSecurityInfo  = Always includes inheritance
    # Get/SetFileSecurity       = Can exclude/disable inheritance
    # Here we read effective permissions with GetNamedSecurityInfo, i.e.,
    # including inherited permissions. However, we'll set permissions with
    # SetFileSecurity and NO_INHERITANCE, to disable inheritance.
    sec_des = win32security.GetNamedSecurityInfo(
        path, win32security.SE_FILE_OBJECT,
        win32security.DACL_SECURITY_INFORMATION)
    dacl = sec_des.GetSecurityDescriptorDacl()

    system_ace = None
    for _ in range(0, dacl.GetAceCount()):
        ace = dacl.GetAce(0)
        try:
            if ace[2] and ace[2].IsValid() and win32security.LookupAccountSid(
                    None, ace[2]) == SECURITY_NT_AUTHORITY:
                system_ace = ace
        except pywinerror:
            print("Found orphaned SID:", ace[2])
        dacl.DeleteAce(0)

    if system_ace:
        dacl.AddAccessAllowedAceEx(
            dacl.GetAclRevision(),
            win32security.NO_INHERITANCE, system_ace[1], system_ace[2])

    sids = win_get_object_sids(path)

    for user_type, sid in enumerate(sids):
        win_perm = convert_stat_to_win(mode, user_type, object_type)

        if win_perm > 0:
            dacl.AddAccessAllowedAceEx(
                dacl.GetAclRevision(),
                win32security.NO_INHERITANCE, win_perm, sid)

    sec_des.SetSecurityDescriptorDacl(1, dacl, 0)
    win32security.SetFileSecurity(
        path, win32security.DACL_SECURITY_INFORMATION, sec_des)


def print_win_inheritance(flags):
    """Display inheritance flags."""
    print("  -Flags:", hex(flags))
    if flags == win32security.NO_INHERITANCE:
        print("    ", "NO_INHERITANCE")
    else:
        for i in WIN_INHERITANCE_TYPES:
            if flags & getattr(win32security, i) == getattr(win32security, i):
                print("    ", i)


def print_mode_permissions(mode):
    """Print component permissions in a stat mode."""
    print("Mode:", oct(mode), "(Decimal: " + str(mode) + ")")
    for i in STAT_KEYS:
        if mode & getattr(stat, i) == getattr(stat, i):
            print("  stat." + i)


def print_win_ace_type(ace_type):
    """Print ACE type."""
    print("  -Type:")
    for i in WIN_ACE_TYPES:
        if getattr(ntsecuritycon, i) == ace_type:
            print("    ", i)


def print_win_permissions(win_perm, flags, object_type):
    """Print permissions from ACE information."""
    print("  -Permissions Mask:", hex(win_perm), "(" + str(win_perm) + ")")

    # files and directories do permissions differently
    if object_type == FILE:
        permissions = WIN_FILE_PERMISSIONS
    else:
        permissions = WIN_DIR_PERMISSIONS
        # directories have ACE that is inherited by children within them
        if flags & ntsecuritycon.OBJECT_INHERIT_ACE == \
                ntsecuritycon.OBJECT_INHERIT_ACE and flags & \
                ntsecuritycon.INHERIT_ONLY_ACE == \
                ntsecuritycon.INHERIT_ONLY_ACE:
            permissions = WIN_DIR_INHERIT_PERMISSIONS

    calc_mask = 0  # see if we are printing all of the permissions
    for i in permissions:
        if getattr(ntsecuritycon, i) & win_perm == getattr(
                ntsecuritycon, i):
            calc_mask = calc_mask | getattr(ntsecuritycon, i)
            print("    ", i)
    print("  -Mask calculated from printed permissions:", hex(calc_mask))


def print_obj_info(path):
    """Prints object security permission info."""
    if not os.path.exists(path):
        print(path, "does not exist!")
        raise FileNotFoundError('Path %s could not be found.' % path)

    object_type = get_object_type(path)

    print("----------------------------------------")
    if object_type == FILE:
        print("FILE:", path)
    else:
        print("DIRECTORY:", path)

    print_mode_permissions(get_mode(path))

    print("Owner:", get_owner(path))
    print("Group:", get_group(path))

    if IS_WINDOWS:
        _print_win_obj_info(path)


def _print_win_obj_info(path):
    """Print windows object security info."""
    # get ACEs
    sec_descriptor = win32security.GetFileSecurity(
        path, win32security.DACL_SECURITY_INFORMATION)
    dacl = sec_descriptor.GetSecurityDescriptorDacl()
    if dacl is None:
        print("No Discretionary ACL")
        return

    for ace_no in range(0, dacl.GetAceCount()):
        ace = dacl.GetAce(ace_no)
        print("ACE", ace_no)

        print('  -SID:', win32security.LookupAccountSid(None, ace[2]))

        print_win_ace_type(ace[0][0])
        print_win_inheritance(ace[0][1])
        print_win_permissions(ace[1], ace[0][1], get_object_type(path))


def perm_test(mode=stat.S_IRUSR | stat.S_IWUSR):
    """Creates test file and modifies permissions."""
    path = ''.join(
        random.choice(string.ascii_letters) for i in range(10)) + '.txt'
    file_hdl = open(path, 'w+')
    file_hdl.write("new file")
    file_hdl.close()
    print("Created test file:", path)

    print("BEFORE Permissions:")
    print_obj_info(path)

    print("Setting permissions:")
    print_mode_permissions(mode)
    set_mode(path, mode)

    print("AFTER Permissions:")
    print_obj_info(path)
