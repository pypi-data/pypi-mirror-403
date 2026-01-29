"""
Command-line interface for gym_wm.

This module provides a rich CLI using Typer for dataset collection,
visualization, and management.

Usage:
    gym-wm collect PointMaze_UMaze-v3 --episodes 100
    gym-wm visualize pointmaze/random-v0
    gym-wm list-envs
    gym-wm list-datasets
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Initialize app and console
app = typer.Typer(
    name="gym-wm",
    help="🎮 Generate and manage offline RL datasets for world-model research",
    rich_markup_mode="rich",
    add_completion=False,
)
console = Console()


def _setup_logging(verbose: bool = False) -> None:
    """Configure loguru logger."""
    import sys

    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=level,
        colorize=True,
    )


@app.command("collect")
def collect(
    env_id: Annotated[str, typer.Argument(help="Gymnasium environment ID")],
    episodes: Annotated[int, typer.Option("--episodes", "-n", help="Number of episodes")] = 100,
    name: Annotated[
        Optional[str], typer.Option("--name", help="Dataset name (auto-generated if not set)")
    ] = None,
    img_size: Annotated[int, typer.Option("--img-size", help="RGB image size (HxW)")] = 84,
    output: Annotated[
        Optional[Path], typer.Option("--output", "-o", help="Output directory")
    ] = None,
    seed: Annotated[Optional[int], typer.Option("--seed", help="Random seed")] = None,
    policy: Annotated[
        str, typer.Option("--policy", help="Policy type: random, pd")
    ] = "random",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
) -> None:
    """🎯 Collect an offline dataset from a Gymnasium environment.

    Examples:
        gym-wm collect PointMaze_UMaze-v3 --episodes 100
        gym-wm collect FetchReach-v4 -n 50 --policy pd --seed 42
        gym-wm collect Ant-v5 --img-size 128 --output ./my_datasets
    """
    _setup_logging(verbose)

    from gym_wm.core.generator import collect_dataset
    from gym_wm.core.policies import create_pd_policy, random_policy

    # Select policy
    if policy == "pd":
        policy_fn = create_pd_policy()
        policy_name = "PD Controller"
    else:
        policy_fn = random_policy
        policy_name = "Random"

    console.print(
        Panel.fit(
            f"[bold cyan]Dataset Collection[/bold cyan]\n\n"
            f"Environment: [green]{env_id}[/green]\n"
            f"Episodes: [yellow]{episodes}[/yellow]\n"
            f"Policy: [magenta]{policy_name}[/magenta]\n"
            f"Image Size: [blue]{img_size}x{img_size}[/blue]",
            title="🎮 gym-wm",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Collecting dataset...", total=None)

        try:
            dataset = collect_dataset(
                env_id=env_id,
                num_episodes=episodes,
                dataset_name=name,
                img_height=img_size,
                img_width=img_size,
                data_path=output,
                policy=policy_fn,
                seed=seed,
            )
            progress.update(task, completed=100, total=100)

            console.print(
                Panel.fit(
                    f"[bold green]✓ Dataset Created Successfully![/bold green]\n\n"
                    f"Dataset ID: [cyan]{dataset.spec.dataset_id}[/cyan]\n"
                    f"Episodes: [yellow]{dataset.total_episodes}[/yellow]\n"
                    f"Total Steps: [blue]{dataset.total_steps}[/blue]",
                    title="Success",
                    border_style="green",
                )
            )
        except Exception as e:
            progress.stop()
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(1)


@app.command("visualize")
def visualize(
    dataset_name: Annotated[str, typer.Argument(help="Dataset name to visualize")],
    episode: Annotated[int, typer.Option("--episode", "-e", help="Episode index")] = 0,
    output: Annotated[
        Optional[Path], typer.Option("--output", "-o", help="Output directory for figures")
    ] = None,
    save_video: Annotated[
        bool, typer.Option("--save-video", help="Save episode as video")
    ] = False,
    summary: Annotated[
        bool, typer.Option("--summary", help="Show dataset summary")
    ] = False,
    data_path: Annotated[
        Optional[Path], typer.Option("--data-path", help="Path to datasets directory")
    ] = None,
    no_show: Annotated[bool, typer.Option("--no-show", help="Don't display plots")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
) -> None:
    """📊 Visualize a collected dataset.

    Examples:
        gym-wm visualize pointmaze/random-v0
        gym-wm visualize pointmaze/random-v0 --episode 5 --save-video
        gym-wm visualize pointmaze/random-v0 --summary
    """
    _setup_logging(verbose)

    import matplotlib.pyplot as plt

    from gym_wm.core.visualize import (
        create_episode_video,
        load_dataset,
        plot_dataset_summary,
        plot_episode_frames,
        plot_episode_trajectory,
    )

    console.print(f"[bold cyan]Loading dataset:[/bold cyan] {dataset_name}")

    try:
        dataset = load_dataset(dataset_name, data_path)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    # Display dataset info
    table = Table(title="Dataset Info")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Dataset ID", dataset.spec.dataset_id)
    table.add_row("Episodes", str(dataset.total_episodes))
    table.add_row("Total Steps", str(dataset.total_steps))
    console.print(table)

    output_dir = Path(output) if output else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    if summary:
        console.print("[bold]Generating summary...[/bold]")
        fig = plot_dataset_summary(dataset)
        if output_dir:
            fig.savefig(output_dir / "summary.png", dpi=200, bbox_inches="tight")
            console.print(f"[green]Saved:[/green] {output_dir / 'summary.png'}")
    else:
        console.print(f"[bold]Visualizing episode {episode}...[/bold]")

        # Plot episode frames
        fig1 = plot_episode_frames(dataset, episode)
        if output_dir:
            fig1.savefig(output_dir / f"episode{episode}_frames.png", dpi=200, bbox_inches="tight")
            console.print(f"[green]Saved:[/green] {output_dir / f'episode{episode}_frames.png'}")

        # Plot trajectory
        fig2 = plot_episode_trajectory(dataset, episode)
        if output_dir:
            fig2.savefig(
                output_dir / f"episode{episode}_trajectory.png", dpi=200, bbox_inches="tight"
            )
            console.print(
                f"[green]Saved:[/green] {output_dir / f'episode{episode}_trajectory.png'}"
            )

    if save_video:
        video_path = output_dir / f"episode{episode}.mp4" if output_dir else None
        create_episode_video(dataset, episode, video_path)
        console.print(f"[green]Saved video:[/green] {video_path or 'episode.mp4'}")

    if not no_show:
        plt.show()


@app.command("list-envs")
def list_envs() -> None:
    """🌍 List supported environment families and examples."""
    from gym_wm.core.environments import get_supported_env_families

    families = get_supported_env_families()

    console.print(
        Panel.fit(
            "[bold cyan]Supported Environment Families[/bold cyan]",
            title="🎮 gym-wm",
        )
    )

    for family, envs in families.items():
        table = Table(title=f"[bold]{family.upper()}[/bold]", show_header=False, box=None)
        table.add_column("Environment", style="green")

        for env in envs:
            table.add_row(f"  • {env}")

        console.print(table)
        console.print()


@app.command("list-datasets")
def list_datasets_cmd(
    data_path: Annotated[
        Optional[Path], typer.Option("--data-path", "-d", help="Path to datasets directory")
    ] = None,
) -> None:
    """📁 List available local datasets."""
    from gym_wm.core.visualize import list_datasets

    datasets = list_datasets(data_path)

    if not datasets:
        console.print("[yellow]No datasets found.[/yellow]")
        console.print(
            "Use [cyan]gym-wm collect <env_id>[/cyan] to create a dataset."
        )
        return

    table = Table(title="[bold]Available Datasets[/bold]")
    table.add_column("#", style="dim")
    table.add_column("Dataset Name", style="cyan")

    for i, ds in enumerate(datasets, 1):
        table.add_row(str(i), ds)

    console.print(table)


@app.command("inspect")
def inspect(
    dataset_name: Annotated[str, typer.Argument(help="Dataset name to inspect")],
    data_path: Annotated[
        Optional[Path], typer.Option("--data-path", "-d", help="Path to datasets directory")
    ] = None,
) -> None:
    """🔍 Inspect a dataset and show detailed information."""
    from gym_wm.utils.inspect import inspect_dataset

    try:
        info = inspect_dataset(dataset_name, data_path)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    table = Table(title=f"[bold]Dataset: {info['dataset_id']}[/bold]")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Episodes", str(info["total_episodes"]))
    table.add_row("Total Steps", str(info["total_steps"]))
    table.add_row("Observation Keys", ", ".join(info["observation_keys"]))
    table.add_row("Has Images", "✓" if info["has_images"] else "✗")

    if info.get("has_images"):
        table.add_row("Image Shape", str(info.get("image_shape")))
        table.add_row("Image Dtype", str(info.get("image_dtype")))
        table.add_row("Frames (Episode 0)", str(info.get("num_frames_episode_0")))

    console.print(table)


@app.command("compare")
def compare(
    datasets: Annotated[
        list[str], typer.Argument(help="Dataset names to compare")
    ],
    data_path: Annotated[
        Optional[Path], typer.Option("--data-path", "-d", help="Path to datasets directory")
    ] = None,
    output: Annotated[
        Optional[Path], typer.Option("--output", "-o", help="Output path for figure")
    ] = None,
    no_show: Annotated[bool, typer.Option("--no-show", help="Don't display plot")] = False,
) -> None:
    """📈 Compare multiple datasets side by side.

    Examples:
        gym-wm compare pointmaze/random-v0 pointmaze/pd-v0
    """
    import matplotlib.pyplot as plt

    from gym_wm.core.visualize import visualize_comparison

    console.print(f"[bold cyan]Comparing {len(datasets)} datasets...[/bold cyan]")

    try:
        fig = visualize_comparison(datasets, data_path, save_path=output)
        if output:
            console.print(f"[green]Saved comparison to:[/green] {output}")
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    if not no_show:
        plt.show()


@app.command("version")
def version() -> None:
    """📦 Show version information."""
    from gym_wm import __version__

    console.print(
        Panel.fit(
            f"[bold cyan]gym-wm[/bold cyan] version [green]{__version__}[/green]\n\n"
            f"A toolbox for generating offline RL datasets\n"
            f"for world-model research using Gymnasium & Minari.",
            title="📦 Version",
        )
    )


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
