"""CLI commands for wafer targets — live resource management.

These commands always hit provider APIs to show real state.
Registered as: wafer targets list|show|terminate|sync|provision
"""

from __future__ import annotations

from datetime import UTC, datetime

import typer

targets_live_app = typer.Typer(
    name="targets",
    help="""Manage live GPU resources across cloud providers.

Unlike 'wafer specs' (local config files), these commands query provider APIs
to show what's actually running.

  wafer targets list                    # All running resources
  wafer targets list --unbound          # Orphans (no matching spec)
  wafer targets list --provider runpod  # Filter by provider
  wafer targets terminate <resource-id> # Kill a resource
  wafer targets terminate --unbound     # Kill all orphans
  wafer targets sync                    # Refresh bindings
  wafer targets provision <spec-name>   # Provision from a spec
""",
)


@targets_live_app.command("list")
def targets_list(
    provider: str | None = typer.Option(None, "--provider", "-p", help="Filter by provider"),
    pool: str | None = typer.Option(None, "--pool", help="Filter by pool query from config.toml"),
) -> None:
    """List all running GPU resources across providers.

    Queries RunPod and DigitalOcean APIs to show live state.

    Examples:
        wafer targets list
        wafer targets list --provider runpod
        wafer targets list --pool mi300x-rocm7
    """
    import trio
    from wafer_core.targets.providers import get_all_cloud_providers, get_provider
    from wafer_core.targets.types import Target, TargetProvider

    async def _list() -> list[Target]:
        all_targets: list[Target] = []

        if provider:
            prov = get_provider(provider)
            all_targets = await prov.list_targets()
        else:
            providers = get_all_cloud_providers()

            async def _fetch(prov_impl: TargetProvider, results: list[Target]) -> None:
                try:
                    targets = await prov_impl.list_targets()
                    results.extend(targets)
                except Exception as e:
                    typer.echo(
                        f"  Warning: failed to query {type(prov_impl).__name__}: {e}", err=True
                    )

            async with trio.open_nursery() as nursery:
                for _, prov_impl in providers:
                    nursery.start_soon(_fetch, prov_impl, all_targets)

        return all_targets

    all_targets = trio.run(_list)

    # Hydrate targets with cached labels
    from dataclasses import replace
    from wafer_core.targets.state_cache import load_all_labels

    cached_labels = load_all_labels()
    all_targets = [
        replace(t, labels=cached_labels[t.resource_id])
        if t.resource_id in cached_labels
        else t
        for t in all_targets
    ]

    # Apply pool filter if specified
    if pool:
        from wafer_core.targets.pool import load_pool_query, match_targets

        try:
            query = load_pool_query(pool)
        except KeyError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(1) from None

        all_targets = match_targets(query, all_targets)
        typer.echo(f"Pool {pool!r}: {len(all_targets)} matching target(s)\n")

    if not all_targets:
        typer.echo("No running resources found.")
        return

    typer.echo(f"{len(all_targets)} resource(s):\n")
    for target in all_targets:
        _print_target(target)


def _print_target(target: Target) -> None:
    """Print a single target's info."""
    ssh_info = ""
    if target.public_ip and target.ssh_port:
        ssh_info = f"  ssh={target.ssh_username}@{target.public_ip}:{target.ssh_port}"

    name_part = f"  name={target.name}" if target.name else ""
    spec_part = f"  spec={target.spec_name}" if target.spec_name else ""
    price_part = f"  ${target.price_per_hour:.2f}/hr" if target.price_per_hour else ""

    # Show interesting labels (skip 'image' — too long)
    label_keys = sorted(k for k in target.labels if k != "image")
    labels_part = ""
    if label_keys:
        labels_part = "  " + " ".join(f"{k}={target.labels[k]}" for k in label_keys)

    typer.echo(
        f"  {target.resource_id}  [{target.provider}]  "
        f"status={target.status}  gpu={target.gpu_type}"
        f"{spec_part}{name_part}{ssh_info}{price_part}{labels_part}"
    )
    typer.echo()


