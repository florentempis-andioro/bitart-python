import click
import sys
import os
import re
import yaml
from .compute import ComputeContext, EXTENT, MAX_ZOOM
from .util import crunch64
from .parser import EquationParser

DEFAULT_ZOOM = 1

def make_metadata(fn, stats, mode, modulo, depth, problem, zoom):
    fn_desc = f"f(x,y) = {fn}"
    fn_serialized = crunch64(safe_yaml_dump(str(fn))) # Ruby does YAML.dump(fn), here fn string representation is what matters mostly or AST dump
    # Actually Ruby dumps the AST object via YAML. 
    # For now let's dump the string representation as that's what we have easiest access to without custom representers
    
    scale = 1 << zoom
    
    result = {
        'equation': fn_desc,
        'eqn_serialized': fn_serialized,
        'depth': depth,
        'color_mode': mode,
        'modulo': modulo,
        'problem': problem,
        'scale': scale,
        'extent': EXTENT // scale # integer division
    }
    result.update(stats)
    return result

def safe_yaml_dump(obj):
    # Simple wrapper
    return yaml.dump(obj)

@click.command()
@click.option('-o', '--output', 'filename', help="Output filename; defaults to base-64-encoded equation text.")
@click.option('-d', '--depth', type=int, default=4, help="Set equation depth.")
@click.option('-m', '--max-depth', type=int, help="Enable random depth selection to the given maximum.")
@click.option('-i', '--no-meta', is_flag=True, help="Suppress the '<filename>.yaml' description file.")
@click.option('-r', '--run', 'command', help="Execute 'command' followed by the output filename on completion.")
@click.option('-k', '--keep', 'reject_bad', is_flag=True, default=True, help="Keep the first image, regardless of quality (inverted logic to match ruby -k means keep bad, default is reject)")
# Wait, ruby: -k --keep "Keep the first image". default reject_bad=true. If keep is set, reject_bad=false.
# So if flag is present, reject_bad should be False.
# Click flag: default False. If present True. 
# So we want reject_bad to be False if keep is True.
@click.option('-q', '--quiet', is_flag=True, help="Quiet output.")
@click.option('-z', '--zoom', type=click.IntRange(0, MAX_ZOOM), help="Zoom power (default is random)")
def main(filename, depth, max_depth, no_meta, command, reject_bad, quiet, zoom): # reject_bad here is the value of 'keep' flag
    # transform keep flag to reject_bad logic
    # If keep (-k) is set, reject_bad_flag is True. We want logic_reject_bad = False.
    # If keep is not set, reject_bad_flag is False. We want logic_reject_bad = True.
    
    # Wait, the Argument name is reject_bad. 
    # Let's fix the parameter name to be clear.
    # The flag is --keep. 
    pass

@click.command()
@click.option('-o', '--output', 'filename', help="Output filename; defaults to base-64-encoded equation text.")
@click.option('-d', '--depth', type=int, default=4, help="Set equation depth.")
@click.option('-m', '--max-depth', type=int, help="Enable random depth selection to the given maximum.")
@click.option('-i', '--no-meta', is_flag=True, help="Suppress the '<filename>.yaml' description file.")
@click.option('-r', '--run', 'command', help="Execute 'command' followed by the output filename on completion.")
@click.option('-k', '--keep', is_flag=True, help="Keep the first image, regardless of quality.")
@click.option('-q', '--quiet', is_flag=True, help="Quiet output.")
@click.option('-z', '--zoom', type=click.IntRange(0, MAX_ZOOM), help="Zoom power (default is random)")
@click.option('-e', '--equation', help="Custom equation string (e.g. 'x ^ y'). Overrides depth/generator.")
@click.option('-c', '--color', type=click.Choice(['onebit', 'gradient', 'rgb', 'red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'orange', 'grey']), help="Force specific color mode.")
def main(filename, depth, max_depth, no_meta, command, keep, quiet, zoom, equation, color):
    
    def info(msg):
        if not quiet:
            click.echo(msg)
            
    def blabber(msg):
        if not quiet:
            # Ruby had verbosity levels, simple quiet/verbose here
            click.echo(msg)
            
    def errmsg(msg):
        click.echo(f"Error: {msg}", err=True)

    # Logic
    import random
    
    final_depth = depth
    if max_depth:
        # Ruby: [2, rand(opts.max_depth - 1)].max
        # rand(n) returns 0..n-1
        # so rand(max_depth - 1) is 0..(max_depth-2)
        # effectively roughly similar range
        final_depth = max(2, random.randint(0, max_depth - 2))
        info(f"Depth: {final_depth}")

    # Zoom
    # Ruby: zoom = opts.zoom || DEFAULT_ZOOM
    # zoom = rand(MAX_ZOOM + 1) if !opts.zoom && rand() < 0.2
    
    final_zoom = zoom if zoom is not None else DEFAULT_ZOOM
    if zoom is None and random.random() < 0.2:
        final_zoom = random.randint(0, MAX_ZOOM)
        
    info(f"Zoom power: {final_zoom} ({'user set' if zoom is not None else 'random'})")

    reject_bad_logic = not keep

    cc = ComputeContext(depth=final_depth, 
                        attempts=20, 
                        reject_bad=reject_bad_logic,
                        scale_power=final_zoom,
                        color_override=color)

    if equation:
        # Custom equation path
        try:
            parser = EquationParser()
            fn = parser.parse(equation)
            info(f"Custom Equation: {fn}")
            result = cc.render_custom(fn)
        except Exception as err:
            errmsg(f"Failed to parse or render equation: {err}")
            sys.exit(1)
    else:               
        result = cc.compute_and_render()

    if not result or result[0] is None:
        # failed
        errmsg(result[5] if result else "Unknown failure") # result[5] is problem
        sys.exit(1)
        
    image, fn, stats, color_fn, modulo, problem = result
    
    info(f"Function: f(x,y) := {fn}")
    
    if not filename:
        # filename = crunch64( fn.to_s.gsub(/\s/, '') ) + ".png"
        fn_str = str(fn).replace(' ', '')
        filename = crunch64(fn_str) + ".png"
        
    info(f"Saving to {filename}...")
    image.save(filename)
    
    mdname = re.sub(r'\.png$', '.yaml', filename)
    if mdname == filename: mdname += ".yaml" # fallback if extension weird
    
    md = make_metadata(fn, stats, color_fn, modulo, final_depth, problem, final_zoom)
    
    info("Metadata:")
    for k, v in md.items():
        info(f"  {k}: {v}")
        
    if not no_meta:
        info(f"Writing info file {mdname}...")
        with open(mdname, 'w') as f:
            yaml.dump(md, f, default_flow_style=False)
            
    if command:
        os.system(f"{command} {filename}")

if __name__ == '__main__':
    main()
