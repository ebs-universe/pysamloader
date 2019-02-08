

import os
import sys
import six
import shutil
import github
import platform

from doit.task import clean_targets
from doit.tools import create_folder
from doit.action import CmdAction
from setuptools_scm import get_version

DOIT_CONFIG = {
    'default_tasks': ['build',
                      'package_binary'],
}

# Application Information
# -----------------------

SCRIPT_NAME = 'pysamloader'
SCRIPT_VERSION = get_version(root='.', relative_to=__file__)
GITHUB_PATH = 'chintal/{0}'.format(SCRIPT_NAME)

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
    package_content_type = 'application/gzip'
    executable_ext = ''
    pyi_prefix = "LD_LIBRARY_PATH={0} ".format(_get_python_shared_lib())
    publish_pypi = True
    doc_build_actions = [CmdAction('make latexpdf', cwd='docs')]
    doc_clean_actions = [CmdAction('make clean', cwd='docs')]
elif platform.system() == 'Windows':
    import zipfile
    package_ext = '.zip'
    package_content_type = 'application/zip'
    installer_content_type = 'application/x-msi'
    executable_ext = '.exe'
    installer_ext = '.msi'
    pyi_prefix = ""
    publish_pypi = False
    doc_build_actions = [
        CmdAction('make.bat latex', cwd='docs'),
        CmdAction('make.bat', cwd=os.path.join('docs', '_build', 'latex'))
    ]
    doc_clean_actions = [CmdAction('make clean', cwd='docs')]
else:
    raise NotImplementedError("Platform not supported : {0}"
                              "".format(platform.system()))

with open('.release_token', 'r') as f:
    release_token = f.read().strip()


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
_installer_name = "{0}-{1}-{2}{3}".format(SCRIPT_NAME, SCRIPT_VERSION, 
                                          platform.machine().lower(), installer_ext)
_installer_path = os.path.join(_base_folder, 'packaging', 
                               platform.machine().lower(), _installer_name)
_sdist_name = '{0}-{1}.tar.gz'.format(SCRIPT_NAME, SCRIPT_VERSION)
_bdist_name = '{0}-{1}-{2}-none-any.whl'.format(SCRIPT_NAME, SCRIPT_VERSION, pytag)
_egg_info_folder = os.path.join(_base_folder, "{0}.egg-info".format(SCRIPT_NAME))
_doc_name = SCRIPT_NAME + '.pdf'
_doc_path = os.path.join(_base_folder, 'docs', '_build', 'latex', _doc_name)


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
        'actions': [
            _inject_version,
            (create_folder, [_dist_folder]),
            (create_folder, [_work_folder])
        ],
        'targets': [
            os.path.join(_base_folder, SCRIPT_NAME, '_version.py'),
            _dist_folder,
        ],
        'clean': [_clean_work_folder, clean_targets]
    }


def task_build_doc():
    return {
        'actions': doc_build_actions,
        'targets': [_doc_path],
        'clean': doc_clean_actions,
        'task_dep': ['setup_build']
    }


def task_build_binary():
    return {
        'actions': [pyi_prefix + 'pyinstaller {0}.spec'.format(SCRIPT_NAME)],
        'targets': [_executable_path, _binary_dist_folder],
        'task_dep': ['setup_build'],
        'clean': True
    }


def _create_binary_package():
    package_content = [
        (os.path.join(_binary_dist_folder, _executable_name), _executable_name),
        (os.path.join(_base_folder, 'LICENSE'), 'LICENSE'),
        (_doc_path, _doc_name),
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
        'task_dep': ['build_binary', 'build_doc'],
        'actions': [_create_binary_package],
        'targets': [_binary_package_path],
        'clean': True
    }


def _get_github_tag(repo, v):
    found_tags = repo.get_tags()
    for tag in found_tags:
        if tag.name == v:
            print("Found tag : {0}".format(tag), file=sys.stderr)
            return tag
    raise FileNotFoundError


def _get_github_release(repo, v):
    found_releases = repo.get_releases()
    for release in found_releases:
        if release.tag_name == v:
            print("Found GitHub Release : {0}".format(release), file=sys.stderr)
            return release
    try:
        tag = _get_github_tag(repo, v)
        print("Creating GitHub Release : {0}".format(v), file=sys.stderr)
        return repo.create_git_release(tag.name, v, "{0} Release".format(v))
    except FileNotFoundError:
        raise Exception("Cannot publish binary package. "
                        "Create and push github tag for {0} first!".format(v))


def _publish_binary_package():
    g = github.Github(release_token)
    repo = g.get_repo(GITHUB_PATH)
    release = _get_github_release(repo, "v{0}".format(SCRIPT_VERSION))
    release.upload_asset(
        _binary_package_path, content_type=package_content_type,
        label = "{0} Binary Package".format(platform.system())
    )


def task_publish_binary():
    if 'dev' in SCRIPT_VERSION:
        return {'actions': []}
    return {
        'actions': [_publish_binary_package],
        'file_dep': [_binary_package_path],
    }


def _publish_installer():
    g = github.Github(release_token)
    repo = g.get_repo(GITHUB_PATH)
    release = _get_github_release(repo, "v{0}".format(SCRIPT_VERSION))
    release.upload_asset(
        _installer_path, content_type=installer_content_type,
        label = "{0} Installer".format(platform.system())
    )


def task_publish_installer():
    if 'dev' in SCRIPT_VERSION or not platform.system() == 'Windows':
        return {'actions': []}
    return {
        'actions': [_publish_installer],
        'file_dep': [_installer_path],
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
        return {'actions': []}
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
            'build_pypi',
            'build_doc'
        ],
    }


def task_package():
    return {
        'actions': [],
        'task_dep': [
            'build_pypi',
            'package_binary'
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
