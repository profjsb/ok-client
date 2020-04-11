from client.cli import publish
import unittest
import tempfile
import subprocess
import json
import os
import shlex
import sys

TEST_OK_FILE = {
    "name": "Test Assignment",
    "endpoint": "cal/cs61a/fa19/test",
    "src": [
        "test.py"
    ],
    "tests": {
        "test.py": "doctest,lint_test"
    },
    "default_tests": [
        "test1"
    ],
    "protocols": [
        "restore",
        "file_contents",
        "unlock",
        "grading",
        "analytics",
        "backup"
    ]
}

TEST_FILE = '''
def f(x):
    """
    >>> f(2)
    4
    >>> f(3)
    9
    """
    return x ** 2
def g(x):
    """
    >>> g(2)
    4
    >>> g(3)
    9
    """
    return x ** 3
'''

SCRIPT = """
. {envloc}/{folder}/activate;
python ok {args}
"""

class SmokeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.clean_env_dir = tempfile.TemporaryDirectory()
        cls.create_clean_env()

    @classmethod
    def create_clean_env(cls):
        subprocess.check_call(["virtualenv", "-q", "-p", "python", cls.clean_env_dir.name])

    def setUp(self):
        self.maxDiff = None # the errors are pretty useless if you don't do this
        self.directory = tempfile.TemporaryDirectory()
        publish.package_client(self.directory.name)

    def add_file(self, name, contents):
        with open(os.path.join(self.directory.name, name), "w") as f:
            f.write(contents)

    def add_ok_file(self):
        self.add_file("test.ok", json.dumps(TEST_OK_FILE))

    def run_ok(self, *args):
        command_line = SCRIPT.format(
            envloc=shlex.quote(self.clean_env_dir.name),
            folder="Scripts" if sys.platform == "win32" else "bin",
            args=" ".join(shlex.quote(arg) for arg in args),
        )
        print(command_line)
        with subprocess.Popen(
                os.getenv('SHELL', 'sh'),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=self.directory.name, universal_newlines=True) as proc:
            stdout, stderr = proc.communicate(command_line)
        return stdout, stderr

    def testVersion(self):
        stdout, stderr = self.run_ok("--version")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "^okpy==.*")

    def testUpdate(self):
        stdout, stderr = self.run_ok("--update")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "Current version: v[0-9.]+\nChecking for software updates...\nOK is up to date")

    def testRunNoArgument(self):
        self.add_ok_file()
        self.add_file("test.py", "")
        stdout, stderr = self.run_ok("--local")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, ".*0 test cases passed! No cases failed.*")

    def testPassingTest(self):
        self.add_ok_file()
        self.add_file("test.py", TEST_FILE)
        stdout, stderr = self.run_ok("-q", "f", "--local")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, ".*1 test cases passed! No cases failed.*")

    def testFailingTest(self):
        self.add_ok_file()
        self.add_file("test.py", TEST_FILE)
        stdout, stderr = self.run_ok("-q", "g", "--local")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, ".*0 test cases passed! No cases failed.*")
