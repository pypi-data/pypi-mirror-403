"""
Fit+Test workflow entry point for cph-imgclassification package.

This script runs both training and testing in sequence,
useful for quick experimentation and validation.
"""

from cph_imgclassification.imageclassification.cli import IMGLightningCLI


def cli_main():
    """
    Main function to run fit+test workflow.
    
    Creates CLI instance without running, then manually calls
    fit and test methods.
    """
    # When run=False, Lightning CLI doesn't require a subcommand
    # We can initialize it directly without modifying sys.argv
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
    cli_main()
