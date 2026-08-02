import os
import shutil
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

DEFAULT_URL = "https://pmo-ai-orchestrator-101547847876.southamerica-west1.run.app"
TIMEOUT = 120
DATA_DIR = Path("data")

console = Console()


def ask(base_url: str, query: str) -> dict:
    resp = requests.post(
        f"{base_url.rstrip('/')}/ask",
        json={"query": query},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def print_response(data: dict) -> None:
    console.print()
    console.print(Markdown(data.get("answer", "(sin respuesta)")))

    sources = data.get("sources") or []
    if sources:
        console.print("[bold]Fuentes:[/bold]")
        for s in sources:
            console.print(f"  [dim]- {s.get('fuente', '?')}, Sección: {s.get('seccion', '?')}[/dim]")

    meta = []
    if data.get("ruta"):
        meta.append(f"ruta: {data['ruta']}")
    if data.get("workers_usados"):
        meta.append(f"workers: {', '.join(data['workers_usados'])}")
    fiscalizacion = data.get("fiscalizacion")
    if fiscalizacion and not fiscalizacion.get("ok", True):
        meta.append("fiscalizador: corrigió la respuesta")
    if data.get("tokens") is not None:
        meta.append(f"tokens: {data['tokens']}")
    if data.get("latency_ms") is not None:
        meta.append(f"{data['latency_ms'] / 1000:.1f}s")
    if meta:
        console.print(f"[cyan dim]{' | '.join(meta)}[/cyan dim]")
    console.print()


def cmd_cargar(archivos: list[str]) -> None:
    load_dotenv()
    chroma_path = os.environ.get("CHROMA_PATH", ".chroma")
    bucket = os.environ.get("GCS_BUCKET", "pmo-ai-vectordb")

    if shutil.which("gsutil") is None:
        console.print("[red]Error: gsutil no está instalado. Instala Google Cloud SDK.[/red]")
        sys.exit(1)

    auth = subprocess.run(
        ["gcloud", "auth", "application-default", "print-access-token"],
        capture_output=True,
    )
    if auth.returncode != 0:
        console.print("[red]Error: sin credenciales GCP. Ejecuta: gcloud auth application-default login[/red]")
        sys.exit(1)

    for archivo in archivos:
        origen = Path(archivo)
        if origen.suffix != ".md":
            console.print(f"[yellow]Ignorado (no es .md): {origen}[/yellow]")
            continue
        if not origen.exists():
            console.print(f"[red]No existe: {origen}[/red]")
            sys.exit(1)
        destino = DATA_DIR / origen.name
        if origen.resolve() != destino.resolve():
            shutil.copy(origen, destino)
            console.print(f"Copiado a {destino}")

    from src.worker_rag.load import load_directory

    console.print("\n[bold]Indexando documentos de data/...[/bold]")
    load_directory(str(DATA_DIR))

    console.print(f"\n[bold]Sincronizando índice a gs://{bucket}/chroma/...[/bold]")
    sync = subprocess.run(
        ["gsutil", "-m", "rsync", "-r", chroma_path, f"gs://{bucket}/chroma/"],
    )
    if sync.returncode != 0:
        console.print("[red]Error al sincronizar el índice al bucket.[/red]")
        sys.exit(1)

    console.print("\n[green]Documentos cargados e índice sincronizado.[/green]")
    console.print(
        "[dim]Si el agente no ve los documentos nuevos al consultar, fuerza una nueva "
        "revisión del worker: gcloud run services update pmo-ai-worker-rag "
        "--region southamerica-west1[/dim]"
    )


def cmd_stats(base_url: str) -> None:
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/stats", timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.Timeout:
        console.print("[red]Error: el servidor no respondió a tiempo.[/red]")
        sys.exit(1)
    except requests.ConnectionError:
        console.print("[red]Error: no se pudo conectar al endpoint.[/red]")
        sys.exit(1)
    except requests.HTTPError as e:
        console.print(f"[red]Error del servidor: HTTP {e.response.status_code}[/red]")
        sys.exit(1)

    table = Table(title="Estadísticas de trazabilidad (interactions)")
    table.add_column("Métrica", style="bold")
    table.add_column("Valor")

    table.add_row("Total de interacciones", str(data.get("total_interactions", 0)))
    table.add_row("Tokens totales", str(data.get("total_tokens", 0)))
    table.add_row("Tokens promedio", str(data.get("avg_tokens", 0)))
    table.add_row("Latencia promedio", f"{data.get('avg_latency_ms', 0)} ms")
    table.add_row("Latencia mínima", f"{data.get('min_latency_ms', 0)} ms")
    table.add_row("Latencia máxima", f"{data.get('max_latency_ms', 0)} ms")
    table.add_row("Primera interacción", data.get("first_interaction") or "—")
    table.add_row("Última interacción", data.get("last_interaction") or "—")

    console.print(table)


def main() -> None:
    base_url = os.environ.get("PMO_AI_URL", DEFAULT_URL)
    console.print("[bold]PMO-AI CLI[/bold] — consultas al orquestador en lenguaje natural")
    console.print(f"Endpoint: {base_url}")
    console.print("Escribe tu pregunta y presiona Enter. 'salir' o Ctrl+C para terminar.\n")

    while True:
        try:
            query = console.input("[bold green]pmo-ai>[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nHasta luego.")
            sys.exit(0)

        if not query:
            continue
        if query.lower() in ("salir", "exit", "quit"):
            console.print("Hasta luego.")
            sys.exit(0)

        try:
            with console.status("[dim]Consultando...[/dim]", spinner="dots"):
                data = ask(base_url, query)
        except requests.Timeout:
            console.print(f"\n[red]Error: el servidor no respondió en {TIMEOUT}s. Intenta de nuevo.[/red]\n")
            continue
        except requests.ConnectionError:
            console.print("\n[red]Error: no se pudo conectar al endpoint. Verifica tu conexión a internet.[/red]\n")
            continue
        except requests.HTTPError as e:
            console.print(f"\n[red]Error del servidor: HTTP {e.response.status_code}[/red]\n")
            continue

        print_response(data)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cargar":
        cmd_cargar(sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        cmd_stats(os.environ.get("PMO_AI_URL", DEFAULT_URL))
    else:
        main()
