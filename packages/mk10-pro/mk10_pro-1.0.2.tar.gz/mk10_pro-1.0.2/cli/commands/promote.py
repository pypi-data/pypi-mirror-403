# SPDX-License-Identifier: MIT
"""Promote command."""

import click
from pathlib import Path
import yaml

from engine.core.errors import StateError
from engine.policy.policy import Policy
from engine.evidence.recorder import EvidenceRecorder


@click.command()
@click.option("--title", required=True, help="Title identifier")
@click.option("--version", required=True, help="Version identifier")
@click.option("--state", required=True, type=click.Choice(["CANDIDATE", "RELEASE", "ARCHIVED"]), help="Target state")
@click.option("--workspace", default=".workspace", help="Workspace directory")
@click.option("--signer", help="Signer identifier")
def promote(title: str, version: str, state: str, workspace: str, signer: str):
    """Promote title/version to new state."""
    workspace_path = Path(workspace)
    evidence_dir = workspace_path / "evidence"
    
    if not evidence_dir.exists():
        click.echo(f"Error: Evidence directory not found: {evidence_dir}", err=True)
        raise click.Abort()
    
    # Load evidence
    recorder = EvidenceRecorder(evidence_dir)
    # In a real implementation, would load events from files
    events = recorder.get_all_events()
    
    # Load policy
    policy_path = Path("engine/policy/policy.py").parent
    policy = Policy(
        rules_file=policy_path / "rules.yaml",
        states_file=policy_path / "states.yaml",
    )
    
    # Determine current state (simplified - would load from MTB)
    current_state = "DRAFT"  # Would be loaded from existing MTB
    
    # Check if transition is allowed
    if not policy.can_transition(current_state, state, events):
        click.echo(f"Error: Transition from {current_state} to {state} not allowed", err=True)
        raise click.Abort()
    
    # Record state transition
    recorder.record_state_transition(
        title=title,
        version=version,
        from_state=current_state,
        to_state=state,
        signer=signer,
    )
    
    click.echo(f"Promoted {title}/{version} from {current_state} to {state}")

