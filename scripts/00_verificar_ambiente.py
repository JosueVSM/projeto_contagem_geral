"""Passo 0: confere se o ambiente está pronto (GPU, bibliotecas, pastas, vídeos).

Uso:  python scripts/00_verificar_ambiente.py
"""

import _caminhos  # noqa: F401
import platform

from configuracao import carregar_config, ler_linhas, ler_videos, resolver_pasta


def main():
    print(f"Python {platform.python_version()} em {platform.system()} {platform.release()}")
    try:
        import torch

        print(f"PyTorch {torch.__version__} | CUDA disponível: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            print(f"  GPU: {p.name} ({p.total_memory / 2**30:.1f} GB)")
        else:
            print("  [ATENÇÃO] Sem GPU: o processamento vai rodar na CPU (bem mais lento).")
    except ImportError:
        print("[ERRO] PyTorch não instalado. Veja o README (seção Instalação).")
    try:
        import ultralytics

        print(f"Ultralytics {ultralytics.__version__}")
    except ImportError:
        print("[ERRO] ultralytics não instalado.")
    import cv2

    print(f"OpenCV {cv2.__version__}")

    cfg = carregar_config()
    pasta_videos = resolver_pasta(cfg["pastas"]["videos"])
    print(f"\nPasta de vídeos: {pasta_videos} ({'existe' if pasta_videos.is_dir() else 'NÃO existe'})")
    linhas = ler_linhas()
    print("\nVídeos em config/videos.csv:")
    for _, v in ler_videos(cfg).iterrows():
        status = "OK" if v["existe"] else "ainda não gravado/copiado"
        linha = "linha definida" if v["id"] in linhas else "linha NÃO definida"
        uso = "análise" if v["usar"] else "só teste"
        print(f"  {v['id']:<14} {v['arquivo']:<20} [{status}] [{linha}] [{uso}]")


if __name__ == "__main__":
    main()
