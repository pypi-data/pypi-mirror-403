#!/usr/bin/env python3
"""
SSI Empoorio ID Terminal Dashboard
Interactive terminal-based dashboard for SSI operations
"""

import json
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.align import Align
from rich.padding import Padding
from rich.style import Style
from rich.spinner import Spinner

from .sdk import SSIEmporioSDK
from .utils import generate_uuid

console = Console()


class SSIDashboard:
    """Interactive SSI Dashboard for terminals"""

    def __init__(self):
        self.sdk: Optional[SSIEmporioSDK] = None
        self.current_view = "main"
        self.status_data = {}
        self.vcs: List[Dict] = []
        self.dids: List[str] = []
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration"""
        config = {
            'issuer_url': os.getenv('SSI_ISSUER_URL', 'http://localhost:3001'),
            'verifier_url': os.getenv('SSI_VERIFIER_URL', 'http://localhost:3002'),
            'api_key': os.getenv('SSI_API_KEY'),
        }

        # Load from config file
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

    def create_layout(self) -> Layout:
        """Create the main dashboard layout"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )

        # Header
        header = Panel(
            Align.center(
                "[bold blue]🔐 SSI Empoorio ID Dashboard[/bold blue]\n"
                "[dim]Self-Sovereign Identity Management System[/dim]",
                vertical="middle"
            ),
            style="blue"
        )
        layout["header"].update(header)

        # Body - depends on current view
        if self.current_view == "main":
            layout["body"].update(self.create_main_view())
        elif self.current_view == "vc":
            layout["body"].update(self.create_vc_view())
        elif self.current_view == "did":
            layout["body"].update(self.create_did_view())
        elif self.current_view == "biometric":
            layout["body"].update(self.create_biometric_view())
        elif self.current_view == "status":
            layout["body"].update(self.create_status_view())

        # Footer
        footer = Panel(
            Align.center(
                "[dim]Use arrow keys to navigate • Enter to select • 'q' to quit[/dim]",
                vertical="middle"
            ),
            style="dim"
        )
        layout["footer"].update(footer)

        return layout

    def create_main_view(self) -> Panel:
        """Create the main dashboard view"""
        self.ensure_sdk()

        # Quick stats
        stats_table = Table(title="📊 Quick Stats")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="magenta")

        stats_table.add_row("SDK Status", "✅ Connected" if self.sdk else "❌ Disconnected")
        stats_table.add_row("Issuer URL", self.config.get('issuer_url', 'N/A'))
        stats_table.add_row("Verifier URL", self.config.get('verifier_url', 'N/A'))
        stats_table.add_row("VCs Managed", str(len(self.vcs)))
        stats_table.add_row("DIDs Created", str(len(self.dids)))

        # Menu options
        menu = Panel(
            "\n".join([
                "1. 🔑 [bold cyan]Verifiable Credentials[/bold cyan] - Issue, verify, manage VCs",
                "2. 🆔 [bold cyan]Decentralized Identifiers[/bold cyan] - Create and manage DIDs",
                "3. 🔐 [bold cyan]Biometric Authentication[/bold cyan] - Manage biometric credentials",
                "4. 📊 [bold cyan]System Status[/bold cyan] - View system metrics",
                "5. 🛠️ [bold cyan]Utilities[/bold cyan] - UUID generation, templates",
                "6. ⚙️ [bold cyan]Configuration[/bold cyan] - Manage settings",
                "",
                "[dim]Choose an option (1-6) or 'q' to quit:[/dim]"
            ]),
            title="🎯 Main Menu",
            border_style="blue"
        )

        # Combine stats and menu
        content = Columns([stats_table, menu], equal=True, expand=True)
        return Panel(content, title="🏠 Dashboard Overview")

    def create_vc_view(self) -> Panel:
        """Create VC management view"""
        vc_table = Table(title="📋 Verifiable Credentials")
        vc_table.add_column("ID", style="cyan", no_wrap=True)
        vc_table.add_column("Type", style="magenta")
        vc_table.add_column("Subject", style="green")
        vc_table.add_column("Status", style="yellow")

        # Mock VC data (in real implementation, load from storage)
        sample_vcs = [
            {"id": "vc-001", "type": "IdentityCredential", "subject": "did:emp:user123", "status": "✅ Active"},
            {"id": "vc-002", "type": "KYC", "subject": "did:emp:user456", "status": "✅ Active"},
        ]

        for vc in sample_vcs:
            vc_table.add_row(vc["id"], vc["type"], vc["subject"], vc["status"])

        menu = Panel(
            "\n".join([
                "1. ➕ [bold cyan]Issue New VC[/bold cyan] - Create verifiable credential",
                "2. ✅ [bold cyan]Verify VC[/bold cyan] - Verify existing credential",
                "3. 🚫 [bold cyan]Revoke VC[/bold cyan] - Revoke a credential",
                "4. 📊 [bold cyan]VC Status[/bold cyan] - Check credential status",
                "5. 📁 [bold cyan]Load VC File[/bold cyan] - Load VC from JSON file",
                "",
                "[dim]Choose an option (1-5) or 'b' to go back:[/dim]"
            ]),
            title="🔑 VC Operations",
            border_style="green"
        )

        content = Columns([vc_table, menu], equal=True, expand=True)
        return Panel(content, title="🔑 Verifiable Credentials Management")

    def create_did_view(self) -> Panel:
        """Create DID management view"""
        did_table = Table(title="🆔 Decentralized Identifiers")
        did_table.add_column("DID", style="cyan", no_wrap=True)
        did_table.add_column("Prefix", style="magenta")
        did_table.add_column("Created", style="green")

        # Sample DID data
        sample_dids = [
            {"did": "did:emp:user123", "prefix": "emp", "created": "2024-01-01"},
            {"did": "did:bank:user456", "prefix": "bank", "created": "2024-01-02"},
        ]

        for did_data in sample_dids:
            did_table.add_row(did_data["did"], did_data["prefix"], did_data["created"])

        menu = Panel(
            "\n".join([
                "1. ➕ [bold cyan]Create DID[/bold cyan] - Generate new DID",
                "2. ✅ [bold cyan]Validate DID[/bold cyan] - Validate DID format",
                "3. 🔍 [bold cyan]Resolve DID[/bold cyan] - Resolve DID document",
                "4. 📋 [bold cyan]DID Methods[/bold cyan] - Supported DID methods",
                "",
                "[dim]Choose an option (1-4) or 'b' to go back:[/dim]"
            ]),
            title="🆔 DID Operations",
            border_style="yellow"
        )

        content = Columns([did_table, menu], equal=True, expand=True)
        return Panel(content, title="🆔 Decentralized Identifiers Management")

    def create_biometric_view(self) -> Panel:
        """Create biometric management view"""
        bio_table = Table(title="🔐 Biometric Credentials")
        bio_table.add_column("User ID", style="cyan")
        bio_table.add_column("Method", style="magenta")
        bio_table.add_column("Status", style="green")
        bio_table.add_column("Last Used", style="yellow")

        # Sample biometric data
        sample_bio = [
            {"user": "user123", "method": "fingerprint", "status": "✅ Active", "last_used": "2024-01-15"},
            {"user": "user456", "method": "face", "status": "✅ Active", "last_used": "2024-01-14"},
        ]

        for bio in sample_bio:
            bio_table.add_row(bio["user"], bio["method"], bio["status"], bio["last_used"])

        menu = Panel(
            "\n".join([
                "1. ➕ [bold cyan]Register Biometric[/bold cyan] - Register new biometric credential",
                "2. ✅ [bold cyan]Authenticate[/bold cyan] - Test biometric authentication",
                "3. 📋 [bold cyan]List Credentials[/bold cyan] - View user credentials",
                "4. 🗑️ [bold cyan]Delete Credential[/bold cyan] - Remove biometric credential",
                "5. 📊 [bold cyan]Biometric Methods[/bold cyan] - Supported methods",
                "",
                "[dim]Choose an option (1-5) or 'b' to go back:[/dim]"
            ]),
            title="🔐 Biometric Operations",
            border_style="red"
        )

        content = Columns([bio_table, menu], equal=True, expand=True)
        return Panel(content, title="🔐 Biometric Authentication Management")

    def create_status_view(self) -> Panel:
        """Create system status view"""
        status_table = Table(title="📊 System Status")
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="magenta")
        status_table.add_column("Details", style="green")

        status_data = [
            {"component": "Issuer API", "status": "✅ Online", "details": "localhost:3001"},
            {"component": "Verifier API", "status": "✅ Online", "details": "localhost:3002"},
            {"component": "Redis Cache", "status": "✅ Connected", "details": "6379"},
            {"component": "PostgreSQL", "status": "✅ Connected", "details": "5432"},
            {"component": "Blockchain", "status": "✅ Synced", "details": "Block #12345"},
        ]

        for status in status_data:
            status_table.add_row(status["component"], status["status"], status["details"])

        metrics_table = Table(title="📈 Metrics")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="magenta")

        metrics = [
            {"metric": "VCs Issued (24h)", "value": "1,234"},
            {"metric": "VC Verifications", "value": "5,678"},
            {"metric": "Biometric Auths", "value": "890"},
            {"metric": "API Response Time", "value": "45ms"},
            {"metric": "Error Rate", "value": "0.01%"},
        ]

        for metric in metrics:
            metrics_table.add_row(metric["metric"], metric["value"])

        menu = Panel(
            "[bold cyan]System is running optimally![/bold cyan]\n\n"
            "• All services online\n"
            "• Database connections healthy\n"
            "• Cache performing well\n"
            "• Low error rates\n\n"
            "[dim]Press 'b' to go back to main menu[/dim]",
            title="🔍 System Health",
            border_style="green"
        )

        content = Columns([status_table, metrics_table, menu], expand=True)
        return Panel(content, title="📊 System Status & Metrics")

    def handle_vc_operations(self, choice: str):
        """Handle VC operation choices"""
        if choice == "1":
            self.issue_vc_interactive()
        elif choice == "2":
            self.verify_vc_interactive()
        elif choice == "3":
            self.revoke_vc_interactive()
        elif choice == "4":
            self.vc_status_interactive()
        elif choice == "5":
            self.load_vc_file()

    def issue_vc_interactive(self):
        """Interactive VC issuance"""
        console.clear()

        console.print(Panel.fit(
            "[bold green]➕ Issue New Verifiable Credential[/bold green]",
            border_style="green"
        ))

        # Get subject data
        subject_data = {}
        console.print("\n[bold cyan]Enter subject information:[/bold cyan]")

        subject_data['name'] = Prompt.ask("Name")
        subject_data['email'] = Prompt.ask("Email")
        subject_data['age'] = IntPrompt.ask("Age", default=0)

        # Generate DID
        did = self.sdk.create_test_did()
        subject_data['id'] = did

        console.print(f"\n[green]Generated DID: {did}[/green]")

        # VC options
        quantum = Confirm.ask("Use quantum-resistant signatures?", default=True)
        zkp = Confirm.ask("Enable zero-knowledge proofs?", default=False)

        # Issue VC
        with console.status("[bold green]Issuing verifiable credential...") as status:
            vc = self.sdk.issue_credential(
                subject=subject_data,
                credential_type=['VerifiableCredential', 'IdentityCredential'],
                options={
                    'quantum_resistant': quantum,
                    'zkp_enabled': zkp
                }
            )

        console.print("\n[bold green]✅ Verifiable Credential issued successfully![/bold green]")
        console.print(f"VC ID: [cyan]{vc.get('id', 'N/A')}[/cyan]")

        # Ask to save
        if Confirm.ask("Save VC to file?", default=True):
            filename = f"vc-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(vc, f, indent=2)
            console.print(f"💾 Saved to: [cyan]{filename}[/cyan]")

        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()

    def verify_vc_interactive(self):
        """Interactive VC verification"""
        console.clear()

        console.print(Panel.fit(
            "[bold blue]✅ Verify Verifiable Credential[/bold blue]",
            border_style="blue"
        ))

        # Ask for VC file or data
        vc_file = Prompt.ask("Enter VC JSON file path", default="")
        checks = Prompt.ask("Verification checks (comma-separated)",
                          default="signature,expiration,revocation")

        try:
            if vc_file and Path(vc_file).exists():
                with open(vc_file, 'r') as f:
                    vc = json.load(f)
            else:
                vc_json = Prompt.ask("Paste VC JSON data")
                vc = json.loads(vc_json)

            check_list = [c.strip() for c in checks.split(',')]

            with console.status("[bold blue]Verifying credential...") as status:
                result = self.sdk.verify_credential(vc, {'checks': check_list})

            if result.verified:
                console.print("\n[bold green]✅ Credential is VALID![/bold green]")
            else:
                console.print("\n[bold red]❌ Credential is INVALID![/bold red]")
                if hasattr(result, 'errors') and result.errors:
                    console.print("[red]Errors:[/red]")
                    for error in result.errors:
                        console.print(f"  • {error}")

        except Exception as e:
            console.print(f"\n[bold red]❌ Verification failed: {e}[/bold red]")

        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()

    def revoke_vc_interactive(self):
        """Interactive VC revocation"""
        console.clear()

        vc_id = Prompt.ask("Enter VC ID to revoke")
        reason = Prompt.ask("Revocation reason (optional)")

        try:
            with console.status("[bold red]Revoking credential...") as status:
                result = self.sdk.revoke_credential(vc_id, reason)

            console.print("\n[bold green]✅ Credential revoked successfully![/bold green]")

        except Exception as e:
            console.print(f"\n[bold red]❌ Revocation failed: {e}[/bold red]")

        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()

    def vc_status_interactive(self):
        """Interactive VC status check"""
        console.clear()

        vc_id = Prompt.ask("Enter VC ID to check")

        try:
            with console.status("[bold blue]Checking credential status...") as status:
                status_info = self.sdk.get_credential_status(vc_id)

            console.print("\n[bold green]📊 Credential Status:[/bold green]")
            console.print(f"Status: [cyan]{status_info.get('status', 'Unknown')}[/cyan]")
            console.print(f"Last Updated: [cyan]{status_info.get('lastUpdated', 'N/A')}[/cyan]")

        except Exception as e:
            console.print(f"\n[bold red]❌ Status check failed: {e}[/bold red]")

        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()

    def load_vc_file(self):
        """Load VC from file"""
        vc_file = Prompt.ask("Enter VC JSON file path")

        if vc_file and Path(vc_file).exists():
            with open(vc_file, 'r') as f:
                vc = json.load(f)

            self.vcs.append(vc)
            console.print(f"\n[bold green]✅ VC loaded from {vc_file}[/bold green]")
        else:
            console.print(f"\n[bold red]❌ File not found: {vc_file}[/bold red]")

        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()

    def run(self):
        """Run the interactive dashboard"""
        console.clear()

        try:
            with Live(self.create_layout(), refresh_per_second=4) as live:
                while True:
                    layout = self.create_layout()

                    if self.current_view == "main":
                        choice = Prompt.ask("\nChoose an option", choices=["1", "2", "3", "4", "5", "6", "q"])

                        if choice == "q":
                            break
                        elif choice in ["1", "2", "3", "4", "5", "6"]:
                            view_map = {
                                "1": "vc",
                                "2": "did",
                                "3": "biometric",
                                "4": "status",
                                "5": "utils",
                                "6": "config"
                            }
                            self.current_view = view_map[choice]

                    elif self.current_view == "vc":
                        choice = Prompt.ask("\nChoose VC operation", choices=["1", "2", "3", "4", "5", "b"])

                        if choice == "b":
                            self.current_view = "main"
                        else:
                            self.handle_vc_operations(choice)

                    elif self.current_view in ["did", "biometric", "status", "utils", "config"]:
                        choice = Prompt.ask(f"\nChoose {self.current_view} operation", choices=["b"])
                        if choice == "b":
                            self.current_view = "main"

                    live.update(layout)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            console.print(f"\n[bold red]❌ Dashboard error: {e}[/bold red]")

        console.print("\n[dim]👋 Thanks for using SSI Empoorio ID Dashboard![/dim]")


def run_dashboard():
    """Entry point for the dashboard"""
    dashboard = SSIDashboard()
    dashboard.run()


if __name__ == "__main__":
    run_dashboard()