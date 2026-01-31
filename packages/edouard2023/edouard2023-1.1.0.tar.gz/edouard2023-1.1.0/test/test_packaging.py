# {# pkglts, glabpkg_dev
import edouard2023


def test_package_exists():
    assert edouard2023.__version__

# #}
# {# pkglts, glabdata, after glabpkg_dev

def test_paths_are_valid():
    assert edouard2023.pth_clean.exists()
    try:
        assert edouard2023.pth_raw.exists()
    except AttributeError:
        pass  # package not installed in editable mode

# #}
