import errno
import json
from pathlib import Path
import pytest
from ayla_v2.publish import export_public, inspect_public


def _create_real_symlink_or_skip(link: Path, target: Path) -> None:
    """Skip only a known OS prerequisite, never a failure of the exporter.

    Windows can deny creation of a real symbolic link with WinError 1314.
    The independent simulated-link test below still checks export rejection.
    Other errors are re-raised, and export_public stays outside this handler.
    """
    try:
        link.symlink_to(target)
    except OSError as exc:
        if getattr(exc, "winerror", None) != 1314:
            raise
        pytest.skip(
            "WinError 1314: Windows não permitiu criar o link simbólico real. "
            "A proteção do exportador é verificada separadamente com simulação."
        )

@pytest.fixture
def source(tmp_path):
    root=tmp_path/'legacy';base=root/'ayla_v2';base.mkdir(parents=True)
    (base/'main.py').write_text('print("code only")')
    (base/'public_template').mkdir();(base/'public_template/README.md').write_text('# Test')
    (base/'public_manifest.json').write_text(json.dumps({'files':['main.py','public_manifest.json','public_template/README.md'],'shortcuts':['INICIAR_AYLA.bat']}))
    (root/'INICIAR_AYLA.bat').write_text('test shortcut')
    (base/'data').mkdir();(base/'data/db.sqlite3').write_bytes(b'private db')
    (base/'.env').write_text('secret not for export')
    (root/'.git').mkdir();(root/'.git/config').write_text('private history')
    (root/'Python').mkdir();(root/'Python/main.py').write_text('legacy')
    return root,base

def test_clean_export_no_data_history_secrets(source,tmp_path):
    root,base=source;dest=tmp_path/'new'
    result=export_public(dest,base)
    assert (dest/'ayla_v2/main.py').is_file()
    assert (dest/'INICIAR_AYLA.bat').is_file()
    for rel in ['.git','Python','dart','ayla_v2/.env','ayla_v2/data']:
        assert not (dest/rel).exists()
    assert (root/'.git/config').read_text()=='private history'
    assert inspect_public(dest)==[]

def test_export_refuses_existing_destination(source,tmp_path):
    _,base=source;dest=tmp_path/'exists';dest.mkdir();(dest/'keep').write_text('keep')
    with pytest.raises(ValueError):export_public(dest,base)
    assert (dest/'keep').read_text()=='keep'

def test_export_refuses_inside_old_repo(source):
    root,base=source
    with pytest.raises(ValueError):export_public(root/'new',base)

def test_export_rejects_symlink(source,tmp_path):
    root,base=source;(base/'main.py').unlink()
    secret=tmp_path/'private.py';secret.write_text('private')
    _create_real_symlink_or_skip(base / 'main.py', secret)
    with pytest.raises(ValueError):export_public(tmp_path/'new',base)
    assert not (tmp_path/'new').exists()

def test_export_refuses_path_traversal(source,tmp_path):
    _,base=source
    (base/'public_manifest.json').write_text(json.dumps({'files':['../Python/main.py'],'shortcuts':[]}))
    with pytest.raises(ValueError):export_public(tmp_path/'new',base)

def test_known_key_pattern_blocks_without_echo(source,tmp_path):
    _,base=source
    value='ghp_'+'Z'*40
    (base/'main.py').write_text('TOKEN="'+value+'"')
    with pytest.raises(ValueError) as exc:export_public(tmp_path/'new',base)
    assert value not in str(exc.value)
    assert not (tmp_path/'new').exists()

def test_secret_json_not_exportable(source,tmp_path):
    _,base=source
    value='a'*40+'.'+'b'*10
    (base/'main.py').write_text('OLLAMA_API_KEY = "'+value+'"')
    with pytest.raises(ValueError):export_public(tmp_path/'new',base)

def test_original_brand_image_optional(source,tmp_path):
    _,base=source;(base/'static/assets').mkdir(parents=True)
    (base/'static/assets/aylabrancoc.png').write_bytes(b'brand')
    dest=tmp_path/'new';export_public(dest,base)
    assert (dest/'ayla_v2/static/assets/aylabrancoc.png').read_bytes()==b'brand'


def test_export_rejects_detected_symlink_without_os_privileges(source, tmp_path, monkeypatch):
    """Portable unit check: a detected link must never be exported.

    Only the is_symlink result is simulated. export_public itself executes,
    including its refusal and staging-directory cleanup. No OS link is made.
    """
    _, base = source
    blocked = base / "main.py"
    original_is_symlink = Path.is_symlink

    def reports_link(path):
        return path == blocked or original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", reports_link)
    destination = tmp_path / "new"
    with pytest.raises(ValueError, match="link não permitido"):
        export_public(destination, base)
    assert not destination.exists()
    assert not list(tmp_path.glob(".ayla-export-*"))
    assert blocked.read_text() == 'print("code only")'


def test_symlink_setup_skips_only_windows_missing_privilege(tmp_path, monkeypatch):
    error = OSError("Synthetic missing privilege; no Windows execution")
    error.winerror = 1314

    def deny_creation(self, target, target_is_directory=False):
        raise error

    monkeypatch.setattr(Path, "symlink_to", deny_creation)
    with pytest.raises(pytest.skip.Exception, match="WinError 1314"):
        _create_real_symlink_or_skip(tmp_path / "link", tmp_path / "target")


@pytest.mark.parametrize("winerror, error_number", [
    (5, errno.EACCES),
    (None, errno.EACCES),
    (None, errno.ENOSPC),
])
def test_symlink_setup_does_not_hide_unrelated_errors(
    tmp_path, monkeypatch, winerror, error_number
):
    error = OSError(error_number, "Synthetic unrelated OS error")
    if winerror is not None:
        error.winerror = winerror

    def deny_creation(self, target, target_is_directory=False):
        raise error

    monkeypatch.setattr(Path, "symlink_to", deny_creation)
    with pytest.raises(OSError) as captured:
        _create_real_symlink_or_skip(tmp_path / "link", tmp_path / "target")
    assert captured.value is error
