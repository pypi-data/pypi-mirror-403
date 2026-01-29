"""
CLI entry point for cph-imgclassification package.

This script provides the command-line interface for training image classification models.
- If no subcommand is provided, automatically runs fit + test workflow
- If subcommand (fit/test/validate/predict) is provided, uses standard Lightning CLI
"""

import sys
from cph_imgclassification.imageclassification.cli import IMGLightningCLI


def main():
    """
    Main entry point for the CLI.
    
    Usage:
        # Automatic fit + test (default behavior)
        cph-imgclassification --config config.yaml
        
        # Standard Lightning CLI subcommands
        cph-imgclassification fit --config config.yaml
        cph-imgclassification test --config config.yaml
        cph-imgclassification validate --config config.yaml
        cph-imgclassification predict --config config.yaml
    """
    # Check if subcommand is provided
    if len(sys.argv) > 1 and sys.argv[1] in ['fit', 'test', 'validate', 'predict']:
        # Standard Lightning CLI with subcommand
        cli = IMGLightningCLI()
    else:
        # No subcommand provided - automatically run fit + test workflow
        # Temporarily add 'fit' subcommand to satisfy Lightning CLI parser
        # but we'll use run=False to prevent execution
        original_argv = sys.argv.copy()
        if '--config' in sys.argv:
            # Insert 'fit' as first argument after script name to satisfy parser
            sys.argv.insert(1, 'fit')
        
        try:
            # Create CLI instance without running
            cli = IMGLightningCLI(run=False)
        finally:
            # Restore original argv
            sys.argv = original_argv
        
        # Run training
        # Get ckpt_path from config (can be None for new training)
        fit_config = getattr(cli.config, 'fit', None)
        if fit_config is not None:
            ckpt_path = getattr(fit_config, 'ckpt_path', None)
        else:
            ckpt_path = None
        
        cli.trainer.fit(
            model=cli.model,
            datamodule=cli.datamodule,
            ckpt_path=ckpt_path
        )
        
        # Run testing
        # Get test ckpt_path (defaults to 'best')
        test_config = getattr(cli.config, 'test', None)
        if test_config is not None:
            test_ckpt_path = getattr(test_config, 'ckpt_path', 'best')
        else:
            test_ckpt_path = 'best'
        
        cli.trainer.test(
            datamodule=cli.datamodule,
            ckpt_path=test_ckpt_path
        )


if __name__ == "__main__":
    main()
