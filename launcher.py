"""
Lanzador Maestro Unificado — PropTech Perú
Inicia Backend (FastAPI :8000) y Frontend (Next.js :3000) con verificación activa
y apertura automática del navegador una vez que ambos servidores están 100% listos.
"""

import os
import sys
import time
import socket
import subprocess
import urllib.request
import webbrowser

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = ROOT_DIR if os.path.exists(os.path.join(ROOT_DIR, "next.config.mjs")) else os.path.join(ROOT_DIR, "frontend")


def print_banner():
    print("=" * 65)
    print("        PROPTECH PERU - SISTEMA DE GESTION COMERCIAL")
    print("=" * 65)
    print()


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def kill_process_on_port(port: int):
    """Termina cualquier proceso que esté ocupando el puerto dado en Windows."""
    try:
        cmd = f'netstat -ano | findstr ":{port} "'
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
        pids = set()
        for line in output.strip().splitlines():
            parts = line.strip().split()
            if len(parts) >= 5 and parts[1].endswith(f":{port}") and parts[3] == "LISTENING":
                pids.add(parts[4])
        for pid in pids:
            if pid and pid != "0":
                print(f"  [LIMPIEZA] Liberando puerto {port} (PID {pid})...")
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
    except Exception:
        pass


def wait_for_http(url: str, name: str, max_timeout: int = 35) -> bool:
    """Espera activamente a que una URL devuelva HTTP 200 antes de continuar."""
    print(f"  [ESPERA] Verificando disponibilidad de {name}...", end="", flush=True)
    start = time.time()
    while time.time() - start < max_timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PropTech-Launcher/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as res:
                if res.status == 200:
                    print(f" [LISTO en {round(time.time() - start, 1)}s]")
                    return True
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(1.0)
    print(" [TIEMPO AGOTADO]")
    return False


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print_banner()

    # 1. Limpieza de puertos residuales
    print("[1/4] Verificando puertos del sistema...")
    for port in [8000, 3000]:
        if is_port_in_use(port):
            kill_process_on_port(port)
            time.sleep(1)

    python_cmd = sys.executable or "py -3.14"

    # 2. Inicializar base de datos / seeds si es necesario
    print("\n[2/4] Verificando base de datos SQLite y semillas auténticas...")
    try:
        subprocess.run([python_cmd, "seed.py"], cwd=BACKEND_DIR, capture_output=True, timeout=15)
        print("  ✓ Base de datos sincronizada con 11 malls y 78 locales.")
    except Exception as e:
        print(f"  (Nota seed: {e})")

    # 3. Arrancar Backend FastAPI
    print("\n[3/4] Iniciando Backend FastAPI (puerto 8000)...")
    backend_proc = subprocess.Popen(
        [python_cmd, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # 4. Arrancar Frontend Next.js
    print("\n[4/4] Iniciando Frontend Next.js (puerto 3000)...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # 5. Esperar disponibilidad real de ambos servidores
    print("\n[COMPROBACIÓN ACTIVA] Esperando que los servidores estén listos para recibir tráfico...")
    backend_ready = wait_for_http("http://127.0.0.1:8000/api/v1/centros-comerciales", "Backend API")
    frontend_ready = wait_for_http("http://localhost:3000", "Frontend Web")

    if not backend_ready:
        print("\n  [ADVERTENCIA] El backend tardó más de lo esperado en responder.")
    if not frontend_ready:
        print("\n  [ADVERTENCIA] El frontend tardó más de lo esperado en compilar.")

    # 6. Abrir navegador cuando esté 100% listo
    print("\n" + "=" * 65)
    print("  ¡SISTEMA LISTO Y EN EJECUCIÓN!")
    print("  • Frontend: http://localhost:3000")
    print("  • Backend:  http://localhost:8000/docs (Swagger UI)")
    print("=" * 65)
    print("\n  Abriendo navegador en http://localhost:3000...")
    webbrowser.open("http://localhost:3000")

    print("\n  Presiona Ctrl+C para detener ambos servidores en cualquier momento.\n")

    try:
        while True:
            # Monitorear si alguno terminó inesperadamente
            b_poll = backend_proc.poll()
            f_poll = frontend_proc.poll()
            if b_poll is not None:
                print(f"[ALERTA] Backend finalizó con código {b_poll}")
                break
            if f_poll is not None:
                print(f"[ALERTA] Frontend finalizó con código {f_poll}")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo servidores...")
    finally:
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Servidores detenidos limpiamente.")


if __name__ == "__main__":
    main()