@targets_live_app.command("terminate")
def targets_terminate(
    resource_id: str | None = typer.Argument(None, help="Resource ID to terminate"),
    pool_name: str | None = typer.Option(
        None, "--pool", help="Terminate all targets matching a pool query"
    ),
    provider_name: str | None = typer.Option(
        None, "--provider", "-p", help="Provider hint (avoids querying all providers)"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Terminate a running resource by ID, or all targets matching a pool query.

    Examples:
        wafer targets terminate tkru24z7npcgth
        wafer targets terminate --pool mi300x --yes
        wafer targets terminate --pool runpod-only --provider runpod
    """
    import trio
    from wafer_core.targets.providers import get_all_cloud_providers, get_provider
    from wafer_core.targets.state_cache import remove_binding

    if pool_name:
        _terminate_pool(pool_name, provider_name, yes)
        return

    if not resource_id:
        typer.echo("Provide a resource ID or use --pool <name>.", err=True)
        raise typer.Exit(1)

    async def _terminate() -> bool:
        if provider_name:
            prov = get_provider(provider_name)
            return await prov.terminate(resource_id)

        for name, prov in get_all_cloud_providers():
            target = await prov.get_target(resource_id)
            if target is not None:
                success = await prov.terminate(resource_id)
                if success:
                    remove_binding(resource_id)
                    typer.echo(f"Terminated {resource_id} ({name})")
                return success

        typer.echo(f"Resource {resource_id} not found on any provider.", err=True)
        return False

    success = trio.run(_terminate)
    if not success:
        raise typer.Exit(1)


def _terminate_pool(pool_name: str, provider_name: str | None, yes: bool) -> None:
    """Terminate all targets matching a pool query."""
    import trio
    from wafer_core.targets.pool import load_pool_query, match_targets
    from wafer_core.targets.providers import get_all_cloud_providers, get_provider
    from wafer_core.targets.state_cache import remove_binding
    from wafer_core.targets.types import Target

    try:
        query = load_pool_query(pool_name)
    except KeyError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    async def _do_terminate() -> int:
        all_targets: list[Target] = []
        if provider_name:
            prov = get_provider(provider_name)
            all_targets = await prov.list_targets()
        else:
            for _, prov in get_all_cloud_providers():
                try:
                    all_targets.extend(await prov.list_targets())
                except Exception:
                    pass

        matched = match_targets(query, all_targets)

        if not matched:
            typer.echo(f"No targets match pool {pool_name!r}.")
            return 0

        typer.echo(f"Found {len(matched)} target(s) matching pool {pool_name!r}:")
        for t in matched:
            name_part = f"  name={t.name}" if t.name else ""
            typer.echo(f"  {t.resource_id}  [{t.provider}]  gpu={t.gpu_type}{name_part}")

        if not yes:
            confirm = typer.confirm("Terminate all?")
            if not confirm:
                return 0

        count = 0
        for t in matched:
            prov = get_provider(t.provider)
            if await prov.terminate(t.resource_id):
                remove_binding(t.resource_id)
                typer.echo(f"  Terminated {t.resource_id}")
                count += 1
            else:
                typer.echo(f"  Failed to terminate {t.resource_id}", err=True)

        return count

    count = trio.run(_do_terminate)
    typer.echo(f"\nTerminated {count} resource(s).")


@targets_live_app.command("reconcile")
def targets_reconcile() -> None:
    """Refresh local binding cache from provider APIs.

    Queries all cloud providers, matches resources to specs, and updates
    the local state cache. Reports any drift.

    Example:
        wafer targets reconcile
    """
    import trio
    from wafer_core.targets.providers import get_all_cloud_providers
    from wafer_core.targets.reconcile import reconcile
    from wafer_core.targets.spec_store import load_all_specs
    from wafer_core.targets.state_cache import (
        BindingEntry,
        get_binding_hints,
        save_bindings,
    )
    from wafer_core.targets.types import Target

    async def _sync() -> None:
        specs = load_all_specs()

        all_targets: list[Target] = []
        for name, prov in get_all_cloud_providers():
            typer.echo(f"Querying {name}...")
            try:
                targets = await prov.list_targets()
                typer.echo(f"  Found {len(targets)} resource(s)")
                all_targets.extend(targets)
            except Exception as e:
                typer.echo(f"  Failed: {e}", err=True)

        hints = get_binding_hints()
        result = reconcile(specs, all_targets, binding_hints=hints)

        # Update binding cache with bound results
        new_bindings = {}
        now = datetime.now(UTC).isoformat()
        for spec, target in result.bound:
            new_bindings[target.resource_id] = BindingEntry(
                spec_name=spec.name,
                provider=target.provider,
                bound_at=now,
            )
        save_bindings(new_bindings)

        typer.echo("\nSync complete:")
        typer.echo(f"  Total resources: {len(all_targets)}")
        typer.echo(f"  Matched to specs: {len(result.bound)}")
        typer.echo(f"  No matching spec: {len(result.unbound)}")

    trio.run(_sync)


@targets_live_app.command("provision")
def targets_provision(
    spec_name: str = typer.Argument(..., help="Spec name to provision from"),
) -> None:
    """Explicitly provision a resource from a spec.

    Creates a new cloud resource and binds it to the spec.

    Example:
        wafer targets provision runpod-mi300x
    """
    import trio
    from wafer_core.targets.providers import get_provider
    from wafer_core.targets.spec_store import load_spec
    from wafer_core.targets.state_cache import BindingEntry, add_binding
    from wafer_core.utils.kernel_utils.targets.config import (
        DigitalOceanTarget,
        RunPodTarget,
    )

    try:
        spec = load_spec(spec_name)
    except FileNotFoundError:
        typer.echo(f"Spec not found: {spec_name}", err=True)
        raise typer.Exit(1) from None

    if isinstance(spec, RunPodTarget):
        provider_name = "runpod"
    elif isinstance(spec, DigitalOceanTarget):
        provider_name = "digitalocean"
    else:
        typer.echo(f"Spec type {type(spec).__name__} cannot be provisioned.", err=True)
        raise typer.Exit(1) from None

    async def _provision() -> None:
        from wafer_core.targets.probe import probe_target_labels
        from wafer_core.targets.state_cache import save_labels

        prov = get_provider(provider_name)
        typer.echo(f"Provisioning {spec_name} via {provider_name}...")
        target = await prov.provision(spec)

        # Cache the binding
        add_binding(
            target.resource_id,
            BindingEntry(
                spec_name=spec_name,
                provider=provider_name,
                bound_at=datetime.now(UTC).isoformat(),
            ),
        )

        typer.echo(f"\nProvisioned: {target.resource_id}")
        if target.public_ip:
            typer.echo(f"  SSH: {target.ssh_username}@{target.public_ip}:{target.ssh_port}")

        # Probe software labels (sync — runs subprocess ssh)
        if target.public_ip and target.ssh_port:
            typer.echo("  Probing software versions...")
            try:
                ssh_key = spec.ssh_key if hasattr(spec, "ssh_key") else None
                labels = probe_target_labels(
                    host=target.public_ip,
                    port=target.ssh_port,
                    username=target.ssh_username,
                    ssh_key_path=ssh_key,
                )
                save_labels(target.resource_id, labels)
                if labels:
                    typer.echo(f"  Labels: {' '.join(f'{k}={v}' for k, v in sorted(labels.items()))}")
            except Exception as e:
                typer.echo(f"  Warning: probe failed: {e}", err=True)

    trio.run(_provision)


@targets_live_app.command("pools")
def targets_pools() -> None:
    """List configured pool queries from config.toml.

    Example:
        wafer targets pools
    """
    from wafer_core.targets.pool import list_pool_names, load_pool_query

    names = list_pool_names()
    if not names:
        typer.echo("No pools configured in ~/.wafer/config.toml.")
        typer.echo("\nAdd a pool:\n")
        typer.echo("  [pools.mi300x]")
        typer.echo('  gpu_type = "MI300X"')
        typer.echo("")
        typer.echo("  [pools.mi300x-rocm7]")
        typer.echo('  gpu_type = "MI300X"')
        typer.echo("  [pools.mi300x-rocm7.labels]")
        typer.echo('  rocm_version = "7.0.2"')
        return

    typer.echo(f"{len(names)} pool(s):\n")
    for name in names:
        query = load_pool_query(name)
        parts = []
        if query.gpu_type:
            parts.append(f"gpu_type={query.gpu_type}")
        if query.provider:
            parts.append(f"provider={query.provider}")
        if query.status and query.status != "running":
            parts.append(f"status={query.status}")
        for k, v in sorted(query.labels.items()):
            parts.append(f"{k}={v}")
        criteria = "  ".join(parts) if parts else "(match all)"
        typer.echo(f"  {name}:  {criteria}")


@targets_live_app.command("probe")
def targets_probe(
    resource_id: str = typer.Argument(..., help="Resource ID to probe"),
    provider_name: str | None = typer.Option(
        None, "--provider", "-p", help="Provider hint (avoids querying all providers)"
    ),
) -> None:
    """Probe a running target's software versions via SSH.

    Results are cached in ~/.wafer/target_state.json and shown
    by wafer targets list. Used for targets not provisioned by wafer
    (e.g. dashboard-created pods).

    Examples:
        wafer targets probe ewfo5ckpxlg7y2
        wafer targets probe 543538453 --provider digitalocean
    """
    import trio
    from wafer_core.targets.probe import probe_target_labels
    from wafer_core.targets.providers import get_all_cloud_providers, get_provider
    from wafer_core.targets.state_cache import save_labels

    # Find the target (async — needs provider API)
    async def _find_target():
        if provider_name:
            prov = get_provider(provider_name)
            return await prov.get_target(resource_id)

        for _, prov in get_all_cloud_providers():
            target = await prov.get_target(resource_id)
            if target is not None:
                return target
        return None

    target = trio.run(_find_target)

    if target is None:
        typer.echo(f"Resource {resource_id} not found.", err=True)
        raise typer.Exit(1)

    if not target.public_ip or not target.ssh_port:
        typer.echo(f"Resource {resource_id} has no SSH info (status={target.status}).", err=True)
        raise typer.Exit(1)

    typer.echo(f"Probing {resource_id} ({target.ssh_username}@{target.public_ip}:{target.ssh_port})...")

    labels = probe_target_labels(
        host=target.public_ip,
        port=target.ssh_port,
        username=target.ssh_username,
    )

    save_labels(resource_id, labels)

    if labels:
        typer.echo(f"Labels cached for {resource_id}:")
        for k, v in sorted(labels.items()):
            typer.echo(f"  {k}={v}")
    else:
        typer.echo("Probe returned no labels.")
