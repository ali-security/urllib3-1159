import os
import shutil
import subprocess

import nox

SOURCE_FILES = [
    "docs/",
    "dummyserver/",
    "src/",
    "test/",
    "noxfile.py",
    "setup.py",
]


def tests_impl(session, extras="socks,secure,brotli"):
    # Install deps and the package itself.
    session.install(
        "--index-url",
        "https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        ".[{extras}]".format(extras=extras),
    )
    session.install(
        "--index-url",
        "https://:2023-05-23T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        "lazy-object-proxy==1.6.0",
    )
    session.install(
        "--index-url",
        "https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        "-r",
        "dev-requirements.txt",
    )

    # Show the pip version.
    session.run("pip", "--version")
    # Print the Python version and bytesize.
    session.run("python", "--version")
    session.run("python", "-c", "import struct; print(struct.calcsize('P') * 8)")
    # Print OpenSSL information.
    session.run("python", "-m", "OpenSSL.debug")

    # Inspired from https://hynek.me/articles/ditch-codecov-python/
    # We use parallel mode and then combine in a later CI step
    session.run(
        "coverage",
        "run",
        "--parallel-mode",
        "-m",
        "pytest",
        "-r",
        "a",
        f"--color={'yes' if 'GITHUB_ACTIONS' in os.environ else 'auto'}",
        "--tb=native",
        "--no-success-flaky-report",
        *(session.posargs or ("test/",)),
        env={"PYTHONWARNINGS": "always::DeprecationWarning"},
    )


@nox.session(python=["2.7", "3.6", "3.7", "3.8", "3.9", "3.10", "3.11", "pypy"])
def test(session):
    tests_impl(session)


@nox.session(python=["2.7", "3"])
def google_brotli(session):
    # https://pypi.org/project/Brotli/ is the Google version of brotli, so
    # install it separately and don't install our brotli extra (which installs
    # brotlipy).
    session.install(
        "--index-url",
        "https://:2023-09-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        "brotli",
    )
    tests_impl(session, extras="socks,secure")


@nox.session(python="2.7")
def app_engine(session):
    session.install(
        "--index-url",
        "https://:2023-05-23T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        "lazy-object-proxy==1.6.0",
    )
    session.install(
        "--index-url",
        "https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        "-r",
        "dev-requirements.txt",
    )
    session.install(
        "--index-url",
        "https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        ".",
    )
    session.run(
        "coverage",
        "run",
        "--parallel-mode",
        "-m",
        "pytest",
        "-r",
        "sx",
        "test/appengine",
        *session.posargs,
    )


def git_clone(session, git_url):
    session.run("git", "clone", "--depth", "1", git_url, external=True)


@nox.session(python=["3.10"])
def downstream_botocore(session):
    root = os.getcwd()
    tmp_dir = session.create_tmp()

    session.cd(tmp_dir)
    git_clone(session, "https://github.com/boto/botocore")
    session.chdir("botocore")
    session.run("git", "rev-parse", "HEAD", external=True)
    session.run("python", "scripts/ci/install")

    session.cd(root)
    session.install(
        "--index-url",
        "https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        ".",
        silent=False,
    )
    session.cd(f"{tmp_dir}/botocore")

    session.run("python", "scripts/ci/run-tests")


@nox.session(python=["3.10"])
def downstream_requests(session):
    root = os.getcwd()
    tmp_dir = session.create_tmp()

    session.cd(tmp_dir)
    git_clone(session, "https://github.com/psf/requests")
    session.chdir("requests")
    session.run("git", "rev-parse", "HEAD", external=True)
    session.install(
        "--index-url",
        "https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        ".[socks]",
        silent=False,
    )
    session.install(
        "--index-url",
        "https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        "-r",
        "requirements-dev.txt",
        silent=False,
    )

    session.cd(root)
    session.install(
        "--index-url",
        "https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        ".",
        silent=False,
    )
    session.cd(f"{tmp_dir}/requests")

    session.run("pytest", "tests")


@nox.session()
def format(session):
    """Run code formatters."""
    session.install(
        "--index-url",
        "https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        "pre-commit",
    )
    session.run("pre-commit", "--version")

    process = subprocess.run(
        ["pre-commit", "run", "--all-files"],
        env=session.env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # Ensure that pre-commit itself ran successfully
    assert process.returncode in (0, 1)

    lint(session)


@nox.session
def lint(session):
    session.install(
        "--index-url",
        "https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        "pre-commit",
    )
    session.run("pre-commit", "run", "--all-files")


@nox.session
def docs(session):
    session.install(
        "--index-url",
        "https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        "-r",
        "docs/requirements.txt",
    )
    session.install(
        "--index-url",
        "https://:2023-10-02T00:00:00.000000Z@time-machines-pypi.sealsecurity.io/",
        ".[socks,secure,brotli]",
    )

    session.chdir("docs")
    if os.path.exists("_build"):
        shutil.rmtree("_build")
    session.run("sphinx-build", "-b", "html", "-W", ".", "_build/html")
