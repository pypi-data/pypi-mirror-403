from glob import glob
import os
import sys
from setuptools import setup

if sys.version_info[:2] < (3, 7):
    error = (
        "pygraphx 3.4+ requires Python 3.7 or later (%d.%d detected). \n"
    )
    sys.stderr.write(error + "\n")
    sys.exit(1)


name = "pygraphx"
description = "Python package for creating and manipulating graphs and networks"
authors = {
    "Hagberg": ("Bruce Carroll", "brucecarroll01@proton.me"),
}
maintainer = "pygraphx Developers"
maintainer_email = "pygraphx-discuss@googlegroups.com"
url = "https://networkx.org/"
project_urls = {
    "Bug Tracker": "https://github.com/brucecarroll01/pygraphx/issues",
    "Documentation": "https://networkx.org/documentation/stable/",
    "Source Code": "https://github.com/brucecarroll01/pygraphx",
}
platforms = ["Linux", "Mac OSX", "Windows", "Unix"]
keywords = [
    "Networks",
    "Graph Theory",
    "Mathematics",
    "network",
    "graph",
    "discrete mathematics",
    "math",
]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
    "Topic :: Scientific/Engineering :: Information Analysis",
    "Topic :: Scientific/Engineering :: Mathematics",
    "Topic :: Scientific/Engineering :: Physics",
]

with open("pygraphx/__init__.py") as fid:
    for line in fid:
        if line.startswith("__version__"):
            version = line.strip().split()[-1][1:-1]
            break

packages = [
    "pygraphx",
    "pygraphx.algorithms",
    "pygraphx.algorithms.assortativity",
    "pygraphx.algorithms.bipartite",
    "pygraphx.algorithms.node_classification",
    "pygraphx.algorithms.centrality",
    "pygraphx.algorithms.community",
    "pygraphx.algorithms.components",
    "pygraphx.algorithms.connectivity",
    "pygraphx.algorithms.coloring",
    "pygraphx.algorithms.flow",
    "pygraphx.algorithms.minors",
    "pygraphx.algorithms.traversal",
    "pygraphx.algorithms.isomorphism",
    "pygraphx.algorithms.shortest_paths",
    "pygraphx.algorithms.link_analysis",
    "pygraphx.algorithms.operators",
    "pygraphx.algorithms.approximation",
    "pygraphx.algorithms.tree",
    "pygraphx.classes",
    "pygraphx.generators",
    "pygraphx.drawing",
    "pygraphx.linalg",
    "pygraphx.readwrite",
    "pygraphx.readwrite.json_graph",
    "pygraphx.tests",
    "pygraphx.testing",
    "pygraphx.utils",
]

docdirbase = "share/doc/pygraphx-%s" % version
# add basic documentation
data = [(docdirbase, glob("*.txt"))]
# add examples
for d in [
    ".",
    "advanced",
    "algorithms",
    "basic",
    "3d_drawing",
    "drawing",
    "graph",
    "javascript",
    "jit",
    "pygraphviz",
    "subclass",
]:
    dd = os.path.join(docdirbase, "examples", d)
    pp = os.path.join("examples", d)
    data.append((dd, glob(os.path.join(pp, "*.txt"))))
    data.append((dd, glob(os.path.join(pp, "*.py"))))
    data.append((dd, glob(os.path.join(pp, "*.bz2"))))
    data.append((dd, glob(os.path.join(pp, "*.gz"))))
    data.append((dd, glob(os.path.join(pp, "*.mbox"))))
    data.append((dd, glob(os.path.join(pp, "*.edgelist"))))
# add js force examples
dd = os.path.join(docdirbase, "examples", "javascript/force")
pp = os.path.join("examples", "javascript/force")
data.append((dd, glob(os.path.join(pp, "*"))))

# add the tests
package_data = {
    "pygraphx": ["tests/*.py"],
    "pygraphx.algorithms": ["tests/*.py"],
    "pygraphx.algorithms.assortativity": ["tests/*.py"],
    "pygraphx.algorithms.bipartite": ["tests/*.py"],
    "pygraphx.algorithms.node_classification": ["tests/*.py"],
    "pygraphx.algorithms.centrality": ["tests/*.py"],
    "pygraphx.algorithms.community": ["tests/*.py"],
    "pygraphx.algorithms.components": ["tests/*.py"],
    "pygraphx.algorithms.connectivity": ["tests/*.py"],
    "pygraphx.algorithms.coloring": ["tests/*.py"],
    "pygraphx.algorithms.minors": ["tests/*.py"],
    "pygraphx.algorithms.flow": ["tests/*.py", "tests/*.bz2"],
    "pygraphx.algorithms.isomorphism": ["tests/*.py", "tests/*.*99"],
    "pygraphx.algorithms.link_analysis": ["tests/*.py"],
    "pygraphx.algorithms.approximation": ["tests/*.py"],
    "pygraphx.algorithms.operators": ["tests/*.py"],
    "pygraphx.algorithms.shortest_paths": ["tests/*.py"],
    "pygraphx.algorithms.traversal": ["tests/*.py"],
    "pygraphx.algorithms.tree": ["tests/*.py"],
    "pygraphx.classes": ["tests/*.py"],
    "pygraphx.generators": ["tests/*.py", "atlas.dat.gz"],
    "pygraphx.drawing": ["tests/*.py"],
    "pygraphx.linalg": ["tests/*.py"],
    "pygraphx.readwrite": ["tests/*.py"],
    "pygraphx.readwrite.json_graph": ["tests/*.py"],
    "pygraphx.testing": ["tests/*.py"],
    "pygraphx.utils": ["tests/*.py", "*.pem"],
}


def parse_requirements_file(filename):
    with open(filename) as fid:
        requires = [l.strip() for l in fid.readlines() if not l.startswith("#")]

    return requires


install_requires = []
extras_require = {
    dep: parse_requirements_file("requirements/" + dep + ".txt")
    for dep in ["default", "developer", "doc", "extra", "test"]
}

with open("README.rst", "r") as fh:
    long_description = fh.read()

if __name__ == "__main__":

    setup(
        name=name,
        version=version,
        maintainer=maintainer,
        maintainer_email=maintainer_email,
        author=authors["Hagberg"][0],
        author_email=authors["Hagberg"][1],
        description=description,
        keywords=keywords,
        long_description=long_description,
        platforms=platforms,
        url=url,
        project_urls=project_urls,
        classifiers=classifiers,
        packages=packages,
        data_files=data,
        package_data=package_data,
        install_requires=install_requires,
        extras_require=extras_require,
        python_requires=">=3.7",
        zip_safe=False,
    )
