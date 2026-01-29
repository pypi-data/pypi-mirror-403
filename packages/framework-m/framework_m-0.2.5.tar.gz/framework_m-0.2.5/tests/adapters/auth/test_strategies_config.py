"""Tests for AuthChain configuration via framework_config.toml."""

from unittest.mock import patch


class TestCreateAuthChainFromConfig:
    """Tests for create_auth_chain_from_config function."""

    def test_import_create_auth_chain_from_config(self) -> None:
        """create_auth_chain_from_config should be importable."""
        from framework_m.adapters.auth.strategies import create_auth_chain_from_config

        assert create_auth_chain_from_config is not None

    def test_default_strategies_when_no_config(self) -> None:
        """Should use default strategies when no auth config exists."""
        from framework_m.adapters.auth.strategies import create_auth_chain_from_config

        with patch(
            "framework_m.cli.config.load_config",
            return_value={},
        ):
            chain = create_auth_chain_from_config(jwt_secret="test-secret")

        # Should have default strategies (bearer, header - no api_key since no lookup)
        assert len(chain._strategies) == 2

    def test_configures_strategy_order(self) -> None:
        """Should order strategies according to config."""
        from framework_m.adapters.auth.strategies import (
            ApiKeyAuth,
            BearerTokenAuth,
            HeaderAuth,
            create_auth_chain_from_config,
        )

        config = {
            "auth": {
                "strategies": ["api_key", "bearer", "header"],
            }
        }

        with patch(
            "framework_m.cli.config.load_config",
            return_value=config,
        ):
            chain = create_auth_chain_from_config(
                jwt_secret="test-secret",
                api_key_lookup=lambda k: None,  # type: ignore[return-value,arg-type]
            )

        # Verify order
        assert isinstance(chain._strategies[0], ApiKeyAuth)
        assert isinstance(chain._strategies[1], BearerTokenAuth)
        assert isinstance(chain._strategies[2], HeaderAuth)

    def test_excludes_disabled_strategies(self) -> None:
        """Should exclude strategies not in config."""
        from framework_m.adapters.auth.strategies import (
            BearerTokenAuth,
            create_auth_chain_from_config,
        )

        config = {
            "auth": {
                "strategies": ["bearer"],  # Only bearer
            }
        }

        with patch(
            "framework_m.cli.config.load_config",
            return_value=config,
        ):
            chain = create_auth_chain_from_config(jwt_secret="test-secret")

        assert len(chain._strategies) == 1
        assert isinstance(chain._strategies[0], BearerTokenAuth)

    def test_ignores_unknown_strategies(self) -> None:
        """Should ignore unknown strategy names."""
        from framework_m.adapters.auth.strategies import create_auth_chain_from_config

        config = {
            "auth": {
                "strategies": ["bearer", "unknown_strategy", "header"],
            }
        }

        with patch(
            "framework_m.cli.config.load_config",
            return_value=config,
        ):
            chain = create_auth_chain_from_config(jwt_secret="test-secret")

        # Should have 2 strategies (unknown ignored)
        assert len(chain._strategies) == 2
