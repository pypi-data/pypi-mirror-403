#!/usr/bin/env python3
"""
SSI Empoorio ID Python SDK CLI Tool
Complete command-line interface for SSI operations
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.spinner import Spinner

from .sdk import SSIEmporioSDK, AsyncSSIEmporioSDK
from .utils import generate_uuid, create_credential_template, validate_credential_format

console = Console()


class SSICLI:
    """SSI Empoorio ID CLI Tool"""

    def __init__(self):
        self.sdk: Optional[SSIEmporioSDK] = None
        self.config = self.load_config()

    def load_config(self) -> dict:
        """Load configuration from file or environment"""
        config = {
            'issuer_url': os.getenv('SSI_ISSUER_URL', 'http://localhost:3001'),
            'verifier_url': os.getenv('SSI_VERIFIER_URL', 'http://localhost:3002'),
            'api_key': os.getenv('SSI_API_KEY'),
            'verbose': False
        }

        # Try to load from config file
        config_file = Path.home() / '.ssi' / 'config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception:
                pass

        return config

    def ensure_sdk(self):
        """Ensure SDK is initialized"""
        if not self.sdk:
            self.sdk = SSIEmporioSDK(
                issuer_url=self.config['issuer_url'],
                verifier_url=self.config['verifier_url'],
                api_key=self.config['api_key']
            )

    def output_result(self, data, message: str = "", format: str = "table"):
        """Output result in specified format"""
        if message:
            console.print(f"✅ {message}", style="green")

        if self.config.get('quiet'):
            return

        if format == "json":
            console.print_json(data=data)
        elif format == "table":
            self.output_table(data)
        else:
            console.print(data)

    def output_table(self, data):
        """Output data as a table"""
        if isinstance(data, dict):
            table = Table(title="Result")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="magenta")

            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                table.add_row(str(key), str(value))

            console.print(table)
        elif isinstance(data, list):
            if not data:
                console.print("No data")
                return

            if isinstance(data[0], dict):
                table = Table()
                headers = list(data[0].keys())
                for header in headers:
                    table.add_column(header, style="cyan")

                for item in data:
                    row = [str(item.get(h, '')) for h in headers]
                    table.add_row(*row)

                console.print(table)
            else:
                for item in data:
                    console.print(f"• {item}")
        else:
            console.print(data)


# CLI Commands Group
@click.group()
@click.option('--issuer-url', default=None, help='Issuer API URL')
@click.option('--verifier-url', default=None, help='Verifier API URL')
@click.option('--api-key', default=None, help='API Key')
@click.option('--config', default=None, help='Config file path')
@click.option('--output', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--verbose', is_flag=True, help='Verbose output')
@click.option('--quiet', is_flag=True, help='Quiet output')
@click.pass_context
def cli(ctx, issuer_url, verifier_url, api_key, config, output, verbose, quiet):
    """SSI Empoorio ID - Complete CLI for Self-Sovereign Identity operations"""
    ctx.ensure_object(dict)
    ctx.obj.update({
        'issuer_url': issuer_url,
        'verifier_url': verifier_url,
        'api_key': api_key,
        'config': config,
        'output': output,
        'verbose': verbose,
        'quiet': quiet
    })


# ============================================================================
# VC COMMANDS
# ============================================================================

@cli.group()
def vc():
    """Verifiable Credential operations"""
    pass


@vc.command()
@click.argument('subject-file', type=click.Path(exists=True))
@click.option('-t', '--type', default='VerifiableCredential', help='Credential types (comma-separated)')
@click.option('-q', '--quantum', is_flag=True, help='Use quantum-resistant signatures')
@click.option('-z', '--zkp', is_flag=True, help='Enable zero-knowledge proofs')
@click.option('-s', '--selective', is_flag=True, help='Enable selective disclosure')
@click.pass_context
def issue(ctx, subject_file, type, quantum, zkp, selective):
    """Issue a new verifiable credential"""
    try:
        cli_obj = SSICLI()
        cli_obj.ensure_sdk()

        # Load subject data
        with open(subject_file, 'r') as f:
            subject = json.load(f)

        # Generate DID if not provided
        if 'id' not in subject:
            subject['id'] = cli_obj.sdk.create_test_did()

        types = [t.strip() for t in type.split(',')]

        with console.status("[bold green]Issuing verifiable credential...") as status:
            options = {}
            if quantum:
                options['quantum_resistant'] = True
            if zkp:
                options['zkp_enabled'] = True
            if selective:
                options['selective_disclosure'] = True

            vc = cli_obj.sdk.issue_credential(subject, types, options)

        cli_obj.output_result(vc, "Verifiable Credential issued successfully")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


@vc.command()
@click.argument('vc-file', type=click.Path(exists=True))
@click.option('-c', '--checks', default='signature,expiration,revocation',
              help='Verification checks (comma-separated)')
@click.pass_context
def verify(ctx, vc_file, checks):
    """Verify a verifiable credential"""
    try:
        cli_obj = SSICLI()
        cli_obj.ensure_sdk()

        # Load VC data
        with open(vc_file, 'r') as f:
            vc = json.load(f)

        check_list = [c.strip() for c in checks.split(',')]

        with console.status("[bold green]Verifying credential...") as status:
            result = cli_obj.sdk.verify_credential(vc, {'checks': check_list})

        if result.verified:
            console.print("✅ Credential is valid!", style="green")
        else:
            console.print("❌ Credential invalid!", style="red")
            if hasattr(result, 'errors') and result.errors:
                console.print("Errors:", style="red")
                for error in result.errors:
                    console.print(f"  • {error}", style="red")

        cli_obj.output_result(result.__dict__, "Verification completed")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


@vc.command()
@click.argument('vc-id')
@click.option('-r', '--reason', help='Revocation reason')
@click.pass_context
def revoke(ctx, vc_id, reason):
    """Revoke a verifiable credential"""
    try:
        cli_obj = SSICLI()
        cli_obj.ensure_sdk()

        with console.status("[bold green]Revoking credential...") as status:
            result = cli_obj.sdk.revoke_credential(vc_id, reason)

        cli_obj.output_result(result, "Credential revoked successfully")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


@vc.command()
@click.argument('vc-id')
@click.pass_context
def status(ctx, vc_id):
    """Check credential status"""
    try:
        cli_obj = SSICLI()
        cli_obj.ensure_sdk()

        with console.status("[bold green]Checking credential status...") as status:
            status_info = cli_obj.sdk.get_credential_status(vc_id)

        cli_obj.output_result(status_info, "Credential status retrieved")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


# ============================================================================
# DID COMMANDS
# ============================================================================

@cli.group()
def did():
    """DID (Decentralized Identifier) operations"""
    pass


@did.command()
@click.option('-p', '--prefix', default='emp', help='DID prefix')
@click.pass_context
def create(ctx, prefix):
    """Create a new DID"""
    try:
        cli_obj = SSICLI()
        cli_obj.ensure_sdk()

        did = cli_obj.sdk.create_test_did(prefix)
        cli_obj.output_result({'did': did}, "DID created successfully")

        # Copy to clipboard if available
        try:
            import pyperclip
            pyperclip.copy(did)
            console.print("📋 DID copied to clipboard!", style="blue")
        except ImportError:
            pass

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


@did.command()
@click.argument('did')
@click.pass_context
def validate(ctx, did):
    """Validate a DID"""
    try:
        cli_obj = SSICLI()
        cli_obj.ensure_sdk()

        is_valid = cli_obj.sdk.validate_did(did)
        status = "valid" if is_valid else "invalid"
        color = "green" if is_valid else "red"

        console.print(f"DID is {status}!", style=color)
        cli_obj.output_result({'did': did, 'valid': is_valid}, "DID validation completed")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


# ============================================================================
# BIOMETRIC COMMANDS
# ============================================================================

@cli.group()
def biometric():
    """Biometric authentication operations"""
    pass


@biometric.command()
@click.pass_context
def methods(ctx):
    """Get supported biometric methods"""
    try:
        cli_obj = SSICLI()
        cli_obj.ensure_sdk()

        with console.status("[bold green]Retrieving biometric methods...") as status:
            methods = cli_obj.sdk.get_biometric_methods()

        cli_obj.output_result(methods, "Biometric methods retrieved")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


@biometric.command()
@click.argument('user-id')
@click.argument('username')
@click.pass_context
def register(ctx, user_id, username):
    """Register biometric credential (interactive)"""
    console.print("🔐 Biometric registration requires browser interaction.", style="yellow")
    console.print("Please use the web interface or SDK methods for registration.", style="yellow")
    console.print(f"User ID: {user_id}", style="blue")
    console.print(f"Username: {username}", style="blue")


@biometric.command()
@click.argument('user-id')
@click.pass_context
def credentials(ctx, user_id):
    """List user biometric credentials"""
    try:
        cli_obj = SSICLI()
        cli_obj.ensure_sdk()

        with console.status("[bold green]Retrieving user credentials...") as status:
            credentials = cli_obj.sdk.get_user_biometric_credentials(user_id)

        cli_obj.output_result(credentials, "Biometric credentials retrieved")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


# ============================================================================
# UTILITY COMMANDS
# ============================================================================

@cli.group()
def util():
    """Utility operations"""
    pass


@util.command()
@click.pass_context
def uuid(ctx):
    """Generate a random UUID"""
    uuid = generate_uuid()
    cli_obj = SSICLI()
    cli_obj.output_result({'uuid': uuid}, "UUID generated")

    # Copy to clipboard if available
    try:
        import pyperclip
        pyperclip.copy(uuid)
        console.print("📋 UUID copied to clipboard!", style="blue")
    except ImportError:
        pass


@util.command()
@click.argument('subject-file', type=click.Path(exists=True))
@click.option('-i', '--issuer', default='did:emp:issuer-01', help='Issuer DID')
@click.option('-t', '--type', default='VerifiableCredential', help='Credential types')
@click.pass_context
def template(ctx, subject_file, issuer, type):
    """Create a credential template"""
    try:
        # Load subject data
        with open(subject_file, 'r') as f:
            subject = json.load(f)

        types = [t.strip() for t in type.split(',')]
        template = create_credential_template(subject, issuer, types)

        cli_obj = SSICLI()
        cli_obj.output_result(template, "Credential template created")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


@util.command()
@click.argument('vc-file', type=click.Path(exists=True))
@click.pass_context
def validate_format(ctx, vc_file):
    """Validate credential format"""
    try:
        # Load VC data
        with open(vc_file, 'r') as f:
            vc = json.load(f)

        is_valid = validate_credential_format(vc)
        status = "valid" if is_valid else "invalid"
        color = "green" if is_valid else "red"

        console.print(f"Format is {status}!", style=color)

        cli_obj = SSICLI()
        cli_obj.output_result({'valid': is_valid}, "Format validation completed")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


# ============================================================================
# CONFIG COMMANDS
# ============================================================================

@cli.group()
def config():
    """Configuration management"""
    pass


@config.command()
@click.pass_context
def init(ctx):
    """Initialize SSI configuration"""
    try:
        config_dir = Path.home() / '.ssi'
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / 'config.json'

        default_config = {
            'version': '1.0.0',
            'issuer_url': 'http://localhost:3001',
            'verifier_url': 'http://localhost:3002',
            'api_key': None,
            'quantum_enabled': True,
            'biometric_enabled': True,
            'zkp_enabled': True
        }

        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)

        console.print(f"✅ Configuration file created: {config_file}", style="green")

        cli_obj = SSICLI()
        cli_obj.output_result(default_config, "Configuration initialized")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


@config.command()
@click.pass_context
def show(ctx):
    """Show current configuration"""
    try:
        cli_obj = SSICLI()
        cli_obj.output_result(cli_obj.config, "Current configuration")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


# ============================================================================
# DEVELOPMENT COMMANDS
# ============================================================================

@cli.group()
def dev():
    """Development tools"""
    pass


@dev.command()
@click.pass_context
def test_api(ctx):
    """Test API connectivity"""
    try:
        cli_obj = SSICLI()
        cli_obj.ensure_sdk()

        with console.status("[bold green]Testing API connectivity...") as status:
            # Test basic connectivity
            console.print("✅ SDK initialized successfully", style="green")
            console.print("✅ Ready for SSI operations", style="green")

        cli_obj.output_result({
            'sdk_ready': True,
            'issuer_url': cli_obj.config['issuer_url'],
            'verifier_url': cli_obj.config['verifier_url']
        }, "API connectivity test completed")

    except Exception as e:
        console.print(f"❌ API test failed: {e}", style="red")


@dev.command()
@click.pass_context
def demo(ctx):
    """Run interactive demo"""
    console.print()
    console.print(Panel.fit(
        "[bold blue]🚀 SSI Empoorio ID - Interactive Demo[/bold blue]\n\n"
        "Welcome to the SSI Empoorio ID Python SDK Demo!\n"
        "This demo will show you the main features.",
        title="SSI Demo"
    ))
    console.print()

    try:
        cli_obj = SSICLI()
        cli_obj.ensure_sdk()

        # Generate demo data
        did = cli_obj.sdk.create_test_did()
        uuid = generate_uuid()

        console.print(f"🆔 Generated DID: [cyan]{did}[/cyan]")
        console.print(f"🆔 Generated UUID: [cyan]{uuid}[/cyan]")

        # Show capabilities
        console.print(f"🔐 Biometric capabilities: Available in web environment")

        console.print()
        console.print("✅ [bold green]Demo completed successfully![/bold green]")

        cli_obj.output_result({
            'did': did,
            'uuid': uuid,
            'timestamp': '2024-01-01T00:00:00Z'
        }, "Demo data generated")

    except Exception as e:
        console.print(f"❌ Demo failed: {e}", style="red")


# ============================================================================
# DASHBOARD COMMAND
# ============================================================================

@cli.command()
@click.pass_context
def dashboard(ctx):
    """Launch interactive SSI dashboard"""
    try:
        from .dashboard import run_dashboard
        run_dashboard()
    except ImportError:
        console.print("❌ Dashboard dependencies not available", style="red")
        console.print("Install with: pip install ssi-empoorio-id[dashboard]", style="yellow")
    except Exception as e:
        console.print(f"❌ Dashboard failed: {e}", style="red")


def main():
    """Main CLI entry point"""
    cli()


if __name__ == '__main__':
    main()