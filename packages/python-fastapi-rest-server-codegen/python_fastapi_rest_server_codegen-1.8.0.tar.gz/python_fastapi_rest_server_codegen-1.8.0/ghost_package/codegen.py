import subprocess
import os
import lcdp_api.rest
from pathlib import Path

try:
  import importlib.resources as pkg_resources
except ImportError:
  # Try backported to PY<37 `importlib_resources`.
  import importlib_resources as pkg_resources

# Get current script dir
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

# Codegen command constants
OPENAPI_CODEGEN_CLASS = "org.openapitools.codegen.OpenAPIGenerator"

def get_api_path(api_filename):
  return pkg_resources.path(lcdp_api.rest, api_filename)

def get_codegen_cli_path():
  return pkg_resources.path(__package__, "openapi-generator-cli.jar")

def get_codegen_path():
    return pkg_resources.path(__package__, "python-fastapi-rest-server-codegen.jar")


def generate_provider(api_spec_file_name, out_dir):
  with get_api_path(api_spec_file_name) as api_spec_file_path:
    api_name = get_api_name_from_spec_file_path(api_spec_file_path)

    api_spec_file_abs_path = os.path.join(CURRENT_DIR, "..", api_spec_file_path)

    # Compute generator path
    with get_codegen_path() as server_codegen_jar_path, get_codegen_cli_path() as cli_jar_path:
      openapi_codegen_java_classpath = compute_codegen_java_classpath(cli_jar_path, server_codegen_jar_path)

      execute_provider_codegen(openapi_codegen_java_classpath, server_codegen_jar_path.stem, api_spec_file_abs_path,
                              out_dir, "api.provide.gen", "api.provide.impl", api_name)

def get_api_name_from_spec_file_path(api_spec_file_path):
  api_name = os.path.basename(api_spec_file_path).split(".")[0]
  return api_name.replace("-", "_")


def compute_codegen_java_classpath(cli_jar_path, codegen_jar_path):
  sep = ";" if os.name == "nt" else ":"
  return sep.join([str(cli_jar_path), str(codegen_jar_path)])


def execute_provider_codegen(openapi_codegen_java_classpath, codegen_name,
                              api_spec_file_path, outdir,
                              package_name, package_name_impl, api_name):
  """
    Provider is generated above leaf
  """
  properties = [
    "--package-name", package_name + "." + api_name
  ]

  additional_properties = [
    "controllerPackage=" + api_name + '.controllers',
    "packageNameImpl=" + package_name_impl + "." + api_name + ".controllers",
    "testPackage=" + api_name + '.tests',
    "apiDocPath=" + api_name + '/docs',
    "modelDocPath=" + api_name + '/docs',
    "fastapiImplementationPackage=" + package_name_impl + "." + api_name + ".controllers",
    "commonPackageName=" + package_name + ".common",
  ]

  execute_codegen_command(openapi_codegen_java_classpath, codegen_name, api_spec_file_path, outdir, properties,
                          additional_properties)

def execute_codegen_command(openapi_codegen_java_classpath, codegen_name, api_spec_file_path, outdir, properties,
                            additional_properties):
  subprocess.check_call(["java", "-cp", openapi_codegen_java_classpath, OPENAPI_CODEGEN_CLASS, "generate", "-g",
                         codegen_name, "-i", api_spec_file_path, "-o", outdir] +
                         properties +
                         # controllerPackage is used by server codegen
                         ["--additional-properties=" + ",".join(additional_properties)
                         ])
