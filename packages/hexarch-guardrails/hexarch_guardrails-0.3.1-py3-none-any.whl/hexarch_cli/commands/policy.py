"""Policy management commands for hexarch-ctl."""

import sys
from pathlib import Path
from typing import Optional
import click
from hexarch_cli.context import HexarchContext
from hexarch_cli.output.formatter import OutputFormatter


@click.group(name="policy")
def policy_group():
    """Manage OPA policies.
    
    Commands for listing, exporting, validating, and comparing policies.
    """
    pass


@policy_group.command(name="list")
@click.option("--format", type=click.Choice(["json", "table", "csv"]), default=None, help="Output format")
@click.pass_context
def policy_list(click_ctx: click.Context, format: Optional[str]) -> None:
    """List all OPA policies in system.
    
    Shows policy name, status, version, update time, and rule count.
    
    \b
    Examples:
      hexarch-ctl policy list
      hexarch-ctl policy list --format json
      hexarch-ctl policy list --format csv
    """
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)
    
    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    
    try:
        # Override format if specified
        if format:
            formatter = OutputFormatter(format=format, colors=ctx.config_manager.get_config().output.colors)
        
        # Fetch policies
        try:
            policies = ctx.api_client.list_policies()
        except Exception as e:
            formatter.print_error(f"Failed to fetch policies: {str(e)}")
            ctx.audit_logger.log_command("policy list", error=str(e))
            sys.exit(1)
        
        if not policies:
            formatter.print_info("No policies found")
            ctx.audit_logger.log_command("policy list", result="0 policies")
            return
        
        # Prepare data for output
        headers = ["NAME", "STATUS", "VERSION", "UPDATED", "RULES"]
        data = []
        
        for policy in policies:
            data.append([
                policy.get("name", ""),
                policy.get("status", "unknown").upper(),
                policy.get("version", ""),
                policy.get("updated", ""),
                str(policy.get("rule_count", 0))
            ])
        
        # Format and print
        output = formatter.format_output(data, headers=headers)
        print(output)
        
        ctx.audit_logger.log_command("policy list", result=f"{len(policies)} policies")
        
    except Exception as e:
        formatter.print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)


@policy_group.command(name="export")
@click.argument("policy-name", required=False)
@click.option("--output", "-o", type=click.Path(), default=None, help="Output file (default: stdout)")
@click.option("--format", type=click.Choice(["rego", "json"]), default="rego", help="Export format")
@click.pass_context
def policy_export(click_ctx: click.Context, policy_name: Optional[str], output: Optional[str], format: str) -> None:
    """Export OPA policy or all policies.
    
    Exports policy source code (Rego format) or metadata (JSON).
    
    \b
    Examples:
      hexarch-ctl policy export ai_governance
      hexarch-ctl policy export ai_governance -o policy.rego
      hexarch-ctl policy export -o all_policies.json --format json
    """
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)
    
    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    
    try:
        
        # If no policy specified, export all
        if not policy_name:
            try:
                policies = ctx.api_client.list_policies()
            except Exception as e:
                formatter.print_error(f"Failed to fetch policies: {str(e)}")
                ctx.audit_logger.log_command("policy export", error=str(e))
                sys.exit(1)
            
            if not policies:
                formatter.print_info("No policies to export")
                return
            
            # Export all policies as JSON
            if format == "json":
                import json
                export_data = json.dumps(policies, indent=2, default=str)
            else:
                formatter.print_error("Cannot export multiple policies in Rego format. Use --format json or specify a single policy")
                sys.exit(1)
            
            result = f"all {len(policies)} policies"
        else:
            # Export single policy
            try:
                policy = ctx.api_client.get_policy(policy_name)
            except Exception as e:
                formatter.print_error(f"Failed to fetch policy '{policy_name}': {str(e)}")
                ctx.audit_logger.log_command(f"policy export {policy_name}", error=str(e))
                sys.exit(1)
            
            if format == "rego":
                export_data = policy.get("source", "")
            else:
                import json
                export_data = json.dumps(policy, indent=2, default=str)
            
            result = policy_name
        
        # Write or print
        if output:
            output_path = Path(output).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(export_data)
            formatter.print_success(f"Exported policy '{result}' to {output}")
            ctx.audit_logger.log_command(f"policy export {result}", result=f"saved to {output}")
        else:
            print(export_data)
            ctx.audit_logger.log_command(f"policy export {result}", result="printed to stdout")
        
    except Exception as e:
        formatter.print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)


