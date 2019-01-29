

import os
import sys
import six
import platform

from pkg_resources import get_distribution

SCRIPT_NAME = 'pysamloader'
SCRIPT_VERSION = get_distribution(SCRIPT_NAME).version


def _get_python_shared_lib():
    real_exec = sys.executable
    while os.path.islink(real_exec):
        real_exec = os.readlink(real_exec)
    return os.path.normpath(
        os.path.join(os.path.split(real_exec)[0], os.pardir, 'lib')
    )


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


def _base_folder():
    return os.path.join(os.path.split(__file__)[0])


def _dist_folder():
    return os.path.join(_base_folder(), 'dist')


def _binary_dist_folder():
    target = 'binary-{0}'.format(platform.system().lower())
    return os.path.join(_dist_folder(), target)


def _executable_name():
    return SCRIPT_NAME + executable_ext


def _executable_path():
    return os.path.join(_binary_dist_folder(), _executable_name())


def _binary_package_name():
    return "{0}-{1}-{2}-{3}{4}".format(
        SCRIPT_NAME, SCRIPT_VERSION,
        platform.system().lower(), platform.machine().lower(), 
        package_ext
    )


def _binary_package_path():
    return os.path.join(_binary_dist_folder(), _binary_package_name())


def _sdist_name():
    return '{0}-{1}.tar.gz'.format(SCRIPT_NAME, SCRIPT_VERSION)


def _bdist_name():
    if six.PY2:
        pytag = 'py2'
    elif six.PY3:
        pytag = 'py3'
    else:
        pytag = 'unknown'
    return '{0}-{1}-{2}-none-any.whl'.format(SCRIPT_NAME, SCRIPT_VERSION, pytag)


def task_build_binary():
    return {
        'actions': [pyi_prefix + 'pyinstaller {0}.spec'.format(SCRIPT_NAME)],
        'targets': [_executable_path()]
    }


def _create_binary_package():
    package_content = [
        (os.path.join(_binary_dist_folder(), _executable_name()), _executable_name()),
        (os.path.join(_base_folder(), 'LICENSE'), 'LICENSE'),
        (os.path.join(_base_folder(), 'README.rst'), 'README.rst'),
        (os.path.join(_base_folder(), 'pysamloader', 'devices'), 'devices'),
    ]

    def _filter_py(tarinfo):
        if os.path.splitext(tarinfo.name)[1] == '.pyc':
            return None
        if tarinfo.isdir() and tarinfo.name.endswith('__pycache__'):
            return None
        return tarinfo

    if platform.system() == 'Linux':
        print("Create Tarfile {0}".format(_binary_package_path()), file=sys.stderr)
        with tarfile.open(_binary_package_path(), "w:gz") as tar:
            for item, arc in package_content:
                print("Adding {0}".format(item), file=sys.stderr)
                tar.add(item, arcname=arc, filter=_filter_py)
    elif platform.system() == 'Windows':
        print("Create Zipfile {0}".format(_binary_package_path()), file=sys.stderr)
        with zipfile.ZipFile(_binary_package_path(), "w") as zfile:
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
        'targets': [_binary_package_path()]
    }


def task_publish_binary():
    return {
        'actions': [],
        'file_dep': [_binary_package_path()],
    }


def task_build_pypi():
    return {
        'actions': ['python setup.py sdist bdist_wheel'],
        'targets': [
            os.path.join(_dist_folder(), _sdist_name()),
            os.path.join(_dist_folder(), _bdist_name()),
        ]
    }


def task_publish_pypi():
    if 'dev' in SCRIPT_VERSION or not publish_pypi:
        return {
            'actions': []
        }
    return {
        'file_dep': [
            os.path.join(_dist_folder(), _sdist_name()),
            os.path.join(_dist_folder(), _bdist_name()),
        ],
        'actions': [
            'twine upload %(dependencies)s --sign'
        ]
    }


def task_publish():
    return {
        'actions': [],
        'task_dep': [
            'publish_binary',
            'publish_pypi'
        ]
    }
