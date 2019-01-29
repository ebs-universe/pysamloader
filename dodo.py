

import os
import sys
import six
import shutil
import platform

from doit.task import clean_targets
from setuptools_scm import get_version

# Application Information
# -----------------------

SCRIPT_NAME = 'pysamloader'
SCRIPT_VERSION = get_version(root='.', relative_to=__file__)


# Platform and Build Environment Information
# ------------------------------------------

def _get_python_shared_lib():
    real_exec = sys.executable
    while os.path.islink(real_exec):
        real_exec = os.readlink(real_exec)
    return os.path.normpath(
        os.path.join(os.path.split(real_exec)[0], os.pardir, 'lib')
    )

if six.PY2:
    pytag = 'py2'
elif six.PY3:
    pytag = 'py3'
else:
    pytag = 'unknown'

if platform.system() == 'Linux':
    import tarfile
    package_ext = '.tar.gz'
    executable_ext = ''
    pyi_prefix = "LD_LIBRARY_PATH={0} ".format(_get_python_shared_lib())
    publish_pypi = True
elif platform.system() == 'Windows':
    import zipfile
    package_ext = '.zip'
    executable_ext = '.exe'
    pyi_prefix = ""
    publish_pypi = False
else:
    raise NotImplementedError("Platform not supported : {0}"
                              "".format(platform.system()))

# Names and Paths
# ---------------

_base_folder = os.path.join(os.path.split(__file__)[0])
_work_folder = os.path.join(_base_folder, 'build')
_dist_folder = os.path.join(_base_folder, 'dist')
_binary_dist_folder = os.path.join(
    _dist_folder, 'binary-{0}'.format(platform.system().lower()))
_executable_name = SCRIPT_NAME + executable_ext
_executable_path = os.path.join(_binary_dist_folder, _executable_name)
_binary_package_name = "{0}-{1}-{2}-{3}{4}".format(
    SCRIPT_NAME, SCRIPT_VERSION,
    platform.system().lower(), platform.machine().lower(), package_ext)
_binary_package_path = os.path.join(_binary_dist_folder, _binary_package_name)
_sdist_name = '{0}-{1}.tar.gz'.format(SCRIPT_NAME, SCRIPT_VERSION)
_bdist_name = '{0}-{1}-{2}-none-any.whl'.format(SCRIPT_NAME, SCRIPT_VERSION, pytag)
_egg_info_folder = os.path.join(_base_folder, "{0}.egg-info".format(SCRIPT_NAME))


# Build Steps
# -----------

def _inject_version():
    # Build version file for injection into the binary
    with open(os.path.join(_base_folder, SCRIPT_NAME, '_version.py'), 'w') as f:
        f.write('__version__ = "{0}"'.format(SCRIPT_VERSION))


def _clean_work_folder():
    if not os.path.exists(_work_folder):
        return
    shutil.rmtree(_work_folder)


def task_setup_build():
    return {
        'actions': [_inject_version],
        'targets': [
            os.path.join(_base_folder, SCRIPT_NAME, '_version.py'),
            _dist_folder,
        ],
        'clean': [_clean_work_folder, clean_targets]
    }


def task_build_binary():
    return {
        'actions': [pyi_prefix + 'pyinstaller {0}.spec'.format(SCRIPT_NAME)],
        'targets': [_executable_path, 
                    _binary_dist_folder],
        'task_dep': ['setup_build'],
        'clean': True
    }


def _create_binary_package():
    package_content = [
        (os.path.join(_binary_dist_folder, _executable_name), _executable_name),
        (os.path.join(_base_folder, 'LICENSE'), 'LICENSE'),
        (os.path.join(_base_folder, 'README.rst'), 'README.rst'),
        (os.path.join(_base_folder, 'pysamloader', 'devices'), 'devices'),
    ]

    def _filter_py(tarinfo):
        if os.path.splitext(tarinfo.name)[1] == '.pyc':
            return None
        if tarinfo.isdir() and tarinfo.name.endswith('__pycache__'):
            return None
        return tarinfo

    if platform.system() == 'Linux':
        print("Create Tarfile {0}".format(_binary_package_path), file=sys.stderr)
        with tarfile.open(_binary_package_path, "w:gz") as tar:
            for item, arc in package_content:
                print("Adding {0}".format(item), file=sys.stderr)
                tar.add(item, arcname=arc, filter=_filter_py)
    elif platform.system() == 'Windows':
        print("Create Zipfile {0}".format(_binary_package_path), file=sys.stderr)
        with zipfile.ZipFile(_binary_package_path, "w") as zfile:
            for item, arc in package_content:
                if os.path.isfile(item):
                    print("Adding {0}".format(item), file=sys.stderr)
                    zfile.write(item, arcname=arc)
                else:
                    print("Entering {0}".format(item), file=sys.stderr)
                    for f in os.listdir(item):
                        fullpath = os.path.join(item, f)
                        if os.path.isfile(fullpath):
                            print("Adding {0}".format(fullpath), file=sys.stderr)
                            zfile.write(fullpath, arcname=os.path.join(arc, f))


def task_package_binary():
    return {
        'task_dep': ['build_binary'],
        'actions': [_create_binary_package],
        'targets': [_binary_package_path],
        'clean': True
    }


def task_publish_binary():
    return {
        'actions': [],
        'file_dep': [_binary_package_path],
    }


def task_build_pypi():
    return {
        'actions': ['python setup.py sdist bdist_wheel'],
        'targets': [
            os.path.join(_dist_folder, _sdist_name),
            os.path.join(_dist_folder, _bdist_name),
            os.path.join(_egg_info_folder, "dependency_links.txt"),
            os.path.join(_egg_info_folder, "entry_points.txt"),
            os.path.join(_egg_info_folder, "PKG-INFO"),
            os.path.join(_egg_info_folder, "requires.txt"),
            os.path.join(_egg_info_folder, "SOURCES.txt"),
            os.path.join(_egg_info_folder, "top_level.txt"),
            _egg_info_folder,
        ],
        'task_dep': ['setup_build'],
        'clean': True
    }


def task_publish_pypi():
    if 'dev' in SCRIPT_VERSION or not publish_pypi:
        return {
            'actions': []
        }
    return {
        'file_dep': [
            os.path.join(_dist_folder, _sdist_name),
            os.path.join(_dist_folder, _bdist_name),
        ],
        'actions': [
            'twine upload %(dependencies)s --sign'
        ]
    }


def task_build():
    return {
        'actions': [],
        'task_dep': [
            'build_binary',
            'build_pypi'
        ],
    }


def task_publish():
    return {
        'actions': [],
        'task_dep': [
            'publish_binary',
            'publish_pypi'
        ]
    }
