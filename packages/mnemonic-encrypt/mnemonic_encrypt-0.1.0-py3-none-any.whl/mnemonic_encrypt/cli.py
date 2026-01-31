"""
Command-line interface for MnemonicEncrypt.

This module provides an interactive CLI tool for encrypting and decrypting
cryptocurrency mnemonic phrases.
"""

import sys
from getpass import getpass
import click
from .core import MnemonicEncryptor
from .__version__ import __version__


@click.group()
@click.version_option(version=__version__, prog_name="mnemonic-encrypt")
def cli() -> None:
    """
    🔐 MnemonicEncrypt - Secure Mnemonic Encryption Tool
    
    Powered by AnyEncrypt, providing military-grade mnemonic protection.
    """
    pass


@cli.command()
@click.option(
    "--mnemonic",
    "-m",
    help="Mnemonic phrase (not recommended in command line)",
)
@click.option(
    "--password",
    "-p",
    help="Encryption password (not recommended in command line)",
)
def encrypt(mnemonic: str, password: str) -> None:
    """
    Encrypt mnemonic phrase
    
    Encrypt your mnemonic with a strong password. The ciphertext can be safely
    stored in cloud storage, on paper, or in notes.
    """
    encryptor = MnemonicEncryptor()
    
    # Interactive input (more secure)
    if not mnemonic:
        click.echo("📝 Please enter your mnemonic phrase (space-separated):")
        mnemonic = input().strip()
    
    if not mnemonic:
        click.echo("❌ Error: Mnemonic cannot be empty", err=True)
        sys.exit(1)
    
    # Validate mnemonic first
    try:
        if not encryptor.validate_mnemonic(mnemonic):
            click.echo(
                "❌ Error: Invalid mnemonic format\n"
                "   Please ensure you entered a valid BIP39 mnemonic (12/15/18/21/24 words)",
                err=True
            )
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        sys.exit(1)
    
    # Get password
    if not password:
        password = getpass("🔑 Enter encryption password: ")
        password_confirm = getpass("🔑 Confirm password: ")
        
        if password != password_confirm:
            click.echo("❌ Passwords do not match", err=True)
            sys.exit(1)
    
    if len(password) < 8:
        click.echo(
            "⚠️  Warning: Password is less than 8 characters, recommend 16+ characters"
        )
        if not click.confirm("Continue?"):
            sys.exit(0)
    
    # Encrypt
    try:
        ciphertext = encryptor.encrypt(mnemonic, password)
        
        click.echo("\n" + "="*60)
        click.echo("✅ Encryption successful!")
        click.echo("="*60)
        click.echo(f"\nCiphertext:\n")
        click.echo(click.style(ciphertext, fg="green", bold=True))
        click.echo("\n" + "="*60)
        click.echo("💡 Tip:")
        click.echo("   • Save this ciphertext safely (cloud storage or paper)")
        click.echo("   • Remember or store the password separately")
        click.echo("="*60 + "\n")
        
    except Exception as e:
        click.echo(f"\n❌ Encryption failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--ciphertext",
    "-c",
    help="Ciphertext",
)
@click.option(
    "--password",
    "-p",
    help="Decryption password (not recommended in command line)",
)
def decrypt(ciphertext: str, password: str) -> None:
    """
    Decrypt mnemonic phrase
    
    Decrypt an encrypted mnemonic phrase with password.
    """
    encryptor = MnemonicEncryptor()
    
    # Input ciphertext
    if not ciphertext:
        click.echo("📝 Please enter the ciphertext:")
        ciphertext = input().strip()
    
    if not ciphertext:
        click.echo("❌ Error: Ciphertext cannot be empty", err=True)
        sys.exit(1)
    
    # Get password
    if not password:
        password = getpass("🔑 Enter decryption password: ")
    
    # Decrypt
    try:
        plaintext = encryptor.decrypt(ciphertext, password)
        
        click.echo("\n" + "="*60)
        click.echo("✅ Decryption successful!")
        click.echo("="*60)
        click.echo(f"\nMnemonic phrase:\n")
        click.echo(click.style(plaintext, fg="yellow", bold=True))
        click.echo("\n" + "="*60)
        click.echo("⚠️  Warning:")
        click.echo("   • Use immediately and clear screen history")
        click.echo("   • Do not take screenshots or photos")
        click.echo("="*60 + "\n")
        
    except Exception as e:
        click.echo(f"\n❌ Decryption failed: {e}", err=True)
        click.echo("\n💡 Tip:")
        click.echo("   • Please check if the password is correct")
        click.echo("   • Please check if the ciphertext is complete")
        sys.exit(1)


@cli.command()
@click.option(
    "--strength",
    "-s",
    type=click.Choice(["128", "256"]),
    default="128",
    help="Mnemonic strength (128=12 words, 256=24 words)",
)
@click.option(
    "--show-all",
    is_flag=True,
    help="Show all available strengths",
)
def generate(strength: str, show_all: bool) -> None:
    """
    Generate new mnemonic phrase
    
    Generate a new BIP39-compliant mnemonic phrase.
    """
    encryptor = MnemonicEncryptor()
    
    if show_all:
        click.echo("📊 Available mnemonic strengths:\n")
        strengths = [
            (128, 12),
            (160, 15),
            (192, 18),
            (224, 21),
            (256, 24),
        ]
        for bits, words in strengths:
            click.echo(f"   • {bits} bits = {words} words")
        click.echo("\nUse -s or --strength option to specify strength")
        return
    
    strength_int = int(strength)
    word_count = encryptor.get_word_count(strength_int)
    
    try:
        mnemonic = encryptor.generate(strength=strength_int)
        
        click.echo("\n" + "="*60)
        click.echo(f"✅ Generated {word_count}-word mnemonic")
        click.echo("="*60)
        click.echo(f"\nMnemonic phrase:\n")
        click.echo(click.style(mnemonic, fg="cyan", bold=True))
        click.echo("\n" + "="*60)
        click.echo("💡 Recommendation:")
        click.echo("   • Use 'mnemonic-encrypt encrypt' to encrypt and save immediately")
        click.echo("   • Do not screenshot or photograph plaintext mnemonic")
        click.echo("="*60 + "\n")
        
    except Exception as e:
        click.echo(f"❌ Generation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("mnemonic", required=False)
def verify(mnemonic: str) -> None:
    """
    Verify if mnemonic is valid
    
    Check if mnemonic phrase complies with BIP39 standard.
    """
    encryptor = MnemonicEncryptor()
    
    if not mnemonic:
        click.echo("📝 Please enter mnemonic phrase:")
        mnemonic = input().strip()
    
    if not mnemonic:
        click.echo("❌ Error: Mnemonic cannot be empty", err=True)
        sys.exit(1)
    
    is_valid = encryptor.validate_mnemonic(mnemonic)
    word_count = len(mnemonic.split())
    
    if is_valid:
        click.echo(f"\n✅ Valid mnemonic! ({word_count} words)\n")
    else:
        click.echo(f"\n❌ Invalid mnemonic ({word_count} words)")
        click.echo("\n💡 Tip:")
        click.echo("   • BIP39 standard supports 12/15/18/21/24 words")
        click.echo("   • Please check if words are spelled correctly\n")
        sys.exit(1)


if __name__ == "__main__":
    cli()
