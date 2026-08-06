"""Tests for FTSIndex.resolve_relative_link_targets().

Docs-site vaults author markdown links for the rendered route rather than
the file tree: extensionless targets, folder targets, and site-absolute
routes with numeric ordering prefixes stripped.  The resolution pass runs
inside ``build_index()`` / ``reindex()`` alongside the wikilink pass.
"""

from __future__ import annotations

from pathlib import Path

from markdown_vault_mcp.vault import Vault


class TestResolveRelativeLinkTargets:
    """Vault-level integration tests mirroring TestResolveVaultWikilinks."""

    def test_extensionless_link_resolves(self, tmp_path: Path) -> None:
        """[x](./04.task-model) resolves to 04.task-model.md next door."""
        vault = tmp_path / "vault"
        (vault / "docs").mkdir(parents=True)
        (vault / "docs" / "guide.md").write_text(
            "# Guide\n\nSee [task model](./04.task-model).\n", encoding="utf-8"
        )
        (vault / "docs" / "04.task-model.md").write_text(
            "# Task model\n", encoding="utf-8"
        )

        col = Vault(source_dir=vault)
        col.index.build_index()

        outlinks = col.graph.get_outlinks("docs/guide.md")
        assert len(outlinks) == 1
        assert outlinks[0].target_path == "docs/04.task-model.md"
        assert outlinks[0].exists is True
        assert col.graph.get_broken_links() == []

    def test_folder_link_resolves_to_index(self, tmp_path: Path) -> None:
        """[x](../agents) and [x](../agents/) resolve to agents/index.md."""
        vault = tmp_path / "vault"
        (vault / "docs").mkdir(parents=True)
        (vault / "agents").mkdir()
        (vault / "docs" / "guide.md").write_text(
            "# Guide\n\nSee [agents](../agents) and [again](../agents/).\n",
            encoding="utf-8",
        )
        (vault / "agents" / "index.md").write_text("# Agents\n", encoding="utf-8")

        col = Vault(source_dir=vault)
        col.index.build_index()

        outlinks = col.graph.get_outlinks("docs/guide.md")
        assert len(outlinks) == 2
        for link in outlinks:
            assert link.target_path == "agents/index.md"
            assert link.exists is True
        assert col.graph.get_broken_links() == []

    def test_site_absolute_route_resolves(self, tmp_path: Path) -> None:
        """[x](/services/vault) matches 07.services/vault/index.md by route."""
        vault = tmp_path / "vault"
        (vault / "docs").mkdir(parents=True)
        (vault / "07.services" / "vault").mkdir(parents=True)
        (vault / "docs" / "guide.md").write_text(
            "# Guide\n\nSee [service](/services/vault).\n", encoding="utf-8"
        )
        (vault / "07.services" / "vault" / "index.md").write_text(
            "# Vault service\n", encoding="utf-8"
        )

        col = Vault(source_dir=vault)
        col.index.build_index()

        outlinks = col.graph.get_outlinks("docs/guide.md")
        assert len(outlinks) == 1
        assert outlinks[0].target_path == "07.services/vault/index.md"
        assert outlinks[0].exists is True
        assert col.graph.get_broken_links() == []

    def test_site_absolute_route_matches_plain_file(self, tmp_path: Path) -> None:
        """[x](/ai-office/architecture/sync) matches 00.ai-office/01.architecture/sync.md."""
        vault = tmp_path / "vault"
        (vault / "docs").mkdir(parents=True)
        (vault / "00.ai-office" / "01.architecture").mkdir(parents=True)
        (vault / "docs" / "guide.md").write_text(
            "# Guide\n\nSee [sync](/ai-office/architecture/sync).\n",
            encoding="utf-8",
        )
        (vault / "00.ai-office" / "01.architecture" / "sync.md").write_text(
            "# Sync\n", encoding="utf-8"
        )

        col = Vault(source_dir=vault)
        col.index.build_index()

        outlinks = col.graph.get_outlinks("docs/guide.md")
        assert len(outlinks) == 1
        assert outlinks[0].target_path == "00.ai-office/01.architecture/sync.md"
        assert outlinks[0].exists is True

    def test_genuinely_broken_stays_broken(self, tmp_path: Path) -> None:
        """A target that matches nothing is reported broken, not guessed."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "guide.md").write_text(
            "# Guide\n\nSee [gone](./no-such-page).\n", encoding="utf-8"
        )

        col = Vault(source_dir=vault)
        col.index.build_index()

        broken = col.graph.get_broken_links()
        assert len(broken) == 1
        assert broken[0].raw_target == "./no-such-page"

    def test_working_md_link_untouched(self, tmp_path: Path) -> None:
        """An already-correct [x](target.md) link is never rewritten."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "guide.md").write_text(
            "# Guide\n\nSee [ok](./target.md).\n", encoding="utf-8"
        )
        (vault / "target.md").write_text("# Target\n", encoding="utf-8")

        col = Vault(source_dir=vault)
        col.index.build_index()

        outlinks = col.graph.get_outlinks("guide.md")
        assert len(outlinks) == 1
        assert outlinks[0].target_path == "target.md"
        assert outlinks[0].exists is True

    def test_md_file_preferred_over_route_match(self, tmp_path: Path) -> None:
        """Extensionless sibling wins over a same-route document elsewhere."""
        vault = tmp_path / "vault"
        (vault / "docs").mkdir(parents=True)
        (vault / "docs" / "guide.md").write_text(
            "# Guide\n\nSee [page](./page).\n", encoding="utf-8"
        )
        (vault / "docs" / "page.md").write_text("# Page\n", encoding="utf-8")

        col = Vault(source_dir=vault)
        col.index.build_index()

        outlinks = col.graph.get_outlinks("docs/guide.md")
        assert outlinks[0].target_path == "docs/page.md"
        assert outlinks[0].exists is True

    def test_relative_route_matches_numeric_prefixed_file(
        self, tmp_path: Path
    ) -> None:
        """[x](../01.about/regulations) matches 02.company/01.about/06.regulations.md."""
        vault = tmp_path / "vault"
        (vault / "02.company" / "02.agents").mkdir(parents=True)
        (vault / "02.company" / "01.about").mkdir()
        (vault / "02.company" / "02.agents" / "AGENTS.md").write_text(
            "# Agents\n\nSee [regulations](../01.about/regulations).\n",
            encoding="utf-8",
        )
        (vault / "02.company" / "01.about" / "06.regulations.md").write_text(
            "# Regulations\n", encoding="utf-8"
        )

        col = Vault(source_dir=vault)
        col.index.build_index()

        outlinks = col.graph.get_outlinks("02.company/02.agents/AGENTS.md")
        assert len(outlinks) == 1
        assert outlinks[0].target_path == "02.company/01.about/06.regulations.md"
        assert outlinks[0].exists is True
        assert col.graph.get_broken_links() == []

    def test_percent_encoded_link_resolves(self, tmp_path: Path) -> None:
        """[x](2%3D%3D%3DClient%20co/index.md) resolves to '2===Client co/index.md'."""
        vault = tmp_path / "vault"
        (vault / "2===Client co").mkdir(parents=True)
        (vault / "guide.md").write_text(
            "# Guide\n\nSee [client](./2%3D%3D%3DClient%20co/index.md).\n",
            encoding="utf-8",
        )
        (vault / "2===Client co" / "index.md").write_text(
            "# Client\n", encoding="utf-8"
        )

        col = Vault(source_dir=vault)
        col.index.build_index()

        outlinks = col.graph.get_outlinks("guide.md")
        assert len(outlinks) == 1
        assert outlinks[0].target_path == "2===Client co/index.md"
        assert outlinks[0].exists is True
        assert col.graph.get_broken_links() == []

    def test_reindex_keeps_resolution(self, tmp_path: Path) -> None:
        """Resolution survives an incremental reindex() run."""
        vault = tmp_path / "vault"
        (vault / "docs").mkdir(parents=True)
        (vault / "docs" / "guide.md").write_text(
            "# Guide\n\nSee [task model](./04.task-model).\n", encoding="utf-8"
        )
        (vault / "docs" / "04.task-model.md").write_text(
            "# Task model\n", encoding="utf-8"
        )

        col = Vault(source_dir=vault)
        col.index.build_index()

        # Touch the source file and reindex incrementally.
        (vault / "docs" / "guide.md").write_text(
            "# Guide v2\n\nSee [task model](./04.task-model).\n", encoding="utf-8"
        )
        col.index.reindex()

        outlinks = col.graph.get_outlinks("docs/guide.md")
        assert len(outlinks) == 1
        assert outlinks[0].target_path == "docs/04.task-model.md"
        assert outlinks[0].exists is True
        assert col.graph.get_broken_links() == []
