"""
Command Line Interface for Chess Post-Game Analyst
"""

import click
import json
import sys
import logging
from pathlib import Path
from colorama import init, Fore, Style
from tqdm import tqdm

from . import PGNParser, GameAnalyzer, __version__
from .classifier import MoveClassifier

# Initialize colorama
init(autoreset=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(level name)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__)
def cli():
    """Chess Post-Game Analyst - Analyze your chess games with Stockfish"""
    pass


@cli.command()
@click.argument('pgn_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'html']), default='text', help='Output format')
@click.option('--depth', '-d', type=int, default=15, help='Stockfish analysis depth')
@click.option('--engine', '-e', type=click.Path(), help='Path to Stockfish engine')
@click.option('--game-number', '-g', type=int, default=0, help='Game number to analyze (0-based)')
@click.option('--threshold', '-t', type=click.Choice(['all', 'inaccuracy', 'mistake', 'blunder']), 
              default='all', help='Minimum threshold for move annotations')
def analyze(pgn_file, output, format, depth, engine, game_number, threshold):
    """Analyze a chess game from a PGN file"""
    
    click.echo(f"{Fore.CYAN}♟️  Chess Post-Game Analyst v{__version__}{Style.RESET_ALL}\n")
    
    try:
        # Load the game
        click.echo(f"Loading game from {Fore.YELLOW}{pgn_file}{Style.RESET_ALL}...")
        parser = PGNParser(pgn_file)
        game = parser.load_game(game_number)
        game_info = parser.get_game_info(game)
        
        click.echo(f"{Fore.GREEN}✓{Style.RESET_ALL} Game loaded: {game_info['white']} vs {game_info['black']}\n")
        
        # Analyze the game
        click.echo("Analyzing game with Stockfish engine...")
        analyzer = GameAnalyzer(engine_path=engine, depth=depth)
        
        # Count moves for progress bar
        move_count = sum(1 for _ in game.mainline())
        
        with tqdm(total=move_count, desc="Analyzing moves", unit="move") as pbar:
            # Monkey patch to update progress
            original_analyze = analyzer.analyze
            
            def analyze_with_progress(g, gi):
                result = original_analyze(g, gi)
                pbar.update(move_count)
                return result
            
            analyzer.analyze = analyze_with_progress
            result = analyzer.analyze(game, game_info)
        
        click.echo(f"\n{Fore.GREEN}✓{Style.RESET_ALL} Analysis complete!\n")
        
        # Output the results
        if format == 'text':
            output_text = format_text_output(result, threshold)
        elif format == 'json':
            output_text = json.dumps(result.to_dict(), indent=2)
        elif format == 'html':
            output_text = format_html_output(result, threshold)
        else:
            output_text = format_text_output(result, threshold)
        
        # Write or print output
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(output_text)
            click.echo(f"{Fore.GREEN}✓{Style.RESET_ALL} Results saved to {Fore.YELLOW}{output}{Style.RESET_ALL}")
        else:
            click.echo(output_text)
            
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {str(e)}{Style.RESET_ALL}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--port', '-p', type=int, default=5000, help='Port to run web server on')
@click.option('--host', '-h', default='127.0.0.1', help='Host to bind to')
@click.option('--debug', is_flag=True, help='Run in debug mode')
def serve(port, host, debug):
    """Start the web interface"""
    click.echo(f"{Fore.CYAN}♟️  Starting Chess Analyst Web Server{Style.RESET_ALL}\n")
    
    try:
        from web.app import app
        click.echo(f"Server running at {Fore.GREEN}http://{host}:{port}{Style.RESET_ALL}")
        click.echo(f"Press {Fore.YELLOW}CTRL+C{Style.RESET_ALL} to quit\n")
        app.run(host=host, port=port, debug=debug)
    except ImportError:
        click.echo(f"{Fore.RED}✗ Web interface dependencies not found{Style.RESET_ALL}", err=True)
        click.echo("Install with: pip install flask flask-cors", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {str(e)}{Style.RESET_ALL}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--engine-path', type=click.Path(), help='Set Stockfish engine path')
@click.option('--show', is_flag=True, help='Show current configuration')
def config(engine_path, show):
    """Configure Chess Analyst settings"""
    config_file = Path.home() / '.chess-analyst-config.json'
    
    if show:
        if config_file.exists():
            with open(config_file, 'r') as f:
                cfg = json.load(f)
            click.echo(f"{Fore.CYAN}Current Configuration:{Style.RESET_ALL}")
            click.echo(json.dumps(cfg, indent=2))
        else:
            click.echo(f"{Fore.YELLOW}No configuration file found{Style.RESET_ALL}")
        return
    
    if engine_path:
        cfg = {}
        if config_file.exists():
            with open(config_file, 'r') as f:
                cfg = json.load(f)
        
        cfg['engine_path'] = str(engine_path)
        
        with open(config_file, 'w') as f:
            json.dump(cfg, f, indent=2)
        
        click.echo(f"{Fore.GREEN}✓{Style.RESET_ALL} Engine path set to: {engine_path}")


def format_text_output(result: 'AnalysisResult', threshold: str) -> str:
    """Format analysis result as text"""
    lines = []
    
    # Header
    lines.append("♟️  Chess Game Analysis Report")
    lines.append("━" * 60)
    lines.append("")
    
    # Game info
    info = result.game_info
    lines.append("Game Information:")
    lines.append(f"  White: {info['white']} ({info['white_elo']})")
    lines.append(f"  Black: {info['black']} ({info['black_elo']})")
    lines.append(f"  Event: {info['event']}")
    lines.append(f"  Result: {info['result']}")
    lines.append("")
    
    # Overall stats
    lines.append("Overall Statistics:")
    lines.append(f"  White Accuracy: {result.white_accuracy:.1f}%")
    lines.append(f"  Black Accuracy: {result.black_accuracy:.1f}%")
    lines.append(f"  Total Moves: {result.total_moves}")
    lines.append("")
    
    # Move breakdown
    lines.append("Move Analysis:")
    ws = result.white_stats
    bs = result.black_stats
    lines.append(f"  ✨ Brilliant Moves: {ws['brilliant'] + bs['brilliant']}")
    lines.append(f"  ✅ Good Moves: {ws['good'] + bs['good']}")
    lines.append(f"  ⚠️  Inaccuracies: {ws['inaccuracies'] + bs['inaccuracies']}")
    lines.append(f"  ❌ Mistakes: {ws['mistakes'] + bs['mistakes']}")
    lines.append(f"  💥 Blunders: {ws['blunders'] + bs['blunders']}")
    lines.append("")
    
    # Critical moments
    if result.critical_moments:
        lines.append("Key Moments:")
        for moment in result.critical_moments:
            symbol = MoveClassifier.get_symbol(moment['classification'])
            lines.append(f"  Move {moment['move_number']}: {moment['player']} {symbol} {moment['classification']}")
            lines.append(f"    Evaluation change: {moment['eval_change']:+.1f}")
            if moment['best_move']:
                lines.append(f"    Best move was: {moment['best_move']}")
        lines.append("")
    
    return "\n".join(lines)


def format_html_output(result: 'AnalysisResult', threshold: str) -> str:
    """Format analysis result as HTML"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Chess Game Analysis</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        .info {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
        .stat-box {{ background: #3498db; color: white; padding: 15px; border-radius: 5px; }}
        .moves {{ margin: 20px 0; }}
        .critical {{ background: #e74c3c; color: white; padding: 10px; margin: 5px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>♟️ Chess Game Analysis</h1>
    <div class="info">
        <h2>Game Information</h2>
        <p><strong>White:</strong> {result.game_info['white']} ({result.game_info['white_elo']})</p>
        <p><strong>Black:</strong> {result.game_info['black']} ({result.game_info['black_elo']})</p>
        <p><strong>Event:</strong> {result.game_info['event']}</p>
        <p><strong>Result:</strong> {result.game_info['result']}</p>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <h3>White Accuracy</h3>
            <h2>{result.white_accuracy:.1f}%</h2>
        </div>
        <div class="stat-box">
            <h3>Black Accuracy</h3>
            <h2>{result.black_accuracy:.1f}%</h2>
        </div>
    </div>
    
    <div class="moves">
        <h2>Move Breakdown</h2>
        <p>✨ Brilliant: {result.white_stats['brilliant'] + result.black_stats['brilliant']}</p>
        <p>✅ Good: {result.white_stats['good'] + result.black_stats['good']}</p>
        <p>⚠️ Inaccuracies: {result.white_stats['inaccuracies'] + result.black_stats['inaccuracies']}</p>
        <p>❌ Mistakes: {result.white_stats['mistakes'] + result.black_stats['mistakes']}</p>
        <p>💥 Blunders: {result.white_stats['blunders'] + result.black_stats['blunders']}</p>
    </div>
</body>
</html>
"""
    return html


def main():
    """Entry point for CLI"""
    cli()


if __name__ == '__main__':
    main()
