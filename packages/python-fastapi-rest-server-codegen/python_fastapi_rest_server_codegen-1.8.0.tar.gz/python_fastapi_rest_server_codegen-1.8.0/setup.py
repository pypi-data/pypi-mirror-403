import subprocess
import glob
import shutil
import os
from setuptools import setup
from setuptools.command.build_py import build_py

try:
  import importlib.resources as pkg_resources
except ImportError:
  # Try backported to PY<37 `importlib_resources`.
  import importlib_resources as pkg_resources

TOP_LEVEL_PACKAGE_NAME = "python_fastapi_rest_server_codegen"

class CustomBuild(build_py):
  def run(self):
    # Build target jar
    subprocess.check_call(["mvn", "clean", "package"])

    # Run classic build that will convert ghost_package to toplevel
    build_py.run(self)

    # Find toplevel and add files in it
    toplevel_package = os.path.join(self.build_lib, TOP_LEVEL_PACKAGE_NAME)
    for file in glob.glob("target/*.jar"):
      shutil.copy(file, toplevel_package)

    import openapi_generator_cli
    with pkg_resources.path(openapi_generator_cli, "openapi-generator-cli.jar") as openapi_generator_cli_jar:
      shutil.copy(str(openapi_generator_cli_jar), toplevel_package)

setup(
  name="python_fastapi_rest_server_codegen",
  version_config={
    "dirty_template": "{tag}.post{ccount}+git.{sha}", # See : https://github.com/dolfinus/setuptools-git-versioning/pull/16#issuecomment-867444549
  },
  install_requires=[
    'connexion==3.1.0',
    'python_dateutil >= 2.6.0',
    'Flask == 2.2.5',
    'Werkzeug == 2.2.2',
    'pyjwt==2.8.0',
  ],
  setup_requires=[
    'setuptools-git-versioning==1.4.0',
    'python-openapi-generator-cli-jar==7.8.0'
  ],
  packages=[TOP_LEVEL_PACKAGE_NAME],
  package_data={
    # If any package contains *.jar files, include them:
    TOP_LEVEL_PACKAGE_NAME: ['*.jar'],
  },
  package_dir={TOP_LEVEL_PACKAGE_NAME: 'ghost_package'},
  license='Apache-2.0',
  description='Python rest server codegen for Le Comptoir Des Pharmacies',
  long_description='Python rest server codegen for Le Comptoir Des Pharmacies',
  author='Le Comptoir Des Pharmacies',
  author_email='g.thrasibule@lecomptoirdespharmacies.fr',
  url='https://bitbucket.org/lecomptoirdespharmacies/lcdp-openapi-codegen',
  keywords=['openapi', 'python-fastapi-rest-server-codegen', 'openapi3'],
  cmdclass={'build_py': CustomBuild},
)