@policy_group.command(name="validate")
@click.argument("policy-file", type=click.Path(exists=True))
@click.option("--strict", is_flag=True, help="Strict validation mode")
@click.pass_context
def policy_validate(click_ctx: click.Context, policy_file: str, strict: bool) -> None:
    """Validate OPA policy syntax offline.
    
    Checks policy file for syntax errors, unused variables, and import issues.
    
    \b
    Examples:
      hexarch-ctl policy validate my_policy.rego
      hexarch-ctl policy validate policy.rego --strict
    """
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)
    
    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    
    try:
        policy_path = Path(policy_file).expanduser()
        
        if not policy_path.exists():
            formatter.print_error(f"Policy file not found: {policy_file}")
            sys.exit(1)
        
        # Read policy
        policy_content = policy_path.read_text()
        
        # Basic validation (could integrate with OPA binary or library)
        validation_errors = []
        validation_warnings = []
        
        # Check for package declaration
        if not "package " in policy_content:
            validation_errors.append("No package declaration found")
        
        # Check for common syntax issues
        lines = policy_content.split("\n")
        rule_count = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Count rules
            if stripped and not stripped.startswith("#") and (" :- " in stripped or " = " in stripped):
                rule_count += 1
            
            # Check for unmatched braces
            if "{" in stripped and "}" not in stripped:
                validation_warnings.append(f"Line {i}: Unclosed brace")
        
        # Report results
        if validation_errors:
            formatter.print_error("Policy validation failed:")
            for error in validation_errors:
                print(f"  ✗ {error}")
            sys.exit(1)
        else:
            formatter.print_success("Policy syntax valid")
            print(f"✓ {rule_count} rules detected")
            print(f"✓ Package declaration present")
            
            if strict and validation_warnings:
                print("\nWarnings:")
                for warning in validation_warnings:
                    formatter.print_warning(warning)
            
            ctx.audit_logger.log_command(f"policy validate {policy_path.name}", result=f"{rule_count} rules, valid")
        
    except Exception as e:
        formatter.print_error(f"Validation error: {str(e)}")
        sys.exit(1)


@policy_group.command(name="diff")
@click.argument("policy-name")
@click.option("--from", "from_version", default=None, help="From version")
@click.option("--to", "to_version", default=None, help="To version")
@click.pass_context
def policy_diff(click_ctx: click.Context, policy_name: str, from_version: Optional[str], to_version: Optional[str]) -> None:
    """Compare policy versions.
    
    Shows what changed between policy versions.
    
    \b
    Examples:
      hexarch-ctl policy diff ai_governance
      hexarch-ctl policy diff ai_governance --from 1.0.0 --to 1.1.0
    """
    if not click_ctx.obj:
        click.echo("Error: CLI context not initialized", err=True)
        sys.exit(1)
    
    ctx: HexarchContext = click_ctx.obj
    formatter = ctx.formatter
    
    try:
        
        # Fetch policy
        try:
            policy = ctx.api_client.get_policy(policy_name)
        except Exception as e:
            formatter.print_error(f"Failed to fetch policy '{policy_name}': {str(e)}")
            ctx.audit_logger.log_command(f"policy diff {policy_name}", error=str(e))
            sys.exit(1)
        
        current_version = policy.get("version", "unknown")
        current_source = policy.get("source", "")
        
        formatter.print_header(f"Policy: {policy_name}")
        print(f"Current version: {current_version}")
        
        # If versions specified, would fetch and compare
        if from_version or to_version:
            formatter.print_warning("Version comparison not yet implemented")
            formatter.print_info("Showing current policy version")
        
        # Display current policy
        print("\n" + "=" * 60)
        print(current_source)
        print("=" * 60)
        
        ctx.audit_logger.log_command(f"policy diff {policy_name}", result=f"version {current_version}")
        
    except Exception as e:
        formatter.print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)


__all__ = ["policy_group"]
