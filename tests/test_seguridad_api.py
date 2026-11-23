"""Ejecuta las pruebas de seguridad de la API completa en un proceso aparte."""
import os
import subprocess
import sys


def test_pruebas_de_seguridad_de_la_api():
    carpeta = os.path.join(os.path.dirname(__file__), "integracion")
    resultado = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", carpeta],
        capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)), timeout=300,
    )
    assert resultado.returncode == 0, resultado.stdout[-4000:] + resultado.stderr[-2000:]
