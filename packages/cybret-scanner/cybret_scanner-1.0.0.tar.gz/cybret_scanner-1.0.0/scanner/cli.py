"""
Command-line interface for CYBRET AI Scanner
"""

import click
import uuid
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from scanner.parsers.python_parser import PythonParser
from scanner.parsers.javascript_parser import JavaScriptParser
from scanner.parsers.java_parser import JavaParser
from scanner.parsers.go_parser import GoParser
from scanner.graph.builder import GraphBuilder
from scanner.detectors.idor import IDORDetector
from scanner.detectors.auth_bypass import AuthBypassDetector
from scanner.config import settings
from scanner.banner import print_banner, print_scan_header, print_scan_summary, print_cybret_footer

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """CYBRET AI Logic Vulnerability Scanner"""
    pass


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option(
    "--language",
    "-l",
    type=click.Choice(["python", "javascript", "java", "go"], case_sensitive=False),
    required=True,
    help="Programming language to scan",
)
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--llm-analyze",
    is_flag=True,
    help="Enable LLM-powered autonomous vulnerability analysis and remediation",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["openai", "anthropic", "openrouter", "ollama", "mock"], case_sensitive=False),
    help="LLM provider to use (auto-detects from environment if not specified)",
)
@click.option(
    "--llm-report",
    type=click.Path(),
    help="Output file for LLM remediation report (markdown format)",
)
@click.option(
    "--auto-apply",
    is_flag=True,
    help="Automatically apply approved fixes to source files (creates backups)",
)
@click.option(
    "--backup-dir",
    type=click.Path(),
    default=".scanner-backups",
    help="Directory for backup files (default: .scanner-backups)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be applied without making changes",
)
@click.option(
    "--create-pr",
    is_flag=True,
    help="Automatically create a pull request with applied fixes",
)
@click.option(
    "--pr-branch",
    type=str,
    default="security/llm-auto-fixes",
    help="Branch name for the pull request (default: security/llm-auto-fixes)",
)
@click.option(
    "--pr-base",
    type=str,
    default="main",
    help="Base branch for the pull request (default: main)",
)
@click.option(
    "--generate-tests",
    is_flag=True,
    help="Automatically generate security tests for applied fixes",
)
@click.option(
    "--test-framework",
    type=click.Choice(["auto", "jest", "mocha", "pytest", "unittest", "junit"], case_sensitive=False),
    default="auto",
    help="Testing framework to use (default: auto-detect)",
)
@click.option(
    "--test-directory",
    type=str,
    default="tests/security",
    help="Directory for generated tests (default: tests/security)",
)
def scan(directory, language, output, verbose, llm_analyze, llm_provider, llm_report, auto_apply, backup_dir, dry_run, create_pr, pr_branch, pr_base, generate_tests, test_framework, test_directory):
    """Scan a directory for logic vulnerabilities"""
    
    # Print branded banner
    print_banner(console)
    
    # Print scan configuration
    print_scan_header(
        directory=directory,
        language=language,
        llm_enabled=llm_analyze,
        console=console
    )

    scan_id = f"cli_scan_{uuid.uuid4().hex[:8]}"
    start_time = time.time()

    try:
        # Select parser
        parser_map = {
            "python": PythonParser,
            "javascript": JavaScriptParser,
            "java": JavaParser,
            "go": GoParser,
        }
        parser = parser_map[language]()

        # Parse code
        print("Parsing code...")
        ast_nodes = parser.parse_directory(Path(directory))
        print(f"Parsed {len(ast_nodes)} files")

        # Extract entities
        all_entities = []
        for ast_node in ast_nodes:
            entities = parser.extract_entities(ast_node)
            all_entities.extend(entities)

        print(f"Extracted {len(all_entities)} code entities")

        # Build symbol table (for JavaScript/TypeScript)
        symbol_table = None
        all_routes = []
        all_mounts = []
        if language == "javascript":
            print("Building symbol table...")
            from scanner.extractors.symbol_table import SymbolTable
            symbol_table = SymbolTable()
            
            # First pass: Extract all imports, exports, functions
            for ast_node in ast_nodes:
                imports, exports, functions = parser.extract_symbols(ast_node)
                file_path = ast_node.get_attribute("file_path", "")
                symbol_table.add_imports(file_path, imports)
                symbol_table.add_exports(file_path, exports)
                symbol_table.add_functions(file_path, functions)
            
            stats = symbol_table.get_statistics()
            print(f"Symbol table: {stats['files']} files, {stats['imports']} imports, {stats['exports']} exports")
            
            # Second pass: Extract routes with symbol resolution
            print("Extracting routes with handler resolution...")
            from scanner.extractors.route_graph_extractor import RouteGraphExtractor
            route_extractor = RouteGraphExtractor(symbol_table=symbol_table)
            
            for ast_node in ast_nodes:
                raw_ast = ast_node.get_attribute("raw_ast")
                file_path = ast_node.get_attribute("file_path", "")
                if raw_ast:
                    routes, mounts = route_extractor.extract_routes_from_ast(raw_ast, file_path)
                    all_routes.extend(routes)
                    all_mounts.extend(mounts)
            
            print(f"Extracted {len(all_routes)} routes, {len(all_mounts)} mounts")

        # Build graph
        with GraphBuilder() as graph_builder:
            print("Building knowledge graph...")
            graph_builder.create_constraints()
            stats = graph_builder.build_graph_from_ast(ast_nodes, scan_id)
            graph_builder.create_entities(all_entities, scan_id)
            graph_builder.create_call_relationships(scan_id)
            
            # Create route graph
            if all_routes:
                route_stats = graph_builder.create_route_graph(all_routes, all_mounts, scan_id)
                stats.update(route_stats)

            print(
                f"Graph built: {stats['nodes']} nodes, {stats['relationships']} relationships"
            )
            if all_routes:
                print(f"Route graph: {route_stats['routes']} routes, {route_stats['middleware']} middleware")

            # Run detectors
            vulnerabilities = []

            print("Detecting vulnerabilities...")

            # Use new 2-stage BOLA detector
            from scanner.detectors.bola_2stage import BOLA2StageDetector
            bola_detector = BOLA2StageDetector(graph_builder.driver, graph_builder.database)
            bola_vulns = bola_detector.detect(scan_id)
            bola_detector.save_vulnerabilities(scan_id)
            vulnerabilities.extend(bola_vulns)

            auth_detector = AuthBypassDetector(
                graph_builder.driver, graph_builder.database
            )
            auth_vulns = auth_detector.detect(scan_id)
            auth_detector.save_vulnerabilities(scan_id)
            vulnerabilities.extend(auth_vulns)

        # LLM Analysis (if enabled)
        llm_results = None
        if llm_analyze and vulnerabilities:
            try:
                print("\n" + "="*60)
                print("Starting LLM-Powered Autonomous Remediation")
                print("="*60)
                
                from scanner.llm.remediation import analyze_scan_results
                
                # Build routes mapping for better context
                routes_mapping = None
                if all_routes:
                    routes_mapping = {}
                    for route in all_routes:
                        if route.handler_file and route.handler_line:
                            key = f"{route.handler_file}:{route.handler_line}"
                            routes_mapping[key] = route
                
                # Run LLM analysis
                llm_results = analyze_scan_results(
                    scan_id=scan_id,
                    vulnerabilities=vulnerabilities,
                    codebase_path=directory,
                    routes=routes_mapping,
                    output_file=llm_report
                )
                
                print("\n" + "="*60)
                print("LLM Analysis Complete")
                print("="*60)
                
                # Display LLM summary
                approved_count = len(llm_results.get('approved_fixes', []))
                total_count = llm_results.get('total_vulnerabilities', 0)
                
                console.print(f"\n[bold green]✓ Approved Fixes:[/bold green] {approved_count}/{total_count}")
                
                if approved_count > 0:
                    console.print("\n[bold]Approved Remediations:[/bold]")
                    for i, fix in enumerate(llm_results['approved_fixes'][:5], 1):  # Show first 5
                        console.print(f"  {i}. {fix.get('vulnerability_type', 'Unknown')} at {fix.get('location', 'Unknown')}")
                    
                    if approved_count > 5:
                        console.print(f"  ... and {approved_count - 5} more")
                
                if llm_report:
                    console.print(f"\n[bold cyan]📄 Full report saved to:[/bold cyan] {llm_report}")
                
                # Auto-apply fixes (if enabled)
                if auto_apply and approved_count > 0:
                    console.print("\n" + "="*60)
                    console.print("[bold yellow]Auto-Apply Mode[/bold yellow]")
                    console.print("="*60)
                    
                    if dry_run:
                        console.print("[cyan]DRY RUN: Showing what would be applied[/cyan]\n")
                    
                    from scanner.utils.fix_applier import FixApplier
                    
                    applier = FixApplier(
                        codebase_path=directory,
                        backup_dir=backup_dir,
                        dry_run=dry_run
                    )
                    
                    applied_results = applier.apply_fixes(llm_results['approved_fixes'])
                    
                    # Display results
                    success_count = sum(1 for r in applied_results if r['success'])
                    failed_count = len(applied_results) - success_count
                    
                    if dry_run:
                        console.print(f"\n[bold]Dry Run Summary:[/bold]")
                        console.print(f"  Would apply: {success_count} fixes")
                        console.print(f"  Would skip: {failed_count} fixes")
                    else:
                        console.print(f"\n[bold green]✓ Applied:[/bold green] {success_count} fixes")
                        if failed_count > 0:
                            console.print(f"[bold red]✗ Failed:[/bold red] {failed_count} fixes")
                        
                        if success_count > 0:
                            console.print(f"\n[bold cyan]💾 Backups saved to:[/bold cyan] {backup_dir}")
                            console.print("[yellow]⚠️  Review changes before committing![/yellow]")
                    
                    # Show details if verbose
                    if verbose:
                        console.print("\n[bold]Details:[/bold]")
                        for result in applied_results:
                            status = "✓" if result['success'] else "✗"
                            console.print(f"  {status} {result['file']}")
                            if not result['success']:
                                console.print(f"     Error: {result.get('error', 'Unknown')}")
                    
                    # Create PR (if enabled and fixes were applied)
                    if create_pr and success_count > 0 and not dry_run:
                        console.print("\n" + "="*60)
                        console.print("[bold cyan]Creating Pull Request[/bold cyan]")
                        console.print("="*60)
                        
                        from scanner.utils.pr_creator import PRCreator
                        
                        pr_creator = PRCreator(
                            codebase_path=directory,
                            branch_name=pr_branch,
                            base_branch=pr_base
                        )
                        
                        pr_result = pr_creator.create_pr(
                            llm_results=llm_results,
                            applied_results=applied_results,
                            report_path=llm_report
                        )
                        
                        if pr_result['success']:
                            console.print(f"\n[bold green]✓ Pull Request Created![/bold green]")
                            console.print(f"  URL: [cyan]{pr_result['pr_url']}[/cyan]")
                            console.print(f"  Branch: {pr_result['branch']}")
                            console.print(f"  Files changed: {pr_result['files_changed']}")
                        else:
                            console.print(f"\n[bold red]✗ PR Creation Failed[/bold red]")
                            console.print(f"  Error: {pr_result.get('error', 'Unknown')}")
                            
                            if verbose and pr_result.get('details'):
                                console.print(f"\n  Details: {pr_result['details']}")
                    
                    # Generate tests (if enabled and fixes were applied)
                    if generate_tests and success_count > 0 and not dry_run:
                        console.print("\n" + "="*60)
                        console.print("[bold magenta]Generating Security Tests[/bold magenta]")
                        console.print("="*60)
                        
                        from scanner.utils.test_generator import TestGenerator
                        
                        test_gen = TestGenerator(
                            codebase_path=directory,
                            test_framework=test_framework,
                            test_directory=test_directory
                        )
                        
                        test_result = test_gen.generate_tests(
                            llm_results=llm_results,
                            applied_results=applied_results
                        )
                        
                        if test_result['success']:
                            console.print(f"\n[bold green]✓ Tests Generated![/bold green]")
                            console.print(f"  Framework: {test_result['framework']}")
                            console.print(f"  Tests created: {test_result['tests_generated']}")
                            console.print(f"  Test directory: {test_result['test_directory']}")
                            
                            if verbose and test_result.get('test_files'):
                                console.print("\n[bold]Generated test files:[/bold]")
                                for test_file in test_result['test_files'][:5]:
                                    console.print(f"  • {Path(test_file).name}")
                                
                                if len(test_result['test_files']) > 5:
                                    console.print(f"  ... and {len(test_result['test_files']) - 5} more")
                            
                            console.print(f"\n[cyan]Run tests with:[/cyan]")
                            if test_result['framework'] in ['jest', 'mocha']:
                                console.print(f"  npm test")
                            elif test_result['framework'] in ['pytest', 'unittest']:
                                console.print(f"  pytest {test_directory}")
                            elif test_result['framework'] == 'junit':
                                console.print(f"  mvn test")
                        else:
                            console.print(f"\n[bold red]✗ Test Generation Failed[/bold red]")
                            console.print(f"  Error: {test_result.get('error', 'Unknown')}")
                
            except ImportError as e:
                console.print(f"\n[bold red]Error:[/bold red] LLM dependencies not installed. Run: pip install -r requirements-llm.txt")
                if verbose:
                    console.print(f"Details: {e}")
            except Exception as e:
                console.print(f"\n[bold red]Error during LLM analysis:[/bold red] {e}")
                if verbose:
                    import traceback
                    console.print(traceback.format_exc())

        # Calculate scan time
        scan_time = time.time() - start_time
        
        # Count high-confidence findings
        high_confidence = sum(1 for v in vulnerabilities if v.confidence > 0.78)
        
        # Display branded summary
        print_scan_summary(
            vulnerabilities_found=len(vulnerabilities),
            files_scanned=len(ast_nodes),
            scan_time=scan_time,
            high_confidence=high_confidence,
            console=console
        )

        if vulnerabilities:
            # Summary table
            table = Table(title="Vulnerability Summary")
            table.add_column("Severity", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Count", justify="right", style="green")

            # Count by severity and type
            from collections import defaultdict

            counts = defaultdict(lambda: defaultdict(int))
            for vuln in vulnerabilities:
                counts[vuln.severity.value][vuln.vuln_type] += 1

            for severity in ["critical", "high", "medium", "low"]:
                for vuln_type, count in counts[severity].items():
                    table.add_row(severity.upper(), vuln_type, str(count))

            print(table)

            # Detailed vulnerabilities
            if verbose:
                print("\nDetailed Findings:\n")
                for i, vuln in enumerate(vulnerabilities, 1):
                    print(f"{i}. {vuln.title}")
                    print(f"   Severity: {vuln.severity.value.upper()}")
                    print(f"   Location: {vuln.file_path}:{vuln.line_start}")
                    print(f"   Function: {vuln.function_name}")
                    print(f"   CWE: {vuln.cwe}\n")
        else:
            print("No vulnerabilities found!")

        # Save to file
        if output:
            import json

            results = {
                "scan_id": scan_id,
                "directory": directory,
                "language": language,
                "vulnerabilities": [v.to_dict() for v in vulnerabilities],
            }
            
            # Include LLM results if available
            if llm_results:
                results["llm_analysis"] = {
                    "total_analyzed": llm_results.get('total_vulnerabilities', 0),
                    "approved_fixes": len(llm_results.get('approved_fixes', [])),
                    "analyses": llm_results.get('analyses', [])
                }
            
            with open(output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            console.print(f"\n[bold cyan]📄 Results saved to:[/bold cyan] {output}")
        
        # Print footer
        print_cybret_footer(console)

    except Exception as e:
        print(f"\nError: {e}")
        if verbose:
            import traceback

            print(traceback.format_exc())
        raise click.Abort()


@cli.command()
def test_connection():
    """Test Neo4j connection"""
    print_banner(console, compact=True)
    console.print("[cyan]Testing Neo4j connection...[/cyan]\n")

    try:
        with GraphBuilder() as graph_builder:
            console.print(f"[green]✓[/green] Connected to {graph_builder.uri}")
            console.print(f"  [bold]Database:[/bold] {graph_builder.database}")
            console.print(f"  [bold]User:[/bold] {graph_builder.user}")
            console.print("\n[bold green]Connection successful![/bold green]\n")
        print_cybret_footer(console)
    except Exception as e:
        console.print(f"\n[bold red]✗ Connection failed:[/bold red] {e}\n")
        raise click.Abort()


@cli.command()
@click.confirmation_option(prompt="This will delete all data. Continue?")
def clear_graph():
    """Clear all data from Neo4j (DANGEROUS)"""
    print_banner(console, compact=True)
    console.print("[yellow]⚠️  Clearing graph database...[/yellow]\n")

    try:
        with GraphBuilder() as graph_builder:
            graph_builder.clear_graph()
            console.print("[bold green]✓ Graph cleared successfully![/bold green]\n")
        print_cybret_footer(console)
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        raise click.Abort()


@cli.command()
@click.argument("scan_results", type=click.Path(exists=True))
@click.argument("codebase_path", type=click.Path(exists=True))
@click.option(
    "--llm-provider",
    type=click.Choice(["openai", "anthropic", "openrouter", "ollama", "mock"], case_sensitive=False),
    help="LLM provider to use (auto-detects from environment if not specified)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for remediation report (markdown format)",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def analyze(scan_results, codebase_path, llm_provider, output, verbose):
    """Analyze existing scan results with LLM-powered remediation"""
    
    print_banner(console)
    console.print("[bold cyan]LLM-Powered Vulnerability Analysis[/bold cyan]\n")
    console.print(f"[bold]Scan Results:[/bold] {scan_results}")
    console.print(f"[bold]Codebase:[/bold] {codebase_path}\n")
    
    try:
        import json
        from scanner.llm.remediation import RemediationEngine
        from scanner.detectors.base import Vulnerability, VulnerabilitySeverity
        
        # Load scan results
        console.print("[cyan]Loading scan results...[/cyan]")
        with open(scan_results, 'r') as f:
            data = json.load(f)
        
        # Convert to Vulnerability objects
        vulnerabilities = []
        for vuln_data in data.get('vulnerabilities', []):
            # Reconstruct Vulnerability object with only valid fields
            vuln = Vulnerability(
                vuln_id=vuln_data.get('vuln_id', ''),
                vuln_type=vuln_data.get('vuln_type', ''),
                title=vuln_data.get('title', ''),
                description=vuln_data.get('description', ''),
                severity=VulnerabilitySeverity(vuln_data.get('severity', 'medium')),
                confidence=vuln_data.get('confidence', 0.5),
                file_path=vuln_data.get('file_path', ''),
                line_start=vuln_data.get('line_start', 0),
                line_end=vuln_data.get('line_end'),
                function_name=vuln_data.get('function_name'),
                cwe=vuln_data.get('cwe'),
                evidence=vuln_data.get('evidence', {}),
                remediation=vuln_data.get('remediation', ''),
                impact=vuln_data.get('impact', ''),
                code_snippet=vuln_data.get('code_snippet'),
                detector_name=vuln_data.get('detector_name', 'cli_analyze')
            )
            vulnerabilities.append(vuln)
        
        console.print(f"[green]✓[/green] Loaded {len(vulnerabilities)} vulnerabilities\n")
        
        # Initialize remediation engine
        console.print("[cyan]Initializing LLM remediation engine...[/cyan]")
        engine = RemediationEngine(codebase_path, llm_provider=llm_provider)
        console.print(f"[green]✓[/green] Using {engine.llm_client.config.provider.value} - {engine.llm_client.config.model}\n")
        
        # Analyze vulnerabilities
        console.print("[cyan]Analyzing vulnerabilities with LLM...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Processing {len(vulnerabilities)} vulnerabilities...",
                total=None
            )
            
            analyses = engine.analyze_batch(vulnerabilities)
            progress.update(task, completed=True)
        
        # Get approved fixes
        approved = engine.get_approved_fixes(analyses)
        
        console.print(f"\n[bold green]✓ Analysis Complete![/bold green]")
        console.print(f"  Total Analyzed: {len(vulnerabilities)}")
        console.print(f"  Approved Fixes: {len(approved)}")
        console.print(f"  Needs Review: {len(vulnerabilities) - len(approved)}\n")
        
        # Display approved fixes
        if approved and verbose:
            console.print("[bold]Approved Remediations:[/bold]\n")
            for i, analysis in enumerate(approved, 1):
                console.print(f"[bold]{i}. {analysis.get('vulnerability_type', 'Unknown')}[/bold]")
                console.print(f"   Location: {analysis.get('location', 'Unknown')}")
                console.print(f"   Severity: {analysis.get('severity', 'Unknown').upper()}")
                
                fix = analysis.get('fix', {})
                if fix.get('explanation'):
                    console.print(f"   Fix: {fix['explanation'][:100]}...")
                console.print()
        
        # Generate report
        report = engine.generate_remediation_report(analyses)
        
        # Save report
        if output:
            with open(output, 'w') as f:
                f.write(report)
            console.print(f"[bold cyan]📄 Report saved to:[/bold cyan] {output}")
        else:
            # Print report to console if no output file
            console.print("\n" + "="*60)
            console.print(report)
        
        # Print footer
        print_cybret_footer(console)
        
    except ImportError as e:
        console.print(f"\n[bold red]Error:[/bold red] LLM dependencies not installed.")
        console.print("Run: [cyan]pip install -r requirements-llm.txt[/cyan]")
        if verbose:
            console.print(f"Details: {e}")
        raise click.Abort()
    except FileNotFoundError as e:
        console.print(f"\n[bold red]Error:[/bold red] File not found: {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise click.Abort()


@cli.command()
@click.option(
    "--backup-dir",
    type=click.Path(exists=True),
    default=".scanner-backups",
    help="Backup directory to restore from",
)
@click.option(
    "--timestamp",
    type=str,
    help="Specific backup timestamp to restore (format: YYYYMMDD_HHMMSS)",
)
@click.option(
    "--list",
    "list_backups",
    is_flag=True,
    help="List available backups",
)
def rollback(backup_dir, timestamp, list_backups):
    """Rollback auto-applied fixes from backup"""
    
    from scanner.utils.fix_applier import restore_from_backup, FixApplier
    from pathlib import Path
    
    backup_path = Path(backup_dir)
    
    if list_backups:
        # List available backups
        console.print(f"\n[bold]Available Backups in {backup_dir}:[/bold]\n")
        
        if not backup_path.exists():
            console.print("[red]No backup directory found[/red]")
            return
        
        timestamp_dirs = sorted([d for d in backup_path.iterdir() if d.is_dir()])
        
        if not timestamp_dirs:
            console.print("[yellow]No backups found[/yellow]")
            return
        
        for ts_dir in timestamp_dirs:
            backup_files = list(ts_dir.rglob('*.bak'))
            console.print(f"[cyan]{ts_dir.name}[/cyan] - {len(backup_files)} files")
            
            if len(backup_files) > 0:
                # Show first few files
                for backup_file in backup_files[:3]:
                    relative = backup_file.relative_to(ts_dir)
                    console.print(f"  • {relative.parent / relative.stem}")
                
                if len(backup_files) > 3:
                    console.print(f"  ... and {len(backup_files) - 3} more")
            console.print()
        
        return
    
    # Restore from backup
    console.print("\n[bold yellow]⚠️  Rollback Operation[/bold yellow]")
    console.print("This will restore files from backup, overwriting current changes.\n")
    
    if not click.confirm("Are you sure you want to continue?"):
        console.print("[yellow]Rollback cancelled[/yellow]")
        return
    
    console.print("\n[cyan]Restoring files from backup...[/cyan]")
    
    result = restore_from_backup(backup_dir, timestamp)
    
    if result['success']:
        console.print(f"\n[bold green]✓ Rollback successful![/bold green]")
        console.print(f"  Restored: {result['restored']} files")
        
        if result.get('files'):
            console.print("\n[bold]Restored files:[/bold]")
            for file in result['files'][:10]:
                console.print(f"  • {file}")
            
            if len(result['files']) > 10:
                console.print(f"  ... and {len(result['files']) - 10} more")
    else:
        console.print(f"\n[bold red]✗ Rollback failed[/bold red]")
        console.print(f"  Error: {result.get('error', 'Unknown error')}")
        
        if result.get('errors'):
            console.print("\n[bold]Errors:[/bold]")
            for error in result['errors'][:5]:
                console.print(f"  • {error['file']}: {error['error']}")


if __name__ == "__main__":
    cli()
