"""
CLI entry point for cph-imgclassification package.

This script provides the command-line interface for training image classification models.
"""

from cph_imgclassification.imageclassification.cli import IMGLightningCLI


def main():
    """Main entry point for the CLI."""
    cli = IMGLightningCLI()


if __name__ == "__main__":
    main()
