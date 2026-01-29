#!/usr/bin/env python3
"""
NanoPy Dual - CLI for Hashcat GPU Cracker with Learning AI Loop

Commands:
  serve      - Start web server
  crack      - Crack a hash using loop mode
  learn      - Learn patterns from passwords
  generate   - Generate passwords
  patterns   - List learned patterns
  status     - Show status
  hashcat    - Hashcat utilities
"""
import os
import sys
import time
import click
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

console = Console()


@click.group()
@click.option("--data-dir", default=None, help="Data directory for storage")
@click.pass_context
def cli(ctx, data_dir):
    """NanoPy Dual - Hashcat GPU Cracker with Learning AI"""
    ctx.ensure_object(dict)
    ctx.obj["data_dir"] = data_dir


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=8888, help="Port to bind")
@click.pass_context
def serve(ctx, host, port):
    """Start the web server"""
    from .server import run_server
    console.print(f"[green]Starting NanoPy Dual on http://{host}:{port}[/green]")
    run_server(host, port, ctx.obj["data_dir"])


@cli.command()
@click.argument("target_hash")
@click.option("--type", "hash_type", default="sha256", help="Hash type (md5, sha1, sha256, sha512)")
@click.option("--length", default=8, help="Password length to target")
@click.option("--timeout", default=0, help="Max time in seconds (0 = infinite)")
@click.pass_context
def crack(ctx, target_hash, hash_type, length, timeout):
    """Crack a hash using the infinite loop mode"""
    from .loop_cracker import get_cracker
    from .storage import get_storage

    storage = get_storage(ctx.obj["data_dir"])
    cracker = get_cracker(ctx.obj["data_dir"])

    # Check if already cracked
    existing = storage.get_cracked(target_hash)
    if existing:
        console.print(f"[green]Already cracked![/green] Password: [bold]{existing}[/bold]")
        return

    console.print(f"[yellow]Target:[/yellow] {target_hash[:32]}...")
    console.print(f"[yellow]Type:[/yellow] {hash_type}")
    console.print(f"[yellow]Length:[/yellow] {length}")
    console.print()
    console.print("[cyan]Starting infinite loop cracker...[/cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    console.print()

    cracker.start(target_hash, hash_type, length)
    start_time = time.time()

    try:
        with Live(console=console, refresh_per_second=2) as live:
            while cracker.is_running():
                stats = cracker.get_stats()
                elapsed = time.time() - start_time

                if timeout > 0 and elapsed > timeout:
                    cracker.stop()
                    console.print("[yellow]Timeout reached[/yellow]")
                    break

                # Build status display
                table = Table(title="Loop Cracker Status", show_header=False)
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="white")

                table.add_row("Phase", f"[bold]{stats['phase'].upper()}[/bold]")
                table.add_row("Loop #", str(stats["loop_count"]))
                table.add_row("Passwords Generated", str(stats["passwords_generated"]))
                table.add_row("Patterns Learned", str(stats["patterns_learned"]))
                table.add_row("Masks Tried", str(stats["patterns_tried"]))
                table.add_row("Current Masks", str(stats["masks_current"]))
                table.add_row("Time", f"{int(elapsed)}s")

                if stats["result"]:
                    table.add_row("RESULT", f"[green bold]{stats['result']}[/green bold]")

                live.update(table)
                time.sleep(0.5)

        # Final result
        stats = cracker.get_stats()
        if stats["result"]:
            console.print()
            console.print(Panel(
                f"[green bold]PASSWORD FOUND: {stats['result']}[/green bold]",
                title="SUCCESS"
            ))
        else:
            console.print()
            console.print("[yellow]Not cracked (stopped or timeout)[/yellow]")

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Stopping...[/yellow]")
        cracker.stop()


@cli.command()
@click.argument("passwords", nargs=-1)
@click.option("--file", "filepath", help="File with passwords (one per line)")
@click.pass_context
def learn(ctx, passwords, filepath):
    """Learn patterns from passwords"""
    from .learning_ai import get_ai

    ai = get_ai(ctx.obj["data_dir"])
    count = 0

    if filepath and os.path.exists(filepath):
        with open(filepath) as f:
            for line in f:
                pwd = line.strip()
                if pwd:
                    ai.learn(pwd)
                    count += 1

    for pwd in passwords:
        ai.learn(pwd)
        count += 1

    console.print(f"[green]Learned from {count} passwords[/green]")
    console.print(f"Total patterns: {len(ai.patterns)}")


@cli.command()
@click.option("--count", default=10, help="Number of passwords to generate")
@click.option("--length", default=8, help="Password length")
@click.option("--method", default="auto", help="Method: random, pattern, weighted, markov, genetic, auto")
@click.pass_context
def generate(ctx, count, length, method):
    """Generate passwords using AI"""
    from .learning_ai import get_ai

    ai = get_ai(ctx.obj["data_dir"])
    passwords = ai.generate_batch(count, length, method)

    for pwd in passwords:
        pattern = ai.get_pattern(pwd)
        console.print(f"[white]{pwd}[/white]  [dim]{pattern}[/dim]")


