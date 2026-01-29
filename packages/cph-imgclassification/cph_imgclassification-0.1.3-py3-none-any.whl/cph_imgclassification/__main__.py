"""
CLI entry point for cph-imgclassification package.

This script provides the command-line interface for training image classification models.
- If no subcommand is provided, automatically runs fit + test workflow
- If subcommand (fit/test/validate/predict) is provided, uses standard Lightning CLI
"""

import sys
# Don't import Lightning CLI at module level - import it inside main() after modifying sys.argv


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
    # Check if first argument is a subcommand
    # We need to check BEFORE any Lightning CLI parsing happens
    has_subcommand = False
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        if first_arg in ['fit', 'test', 'validate', 'predict']:
            has_subcommand = True
    
    if has_subcommand:
        # Standard Lightning CLI with subcommand
        from cph_imgclassification.imageclassification.cli import IMGLightningCLI
        cli = IMGLightningCLI()
    else:
        # No subcommand provided - automatically run fit + test workflow
        # When run=False, Lightning CLI doesn't require a subcommand
        # We can initialize it directly without modifying sys.argv
        from cph_imgclassification.imageclassification.cli import IMGLightningCLI
        
        # Create CLI instance without running
        # This will instantiate model, datamodule, and trainer from config
        cli = IMGLightningCLI(run=False)
        
        # Ensure datamodule is set up for training
        # Lightning will call this automatically in fit(), but we ensure it's ready
        if not hasattr(cli.datamodule, 'train_dataloader'):
            cli.datamodule.setup('fit')
        
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
        
        # Ensure datamodule is set up for testing
        cli.datamodule.setup('test')
        
        cli.trainer.test(
            model=cli.model,
            datamodule=cli.datamodule,
            ckpt_path=test_ckpt_path
        )


if __name__ == "__main__":
    main()
