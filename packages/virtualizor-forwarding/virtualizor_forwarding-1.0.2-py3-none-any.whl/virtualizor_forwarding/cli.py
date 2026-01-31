"""
CLI (Command Line Interface) for Virtualizor Forwarding Tool.

Main entry point for all commands.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, List

from .config import ConfigManager
from .api import VirtualizorClient, APIError, AuthenticationError
from .models import HostProfile, Protocol, ForwardingRule, VMStatus
from .services.vm_manager import VMManager
from .services.forwarding_manager import ForwardingManager
from .services.batch_processor import BatchProcessor
from .tui import TUIRenderer
from .utils import parse_comma_ids


class CLI:
    """Main CLI application."""

    def __init__(self) -> None:
        """Initialize CLI."""
        self._config_manager = ConfigManager()
        self._tui: Optional[TUIRenderer] = None
        self._verbose = False
        self._debug = False

    def _get_tui(self, no_color: bool = False) -> TUIRenderer:
        """Get or create TUI renderer."""
        if self._tui is None:
            self._tui = TUIRenderer(no_color=no_color)
        return self._tui

    def _get_client(self, host_name: Optional[str] = None) -> VirtualizorClient:
        """
        Get API client for specified or default host.

        Args:
            host_name: Host name or None for default.

        Returns:
            VirtualizorClient instance.

        Raises:
            SystemExit: If no host configured.
        """
        config = self._config_manager.load()

        if host_name:
            profile = config.hosts.get(host_name)
            if not profile:
                self._get_tui().print_error(f"Host '{host_name}' not found")
                sys.exit(1)
        else:
            profile = self._config_manager.get_default()
            if not profile:
                self._get_tui().print_error(
                    "No default host configured. Use 'config add' first."
                )
                sys.exit(1)

        return VirtualizorClient(profile)

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run CLI with arguments.

        Args:
            args: Command line arguments (uses sys.argv if None).

        Returns:
            Exit code.
        """
        parser = self._create_parser()
        parsed = parser.parse_args(args)

        self._verbose = getattr(parsed, "verbose", False)
        self._debug = getattr(parsed, "debug", False)
        no_color = getattr(parsed, "no_color", False)
        self._tui = TUIRenderer(no_color=no_color)

        if not hasattr(parsed, "func"):
            parser.print_help()
            return 0

        try:
            return parsed.func(parsed)
        except KeyboardInterrupt:
            self._tui.print_warning("Operation cancelled")
            return 130
        except APIError as e:
            self._tui.print_error(str(e))
            return 1
        except Exception as e:
            if self._debug:
                raise
            self._tui.print_error(f"Error: {e}")
            return 1

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with all subcommands."""
        parser = argparse.ArgumentParser(
            prog="vf",
            description="Virtualizor Domain/Port Forwarding Manager",
        )
        parser.add_argument(
            "--host", "-H", help="Use specific host profile", metavar="NAME"
        )
        parser.add_argument(
            "--no-color", action="store_true", help="Disable colored output"
        )
        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Verbose output"
        )
        parser.add_argument("--debug", action="store_true", help="Debug mode")

        subparsers = parser.add_subparsers(title="commands", dest="command")

        # Config commands
        self._add_config_commands(subparsers)

        # VM commands
        self._add_vm_commands(subparsers)

        # Forward commands
        self._add_forward_commands(subparsers)

        # Batch commands
        self._add_batch_commands(subparsers)

        return parser

    def _add_config_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add config subcommands."""
        config_parser = subparsers.add_parser(
            "config", help="Manage host configurations"
        )
        config_sub = config_parser.add_subparsers(
            title="config commands", dest="config_cmd"
        )

        # config add
        add_parser = config_sub.add_parser("add", help="Add new host profile")
        add_parser.add_argument("name", help="Host profile name")
        add_parser.add_argument("--url", required=True, help="API URL")
        add_parser.add_argument("--key", required=True, help="API Key")
        add_parser.add_argument(
            "--pass", dest="password", required=True, help="API Password"
        )
        add_parser.add_argument("--default", action="store_true", help="Set as default")
        add_parser.set_defaults(func=self._cmd_config_add)

        # config remove
        rm_parser = config_sub.add_parser("remove", help="Remove host profile")
        rm_parser.add_argument("name", help="Host profile name")
        rm_parser.set_defaults(func=self._cmd_config_remove)

        # config list
        list_parser = config_sub.add_parser("list", help="List host profiles")
        list_parser.set_defaults(func=self._cmd_config_list)

        # config set-default
        default_parser = config_sub.add_parser("set-default", help="Set default host")
        default_parser.add_argument("name", help="Host profile name")
        default_parser.set_defaults(func=self._cmd_config_set_default)

        # config test
        test_parser = config_sub.add_parser("test", help="Test host connection")
        test_parser.add_argument(
            "name", nargs="?", help="Host profile name (default if omitted)"
        )
        test_parser.set_defaults(func=self._cmd_config_test)

    def _add_vm_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add VM subcommands."""
        vm_parser = subparsers.add_parser("vm", help="Manage virtual machines")
        vm_sub = vm_parser.add_subparsers(title="vm commands", dest="vm_cmd")

        # vm list
        list_parser = vm_sub.add_parser("list", help="List virtual machines")
        list_parser.add_argument(
            "--status", "-s", choices=["up", "down"], help="Filter by status"
        )
        list_parser.add_argument(
            "--all-hosts", action="store_true", help="List from all configured hosts"
        )
        list_parser.add_argument(
            "--json", "-j", action="store_true", help="Output as JSON"
        )
        list_parser.set_defaults(func=self._cmd_vm_list)

    def _add_forward_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add forward subcommands."""
        fwd_parser = subparsers.add_parser("forward", help="Manage port forwarding")
        fwd_sub = fwd_parser.add_subparsers(
            title="forward commands", dest="forward_cmd"
        )

        # forward list
        list_parser = fwd_sub.add_parser("list", help="List forwarding rules")
        list_parser.add_argument("--vpsid", "-v", help="VM ID")
        list_parser.add_argument(
            "--auto", action="store_true", help="Auto-select if single VM"
        )
        list_parser.add_argument(
            "--json", "-j", action="store_true", help="Output as JSON"
        )
        list_parser.set_defaults(func=self._cmd_forward_list)

        # forward add
        add_parser = fwd_sub.add_parser("add", help="Add forwarding rule")
        add_parser.add_argument("--vpsid", "-v", help="VM ID")
        add_parser.add_argument(
            "--protocol", "-p", choices=["HTTP", "HTTPS", "TCP"], help="Protocol"
        )
        add_parser.add_argument("--domain", "-d", help="Source hostname/domain")
        add_parser.add_argument("--src-port", "-s", type=int, help="Source port")
        add_parser.add_argument("--dest-port", "-t", type=int, help="Destination port")
        add_parser.add_argument(
            "--dest-ip", help="Destination IP (default: VM internal IP)"
        )
        add_parser.add_argument(
            "--interactive", "-i", action="store_true", help="Interactive mode"
        )
        add_parser.set_defaults(func=self._cmd_forward_add)

        # forward edit
        edit_parser = fwd_sub.add_parser("edit", help="Edit forwarding rule")
        edit_parser.add_argument("--vpsid", "-v", help="VM ID")
        edit_parser.add_argument("--vdfid", "-f", help="Forwarding rule ID")
        edit_parser.add_argument(
            "--protocol", "-p", choices=["HTTP", "HTTPS", "TCP"], help="Protocol"
        )
        edit_parser.add_argument("--domain", "-d", help="Source hostname/domain")
        edit_parser.add_argument("--src-port", "-s", type=int, help="Source port")
        edit_parser.add_argument("--dest-port", "-t", type=int, help="Destination port")
        edit_parser.add_argument("--dest-ip", help="Destination IP")
        edit_parser.add_argument(
            "--interactive", "-i", action="store_true", help="Interactive mode"
        )
        edit_parser.set_defaults(func=self._cmd_forward_edit)

        # forward delete
        del_parser = fwd_sub.add_parser("delete", help="Delete forwarding rules")
        del_parser.add_argument("--vpsid", "-v", help="VM ID")
        del_parser.add_argument(
            "--vdfid", "-f", help="Forwarding rule ID(s), comma-separated"
        )
        del_parser.add_argument(
            "--force", action="store_true", help="Skip confirmation"
        )
        del_parser.add_argument(
            "--interactive", "-i", action="store_true", help="Interactive mode"
        )
        del_parser.set_defaults(func=self._cmd_forward_delete)

    def _add_batch_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add batch subcommands."""
        batch_parser = subparsers.add_parser("batch", help="Batch operations")
        batch_sub = batch_parser.add_subparsers(
            title="batch commands", dest="batch_cmd"
        )

        # batch import
        import_parser = batch_sub.add_parser("import", help="Import rules from JSON")
        import_parser.add_argument("--vpsid", "-v", required=True, help="VM ID")
        import_parser.add_argument(
            "--from-file", "-f", required=True, help="JSON file path"
        )
        import_parser.add_argument(
            "--dry-run", action="store_true", help="Validate only"
        )
        import_parser.set_defaults(func=self._cmd_batch_import)

        # batch export
        export_parser = batch_sub.add_parser("export", help="Export rules to JSON")
        export_parser.add_argument("--vpsid", "-v", required=True, help="VM ID")
        export_parser.add_argument(
            "--to-file", "-o", required=True, help="Output file path"
        )
        export_parser.set_defaults(func=self._cmd_batch_export)

    # Config command handlers
    def _cmd_config_add(self, args: argparse.Namespace) -> int:
        """Handle config add command."""
        profile = HostProfile.create(
            name=args.name,
            api_url=args.url,
            api_key=args.key,
            api_pass=args.password,
        )
        self._config_manager.add_host(args.name, profile)

        if args.default:
            self._config_manager.set_default(args.name)

        self._tui.print_success(f"Host '{args.name}' added successfully")
        return 0

    def _cmd_config_remove(self, args: argparse.Namespace) -> int:
        """Handle config remove command."""
        self._config_manager.remove_host(args.name)
        self._tui.print_success(f"Host '{args.name}' removed")
        return 0

    def _cmd_config_list(self, args: argparse.Namespace) -> int:
        """Handle config list command."""
        config = self._config_manager.load()
        if not config.hosts:
            self._tui.print_warning("No hosts configured. Use 'config add' to add one.")
            return 0

        self._tui.render_host_tree(config.hosts, config.default_host)
        return 0

    def _cmd_config_set_default(self, args: argparse.Namespace) -> int:
        """Handle config set-default command."""
        self._config_manager.set_default(args.name)
        self._tui.print_success(f"Default host set to '{args.name}'")
        return 0

    def _cmd_config_test(self, args: argparse.Namespace) -> int:
        """Handle config test command."""
        host_name = args.name or getattr(args, "host", None)
        client = self._get_client(host_name)

        with self._tui.show_spinner("Testing connection..."):
            try:
                client.test_connection()
                self._tui.print_success("Connection successful!")
                return 0
            except AuthenticationError:
                self._tui.print_error("Authentication failed. Check API credentials.")
                return 1
            except Exception as e:
                self._tui.print_error(f"Connection failed: {e}")
                return 1

    # VM command handlers
    def _cmd_vm_list(self, args: argparse.Namespace) -> int:
        """Handle vm list command."""
        import json as json_module

        if args.all_hosts:
            return self._cmd_vm_list_all_hosts(args)

        client = self._get_client(getattr(args, "host", None))
        vm_manager = VMManager(client)

        with self._tui.show_spinner("Fetching VMs..."):
            status_filter = VMStatus(args.status) if args.status else None
            vms = vm_manager.list_all(status_filter)

        if args.json:
            data = [vm.to_dict() for vm in vms]
            print(json_module.dumps(data, indent=2))
        else:
            if not vms:
                self._tui.print_warning("No VMs found")
            else:
                self._tui.render_vm_table(vms)

        return 0

    def _cmd_vm_list_all_hosts(self, args: argparse.Namespace) -> int:
        """List VMs from all configured hosts."""
        import json as json_module

        config = self._config_manager.load()
        all_vms = []

        for host_name, profile in config.hosts.items():
            try:
                client = VirtualizorClient(profile)
                vm_manager = VMManager(client)
                vms = vm_manager.list_all()
                for vm in vms:
                    vm_dict = vm.to_dict()
                    vm_dict["host"] = host_name
                    all_vms.append(vm_dict)
            except Exception as e:
                self._tui.print_warning(f"Failed to fetch from {host_name}: {e}")

        if args.json:
            print(json_module.dumps(all_vms, indent=2))
        else:
            self._tui.print_info(f"Total VMs across all hosts: {len(all_vms)}")

        return 0

    # Forward command handlers
    def _cmd_forward_list(self, args: argparse.Namespace) -> int:
        """Handle forward list command."""
        import json as json_module

        client = self._get_client(getattr(args, "host", None))
        vm_manager = VMManager(client)
        fwd_manager = ForwardingManager(client)

        vpsid = args.vpsid
        if not vpsid:
            vms = vm_manager.list_all()
            if args.auto and len(vms) == 1:
                vpsid = vms[0].vpsid
                self._tui.print_info(f"Auto-selected VM: {vms[0].hostname}")
            else:
                vm = self._tui.prompt_vm_selection(vms)
                if not vm:
                    return 1
                vpsid = vm.vpsid

        with self._tui.show_spinner("Fetching forwarding rules..."):
            rules = fwd_manager.list_rules(vpsid)

        if args.json:
            data = [rule.to_dict() for rule in rules]
            print(json_module.dumps(data, indent=2))
        else:
            if not rules:
                self._tui.print_warning("No forwarding rules found")
            else:
                self._tui.render_forwarding_table(rules)

        return 0

    def _cmd_forward_add(self, args: argparse.Namespace) -> int:
        """Handle forward add command."""
        client = self._get_client(getattr(args, "host", None))
        vm_manager = VMManager(client)
        fwd_manager = ForwardingManager(client)

        # Get VPSID
        vpsid = args.vpsid
        if not vpsid or args.interactive:
            vms = vm_manager.list_all()
            vm = self._tui.prompt_vm_selection(vms)
            if not vm:
                return 1
            vpsid = vm.vpsid

        # Get protocol
        protocol = Protocol.from_string(args.protocol) if args.protocol else None
        if not protocol or args.interactive:
            protocol = self._tui.prompt_protocol(protocol)

        # Auto-configure ports for HTTP/HTTPS
        auto_src, auto_dest = fwd_manager.auto_configure_ports(protocol)

        # Get source hostname
        src_hostname = args.domain
        if not src_hostname or args.interactive:
            if protocol == Protocol.TCP:
                # For TCP, get source IP from HAProxy config
                src_ip = fwd_manager.get_source_ip_for_tcp(vpsid)
                src_hostname = self._tui.prompt_input("Source IP", default=src_ip)
            else:
                src_hostname = self._tui.prompt_input("Domain name")

        # Get ports
        src_port = args.src_port or auto_src
        dest_port = args.dest_port or auto_dest

        if src_port is None or args.interactive:
            src_port = self._tui.prompt_int("Source port", default=src_port)
        if dest_port is None or args.interactive:
            dest_port = self._tui.prompt_int("Destination port", default=dest_port)

        # Get destination IP
        dest_ip = args.dest_ip
        if not dest_ip:
            dest_ip = vm_manager.get_internal_ip(vpsid)
        if not dest_ip or args.interactive:
            dest_ip = self._tui.prompt_input("Destination IP", default=dest_ip)

        # Create rule
        rule = ForwardingRule(
            protocol=protocol,
            src_hostname=src_hostname,
            src_port=src_port,
            dest_ip=dest_ip,
            dest_port=dest_port,
        )

        # Show confirmation
        self._tui.render_rule_detail(rule)
        if not self._tui.prompt_confirm("Add this forwarding rule?", default=True):
            self._tui.print_warning("Cancelled")
            return 0

        # Execute
        with self._tui.show_spinner("Adding forwarding rule..."):
            response = fwd_manager.add_rule(vpsid, rule)

        if response.success:
            self._tui.print_success("Forwarding rule added successfully")
            return 0
        else:
            self._tui.print_error(f"Failed: {response.get_error_message()}")
            return 1

    def _cmd_forward_edit(self, args: argparse.Namespace) -> int:
        """Handle forward edit command."""
        client = self._get_client(getattr(args, "host", None))
        vm_manager = VMManager(client)
        fwd_manager = ForwardingManager(client)

        # Get VPSID
        vpsid = args.vpsid
        if not vpsid or args.interactive:
            vms = vm_manager.list_all()
            vm = self._tui.prompt_vm_selection(vms)
            if not vm:
                return 1
            vpsid = vm.vpsid

        # Get rule to edit
        vdfid = args.vdfid
        if not vdfid or args.interactive:
            rules = fwd_manager.list_rules(vpsid)
            rule = self._tui.prompt_rule_selection(rules)
            if not rule:
                return 1
            vdfid = rule.id
            current_rule = rule
        else:
            current_rule = fwd_manager.get_rule_by_id(vpsid, vdfid)
            if not current_rule:
                self._tui.print_error(f"Rule {vdfid} not found")
                return 1

        # Get new values (use current as defaults)
        protocol = Protocol.from_string(args.protocol) if args.protocol else None
        if args.interactive:
            protocol = self._tui.prompt_protocol(current_rule.protocol)

        # Auto-configure ports if protocol changed
        if protocol and protocol != current_rule.protocol:
            auto_src, auto_dest = fwd_manager.auto_configure_ports(protocol)
        else:
            auto_src, auto_dest = None, None

        src_hostname = args.domain
        if args.interactive:
            src_hostname = self._tui.prompt_input(
                "Domain/IP", default=current_rule.src_hostname
            )

        src_port = args.src_port or auto_src
        if args.interactive:
            src_port = self._tui.prompt_int(
                "Source port", default=src_port or current_rule.src_port
            )

        dest_port = args.dest_port or auto_dest
        if args.interactive:
            dest_port = self._tui.prompt_int(
                "Dest port", default=dest_port or current_rule.dest_port
            )

        dest_ip = args.dest_ip
        if args.interactive:
            dest_ip = self._tui.prompt_input("Dest IP", default=current_rule.dest_ip)

        # Merge updates
        updated_rule = fwd_manager.merge_rule_update(
            current_rule,
            protocol=protocol,
            src_hostname=src_hostname,
            src_port=src_port,
            dest_port=dest_port,
            dest_ip=dest_ip,
        )

        # Show comparison
        self._tui.render_comparison(current_rule, updated_rule)
        if not self._tui.prompt_confirm("Apply these changes?", default=True):
            self._tui.print_warning("Cancelled")
            return 0

        # Execute
        with self._tui.show_spinner("Updating forwarding rule..."):
            response = fwd_manager.edit_rule(vpsid, vdfid, updated_rule)

        if response.success:
            self._tui.print_success("Forwarding rule updated successfully")
            return 0
        else:
            self._tui.print_error(f"Failed: {response.get_error_message()}")
            return 1

    def _cmd_forward_delete(self, args: argparse.Namespace) -> int:
        """Handle forward delete command."""
        client = self._get_client(getattr(args, "host", None))
        vm_manager = VMManager(client)
        fwd_manager = ForwardingManager(client)

        # Get VPSID
        vpsid = args.vpsid
        if not vpsid or args.interactive:
            vms = vm_manager.list_all()
            vm = self._tui.prompt_vm_selection(vms)
            if not vm:
                return 1
            vpsid = vm.vpsid

        # Get rule IDs to delete
        vdfids = []
        if args.vdfid:
            vdfids = parse_comma_ids(args.vdfid)
        elif args.interactive:
            rules = fwd_manager.list_rules(vpsid)
            rule = self._tui.prompt_rule_selection(rules)
            if not rule:
                return 1
            vdfids = [rule.id]

        if not vdfids:
            self._tui.print_error("No rule IDs specified")
            return 1

        # Confirm deletion
        if not args.force:
            self._tui.print_warning(
                f"About to delete {len(vdfids)} rule(s): {', '.join(vdfids)}"
            )
            if not self._tui.prompt_confirm("Are you sure?", default=False):
                self._tui.print_warning("Cancelled")
                return 0

        # Execute
        with self._tui.show_spinner("Deleting forwarding rules..."):
            response = fwd_manager.delete_rules(vpsid, vdfids)

        if response.success:
            self._tui.print_success(f"Deleted {len(vdfids)} forwarding rule(s)")
            return 0
        else:
            self._tui.print_error(f"Failed: {response.get_error_message()}")
            return 1

    # Batch command handlers
    def _cmd_batch_import(self, args: argparse.Namespace) -> int:
        """Handle batch import command."""
        client = self._get_client(getattr(args, "host", None))
        fwd_manager = ForwardingManager(client)
        batch_processor = BatchProcessor(fwd_manager)

        # Import rules from file
        try:
            rules = batch_processor.import_rules(args.from_file)
        except FileNotFoundError:
            self._tui.print_error(f"File not found: {args.from_file}")
            return 1
        except ValueError as e:
            self._tui.print_error(f"Invalid JSON: {e}")
            return 1

        self._tui.print_info(f"Loaded {len(rules)} rules from {args.from_file}")

        if args.dry_run:
            self._tui.print_info("Dry run mode - validating only")

        # Execute batch
        def progress_callback(current: int, total: int) -> None:
            pass  # Progress handled by Rich

        with self._tui.show_progress(len(rules), "Processing rules") as progress:
            task_id = progress._task_id

            def update_progress(current: int, total: int) -> None:
                progress.update(task_id, completed=current)

            result = batch_processor.execute_batch(
                args.vpsid,
                rules,
                dry_run=args.dry_run,
                progress_callback=update_progress,
            )

        # Show results
        if result.is_complete_success:
            self._tui.print_success(f"All {result.total} rules processed successfully")
        elif result.is_partial_success:
            self._tui.print_warning(
                f"Partial success: {result.succeeded}/{result.total} succeeded, "
                f"{result.failed} failed"
            )
        else:
            self._tui.print_error(f"All {result.total} rules failed")

        # Show errors
        for error in result.errors[:5]:  # Show first 5 errors
            self._tui.print_error(f"  - {error.get('error', 'Unknown error')}")

        if len(result.errors) > 5:
            self._tui.print_warning(f"  ... and {len(result.errors) - 5} more errors")

        return 0 if result.is_complete_success else 1

    def _cmd_batch_export(self, args: argparse.Namespace) -> int:
        """Handle batch export command."""
        client = self._get_client(getattr(args, "host", None))
        fwd_manager = ForwardingManager(client)
        batch_processor = BatchProcessor(fwd_manager)

        with self._tui.show_spinner("Exporting rules..."):
            count = batch_processor.export_rules(args.vpsid, args.to_file)

        self._tui.print_success(f"Exported {count} rules to {args.to_file}")
        return 0


def main() -> int:
    """Main entry point."""
    cli = CLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