@cli.command()
@click.option("--limit", default=50, help="Number of patterns to show")
@click.option("--length", default=None, type=int, help="Filter by length")
@click.pass_context
def patterns(ctx, limit, length):
    """List learned patterns"""
    from .storage import get_storage

    storage = get_storage(ctx.obj["data_dir"])
    all_patterns = storage.get_patterns(limit=limit)

    if length:
        all_patterns = [p for p in all_patterns if p["length"] == length]

    table = Table(title="Learned Patterns")
    table.add_column("#", style="dim")
    table.add_column("Pattern", style="cyan")
    table.add_column("Mask", style="green")
    table.add_column("Count", style="yellow")
    table.add_column("Length", style="dim")

    for i, p in enumerate(all_patterns, 1):
        table.add_row(
            str(i),
            p["pattern"],
            p["mask"],
            str(p["count"]),
            str(p["length"])
        )

    console.print(table)
    console.print(f"Total: {storage.get_pattern_count()} patterns")


@cli.command()
@click.pass_context
def status(ctx):
    """Show overall status"""
    from .storage import get_storage
    from .learning_ai import get_ai
    from .hashcat import get_hashcat
    from .loop_cracker import get_cracker

    storage = get_storage(ctx.obj["data_dir"])
    ai = get_ai(ctx.obj["data_dir"])
    hashcat = get_hashcat()
    cracker = get_cracker(ctx.obj["data_dir"])

    storage_stats = storage.get_stats()
    ai_stats = ai.get_stats()
    loop_stats = cracker.get_stats()

    console.print(Panel("[bold]NanoPy Dual Status[/bold]"))

    # Storage
    table = Table(title="Storage", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Patterns", str(storage_stats["patterns"]))
    table.add_row("Cracked", str(storage_stats["cracked"]))
    table.add_row("LevelDB", "✓" if storage_stats["leveldb"] else "✗")
    console.print(table)

    # AI
    table = Table(title="Learning AI", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Total Learned", str(ai_stats["total_learned"]))
    table.add_row("Unique Patterns", str(ai_stats["unique_patterns"]))
    table.add_row("Generation", str(ai_stats["generation"]))
    console.print(table)

    # Hashcat
    table = Table(title="Hashcat", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Available", "✓" if hashcat.is_available() else "✗")
    table.add_row("Version", hashcat.get_version() or "N/A")
    console.print(table)

    # Loop
    if loop_stats["running"]:
        table = Table(title="Loop Cracker (RUNNING)", show_header=False)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Phase", loop_stats["phase"])
        table.add_row("Loop #", str(loop_stats["loop_count"]))
        table.add_row("Target", loop_stats["target_hash"])
        console.print(table)


@cli.group()
def hashcat():
    """Hashcat utilities"""
    pass


@hashcat.command("check")
def hashcat_check():
    """Check if hashcat is available"""
    from .hashcat import get_hashcat

    hc = get_hashcat()
    if hc.is_available():
        console.print(f"[green]✓ Hashcat available[/green]")
        console.print(f"Version: {hc.get_version()}")
    else:
        console.print("[red]✗ Hashcat not found[/red]")
        console.print("Install hashcat: https://hashcat.net/hashcat/")


@hashcat.command("hash")
@click.argument("password")
@click.option("--type", "hash_type", default="sha256", help="Hash type")
def hashcat_hash(password, hash_type):
    """Generate hash from password"""
    from .hashcat import get_hashcat, HashType

    hc = get_hashcat()
    types = {"md5": HashType.MD5, "sha1": HashType.SHA1,
             "sha256": HashType.SHA256, "sha512": HashType.SHA512}
    ht = types.get(hash_type.lower(), HashType.SHA256)

    hash_val = hc.hash_string(password, ht)
    console.print(f"Password: [bold]{password}[/bold]")
    console.print(f"Type: {hash_type}")
    console.print(f"Hash: [green]{hash_val}[/green]")


@cli.command()
@click.option("--limit", default=20, help="Number to show")
@click.pass_context
def cracked(ctx, limit):
    """List cracked passwords"""
    from .storage import get_storage

    storage = get_storage(ctx.obj["data_dir"])
    items = storage.get_cracked_list(limit=limit)

    if not items:
        console.print("[yellow]No cracked passwords yet[/yellow]")
        return

    table = Table(title="Cracked Passwords")
    table.add_column("Hash", style="dim", max_width=20)
    table.add_column("Password", style="green bold")
    table.add_column("Type", style="cyan")
    table.add_column("Pattern", style="yellow")
    table.add_column("Method", style="dim")

    for item in items:
        table.add_row(
            item["hash"][:16] + "...",
            item["password"],
            item["hash_type"],
            item["pattern"] or "",
            item["method"]
        )

    console.print(table)


if __name__ == "__main__":
    cli()
