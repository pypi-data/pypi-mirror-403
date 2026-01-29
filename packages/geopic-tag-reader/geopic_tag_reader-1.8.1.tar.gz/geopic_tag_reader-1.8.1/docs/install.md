# Install as a command-line tool

GeoPicTagReader can be installed using two methods:

- :simple-python: From [PyPI](https://pypi.org/project/geopic-tag-reader/), the Python central package repository
- :simple-git: Using this [Git repository](https://gitlab.com/panoramax/server/geo-picture-tag-reader)

GeoPicTagReader is compatible with all Python versions >= 3.8.

!!! note
    Due to [Pyexiv2 dependency on a recent GLIBC version](https://github.com/LeoHsiao1/pyexiv2/issues/120), you have to make sure to run on a recent, up-to-date operating system.

=== ":simple-python: PyPI"

    Just launch this command:

    ```bash
    pip install geopic_tag_reader
    ```

=== "pipx"

    Alternatively, you can use [pipx](https://github.com/pypa/pipx) if you want all the script dependencies to be in a custom virtual env.

    You need to [install pipx](https://pypa.github.io/pipx/installation/), then:

    ```bash
    pipx install geopic_tag_reader
    ```

=== ":simple-git: Git repository"

    Download the repository:

	<div class="annotate" markdown>

    ```bash
    git clone https://gitlab.com/panoramax/server/geo-picture-tag-reader.git geopic_tag_reader
    cd geopic_tag_reader/
    
    # Create the virtual environment in a folder named "env" (1)
    python3 -m venv env

    # Launches utilities to make environment available in your Bash
    source ./env/bin/activate

    # Then, install the dependencies using pip:
    pip install -e .
    ```
    </div>

    1. To avoid conflicts, it's considered a good practice to create a _[virtual environment](https://docs.python.org/3/library/venv.html)_ (or virtualenv).

After this you should be able to use the CLI tool with the name `geopic-tag-reader`:

```bash
geopic-tag-reader --help
```

### Write EXIF tags

If you want to be able to write exif tags, you need to also install the `write-exif` extra:

This will install [libexiv2](https://exiv2.org/) if available in the target platform.

=== ":simple-python: PyPI"

    ```bash
    pip install geopic_tag_reader[write-exif]
    ```

=== "pipx"

    ```bash
    pipx install geopic_tag_reader[write-exif]
    ```

=== ":simple-git: Git repository"

    ```bash
    pip install -e .[write-exif]
    ```
