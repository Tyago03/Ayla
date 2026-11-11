"""Ditado local opcional. Download só no instalador; áudio processado em memória.

Usa CPU int8 para não ocupar a VRAM dedicada ao Qwen. Nunca grava áudio em disco.
"""
from importlib.util import find_spec
from io import BytesIO
from pathlib import Path
import threading
from .errors import AppError

MODEL_PATH = Path(__file__).resolve().parent / "data" / "speech-model"
MAX_AUDIO_BYTES = 5 * 1024 * 1024
MAX_SECONDS = 60

class LocalSpeech:
    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = model_path
        self._model = None
        self._gate = threading.BoundedSemaphore(1)

    def status(self) -> dict:
        installed = find_spec("faster_whisper") is not None
        files = all((self.model_path / name).is_file() for name in ("model.bin", "config.json", "tokenizer.json"))
        return {"disponivel": installed and files, "dependencia": installed, "modelo_baixado": files,
                "modo": "Whisper base · CPU · local", "limite_segundos": MAX_SECONDS}

    def transcribe(self, raw: bytes) -> str:
        if not raw or len(raw) > MAX_AUDIO_BYTES:
            raise AppError("Áudio vazio ou acima do limite de 5 MB.", 413)
        if not self.status()["disponivel"]:
            raise AppError("Ditado local não instalado. Execute ATIVAR_DITADO_LOCAL_AYLA.bat, reinicie o servidor e tente novamente.", 503)
        if not self._gate.acquire(blocking=False):
            raise AppError("Já existe um áudio sendo transcrito. Aguarde.", 429)
        try:
            # Decodifica no máximo 60 s; não usa um caminho fornecido pelo usuário.
            import av
            import numpy as np
            from faster_whisper import WhisperModel
            chunks, samples = [], 0
            with av.open(BytesIO(raw)) as container:
                resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
                for frame in container.decode(audio=0):
                    for out in resampler.resample(frame):
                        values = out.to_ndarray().reshape(-1)
                        samples += len(values)
                        if samples > MAX_SECONDS * 16000:
                            raise AppError("Use áudios de até 60 segundos.", 413)
                        chunks.append(values)
                for out in resampler.resample(None):
                    values = out.to_ndarray().reshape(-1)
                    samples += len(values)
                    if samples > MAX_SECONDS * 16000:
                        raise AppError("Use áudios de até 60 segundos.", 413)
                    chunks.append(values)
            if not chunks:
                raise AppError("Não encontrei áudio nessa gravação.", 422)
            audio = np.concatenate(chunks).astype(np.float32) / 32768.0
            if self._model is None:
                self._model = WhisperModel(str(self.model_path), device="cpu", compute_type="int8", cpu_threads=4, local_files_only=True)
            segments, _ = self._model.transcribe(audio, language="pt", beam_size=3,
                                                vad_filter=True, condition_on_previous_text=False)
            text = " ".join(s.text.strip() for s in segments).strip()
            if not text:
                raise AppError("Não identifiquei fala. Aproxime-se do microfone e tente novamente.", 422)
            if len(text) > 1000:
                raise AppError("A transcrição passou de 1.000 caracteres. Faça um ditado mais curto.", 422)
            return text
        except AppError:
            raise
        except Exception as exc:
            raise AppError("Não consegui transcrever esse áudio. Confira o formato, a instalação local e o microfone.", 422) from exc
        finally:
            self._gate.release()


def install_model() -> None:
    from faster_whisper.utils import download_model
    MODEL_PATH.mkdir(parents=True, exist_ok=True)
    print("Baixando Whisper base multilíngue do repositório público do modelo. Esta etapa usa internet.")
    download_model("base", output_dir=str(MODEL_PATH))
    # Confirma que o modelo baixado pode ser carregado, sem nova requisição.
    from faster_whisper import WhisperModel
    WhisperModel(str(MODEL_PATH), device="cpu", compute_type="int8", local_files_only=True)
    print("Ditado local preparado. Reinicie a Ayla e selecione Ditado local em Voz e microfone.")

if __name__ == "__main__":
    install_model()
