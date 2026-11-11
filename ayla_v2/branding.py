"""Usa a identidade original, sem exigir download nem expor caminhos arbitrários."""
from pathlib import Path


def find_wordmark(base: Path) -> Path:
    # A cópia do repositório fica ao lado de ayla_v2: dart/assets/aylabrancoc.png.
    # O atualizador também pode copiar a imagem para static/assets.
    candidates = (
        base / "static" / "assets" / "aylabrancoc.png",
        base.parent / "dart" / "assets" / "aylabrancoc.png",
        base.parent / "dart" / "assets" / "images" / "aylabrancoc.png",
        base / "static" / "assets" / "logomarcabranco.png",
        base.parent / "dart" / "assets" / "logomarcabranco.png",
    )
    for path in candidates:
        if path.is_file():
            return path
    return base / "static" / "assets" / "wordmark-fallback.svg"
